"""Compara dos salidas locales de mapeo CEIBA.

Estructura de cada entrada (LINEA_BASE y ACTUAL):
  metadata/<recurso>-1.0.json   registro de versión con datasetVersion.metadataBlocks
  load_plan.csv               filas con la columna resource
  version_dates.csv           filas con la columna source_id
  curation.csv                filas con resource, kind y field
  mapping_problems.json       objeto recurso -> lista de mensajes

Use --metadata-subdir si ambos directorios tienen otro nombre para los
metadatos, o --metadata-subdir . si los registros JSON están junto a los reportes.
El emparejamiento se hace por nombre de archivo sin el sufijo -1.0.json.
Los cambios internos se calculan para recursos presentes en ambos lados.

SALIDA debe estar fuera de ambas entradas. Contendrá summary.json con conteos
y, con --detailed, details.json con rutas JSON, valores y filas individuales.
Trate details.json como un archivo local sensible. Los archivos ya existentes
se protegen contra sobreescritura. La terminal solo presenta totales e incidencias
generales. El código de salida es 0 al completar la comparación, aun si hay
diferencias, y 2 ante entradas incompletas o un error de lectura o escritura.

Se ignora el orden de claves JSON, de campos de bloque (emparejados por typeName)
y de columnas y filas CSV. Las demás listas JSON conservan su orden. Los CSV
y los mensajes de mapping_problems.json conservan sus duplicados. En los CSV,
una fila editada aparece como la eliminación de la anterior y la adición de la nueva.
Las rutas de fecha previstas se cuentan aparte. Los cambios estructurales y
las demás rutas se marcan para revisión. El desglose por subcampo representa
cambios detectados dentro de compuestos, sin desglosar un compuesto añadido o
eliminado en su totalidad. Se requiere Python 3.10 o posterior.
"""

import argparse
import csv
import json
import os
import sys
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path


RECORD_SUFFIX = "-1.0.json"
CSV_REPORTS = {
    "load_plan.csv": "resource",
    "version_dates.csv": "source_id",
    "curation.csv": "resource",
}
PROBLEMS_REPORT = "mapping_problems.json"
MISSING = object()
METADATA_PATH = ("datasetVersion", "metadataBlocks")
DATE_PATHS = {
    ("citation", "distributionDate"): {()},
    ("citation", "dsDescription"): {("value", "dsDescriptionDate")},
    ("biologicalMetadata", "temporalCoverage"): {
        ("value", "simpleCalendarDate"),
        ("value", "initialCalendarDate"),
        ("value", "finalCalendarDate"),
    },
    ("institutional", "access"): {("value", "restrictedUntil")},
}


class InvalidInput(ValueError):
    """Código fijo de incidencia, apto para un reporte sin datos individuales."""


def unique_object(pairs):
    result = dict(pairs)
    if len(result) != len(pairs):
        raise InvalidInput("duplicate_json_key")
    return result


def invalid_constant(_):
    raise InvalidInput("invalid_json")


def read_json(path):
    with path.open(encoding="utf-8-sig") as stream:
        return json.load(stream, object_pairs_hook=unique_object, parse_constant=invalid_constant)


def read_input(path, reader):
    try:
        if path.is_symlink():
            raise InvalidInput("symlink")
        return reader(path), None
    except FileNotFoundError:
        return None, "missing"
    except InvalidInput as error:
        return None, str(error)
    except json.JSONDecodeError:
        return None, "invalid_json"
    except (csv.Error, UnicodeError):
        return None, "invalid_text"
    except (ValueError, RecursionError):
        return None, "unsupported_content"
    except OSError:
        return None, "unreadable"


