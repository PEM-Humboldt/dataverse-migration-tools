"""Pruebas sintéticas de la asociación del inventario biológico en CEIBA."""

import logging
import sys
from copy import deepcopy
from pathlib import Path
from types import ModuleType, SimpleNamespace

import pytest
from openpyxl import Workbook


@pytest.fixture
def isolated_imports(monkeypatch):
    """Sustituye la configuración y el logger antes de importar la ingesta."""
    config_module = ModuleType("src.config")
    config_module.Config = lambda: SimpleNamespace(
        ceiba_data_dir="salida-sintetica", metadata_dir="metadata"
    )
    logger_module = ModuleType("src.utilitarios.logger")
    logger_module.logger = logging.getLogger("tests.ceiba.inventory")
    monkeypatch.setitem(sys.modules, "src.config", config_module)
    monkeypatch.setitem(sys.modules, "src.utilitarios.logger", logger_module)


@pytest.fixture
def inventory_format(isolated_imports):
    from src.formato import ceiba_format

    return ceiba_format


@pytest.fixture
def inventory_workbook(tmp_path):
    """Crea un libro temporal con las tres hojas mínimas del inventario."""
    def create_workbook(biological, macro=(), general=()):
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "Biológico"
        sheet.append(["URL CEIBA", "Proyecto", "Proyecto Macro"])
        for row in biological:
            sheet.append(row)

        sheet = workbook.create_sheet("Proyectos Macro")
        sheet.append(["NO. PROYECTO", "NOMBRE DIEGO", "SUSCRITO"])
        for row in macro:
            sheet.append(row)

        sheet = workbook.create_sheet("GENERAL")
        sheet.append(["ENLACE", "ACCIÓN", "MES", "AÑO"])
        for row in general:
            sheet.append(row)

        path = tmp_path / "inventario-sintetico.xlsx"
        workbook.save(path)
        return path

    return create_workbook


@pytest.mark.parametrize(
    ("inventory_identifier", "ceiba_identifier", "outcome"),
    [
        pytest.param("muestra-a", "muestra-a", "exact", id="exact"),
        pytest.param("MUESTRA-A", "muestra-a", "normalized", id="case"),
        pytest.param("mues tra-a ", "muestra-a", "normalized", id="spaces"),
        pytest.param(" Mues TRA-A", "muestra-a", "normalized", id="spaces-and-case"),
        pytest.param("mues\ttra-\u00a0a", "muestra-a", "normalized", id="other-whitespace"),
        pytest.param("muestra-a", "muestra-b", "missing", id="no-match"),
        pytest.param(" \t", "\u00a0", "missing", id="empty-normalized-keys"),
        pytest.param("muestra-a", "muestra_a", "missing", id="punctuation-is-significant"),
        pytest.param("árbol-a", "arbol-a", "missing", id="accents-are-significant"),
        pytest.param("ÁR BOL-A", "árbol-a", "normalized", id="accent-preserved-when-lowercasing"),
        pytest.param("muestra%20a", "muestra a", "missing", id="url-sequences-not-decoded"),
    ],
)
def test_resolves_only_exact_or_normalized_matches(
    inventory_format, inventory_identifier, ceiba_identifier, outcome
):
    row = {"proyecto": "Proyecto ficticio"}
    index = {"biologico": {inventory_identifier: row}}

    view, counts = inventory_format.resolve_ceiba_inventory(
        index, [ceiba_identifier], [inventory_identifier]
    )

    assert {kind: count for kind, count in counts.items() if count} == {outcome: 1}
    assert view["biologico"].get(ceiba_identifier) == (None if outcome == "missing" else row)


