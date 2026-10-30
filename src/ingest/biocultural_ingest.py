from pathlib import Path

from src.config import Config
import requests
from src.utilitarios.logger import logger
from src.utilitarios.files import write_json, save_file_as_stream, write_csv

config = Config()

def harvest_server():
    """Dataverse version and metadata block definitions

    The list of blocks is requested to discover their names ;
    only the definitions are saved.
    """

    logger.info("Harvesting server ...")

    version = config.api_origin.get_info_version()

    path = Path(config.dv_data_dir)
    write_json(version.json(), path, "version.json")

    save_metadatablocks(path)

    logger.info(f"The server was succesfully harvested! Check your data directory.")

def save_metadatablocks(path):
    r = config.api_origin.get_metadatablocks()
    metadatablocks = r.json()['data']

    for block in metadatablocks:
        b = config.api_origin.get_metadatablock(block['name'])

        filepath =  path / "metadatablocks"
        file_name = f"{block['name']}.json"
        write_json(b.json()['data'], filepath , file_name)

    logger.info(f"The server's metadatablocks were succesfully saved! Check your data directory.")  

def fetch_all_dataverses():
    logger.info("Fetching all Dataverses...")

    dv_list = [{'id': 1, 'alias': ':root'}]

    # Fetches all dataverses alias
    dataverses = config.api_origin.get_children(children_types='dataverses')
    for dv in dataverses: 
        dv_list.append({
            'id': dv.get('dataverse_id'), 
            'alias': dv.get('dataverse_alias')
        })

    return dv_list

def fetch_dataverse_content(alias):
    # Gets all datasets for each dataverse
    dv_contents = config.api_origin.get_dataverse_contents(identifier=alias)
    content = dv_contents.json()['data']

    return content

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
    
def fetch_dataset_versions(dataset):
    """Returns a dictionary for each version and saves it as JSON
    Downloads the files from each version
    """

    current_v = 0
    id = dataset.get('dataset_id')
    pid = dataset.get('persistent_id')

    logger.info(f"======= Downloading metadata and files from {pid} =======")

    # Fetches all versions for current dataset
    result = config.api_origin.get_dataset_versions(identifier=id, is_pid=False)
    versions = result.json()['data']

    # Loops over each version
    for version in versions:

        # Gets current version number
        identifier = extract_pid_identifier(pid)
        current_v = get_dataset_version(version)
        filename = f"{identifier}-{current_v}.json"

        version_record = {
            "metadataLanguage": "es", 
            "datasetVersion": version
        }

        json_path = Path(config.dv_data_dir)/Path(config.metadata_dir)
        write_json(version_record, json_path, filename)

        download_version_files(pid, current_v)

    logger.info(f"For dataset {pid}, {len(versions)} version(s) succesfully downloaded.")

def download_version_files(pid, current_v):
    """Makes an API call to download all files from version in a ZIP and saves them to disk
    """
    version = ':draft' if current_v == 'DRAFT' else current_v
    api_url = f"/api/access/dataset/:persistentId/versions/{version}"
    url = config.dv_origin_url + api_url 

    params = {
        "persistentId": pid,
        "format": "original"
    }

    response = requests.get(
        url=url,
        headers={"X-Dataverse-key": config.dv_origin_api_token},
        params=params,
        stream=True,
        allow_redirects=True
    )

    identifier = extract_pid_identifier(pid)
    folder_name = f"{identifier}-{current_v}"

    if response.status_code == 200:
        files_path = Path(config.dv_data_dir)/Path(config.files_dir)
        save_file_as_stream(response, files_path, folder_name, "files.zip")
    else:
        api_message = response.json().get("message", "No details available")
        raise RuntimeError(f"Error while fetching the files for {pid}, response is {response.status_code} - {api_message}")

def extract_pid_identifier(pid):
    return pid.split("/")[1]

def get_dataset_version(metadata):
    if 'versionNumber' in metadata:
        v = metadata.get('versionNumber')
        vm = metadata.get('versionMinorNumber', 0)
        return f"{v}.{vm}"
    else:
        v = metadata.get('versionState')
        return v

def build_pid(item):
    """Persistent identifier of a `dataset` item of /contents (protocol, authority, separator, identifier).

    Built from the item's fields, not from a fixed prefix: some datasets have another
    prefix (doi:10.5072/FK2/MH9E0K, a DataCite test DOI).
    """
    return f"{item['protocol']}:{item['authority']}{item.get('separator', '/')}{item['identifier']}"

def main():
    logger.info("=============== Ingesting BioCultural's resources ===============")
    logger.info("Starting main...")

    try:
        harvest_server()
        dataverses = fetch_all_dataverses()
    except Exception as e:
        logger.exception("Fatal error during server harvesting! Aborting process.")
        return

    successes = 0
    fails = 0
    all_datasets = []
    collections_dir = Path(config.dv_data_dir) / "collections"

    for dv in dataverses:
        dv_id = dv['id']
        alias = dv['alias']

        logger.info(f"Starting to fetch data from {alias} dataverse...")
            
        try:
            # Fetches general Dataverse data
            dv_data = config.api_origin.get_dataverse(dv_id)
            write_json(dv_data.json()['data'], collections_dir, f"{alias}.json")

            # Gets a resume of the content inside the current dataverse
            content = fetch_dataverse_content(alias)
            write_json(content, collections_dir, f"{alias}_contents.json")

            # Get's ID and PID of each dataset inside current dataverse
            dataset_list = extract_dataset_pids(content, alias)
            all_datasets.extend(dataset_list)

        except Exception as e:
            logger.exception(f"Failed to fetch metadata or contents for dataverse {alias}. Skipping.")
            continue

        for dataset in dataset_list:
            pid = dataset.get('persistent_id')
            try:
                fetch_dataset_versions(dataset)
                successes+=1
            except Exception as e:
                fails+=1
                logger.exception(f"Failed to process dataset {pid}")

    # Write CSV inventory
    if all_datasets:
        write_csv(all_datasets, config.dv_data_dir, "inventory.csv")

    logger.info(f"Process finished. A total of {successes + fails} datasets reviewed. Number of successes: {successes} - Number of {fails}")
if __name__ == "__main__":
    main()