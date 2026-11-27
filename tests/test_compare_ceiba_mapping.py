import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "compare_ceiba_mapping.py"
CURATION_COLUMNS = ("resource", "kind", "field", "value", "note")


def write_csv(path, columns, rows=()):
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(columns)
        writer.writerows(rows)


def field(name, value, type_class="primitive", multiple=False):
    return {"typeName": name, "value": value, "typeClass": type_class, "multiple": multiple}


def write_record(root, resource, blocks, *, subdir="metadata", indent=None, sort_keys=False, **additional):
    record = {
        "metadataLanguage": "es",
        "datasetVersion": {"metadataBlocks": {
            name: {"name": name, "fields": fields} for name, fields in blocks.items()
        }},
        **additional,
    }
    path = root / subdir / f"{resource}-1.0.json"
    path.write_text(json.dumps(record, indent=indent, sort_keys=sort_keys), encoding="utf-8")
    return path


@pytest.fixture
def snapshots(tmp_path):
    baseline, current, output = (tmp_path / part for part in ("baseline", "current", "report"))
    for root in (baseline, current):
        (root / "metadata").mkdir(parents=True)
        write_csv(root / "load_plan.csv", ("resource", "release"))
        write_csv(root / "version_dates.csv", ("source_id", "release_time"))
        write_csv(root / "curation.csv", CURATION_COLUMNS)
        (root / "mapping_problems.json").write_text("{}", encoding="utf-8")
    return baseline, current, output


def run_compare(snapshots, *options):
    return subprocess.run(
        [sys.executable, "-I", "-S", "-B", str(SCRIPT), *map(str, snapshots), *options],
        capture_output=True,
        text=True,
        check=False,
    )


def read_report(output, filename="summary.json"):
    return json.loads((output / filename).read_text(encoding="utf-8"))


def test_registros_identicos_y_diferencias_de_formato(snapshots):
    baseline, current, output = snapshots
    fields = [field("title", "Título ficticio"), field("distributionDate", "2024-02-29")]
    for root in (baseline, current):
        write_record(root, "ficticio-identico", {"citation": fields})
    before = write_record(baseline, "ficticio-formato", {"citation": fields})
    after = write_record(current, "ficticio-formato", {"citation": fields}, indent=4, sort_keys=True)
    assert before.read_bytes() != after.read_bytes()
    write_record(baseline, "ficticio-orden", {"citation": fields})
    write_record(current, "ficticio-orden", {"citation": fields[::-1]})

    result = run_compare(snapshots)

    assert result.returncode == 0, result.stderr
    summary = read_report(output)
    assert summary["status"] == "complete"
    records = summary["records"]
    assert (records["baseline"], records["current"], records["identical"], records["modified"]) == (3, 3, 3, 0)
    assert records["fields"] == {}
    assert "ficticio-" not in result.stdout + result.stderr
    assert not (output / "details.json").exists()


def test_cambios_en_fechas_sencillas_y_compuestas(snapshots):
    baseline, current, output = snapshots
    text = field("dsDescriptionValue", "Descripción ficticia")
    old_description = field("dsDescription", [{
        "dsDescriptionValue": text, "dsDescriptionDate": field("dsDescriptionDate", "2024-02-30"),
    }], "compound", True)
    new_description = field("dsDescription", [{"dsDescriptionValue": text}], "compound", True)
    write_record(baseline, "ficticio-fecha", {"citation": [
        field("distributionDate", "2024-02-29"), old_description,
    ]})
    write_record(current, "ficticio-fecha", {"citation": [
        field("distributionDate", "2024-03-01"), new_description,
    ]})

    result = run_compare(snapshots, "--detailed")

    assert result.returncode == 0, result.stderr
    records = read_report(output)["records"]
    assert records["modified"] == 1
    assert records["blocks"]["citation"]["modified"] == 1
    assert records["fields"]["citation"]["distributionDate"]["modified"] == 1
    assert records["fields"]["citation"]["dsDescription"]["modified"] == 1
    assert records["subfields"]["citation"]["dsDescription"]["dsDescriptionDate"]["removed"] == 1
    assert records["date_path_changes"] == {"added": 0, "removed": 1, "modified": 1}
    assert records["resources_with_other_changes"] == 0
    changes = read_report(output, "details.json")["records"]["modified"]["ficticio-fecha"]
    [modified] = [change for change in changes if change["operation"] == "modified"]
    assert modified["baseline"] == "2024-02-29"
    assert modified["current"] == "2024-03-01"
    assert all(change["date_path"] for change in changes)
    assert "2024-03-01" not in result.stdout + result.stderr