@pytest.mark.parametrize(
    ("biological_ids", "ceiba_ids", "expected_counts"),
    [
        pytest.param(
            ["MUESTRA-A", "mues tra-a"], ["muestra-a"],
            {"ambiguous_inventory": 1}, id="distinct-inventory-keys",
        ),
        pytest.param(
            ["MUESTRA-A"], ["muestra-a", "mues tra-a"],
            {"ambiguous_ceiba": 2}, id="ceiba-identifiers",
        ),
        pytest.param(
            ["MUESTRA-A", "Muestra -A"], ["muestra-a", "mues tra-a"],
            {"ambiguous_inventory": 2, "ambiguous_ceiba": 2}, id="both-sides",
        ),
    ],
)
def test_rejects_ambiguous_fallbacks(inventory_format, biological_ids, ceiba_ids, expected_counts):
    index = {"biologico": {name: {"proyecto": name} for name in biological_ids}}

    view, counts = inventory_format.resolve_ceiba_inventory(index, ceiba_ids, biological_ids)

    assert view == index
    assert {kind: count for kind, count in counts.items() if count} == expected_counts


def test_preserves_exact_matches_even_when_both_normalized_groups_collide(inventory_format):
    biological = {"muestra-a": {"proyecto": "Exacto"}, "MUESTRA-A": {"proyecto": "Otra fila"}}
    index = {"biologico": biological}

    view, counts = inventory_format.resolve_ceiba_inventory(
        index, ["muestra-a", "mues tra-a"], biological
    )

    assert view == index
    assert view["biologico"]["muestra-a"] == {"proyecto": "Exacto"}
    assert {kind: count for kind, count in counts.items() if count} == {
        "exact": 1, "ambiguous_inventory": 1, "ambiguous_ceiba": 1,
    }


def test_collects_duplicate_rows_without_changing_existing_workbook_calls(
    inventory_format, inventory_workbook
):
    url = "https://inventario.example.test/resource?r=MUESTRA-A"
    workbook = inventory_workbook([(url, "Primera fila", "M-01"), (url, "Última fila", "M-02")])
    identifiers = []

    legacy_index = inventory_format.map_biologico_inventory(workbook)
    index = inventory_format.map_biologico_inventory(workbook, biological_identifiers=identifiers)

    assert index == legacy_index
    assert index.keys() == {"biologico", "general", "proyecto_macro"}
    assert identifiers == ["MUESTRA-A", "MUESTRA-A"]
    assert index["biologico"]["MUESTRA-A"]["proyecto"] == "Última fila"

    view, counts = inventory_format.resolve_ceiba_inventory(index, ["muestra-a"], identifiers)
    assert "muestra-a" not in view["biologico"]
    assert counts["ambiguous_inventory"] == 1
    assert counts["ambiguous_ceiba"] == 0

    view, counts = inventory_format.resolve_ceiba_inventory(index, ["MUESTRA-A"], identifiers)
    assert view["biologico"]["MUESTRA-A"]["proyecto"] == "Última fila"
    assert counts["exact"] == 1


@pytest.mark.parametrize(
    ("macro_code", "general_present"),
    [pytest.param("M-01", True, id="single-macro-and-exact-general"),
     pytest.param("M-01 | M-02", False, id="multiple-macros-and-alternative-general")],
)
def test_attaches_original_row_and_uses_the_existing_macro_and_general_keys(
    inventory_format, mapeo_ceiba, macro_code, general_present
):
    from src.formato.utilitarios.map_inventory import attach_inventory_data

    raw_id, ceiba_id = "MUESTRA%2F A", "Muestra%2FA"
    row = {
        "url": " https://inventario.example.test/resource?r=MUESTRA%2F A&v=1 ",
        "proyecto": "  Proyecto ágil  ",
        "proyecto_macro": macro_code,
    }
    macro = {"nombre_diego": "Proyecto ficticio"}
    general = {"accion": "Coincidencia literal"}
    index = {
        "biologico": {raw_id: row},
        "proyecto_macro": {"M-01": macro, "M-02": {"nombre_diego": "Otro proyecto"}},
        "general": {raw_id: {"accion": "Grafía alternativa"}},
    }
    if general_present:
        index["general"][ceiba_id] = general
    original = deepcopy(index)

    view, counts = inventory_format.resolve_ceiba_inventory(index, [ceiba_id], [raw_id])
    result = attach_inventory_data(view, ceiba_id, "biologico", {"resource": {"shortName": ceiba_id}})

    assert result == {
        "resource": {"shortName": ceiba_id},
        "inventory": {
            "biologico": row,
            "proyecto_macro_detalle": macro if macro_code == "M-01" else {},
            "general": general if general_present else {},
        },
    }
    assert counts["normalized"] == 1
    assert index == original
    assert view["biologico"][ceiba_id] == original["biologico"][raw_id]
    projects = mapeo_ceiba.map_projects(
        {"name": ceiba_id, "dataset": {}, "inventory": result["inventory"]},
        view["proyecto_macro"],
        [],
    )
    assert [project["projectID"] for project in projects] == (
        ["M-01"] if macro_code == "M-01" else ["M-01", "M-02"]
    )