def read_record(path):
    record = read_json(path)
    version = record.get("datasetVersion") if isinstance(record, dict) else None
    blocks = version.get("metadataBlocks") if isinstance(version, dict) else None
    if not isinstance(blocks, dict):
        raise InvalidInput("invalid_record_shape")

    metadata = {}
    for name, block in blocks.items():
        if not isinstance(block, dict) or not isinstance(block.get("fields"), list):
            raise InvalidInput("invalid_record_shape")
        fields = {}
        for field in block["fields"]:
            type_name = field.get("typeName") if isinstance(field, dict) else None
            if not isinstance(type_name, str) or not type_name:
                raise InvalidInput("invalid_record_shape")
            if type_name in fields:
                raise InvalidInput("duplicate_type_name")
            fields[type_name] = field
        metadata[name] = ({k: v for k, v in block.items() if k != "fields"}, fields)

    body = dict(record, datasetVersion={k: v for k, v in version.items() if k != "metadataBlocks"})
    return body, metadata


def json_key(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=True)


def value_changes(before, after, path=()):
    """Emite ruta, operación y valores, conservando el orden y los duplicados de listas."""
    if before is MISSING:
        yield path, "added", before, after
    elif after is MISSING:
        yield path, "removed", before, after
    elif isinstance(before, dict) and isinstance(after, dict):
        for key in sorted(before.keys() | after.keys()):
            yield from value_changes(before.get(key, MISSING), after.get(key, MISSING), (*path, key))
    elif isinstance(before, list) and isinstance(after, list):
        old_keys, new_keys = list(map(json_key, before)), list(map(json_key, after))
        if old_keys == new_keys:
            return
        matcher = SequenceMatcher(None, old_keys, new_keys, autojunk=False)
        for tag, i, end_i, j, end_j in matcher.get_opcodes():
            if tag == "equal":
                continue
            for offset in range(max(end_i - i, end_j - j)):
                left = before[i + offset] if i + offset < end_i else MISSING
                right = after[j + offset] if j + offset < end_j else MISSING
                index = i + offset if right is MISSING else j + offset
                yield from value_changes(left, right, (*path, index))
    elif before != after or isinstance(before, bool) != isinstance(after, bool):
        yield path, "modified", before, after


def record_changes(before, after):
    old_body, old_blocks = before
    new_body, new_blocks = after
    yield from value_changes(old_body, new_body)
    for block in sorted(old_blocks.keys() | new_blocks.keys()):
        old_properties, old_fields = old_blocks.get(block, (MISSING, {}))
        new_properties, new_fields = new_blocks.get(block, (MISSING, {}))
        path = (*METADATA_PATH, block)
        yield from value_changes(old_properties, new_properties, path)
        for field in sorted(old_fields.keys() | new_fields.keys()):
            yield from value_changes(
                old_fields.get(field, MISSING), new_fields.get(field, MISSING), (*path, "fields", field)
            )


def is_date_change(path):
    if path[:2] != METADATA_PATH or len(path) < 5 or path[3] != "fields":
        return False
    targets = DATE_PATHS.get((path[2], path[4]), ())
    suffix = tuple(part for part in path[5:] if isinstance(part, str))
    return suffix in targets or (suffix[-1:] == ("value",) and suffix[:-1] in targets)


def operation(key, before, after):
    if key not in before:
        return "added"
    if key not in after:
        return "removed"
    return "modified"


def operation_counts():
    return {"added": 0, "removed": 0, "modified": 0}