def test_recursos_exclusivos_y_cambios_inesperados(snapshots):
    baseline, current, output = snapshots
    write_record(baseline, "ficticio-ausente", {})
    write_record(current, "ficticio-nuevo", {})
    write_record(baseline, "ficticio-cambiante", {
        "citation": [field("title", "Título anterior"), field("distributionDate", "2024-02-30")],
        "geospatial": [field("geographicCoverageDescription", "Lugar ficticio")],
    }, inventory_data={"marca": False})
    write_record(current, "ficticio-cambiante", {
        "citation": [field("title", "Título actualizado"), field("notesText", "Nota ficticia")],
        "custom": [field("addedField", "Valor ficticio")],
    }, inventory_data={"marca": 0})

    result = run_compare(snapshots, "--detailed")

    assert result.returncode == 0, result.stderr
    records = read_report(output)["records"]
    assert (records["only_baseline"], records["only_current"], records["modified"]) == (1, 1, 1)
    assert records["blocks"]["geospatial"]["removed"] == 1
    assert records["blocks"]["custom"]["added"] == 1
    assert records["fields"]["geospatial"]["geographicCoverageDescription"]["removed"] == 1
    assert records["fields"]["citation"]["distributionDate"]["removed"] == 1
    assert records["fields"]["citation"]["notesText"]["added"] == 1
    assert records["date_path_changes"]["removed"] == 1
    assert records["other_changes"] == {"added": 3, "removed": 2, "modified": 2}
    assert records["resources_with_other_changes"] == 1
    details = read_report(output, "details.json")["records"]
    assert details["only_baseline"] == ["ficticio-ausente"]
    assert details["only_current"] == ["ficticio-nuevo"]
    assert "ficticio-" not in result.stdout + result.stderr


def test_curacion_y_reportes_con_duplicados(snapshots):
    baseline, current, output = snapshots
    old = ("ficticio-uno", "date", "simpleCalendarDate", "2024-02-30", "Nota anterior")
    new = ("ficticio-dos", "restricted_until", "restrictedUntil", "2024-04-31", "Nota nueva")
    same = ("ficticio-tres", "date", "initialCalendarDate", "2024-04-31", "Nota común")
    edited = (*old[:-1], "Nota editada")
    write_csv(baseline / "curation.csv", CURATION_COLUMNS, [old, same, old, old])
    write_csv(current / "curation.csv", CURATION_COLUMNS[::-1], [row[::-1] for row in (new, old, same, new, edited)])
    write_csv(baseline / "load_plan.csv", ("resource", "release"), [("ficticio-uno", "yes")] * 2)
    write_csv(current / "load_plan.csv", ("release", "resource"), [("yes", "ficticio-uno")])
    write_csv(baseline / "version_dates.csv", ("source_id", "release_time"), [("ficticio-uno", "2024-01-01")])
    write_csv(current / "version_dates.csv", ("source_id", "release_time"), [("ficticio-uno", "2024-01-02")])
    (baseline / "mapping_problems.json").write_text('{"ficticio-uno":["A","B","A"]}', encoding="utf-8")
    (current / "mapping_problems.json").write_text('{"ficticio-uno":["B","A"], "ficticio-dos":["C"]}', encoding="utf-8")

    result = run_compare(snapshots, "--detailed")

    assert result.returncode == 0, result.stderr
    reports = read_report(output)["reports"]
    curation = reports["curation.csv"]
    assert (curation["baseline"], curation["current"], curation["identical"]) == (4, 5, 2)
    assert (curation["added"], curation["removed"], curation["resources_affected"]) == (3, 2, 2)
    assert curation["columns_changed"] is False
    assert curation["by_category"]["date"] == {"baseline": 4, "current": 3, "added": 1, "removed": 2}
    assert curation["by_field"]["restrictedUntil"] == {"baseline": 0, "current": 2, "added": 2, "removed": 0}
    assert (reports["load_plan.csv"]["identical"], reports["load_plan.csv"]["removed"]) == (1, 1)
    assert (reports["version_dates.csv"]["added"], reports["version_dates.csv"]["removed"]) == (1, 1)
    problems = reports["mapping_problems.json"]
    assert (problems["identical"], problems["added"], problems["removed"], problems["resources_affected"]) == (2, 1, 1, 2)
    details = read_report(output, "details.json")["reports"]["curation.csv"]
    assert details["removed"][0]["count"] == 2
    assert sorted(item["count"] for item in details["added"]) == [1, 2]
    assert "ficticio-" not in (output / "summary.json").read_text(encoding="utf-8")