def test_leaves_inventory_empty_when_only_general_has_a_match(inventory_format):
    from src.formato.utilitarios.map_inventory import attach_inventory_data

    index = {"biologico": {}, "general": {"muestra-a": {"accion": "Sólo en GENERAL"}}}
    view, _ = inventory_format.resolve_ceiba_inventory(index, ["muestra-a"], [])

    assert attach_inventory_data(view, "muestra-a", "biologico", {"published": True}) == {
        "published": True, "inventory": {},
    }


@pytest.mark.parametrize(
    ("inventory_type", "identifier"),
    [pytest.param("geografico", "00000000-0000-4000-8000-000000000000", id="geonetwork"),
     pytest.param("sociocultural", "doi:10.0000/FICTICIO", id="biocultural")],
)
def test_shared_attachment_still_uses_exact_keys(inventory_format, inventory_type, identifier):
    from src.formato.utilitarios.map_inventory import attach_inventory_data

    row = {"proyecto_macro": "M-01"}
    macro = {"suscrito": "Entidad ficticia"}
    general = {"accion": "Acción ficticia"}
    index = {
        "biologico": {"MUESTRA": {"proyecto": "Proyecto ficticio"}},
        inventory_type: {identifier: row},
        "proyecto_macro": {"M-01": macro},
        "general": {identifier: general},
    }
    view, _ = inventory_format.resolve_ceiba_inventory(index, ["muestra"], ["MUESTRA"])

    assert attach_inventory_data(view, identifier, inventory_type) == {
        "inventory": {inventory_type: row, "proyecto_macro_detalle": macro, "general": general},
    }
    assert attach_inventory_data(view, f" {identifier}", inventory_type) == {"inventory": {}}


@pytest.mark.parametrize(
    ("rights", "status", "expected_access", "expected_license", "draft"),
    [
        pytest.param(
            "Libre a nivel interno y externo", "PUBLIC", "Fully open access (internal/external)",
            "CC BY-NC 4.0", False, id="open-and-public",
        ),
        pytest.param(
            "Libre a nivel interno", "PRIVATE", "Internal open access", None, True,
            id="internal-and-private",
        ),
        pytest.param(
            "Restringido temporalmente", "PUBLIC", "Restricted", None, False, id="restricted-and-public",
        ),
    ],
)
def test_recovery_keeps_access_license_and_publication_rules(
    inventory_format, mapeo_ceiba, record_ceiba, rights, status, expected_access, expected_license, draft
):
    from src.formato.utilitarios.map_inventory import attach_inventory_data

    record = record_ceiba({"intellectualRights": rights})
    record["ipt_status"] = status
    raw_id = record["name"].upper()
    index = {"biologico": {raw_id: {"fecha_liberacion": "2099-01-02", "objeto_restriccion": "Sensibilidad"}}}
    view, _ = inventory_format.resolve_ceiba_inventory(index, [record["name"]], [raw_id])
    recovered = attach_inventory_data(view, record["name"], "biologico", record)
    tables = {"restriction_reasons": [{
        "restriction_text": "Sensibilidad", "reason_code": "Razón ficticia",
        "proposed_reason": "", "validated": "sí",
    }]}

    previous_access = mapeo_ceiba.map_access(record, tables, [])
    current_access = mapeo_ceiba.map_access(recovered, tables, [])
    previous_options = mapeo_ceiba.load_options(record, {"institutional": {"access": previous_access}})
    current_options = mapeo_ceiba.load_options(recovered, {"institutional": {"access": current_access}})

    assert current_options == previous_options
    assert (current_options["accessType"], current_options["license"], current_options["draft"]) == (
        expected_access, expected_license, draft,
    )
    if expected_access == "Restricted":
        assert "restrictedUntil" not in previous_access
        assert current_access["restrictedUntil"] == "2099-01-02"


