import csv
from pathlib import Path
from src.config import Config

config = Config()

def load_dv_schemas():
    """Lee todos los archivos .tsv de una carpeta y construye `schema` y `vocabulary`."""
    tsv_schema = {}
    vocabulary = {}
    tsv_files = list(Path(config.tsv_files).glob("*.tsv"))

    for file_path in tsv_files:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.reader(f, delimiter="\t")
            headers = []
            reading_fields = False
            reading_vocab = False  # 1. Inicializar la bandera en False

            for row in reader:
                if not row:
                    continue

                first_cell = row[0].strip()

                # Detectar el inicio de la sección de campos (solo guarda títulos y activa bandera)
                if first_cell == "#datasetField":
                    headers = [h.strip() for h in row]
                    reading_fields = True
                    reading_vocab = False
                    continue

                # Detectar el inicio de vocabularios (SOLO guarda títulos y activa bandera, no lee datos aún)
                if first_cell == "#controlledVocabulary":
                    headers = [h.strip() for h in row]
                    reading_fields = False
                    reading_vocab = True
                    continue

                # Si empieza cualquier otra sección con '#', apagar ambas lecturas
                if first_cell.startswith("#"):
                    reading_fields = False
                    reading_vocab = False
                    continue

                # Procesar filas de datos de #datasetField
                if reading_fields and headers:
                    row_dict = dict(zip(headers, row))
                    field_name = row_dict.get("name", "").strip()
                    if not field_name:
                        continue

                    multiple = row_dict.get("allowmultiples", "").strip().upper() == "TRUE"
                    is_controlled = row_dict.get("allowControlledVocabulary", "").strip().upper() == "TRUE"
                    required = row_dict.get("required", "").strip().upper() == "TRUE"
                    controlled_vocab = row_dict.get("allowControlledVocabulary", "False").strip().upper() == "TRUE"
                    parent = row_dict.get("parent", "").strip()

                    if parent:
                        if parent not in tsv_schema:
                            tsv_schema[parent] = {
                                "multiple": True,
                                "typeClass": "compound",
                                "required": required,
                                "controlled_vocab": controlled_vocab,
                                "allowControlledVocabulary": controlled_vocab,
                                "controlled_subfields": set(),
                            }
                        else:
                            tsv_schema[parent]["typeClass"] = "compound"

                        if is_controlled:
                            tsv_schema[parent]["controlled_subfields"].add(field_name)
                    else:
                        tsv_schema[field_name] = {
                            "multiple": multiple,
                            "typeClass": "controlledVocabulary" if is_controlled else "primitive",
                            "required": required,
                            "allowControlledVocabulary": controlled_vocab,
                            "controlled_subfields": set(),
                        }

                # 2. Procesar filas de datos de #controlledVocabulary (las filas que vienen debajo con row[0] vacío)
                elif reading_vocab and headers:
                    row_dict = dict(zip(headers, row))
                    field_name = row_dict.get("DatasetField", "").strip()
                    value = row_dict.get("Value", "").strip()
                    
                    if field_name and value:
                        vocabulary.setdefault(field_name, []).append(value)

    # 3. Retornar ambos diccionarios
    schema = {
        'tsv_schema': tsv_schema,
        'vocabulary': vocabulary
    }
    return schema

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
    tsv_schema = schema['tsv_schema']
    vocabulary = schema['vocabulary']

    for block_name, fields_dict in final_dict.items():
        if not fields_dict:
            continue

        dv_fields = []
        for field_name, raw_val in fields_dict.items():
            if raw_val is None or raw_val == "" or raw_val == []:
                continue

            meta = tsv_schema.get(field_name, {})
            type_class = meta.get("typeClass", "primitive")
            required = meta.get("required", "False")
            multiple = meta.get("multiple", isinstance(raw_val, list))
            is_compound = type_class == "compound"
            has_vocabulary = meta.get("allowControlledVocabulary")

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
                            "required": required,
                            "typeClass": "controlledVocabulary" if sk in controlled_subs else "primitive",
                            "value": sv,
                        }

                        if sk in controlled_subs:
                            sub_obj[sk]["vocabulary"] = vocabulary.get(sk)

                    if sub_obj:
                        built.append(sub_obj)
                final_val = built if multiple else (built[0] if built else None)
            else:
                final_val = raw_val

            if not final_val and final_val is not False:
                continue

            if has_vocabulary:
                dv_fields.append({
                    "typeName": field_name,
                    "multiple": multiple,
                    "required": required,
                    "typeClass": type_class,
                    "value": final_val,
                    "vocabulary": vocabulary.get(field_name)
                })
            else:
                dv_fields.append({
                    "typeName": field_name,
                    "multiple": multiple,
                    "required": required,
                    "typeClass": type_class,
                    "value": final_val,
                })

        if dv_fields:
            metadata_blocks[block_name] = {
                "name": block_name,
                "fields": dv_fields,
            }

    return metadata_blocks