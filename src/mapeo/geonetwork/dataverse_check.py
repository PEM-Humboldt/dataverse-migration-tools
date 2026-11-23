"""Checks a record's Dataverse fields against the block definitions, read by load_dv_schemas()
(src/mapeo/reconstruct_mapping.py, <block>.tsv in TSV_FILES_PATH).

`tsv_schema` (load_dv_schemas()) has one entry per top-level field of all the blocks, with multiple,
typeClass, required and vocabulary; a compound field also has subfields ({subfield: {multiple, required}})
and subfields_vocabulary. It does not say which block a field belongs to, so the block of each field is not
checked here.
"""


def check_item(path, value, multiple, vocabulary, problems):
    """Append to `problems` the problems of a primitive or controlled-vocabulary value."""
    if multiple != isinstance(value, list):
        problems.append(f"{path}: {'debe ser una lista' if multiple else 'no debe ser una lista'}")
    for item in value if isinstance(value, list) else [value]:
        if vocabulary is not None and item not in vocabulary:
            problems.append(f"{path}: «{item}» no está en el vocabulario")
        elif not isinstance(item, str):
            problems.append(f"{path}: el valor no es un texto")


def check_compound(path, value, meta, problems):
    """Append to `problems` the problems of a compound value (dict, or list of dicts if multiple)."""
    if meta["multiple"] != isinstance(value, list):
        problems.append(f"{path}: {'debe ser una lista' if meta['multiple'] else 'no debe ser una lista'}")
    subfields = meta.get("subfields", {})
    for item in value if isinstance(value, list) else [value]:
        if not isinstance(item, dict):
            problems.append(f"{path}: el compuesto no es un diccionario")
            continue
        for child, child_value in item.items():
            if child not in subfields:
                problems.append(f"{path}/{child}: no es un subcampo de {path.split('/')[-1]}")
                continue
            check_item(f"{path}/{child}", child_value, subfields[child]["multiple"],
                       meta.get("subfields_vocabulary", {}).get(child), problems)
        # un subcampo obligatorio lo es cuando el compuesto está presente (p. ej. producerName)
        for child, child_meta in subfields.items():
            if child_meta["required"] and child not in item:
                problems.append(f"{path}/{child}: subcampo obligatorio vacío")


def check_fields(fields, tsv_schema, blocks):
    """Problems of a record's {block: {field: value}} against `tsv_schema` (empty list if none).

    `blocks`: the blocks used by the migration; a block outside this list is a problem.
    """
    problems = []
    for block, block_fields in fields.items():
        if block not in blocks:
            problems.append(f"{block}: bloque desconocido")
            continue
        for field, value in block_fields.items():
            meta = tsv_schema.get(field)
            if meta is None:
                problems.append(f"{block}/{field}: no es un campo de primer nivel de los bloques")
            elif meta["typeClass"] == "compound":
                check_compound(f"{block}/{field}", value, meta, problems)
            else:
                check_item(f"{block}/{field}", value, meta["multiple"], meta.get("vocabulary"), problems)
    present = {field for block_fields in fields.values() for field in block_fields}
    for field, meta in tsv_schema.items():
        if meta["required"] and field not in present:
            problems.append(f"{field}: campo obligatorio vacío")
    return problems
