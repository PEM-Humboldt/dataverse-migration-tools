from src.config import Config
import requests
from src.utilitarios.logger import logger
from src.utilitarios.storage import save_json_metadata, save_file

config = Config()

def get_datasets_pid():
    logger.info("Fetching all PIDs from all datasets...")
    pid_list = []

    # Iterates over each dataverse
    for dv in config.dataverse_names:
        try:
            # Gets all datasets in current dataverse
            result = config.api_origin.get_dataverse_contents(dv)
            dataset_list = result.json()['data']

            # Appends each dataset's pid
            for dataset in dataset_list:
                id = dataset.get('identifier')
                if id is not None: pid_list.append(id)
        except Exception as e:
            logger.error(f"An error occured while fetching the PIDS: {e}")

    logger.info("All PIDs where correctly collected.")
    return pid_list

def fetch_all_versions(pid_list):
    logger.info("Starting dataset's versions download...")
    
    for pid in pid_list:
        try:
            prefix = config.doi_prefix
            DOI = prefix+'/'+pid

            # Fetches all versions for each dataset
            result = config.api_origin.get_dataset_versions(identifier=DOI)
            versions = result.json()['data']

            for version in versions:
                # Gets current version number
                if 'versionNumber' in version:
                    v = version['versionNumber']
                    vm = version['versionMinorNumber']
                    current_v = f"{v}_{vm}"
                else:
                    v = version['versionState']
                    current_v = v

                # Sets correct version format
                version_record = {
                    "metadataLanguage": "es", 
                    "datasetVersion": version
                }

                # Saves version as JSON
                save_json_metadata(version_record, config.dv_metadata_directory, pid, current_v)

                download_files(DOI, pid, current_v)
        except Exception as e:
            logger.error(f"An error occured while fetching datasets versions for {DOI} - ERROR: {e}")

    logger.info("Versions download completed.")

def download_files(DOI, pid, current_v):
    try:
        api_url = f"/api/access/dataset/:persistentId/?persistentId={DOI}"
        url = config.dv_origin_url + api_url 

        params = {
            "persistentId": DOI,
            "format": "original"
        }

        response = requests.get(
            url=url,
            headers={"X-Dataverse-key": config.dv_origin_api_token},
            params=params,
            stream=True,
            allow_redirects=True
        )

        save_file(response, config.dv_files_directory, pid, current_v, "files.zip")
    except Exception as e:
        logger.error(f"An error occured while downloading the dataset's files for {DOI} - ERROR: {e}")

def main():
    logger.info("Starting main...")
    list = get_datasets_pid()
    fetch_all_versions(list)

if __name__ == "__main__":
    main()