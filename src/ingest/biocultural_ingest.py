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

    try:
        version = config.api_origin.get_info_version()
        write_json(version.json(), config.dv_data_dir, "version.json")

        r = config.api_origin.get_metadatablocks()
        metadatablocks = r.json()['data']

        for block in metadatablocks:
            b = config.api_origin.get_metadatablock(block['name'])

            path = Path(config.dv_data_dir) / "metadatablocks"
            file_name = f"{block['name']}.json"
            write_json(b.json()['data'], path , file_name)

        logger.info(f"The server was succesfully harvested! Check your data directory.")
    except Exception as e:
        logger.exception("An error occured while harvesting the server!")

def set_dataset_pid(item):
    """Persistent identifier of a `dataset` item of /contents (protocol, authority, separator, identifier).

    Built from the item's fields, not from a fixed prefix: some datasets have another
    prefix (doi:10.5072/FK2/MH9E0K, a DataCite test DOI).
    """
    return f"{item['protocol']}:{item['authority']}{item.get('separator', '/')}{item['identifier']}"

def get_datasets_pid():
    """Loops over all dataverses and gets all dataset's basic data. 
    Writes a CSV inventory to keep track of all datasets in each dataverse.
    Writes two JSONs for each dataverse: one with dataverse data and one referencing all the datasets included
    Returns a list of dictionarys of each dataset's ID and PID
    """

    logger.info("Fetching all PIDs from all datasets...")
    dataset_list = []
    datasets = []
    dv_list = [{'id': 1, 'alias': ':root'}]

    # Fetches all dataverses alias
    dataverses = config.api_origin.get_children(children_types='dataverses')
    for dv in dataverses : dv_list.append({'id': dv.get('dataverse_id'), 'alias': dv.get('dataverse_alias')})

    # Iterates over each dataverse
    for dv in dv_list:
        dv_id = dv['id']
        alias = dv['alias']
        
        count = 0
        try:
            # Fetches dataverse data
            dv_data = config.api_origin.get_dataverse(dv_id)
            write_json(dv_data.json()['data'], Path(config.dv_data_dir) / "collections", f"{alias}.json")

            # Gets all datasets for each dataverse
            dv_contents = config.api_origin.get_dataverse_contents(identifier=alias)
            content = dv_contents.json()['data']
            write_json(content, Path(config.dv_data_dir) / "collections", f"{alias}_contents.json")


            # Appends each dataset's pid
            for resource in content:
                if resource.get('type') == 'dataset':
                    pid = set_dataset_pid(resource)
                    ds_id = resource.get('id')
                    
                    dataset_list.append({'id': ds_id, 'pid': pid})
                    datasets.append({"persistent_id": pid, "dataset_id": resource["id"],
                                                     "collection": alias})
                    
                    count += 1

            logger.info(f"{count} PIDs collected from dataverse {alias}.")

        except Exception as e:
            logger.exception(f"An error occured while fetching the PIDS: {e}")

    
    # Write CSV inventory
    write_csv(datasets, config.dv_data_dir, "inventory.csv")
    
    logger.info(f"PID recollection finished correctly: {len(dataset_list)} PIDs collected.")
    return dataset_list

def get_identifier(pid):
    return pid.split("/")[1]

def fetch_all_versions(dataset_list):
    """Loops over each dataset and:
    Returns a dictionary for each version and saves it as JSON
    Downloads the files from each version
    """

    logger.info("Fetching all versions from all datasets...")

    successes = 0
    fails = 0
    current_v = 0

    # Loops over all datasets
    for dataset in dataset_list:

        id = dataset['id']
        pid = dataset['pid']
        count = 0
        logger.info(f"======= Downloading metadata and files from {pid} =======")

        try:
            # Fetches all versions for current dataset
            result = config.api_origin.get_dataset_versions(identifier=id, is_pid=False)
            versions = result.json()['data']

            # Loops over each version
            for version in versions:

                # Gets current version number
                if 'versionNumber' in version:
                    v = version['versionNumber']
                    vm = version['versionMinorNumber']
                    current_v = f"{v}.{vm}"
                else:
                    v = version['versionState']
                    current_v = v

                # Sets correct version format
                version_record = {
                    "metadataLanguage": "es", 
                    "datasetVersion": version
                }

                # Creates filename using identifier (drops prefix) and version
                identifier = get_identifier(pid)
                filename = f"{identifier}-{current_v}.json"
                
                # Saves version as JSON
                json_path = Path(config.dv_data_dir)/Path(config.metadata_dir)
                write_json(version_record, json_path, filename)
                logger.info(f"Verion {current_v} metadata for dataset {pid} correctly saved as JSON.")

                # Download version's files as ZIP
                download_files(pid, current_v)
                logger.info(f"Version's {current_v} metadata for dataset {pid} correctly saved as JSON.")
                count += 1
                successes += 1

            logger.info(f"For dataset {pid}, {count} version(s) succesfully downloaded.")
        except Exception as e:
            fails += 1
            logger.exception(f"Some error occured while downloading datasets version {current_v} for {pid} - ERROR: {e}")

    logger.info(f"Versions download completed for {len(dataset_list)} datasets! {successes} versions succesfully downloaded - {fails} versions download fails")

def download_files(pid, current_v):
    """Makes an API call to download all files from version in a ZIP and saves them to disk
    """
        
    try:
        version = ':draft' if current_v == 'DRAFT' else current_v
        api_url = f"/api/access/dataset/:persistentId/versions/{version}?persistentId={pid}" #probar
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

        identifier = get_identifier(pid)
        folder_name = f"{identifier}-{current_v}"

        if response.status_code == 200:
            # Saves files
            files_path = Path(config.dv_data_dir)/Path(config.files_dir)
            save_file_as_stream(response, files_path, folder_name, "files.zip")
        else:
            api_message = response.json().get("message", "No details available")
            logger.error(f"Error while fetching the files for {pid}, response is {response.status_code} - {api_message}")
    except Exception as e:
        logger.exception(f"An error occured while downloading the dataset's files for {pid} - ERROR: {e}")

def main():
    logger.info("=============== Ingesting BioCultural's resources ===============")
    logger.info("Starting main...")

    harvest_server()
    dataset_list = get_datasets_pid()
    fetch_all_versions(dataset_list)

if __name__ == "__main__":
    main()