from src.config import Config
import requests
from src.utilitarios.logger import logger
from src.utilitarios.storage import save_json_metadata, save_file_as_stream

config = Config()

def get_datasets_pid():
    logger.info("Fetching all PIDs from all datasets...")
    pid_list = []
    dv_list = [':root']

    # Fetches all dataverses alias
    dataverses = config.api_origin.get_children(children_types='dataverses')
    for dv in dataverses : dv_list.append(dv.get('dataverse_alias'))

    # Iterates over each dataverse
    for dv in dv_list:
        count = 0
        try:
            # Gets all datasets for each dataverse
            content = config.api_origin.get_children(parent=dv, children_types='datasets')

            # Appends each dataset's pid
            for resource in content:
                count += 1
                pid_list.append(resource.get('pid'))

            logger.info(f"{count} PIDs collected from dataverse {dv}.")

        except Exception as e:
            logger.exception(f"An error occured while fetching the PIDS: {e}")

    logger.info(f"PID recollection finished correctly: {len(pid_list)} PIDs collected.")
    return pid_list

def fetch_all_versions(pid_list):
    logger.info("Fetching all versions from all datasets...")

    successes = 0
    fails = 0
    current_v = 0

    # Loops over all datasets
    for pid in pid_list:
        count = 0
        logger.info(f"======= Downloading metadata and files from {pid} =======")

        try:
            # Fetches all versions for current dataset
            result = config.api_origin.get_dataset_versions(identifier=pid)
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
                identifier = pid.split("/")[1]
                filename = f"{identifier}-{current_v}.json"
                
                # Saves version as JSON
                save_json_metadata(version_record, config.dv_metadata_directory, filename)
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

    logger.info(f"Versions download completed for {len(pid_list)} datasets! {successes} versions succesfully downloaded - {fails} versions download fails")

def download_files(pid, current_v):
    try:
        api_url = f"/api/access/dataset/:persistentId/?persistentId={pid}"
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

        folder_name = f"{pid}-{current_v}"

        if response.status_code == 200:
            # Saves files
            save_file_as_stream(response, config.dv_files_directory, folder_name, "files.zip")
        else:
            logger.error(f"Error while fetching the files for {pid}, response is {response.status_code}")
    except Exception as e:
        logger.exception(f"An error occured while downloading the dataset's files for {pid} - ERROR: {e}")

def main():
    logger.info("=============== Ingesting BioCultural's resources ===============")
    logger.info("Starting main...")
    pid_list = get_datasets_pid()
    fetch_all_versions(pid_list)

if __name__ == "__main__":
    main()