def test_ingest_uses_all_directories_and_logs_only_aggregate_resolution_counts(
    isolated_imports, inventory_workbook, monkeypatch, tmp_path, caplog
):
    from src.ingest import ceiba_ingest

    biological_ids = [
        "Exacto", "RECUPERADO", "NUNCAPUBLICADO", "COLISION", "AMBIGUO", "AMBI GUO",
    ]
    workbook = inventory_workbook(
        [(f"https://inventario.example.test/resource?r={name}", "Proyecto ficticio", "M-01")
         for name in biological_ids],
        macro=[("M-01", "Macro ficticio", "Entidad ficticia")],
        general=[("Recupe rado", "Exacto en GENERAL", 5, 2099), ("RECUPERADO", "Alternativo", 6, 2099)],
    )
    resource_ids = ["Exacto", "Recupe rado", "Nunca publicado", "Colision", "Co lision", "Ambiguo", "Ausente"]
    unpublished = {"Nunca publicado", "Co lision"}
    written_json, written_csv = {}, {}
    monkeypatch.setattr(
        ceiba_ingest, "config", SimpleNamespace(i2d_inventory=workbook, ceiba_data_dir=tmp_path),
    )
    monkeypatch.setattr(ceiba_ingest, "OUTPUT_DIR", str(tmp_path / "metadata"))
    monkeypatch.setattr(ceiba_ingest, "read_resources", lambda: [Path(name) for name in resource_ids])

    def process_metadata(resource):
        published = resource.name not in unpublished
        return {
            "resource_dict": {"published": published, "resource": {"shortName": resource.name}},
            "latest_version": "1" if published else None,
            "ceiba_identifier": resource.name,
        }

    monkeypatch.setattr(ceiba_ingest, "process_metadata", process_metadata)
    monkeypatch.setattr(ceiba_ingest, "export_file_references", lambda *_: None)
    monkeypatch.setattr(
        ceiba_ingest, "write_json",
        lambda data, directory, filename: written_json.update({(Path(directory).name, filename): data}),
    )
    monkeypatch.setattr(
        ceiba_ingest, "write_csv", lambda rows, directory, filename: written_csv.update({filename: rows}),
    )

    with caplog.at_level(logging.INFO, logger="tests.ceiba.inventory"):
        ceiba_ingest.main()

    assert set(written_json) == {(name, "resource_metadata.json") for name in resource_ids}
    records = {name: written_json[name, "resource_metadata.json"] for name in resource_ids}
    assert records["Exacto"]["inventory"]["biologico"]["url"].endswith("r=Exacto")
    recovered = records["Recupe rado"]
    assert recovered.keys() == {"resource", "published", "inventory"}
    assert recovered["resource"]["shortName"] == "Recupe rado"
    assert recovered["inventory"]["biologico"]["url"].endswith("r=RECUPERADO")
    assert recovered["inventory"]["proyecto_macro_detalle"]["nombre_diego"] == "Macro ficticio"
    assert recovered["inventory"]["general"]["accion"] == "Exacto en GENERAL"
    assert records["Nunca publicado"]["published"] is False
    assert records["Nunca publicado"]["inventory"]["biologico"]["url"].endswith("r=NUNCAPUBLICADO")
    for name in ("Colision", "Co lision", "Ambiguo", "Ausente"):
        assert records[name]["inventory"] == {}
    assert written_csv["inventory.csv"] == [
        {"resource": name, "latest_version": None if name in unpublished else "1"} for name in resource_ids
    ]

    [summary] = [message for message in caplog.messages if message.startswith("Inventario biológico CEIBA:")]
    assert summary == (
        "Inventario biológico CEIBA: coincidencias exactas=1, normalizadas recuperadas=2, "
        "sin correspondencia=1, rechazos por ambigüedad en el inventario=1 y en CEIBA=2."
    )
