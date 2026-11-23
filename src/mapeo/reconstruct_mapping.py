import csv
from pathlib import Path
from src.config import Config

config = Config()

def load_dv_schemas():
    """Lee todos los archivos .tsv de una carpeta y construye `tsv_schema` con sus vocabularios integrados."""
    tsv_schema = {}
    vocabulary = {}
    # Mapa auxiliar para saber qué subcampo pertenece a qué padre: {"country": "geographicCoverage", ...}
    subfield_to_parent = {}
    
    tsv_files = list(Path(config.tsv_files).glob("*.tsv"))

    for file_path in tsv_files:
        with open(file_path, mode="r", encoding="utf-8-sig") as f:
            reader = csv.reader(f, delimiter="\t")
            headers = []
            reading_fields = False
            reading_vocab = False

            for row in reader:
                if not row:
                    continue

                first_cell = row[0].strip()

                # 1. Detectar inicio de sección de campos
                if first_cell == "#datasetField":
                    headers = [h.strip() for h in row]
                    reading_fields = True
                    reading_vocab = False
                    continue

                # 2. Detectar inicio de vocabularios
                if first_cell == "#controlledVocabulary":
                    headers = [h.strip() for h in row]
                    reading_fields = False
                    reading_vocab = True
                    continue

                # 3. Cualquier otra sección con '#' apaga ambas lecturas
                if first_cell.startswith("#"):
                    reading_fields = False
                    reading_vocab = False
                    continue

                # 4. Procesar filas de datos de #datasetField
                if reading_fields and headers:
                    row_dict = dict(zip(headers, row))
                    field_name = row_dict.get("name", "").strip()
                    if not field_name:
                        continue

                    multiple = row_dict.get("allowmultiples", "").strip().upper() == "TRUE"
                    is_controlled = row_dict.get("allowControlledVocabulary", "").strip().upper() == "TRUE"
                    required = row_dict.get("required", "").strip().upper() == "TRUE"
                    parent = row_dict.get("parent", "").strip()

                    if parent:
                        subfield_to_parent[field_name] = parent
                        if parent not in tsv_schema:
                            tsv_schema[parent] = {
                                "multiple": True,
                                "typeClass": "compound",
                                "required": required,
                                "allowControlledVocabulary": is_controlled,
                                "controlled_subfields": set(),
                                "subfields_vocabulary": {},
                            }
                        else:
                            tsv_schema[parent]["typeClass"] = "compound"
                            tsv_schema[parent].setdefault("subfields_vocabulary", {})

                        if is_controlled:
                            tsv_schema[parent]["controlled_subfields"].add(field_name)

                        # Cada subcampo con su propio `multiple` y `required` (de su fila del TSV, no del padre)
                        tsv_schema[parent].setdefault("subfields", {})[field_name] = {
                            "multiple": multiple,
                            "required": required,
                        }
                    else:
                        tsv_schema[field_name] = {
                            "multiple": multiple,
                            "typeClass": "controlledVocabulary" if is_controlled else "primitive",
                            "required": required,
                            "allowControlledVocabulary": is_controlled,
                            "controlled_subfields": set(),
                        }

                # 5. Procesar filas de datos de #controlledVocabulary
                elif reading_vocab and headers:
                    row_dict = dict(zip(headers, row))
                    field_name = row_dict.get("DatasetField", "").strip()
                    value = row_dict.get("Value", "").strip()

                    if field_name and value:
                        vocabulary.setdefault(field_name, []).append(value)

    for field_name, vocab_list in vocabulary.items():
        if field_name in tsv_schema:
            tsv_schema[field_name]["vocabulary"] = vocab_list
        elif field_name in subfield_to_parent:
            parent_name = subfield_to_parent[field_name]
            tsv_schema[parent_name]["subfields_vocabulary"][field_name] = vocab_list

    return tsv_schema

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
            if field_name not in schema:
                raise ValueError(f"{block_name}/{field_name}: field not in the block definitions (TSV_FILES_PATH)")
            meta = schema[field_name]
            type_class = meta["typeClass"]
            multiple = meta["multiple"]
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