def update_metadata_counts(summary, differences, before, after):
    old_blocks, new_blocks = before[1], after[1]
    block_changes = [(path, op) for path, op, *_ in differences if path[:2] == METADATA_PATH]
    for block in {path[2] for path, _ in block_changes}:
        counts = summary["blocks"].setdefault(block, operation_counts())
        counts[operation(block, old_blocks, new_blocks)] += 1
    field_changes = [(path, op) for path, op in block_changes if len(path) >= 5 and path[3] == "fields"]
    for block, field in {(path[2], path[4]) for path, _ in field_changes}:
        fields = summary["fields"].setdefault(block, {})
        counts = fields.setdefault(field, operation_counts())
        counts[operation(field, old_blocks.get(block, ({}, {}))[1], new_blocks.get(block, ({}, {}))[1])] += 1

    subfield_changes = set()
    for path, op in field_changes:
        block, field = path[2], path[4]
        suffix = [part for part in path[5:] if isinstance(part, str)]
        if len(suffix) < 2 or suffix[0] != "value":
            continue
        old_field = old_blocks.get(block, ({}, {}))[1].get(field, {})
        new_field = new_blocks.get(block, ({}, {}))[1].get(field, {})
        if "compound" in (old_field.get("typeClass"), new_field.get("typeClass")):
            subfield_changes.add((block, field, suffix[1], op if len(suffix) == 2 else "modified"))
    for block, field, subfield, op in subfield_changes:
        fields = summary["subfields"].setdefault(block, {})
        counts = fields.setdefault(field, {}).setdefault(subfield, operation_counts())
        counts[op] += 1


def detailed_change(path, operation_name, before, after):
    result = {"path": path, "operation": operation_name, "date_path": is_date_change(path)}
    if before is not MISSING:
        result["baseline"] = before
    if after is not MISSING:
        result["current"] = after
    return result


def compare_records(baseline, current, metadata_subdir, detailed):
    paths, errors, directory_errors = {}, {}, {}
    for side, root in (("baseline", baseline), ("current", current)):
        try:
            folder = (root / metadata_subdir).resolve()
            if not folder.is_relative_to(root):
                raise InvalidInput("metadata_directory_unavailable")
            paths[side] = {
                p.name.removesuffix(RECORD_SUFFIX): p for p in folder.iterdir() if p.name.endswith(RECORD_SUFFIX)
            }
        except (InvalidInput, OSError, RuntimeError):
            directory_errors[side] = "metadata_directory_unavailable"
    if directory_errors:
        return {"status": "unavailable", "issues": directory_errors}, {}

    old_paths, new_paths = paths["baseline"], paths["current"]
    old_only, new_only = sorted(old_paths.keys() - new_paths.keys()), sorted(new_paths.keys() - old_paths.keys())
    summary = {
        "status": "complete",
        "baseline": len(old_paths), "current": len(new_paths),
        "only_baseline": len(old_only), "only_current": len(new_only),
        "identical": 0, "modified": 0, "not_compared": 0,
        "blocks": {}, "fields": {}, "subfields": {}, "value_changes": operation_counts(),
        "date_path_changes": operation_counts(), "other_changes": operation_counts(),
        "resources_with_other_changes": 0,
    }
    details = {"only_baseline": old_only, "only_current": new_only, "modified": {}, "issues": {}}
    for resource in sorted(old_paths.keys() | new_paths.keys()):
        records = {}
        for side in ("baseline", "current"):
            if resource not in paths[side]:
                continue
            records[side], issue = read_input(paths[side][resource], read_record)
            if issue:
                errors.setdefault(side, Counter())[issue] += 1
                if detailed:
                    details["issues"].setdefault(side, {})[resource] = issue
        if len(records) != 2:
            continue
        before, after = records["baseline"], records["current"]
        if before is None or after is None:
            summary["not_compared"] += 1
            continue
        differences = list(record_changes(before, after))
        if not differences:
            summary["identical"] += 1
            continue
        summary["modified"] += 1
        update_metadata_counts(summary, differences, before, after)
        has_other = False
        for path, operator, *_ in differences:
            summary["value_changes"][operator] += 1
            if is_date_change(path):
                summary["date_path_changes"][operator] += 1
            else:
                summary["other_changes"][operator] += 1
                has_other = True
        summary["resources_with_other_changes"] += has_other
        if detailed:
            details["modified"][resource] = [detailed_change(*change) for change in differences]
    if errors:
        summary.update(status="incomplete", issues=errors)
    return summary, details


