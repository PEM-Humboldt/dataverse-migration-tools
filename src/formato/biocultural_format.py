from pathlib import Path
from src.utilitarios.logger import logger
from src.config import Config
from src.utilitarios.files import write_json

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

def format_version_record(version, filename):
    version_record = {
        "metadataLanguage": "es", 
        "datasetVersion": version
    }

    json_path = Path(config.dv_data_dir)/Path(config.metadata_dir)
    write_json(version_record, json_path, filename)