def test_archivos_ausentes_y_json_invalidos_sin_exponer_datos(snapshots):
    baseline, current, output = snapshots
    identifier = "recurso-privado-ficticio"
    write_record(baseline, identifier, {})
    corrupt = current / "metadata" / f"{identifier}-1.0.json"
    corrupt.write_text('{"persona":"Persona Ficticia","email":"persona@example.test"', encoding="utf-8")
    (current / "load_plan.csv").unlink()
    (baseline / "mapping_problems.json").write_text('{"otro-privado":NaN}', encoding="utf-8")

    result = run_compare(snapshots)

    assert result.returncode == 2
    summary = read_report(output)
    assert summary["status"] == "incomplete"
    records = summary["records"]
    assert records["issues"] == {"current": {"invalid_json": 1}}
    assert records["not_compared"] == 1
    assert (records["only_baseline"], records["only_current"], records["modified"]) == (0, 0, 0)
    assert summary["reports"]["load_plan.csv"] == {"status": "unavailable", "issues": {"current": "missing"}}
    assert summary["reports"]["mapping_problems.json"]["issues"] == {"baseline": "invalid_json"}
    visible = result.stdout + result.stderr + (output / "summary.json").read_text(encoding="utf-8")
    for sensitive in (identifier, "Persona Ficticia", "persona@example.test", "otro-privado"):
        assert sensitive not in visible


def test_formato_plano_y_listas_ordenadas(snapshots):
    baseline, current, output = snapshots
    write_record(baseline, "ficticio-lista", {"citation": [field("subject", ["Uno", "Dos", "Dos"])]}, subdir=".")
    write_record(current, "ficticio-lista", {"citation": [field("subject", ["Dos", "Uno", "Dos"])]}, subdir=".")

    result = run_compare(snapshots, "--metadata-subdir", ".")

    assert result.returncode == 0, result.stderr
    records = read_report(output)["records"]
    assert records["modified"] == 1
    assert records["fields"]["citation"]["subject"]["modified"] == 1


def test_detalle_local_y_salida_agregada_ante_cambios_de_contacto(snapshots):
    baseline, current, output = snapshots
    resource = "ficticio-con-contacto"
    old_email, new_email = "antes@example.test", "despues@example.test"
    for root, email in ((baseline, old_email), (current, new_email)):
        contact = field("datasetContact", [{
            "datasetContactName": field("datasetContactName", "Persona Ficticia"),
            "datasetContactEmail": field("datasetContactEmail", email),
        }], "compound", True)
        write_record(root, resource, {"citation": [contact]})

    result = run_compare(snapshots, "--detailed")

    assert result.returncode == 0, result.stderr
    records = read_report(output)["records"]
    assert records["resources_with_other_changes"] == 1
    assert records["subfields"]["citation"]["datasetContact"]["datasetContactEmail"]["modified"] == 1
    visible = result.stdout + result.stderr + (output / "summary.json").read_text(encoding="utf-8")
    for sensitive in (resource, old_email, new_email, "Persona Ficticia"):
        assert sensitive not in visible
    [change] = read_report(output, "details.json")["records"]["modified"][resource]
    assert (change["baseline"], change["current"]) == (old_email, new_email)
    assert (output / "details.json").stat().st_mode & 0o077 == 0


def test_directorio_de_metadatos_ausente_no_equivale_a_cero_registros(snapshots):
    baseline, current, output = snapshots
    write_record(baseline, "ficticio-registro", {})
    (current / "metadata").rmdir()

    result = run_compare(snapshots)

    assert result.returncode == 2
    assert read_report(output)["records"] == {
        "status": "unavailable", "issues": {"current": "metadata_directory_unavailable"},
    }


def test_salida_protege_entradas_y_reportes_existentes(snapshots):
    baseline, current, output = snapshots
    original = write_record(baseline, "ficticio-original", {})
    content = original.read_bytes()

    inside = run_compare((baseline, current, baseline / "nuevo-reporte"), "--detailed")
    assert inside.returncode == 2
    assert not (baseline / "nuevo-reporte").exists()
    assert original.read_bytes() == content

    output.mkdir()
    report = output / "summary.json"
    report.write_text("contenido previo", encoding="utf-8")
    repeated = run_compare(snapshots, "--detailed")
    assert repeated.returncode == 2
    assert report.read_text(encoding="utf-8") == "contenido previo"
    assert not (output / "details.json").exists()