def read_csv(path, required_columns):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.reader(stream, strict=True)
        header = next(reader, [])
        if not header and "kind" not in required_columns and not any(reader):
            return [], Counter()
        if len(set(header)) != len(header) or not set(required_columns).issubset(header) or "" in header:
            raise InvalidInput("invalid_csv_header")
        rows = Counter()
        for row in reader:
            if not row:
                continue
            if len(row) != len(header):
                raise InvalidInput("invalid_csv_row")
            rows[tuple(sorted(zip(header, row)))] += 1
    return sorted(header), rows


def compare_counts(before, after):
    added, removed = after - before, before - after
    return {
        "baseline": before.total(), "current": after.total(),
        "identical": (before & after).total(), "added": added.total(), "removed": removed.total(),
    }, added, removed


def unique_resources(rows, column):
    return {resource for row in rows if (resource := dict(row).get(column))}


def group_counts(rows, column):
    groups = Counter()
    for row, count in rows.items():
        groups[dict(row)[column]] += count
    return groups


def curation_breakdown(before, after, added, removed, column):
    old_group, new_group, contributions, withdrawals = (
        group_counts(rows, column) for rows in (before, after, added, removed)
    )
    return {
        key: {"baseline": old_group[key], "current": new_group[key], "added": contributions[key], "removed": withdrawals[key]}
        for key in sorted(old_group.keys() | new_group.keys())
    }


def read_problems(path):
    data = read_json(path)
    if not isinstance(data, dict) or any(
        not isinstance(messages, list) or any(not isinstance(message, str) for message in messages)
        for messages in data.values()
    ):
        raise InvalidInput("invalid_problems_shape")
    return data


def report_inputs(baseline, current, filename, reader):
    before, left_issue = read_input(baseline / filename, reader)
    after, right_issue = read_input(current / filename, reader)
    issues = {side: issue for side, issue in (("baseline", left_issue), ("current", right_issue)) if issue}
    return before, after, issues


def compare_csv(baseline, current, filename, resource_column, detailed):
    is_curation = filename == "curation.csv"
    required = (resource_column, "kind", "field") if is_curation else (resource_column,)
    before, after, issues = report_inputs(baseline, current, filename, lambda path: read_csv(path, required))
    if issues:
        return {"status": "unavailable", "issues": issues}, {}

    old_columns, old_rows = before
    new_columns, new_rows = after
    counts, added, removed = compare_counts(old_rows, new_rows)
    counts.update(
        status="complete", columns_changed=old_columns != new_columns,
        resources_baseline=len(unique_resources(old_rows, resource_column)),
        resources_current=len(unique_resources(new_rows, resource_column)),
        resources_affected=len(unique_resources(added.keys() | removed.keys(), resource_column)),
    )
    if is_curation:
        counts["by_category"] = curation_breakdown(old_rows, new_rows, added, removed, "kind")
        counts["by_field"] = curation_breakdown(old_rows, new_rows, added, removed, "field")
    details = {}
    if detailed:
        details = {"columns_baseline": old_columns, "columns_current": new_columns}
        for name, rows in (("added", added), ("removed", removed)):
            details[name] = [{"row": dict(row), "count": count} for row, count in sorted(rows.items())]
    return counts, details


def compare_problems(baseline, current, detailed):
    before, after, issues = report_inputs(baseline, current, PROBLEMS_REPORT, read_problems)
    if issues:
        return {"status": "unavailable", "issues": issues}, {}
    old = Counter((resource, message) for resource, messages in before.items() for message in messages)
    new = Counter((resource, message) for resource, messages in after.items() for message in messages)
    counts, added, removed = compare_counts(old, new)
    only_old, only_new = before.keys() - after.keys(), after.keys() - before.keys()
    affected = only_old | only_new | {resource for resource, _ in added.keys() | removed.keys()}
    counts.update(
        status="complete", resources_baseline=len(before), resources_current=len(after),
        resources_only_baseline=len(only_old), resources_only_current=len(only_new), resources_affected=len(affected),
    )
    details = {}
    if detailed:
        details = {"only_baseline": sorted(only_old), "only_current": sorted(only_new)}
        for name, messages in (("added", added), ("removed", removed)):
            details[name] = [
                {"resource": resource, "message": message, "count": count}
                for (resource, message), count in sorted(messages.items())
            ]
    return counts, details


