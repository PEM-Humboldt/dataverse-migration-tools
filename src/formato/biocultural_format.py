from pathlib import Path

import openpyxl
from src.formato.utilitarios.map_inventory import map_full_inventory
from src.utilitarios.logger import logger
from src.config import Config
from src.utilitarios.files import read_xlsx, write_json

config = Config()

def build_pid(item):
    """Persistent identifier of a `dataset` item of /contents (protocol, authority, separator, identifier).

    Built from the item's fields, not from a fixed prefix: some datasets have another
    prefix (doi:10.5072/FK2/MH9E0K, a DataCite test DOI).
    """
    return f"{item['protocol']}:{item['authority']}{item.get('separator', '/')}{item['identifier']}"

def extract_pid_identifier(pid):
    """Returns only the identifier of a PID"""
    return pid.split("/")[1]

def extract_dataset_pids(content, alias):
    """
    Returns a list of dictionarys of each dataset's ID and PID
    """

    datasets = []
    count = 0

    for resource in content:
        if resource.get('type') == 'dataset':
            pid = build_pid(resource)
            ds_id = resource.get('id')
            
            datasets.append({"dataset_id": ds_id, "persistent_id": pid, "dv_alias": alias})
            count += 1

    logger.info(f"{count} PIDs collected from dataverse.")

    return datasets

def extract_dataset_version(metadata):
    """Returns the version number of a dataset"""

    if 'versionNumber' in metadata:
        v = metadata.get('versionNumber')
        vm = metadata.get('versionMinorNumber', 0)
        return f"{v}.{vm}"
    else:
        v = metadata.get('versionState')
        return v

def format_version_record(version, filename, inventory_row):
    version_record = {
        "metadataLanguage": "es", 
        "datasetVersion": version,
        "inventory_data": inventory_row
    }

    json_path = Path(config.dv_data_dir)/Path(config.metadata_dir)
    write_json(version_record, json_path, filename)

def map_sociocultural_inventory(excel_file):
    """
    Fetches sociocultural data from I2D Inventory 
    """
    wb = openpyxl.load_workbook(excel_file, data_only=True)

    rows_sociocultural = read_xlsx(wb, "Socioecológico")
    sociocultural_index = {}
    
    for row in rows_sociocultural:
        url = row.get('URL Dataverse')
        if url and url.strip().lower().startswith(("http://", "https://")):
            resource_name = url.split("://")[-1].replace(".org/", ":")
            sociocultural_index[resource_name] = {
                'acceso_recurso': row.get('Acceso al recurso'),
                'fecha_liberacion': row.get('Fecha liberación'),
                'objeto_restriccion': row.get('Objeto de la restricción'),
                'proyecto': row.get('Proyecto'),
                'proyecto_macro': str(row.get('Proyecto Macro')).strip(),
                'contrato_convenio': row.get('Contrato/Convenio'),
                'doi': row.get('DOI'),
                'gbif_key': row.get('GBIF DATASET KEY'),
                'url': url
            }

    incoming_index = map_full_inventory(wb)
    incoming_index['sociocultural'] = sociocultural_index

    return incoming_index