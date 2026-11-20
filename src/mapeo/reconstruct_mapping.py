import csv
from pathlib import Path
from src.config import Config

config = Config()

def load_dv_schemas():
    """Lee todos los archivos .tsv de una carpeta y construye el diccionario `schema`."""
    schema = {}
    tsv_files = list(Path(config.tsv_files).glob("*.tsv"))

    for file_path in tsv_files:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            headers = []
            reading_fields = False

            for row in reader:
                if not row:
                    continue

                first_cell = row[0].strip()

                # 1. Detectar el inicio de la sección de campos
                if first_cell == "#datasetField":
                    headers = [h.strip() for h in row]
                    reading_fields = True
                    continue

                # 2. Detectar si empieza otra sección (#controlledVocabulary, etc.) y detener lectura
                if first_cell.startswith("#"):
                    reading_fields = False
                    continue

                # 3. Procesar cada fila de campo
                if reading_fields and headers:
                    # Emparejar encabezados con los valores de la fila
                    row_dict = dict(zip(headers, row))
                    field_name = row_dict.get("name", "").strip()
                    if not field_name:
                        continue

                    multiple = row_dict.get("allowmultiples", "").strip().upper() == "TRUE"
                    is_controlled = row_dict.get("allowControlledVocabulary", "").strip().upper() == "TRUE"
                    parent = row_dict.get("parent", "").strip()

                    if parent:
                        # Si tiene `parent`, sabemos que el padre es un campo compuesto (`compound`)
                        if parent not in schema:
                            schema[parent] = {
                                "multiple": True,
                                "typeClass": "compound",
                                "controlled_subfields": set(),
                            }
                        else:
                            schema[parent]["typeClass"] = "compound"

                        # Si el subcampo usa vocabulario controlado, lo anotamos en el padre
                        if is_controlled:
                            schema[parent]["controlled_subfields"].add(field_name)
                    else:
                        # Es un campo principal de primer nivel
                        schema[field_name] = {
                            "multiple": multiple,
                            "typeClass": "controlledVocabulary" if is_controlled else "primitive",
                            "controlled_subfields": set(),
                        }

    return schema

def build_dv_value(value, is_compound=False, is_controlled=False):
    """Envuelve valores internos cuando el campo es compuesto (compound)."""
    if not is_compound:
        return value

    # Un compuesto puede ser una lista de dicts (multiple=True) o un dict único (multiple=False, ej. 'access')
    items = value if isinstance(value, list) else [value]
    wrapped_items = []

    for item in items:
        if not isinstance(item, dict):
            continue
        subfields = {}
        for sub_key, sub_val in item.items():
            if sub_val is None or sub_val == "":
                continue
            subfields[sub_key] = {
                "typeName": sub_key,
                "multiple": False,
                "typeClass": "controlledVocabulary" if is_controlled else "primitive",
                "value": sub_val,
            }
        if subfields:
            wrapped_items.append(subfields)

    return wrapped_items if isinstance(value, list) else (wrapped_items[0] if wrapped_items else None)


def unflatten_dataset(final_dict: dict, schema: dict) -> dict:
    """Reconstruye el diccionario de metadataBlocks en formato Dataverse JSON.
    
    `schema`: {
        "nombre_campo": {
            "multiple": True/False,
            "typeClass": "primitive" | "controlledVocabulary" | "compound",
            "controlled_subfields": {"country", ...}  # opcional
        }
    }
    """
    metadata_blocks = {}

    for block_name, fields_dict in final_dict.items():
        if not fields_dict:
            continue

        dv_fields = []
        for field_name, raw_val in fields_dict.items():
            if raw_val is None or raw_val == "" or raw_val == []:
                continue

            meta = schema.get(field_name, {})
            type_class = meta.get("typeClass", "primitive")
            multiple = meta.get("multiple", isinstance(raw_val, list))
            is_compound = type_class == "compound"

            if is_compound:
                # Si tiene subcampos controlados (como country en geographicCoverage)
                items = raw_val if isinstance(raw_val, list) else [raw_val]
                controlled_subs = meta.get("controlled_subfields", set())
                built = []
                for item in items:
                    sub_obj = {}
                    for sk, sv in item.items():
                        if sv is None or sv == "":
                            continue
                        sub_obj[sk] = {
                            "typeName": sk,
                            "multiple": False,
                            "typeClass": "controlledVocabulary" if sk in controlled_subs else "primitive",
                            "value": sv,
                        }
                    if sub_obj:
                        built.append(sub_obj)
                final_val = built if multiple else (built[0] if built else None)
            else:
                final_val = raw_val

            if not final_val and final_val is not False:
                continue

            dv_fields.append({
                "typeName": field_name,
                "multiple": multiple,
                "typeClass": type_class,
                "value": final_val,
            })

        if dv_fields:
            metadata_blocks[block_name] = {
                "name": block_name,
                "fields": dv_fields,
            }

    return metadata_blocks