def compare(baseline, current, metadata_subdir, detailed):
    records, record_details = compare_records(baseline, current, metadata_subdir, detailed)
    reports, report_details = {}, {}
    for filename, resource_column in CSV_REPORTS.items():
        reports[filename], report_details[filename] = compare_csv(baseline, current, filename, resource_column, detailed)
    reports[PROBLEMS_REPORT], report_details[PROBLEMS_REPORT] = compare_problems(baseline, current, detailed)
    complete = records["status"] == "complete" and all(r["status"] == "complete" for r in reports.values())
    return (
        {"status": "complete" if complete else "incomplete", "records": records, "reports": reports},
        {"records": record_details, "reports": report_details},
    )


class QuietArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.exit(2, "Argumentos inválidos. Consulte --help.\n")


def write_report(path, data):
    # O_EXCL protege también destinos ya existentes que sean enlaces.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as stream:
        json.dump(data, stream, ensure_ascii=True, indent=2, sort_keys=True)
        stream.write("\n")


def main(argv=None):
    parser = QuietArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("baseline", type=Path, metavar="LINEA_BASE", help="Directorio de la línea base")
    parser.add_argument("current", type=Path, metavar="ACTUAL", help="Directorio de los resultados actuales")
    parser.add_argument("output", type=Path, metavar="SALIDA", help="Directorio separado para los reportes nuevos")
    parser.add_argument("--metadata-subdir", type=Path, default=Path("metadata"), metavar="RUTA_RELATIVA",
                        help="Subdirectorio de registros en ambas entradas (metadata por defecto, . para salidas planas)")
    parser.add_argument("--detailed", action="store_true", help="Escribe details.json local con valores individuales")
    args = parser.parse_args(argv)

    try:
        baseline, current, output = (path.resolve() for path in (args.baseline, args.current, args.output))
        if not baseline.is_dir() or not current.is_dir():
            raise InvalidInput("Ambos directorios de entrada deben existir.")
        if args.metadata_subdir.is_absolute() or ".." in args.metadata_subdir.parts:
            raise InvalidInput("El subdirectorio de metadatos debe ser relativo a las entradas.")
        if output.is_relative_to(baseline) or output.is_relative_to(current):
            raise InvalidInput("El directorio de salida debe estar fuera de ambas entradas.")
        targets = [output / "summary.json"]
        if args.detailed:
            targets.append(output / "details.json")
        if any(path.exists() or path.is_symlink() for path in targets):
            raise InvalidInput("Ya existe un reporte de salida. Elija otro directorio.")
        summary, details = compare(baseline, current, args.metadata_subdir, args.detailed)
        output.mkdir(mode=0o700, parents=True, exist_ok=True)
        write_report(targets[0], summary)
        if args.detailed:
            write_report(targets[1], details)
    except InvalidInput as error:
        print(str(error), file=sys.stderr)
        return 2
    except (OSError, RuntimeError):
        print("No se pudo completar la lectura o escritura de los reportes.", file=sys.stderr)
        return 2

    records = summary["records"]
    if records["status"] != "unavailable":
        print(f"Registros: {records['baseline']} en línea base, {records['current']} actuales, "
              f"{records['identical']} idénticos, {records['modified']} modificados, "
              f"{records['only_baseline']} solo en línea base, {records['only_current']} solo actuales.")
        print(f"Recursos con cambios fuera de las rutas de fecha: {records['resources_with_other_changes']}.")
    if summary["status"] == "incomplete":
        print("Comparación incompleta. Consulte las incidencias en summary.json.", file=sys.stderr)
        return 2
    print("Comparación completa. Resumen agregado en summary.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
