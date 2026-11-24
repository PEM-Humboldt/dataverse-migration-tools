from pathlib import Path

from src.config import Config
from pyDataverse.models import Datafile
import json
import sys
import requests
import io
import time
from datetime import datetime
import zipfile
from src.utilitarios.logger import logger

config = Config()
total_files_names = json.loads('{}')

def take_version(filename):
    version = filename.split("-")[-1]

    if version == "DRAFT":
        return sys.maxsize

    major, minor = version.split(".")
    return int(major) + int(minor) / (len(minor) * 10)

def check_lock(DOI_NEW):
    print("==== Starting Check lock...")
    try:
        lock = config.api_target.get_dataset_lock(DOI_NEW)
        print("LOCK Response: ", lock)
        if lock.status_code == 503:
            logger.critical("503 - Server {} is unavailable".format(config.base_url_target))
            sys.exit()
        a = 0
        while len(lock.json()['data']) > 0 and a < 300:
            print("I'm inside the while... status is:", lock.status_code)
            logger.debug("Lock {} times {} {}".format(str(a), DOI_NEW, lock.json()))
            time.sleep(10)
            a = a + 1
            lock = config.api_target.get_dataset_lock(DOI_NEW)
            if lock.status_code == 503:
                logger.critical("503 - Server {} is unavailable".format(config.base_url_target))
                sys.exit()
            if lock.status_code != 200:
                logger.error("check_lock func: lock status {} for {}".format(lock.status_code, DOI_NEW))
                return False
    except Exception as e:
        logger.error("check_lock. Error {}, dataset {} ".format(e, DOI_NEW))
        return False
    return True

def find_extension(originalFileFormat):
    original = originalFileFormat.lower()
    if original == "application/x-spss-sav":
        return ".sav"
    elif original == "application/x-spss-por":
        return ".por"
    elif original == "application/x-stata":
        return ".dta"
    elif original == "application/x-dvn-csvspss-zip":
        return ".zip"
    elif original == "application/x-dvn-tabddi-zip":
        return ".zip"
    elif original == "application/x-rlang-transport":
        return ".RData"
    elif original == "text/csv":
        return ".csv"
    elif original == "text/comma-separated-values":
        return ".csv"
    elif original == "text/tsv":
        return ".tsv"
    elif original == "text/tab-separated-values":
        return ".tsv"
    elif original == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet":
        return ".xlsx"
    return ""

def publish_version(vm, DOI_NEW):
    print("==== Starting: Publish_version...")
    check = check_lock(DOI_NEW)

    print("--- Check lock response:", check)
    print("--- VM is: ", vm)
    if check == False:
        return check
    try:
        if vm != 0:
            resp = config.api_target.publish_dataset(DOI_NEW,'minor')
        else:
            resp = config.api_target.publish_dataset(DOI_NEW, 'major')

        print("--- After calling publish_dataset(), response is (fingers crossed): ", resp.json())
        if resp.status_code == 200:
            return True
        else:
            logger.error("publish_version func: Error publishing dataset {} status {}".format(DOI_NEW, resp.status_code))
            return False
    except Exception as e:
        logger.error("publish_version error. Error {}, dataset {} ".format(e, DOI_NEW))
        return False

    return True


def update_file_metadata(prev_file, file, field):
    if (field in file and field not in prev_file) or (field not in file and field in prev_file):
        return True
    else:
        if field in file and field in prev_file:
            if file[field] != prev_file[field]:
                return True

    return False

def check_add_files(files_list, total_files):
    add_files_list = []
    updated_files_list = []

    for file in files_list:
        old_id = file["dataFile"]["id"]
        if old_id not in total_files:
            add_files_list.append(file)
        else:
            prev_file = total_files[old_id]['file']
            update= update_file_metadata(prev_file, file, "description")
            if update:
                updated_files_list.append(file)
            else:
                update = update_file_metadata(prev_file, file, "label")
                if update:
                    updated_files_list.append(file)
                else:
                    update = update_file_metadata(prev_file, file, "directoryLabel")
                    if update:
                        updated_files_list.append(file)
                    else:
                        update = update_file_metadata(prev_file, file, "categories")
                        if update:
                            updated_files_list.append(file)
                        else:
                            update = update_file_metadata(prev_file, file, "restricted")
                            if update:
                                updated_files_list.append(file)
                            else:
                                update = update_file_metadata(prev_file, file, "provFreeform")
                                if update:
                                    updated_files_list.append(file)

    return add_files_list, updated_files_list

def check_delete_files(files_list, total_files):
    delete_files_list = []
    for id_old in total_files:
        found = False
        for file in files_list:
            id = file["dataFile"]["id"]
            if (id == id_old):
                found = True
                break
        if not found:
            delete_files_list.append(total_files[id_old]['file'])
    return delete_files_list

def delete_files(files_list, total_files, DOI_NEW):
    
    for file in files_list:
        old_id = file['dataFile']['id']
        new_id = total_files[old_id]['new_id']
        url = config.base_url_target + "/dvn/api/data-deposit/v1.1/swordv2/edit-media/file/" + str(new_id)
        check = check_lock(DOI_NEW)
        if check == False:
            return check
        req = requests.delete(url, auth=(config.api_token_target, ''))
        if req.status_code == 503:
            logger.critical("503 - Server is unavailable {}", config.base_url_target)
            sys.exit()
        if req.status_code == 200 or req.status_code == 204:
            del total_files[old_id]
        else:
            logger.error("delete_files func: Error to delete file in {}, with {}, status {}".format(DOI_NEW, url, req.status_code))
            return False
    return True

def update_files(files_list, total_files, DOI_NEW):
    headers = {'X-Dataverse-key': config.api_token_target}
    for file in files_list:
        old_id = file["dataFile"]["id"]
        new_id = total_files[old_id]['new_id']
        metadata_json = {}
        if 'description' in file:
            metadata_json["description"] = file['description']
        #if 'label' in file:
        #    metadata_json["label"] = file['label']
        if 'directoryLabel' in file:
            metadata_json["directoryLabel"] = file['directoryLabel']
        if 'categories' in file:
            metadata_json["categories"] = file['categories']
        if 'restricted' in file:
            metadata_json["restrict"] = file['restricted']
        if 'provFreeform' in file:
            metadata_json["provFreeform"] = file['provFreeform']

        url = config.base_url_target + '/api/files/{0}/metadata'.format(new_id)

        json_input = io.StringIO(json.dumps(metadata_json))
        files = { 'jsonData': json_input}
        check = check_lock(DOI_NEW)
        if check == False:
            return check
        resp = requests.post(url, files=files, headers=headers)
        logger.debug("Update file metadata status ".format(resp.status_code))
        if resp.status_code == 503: 
            logger.critical("503 - Server is unavailable {}", config.base_url_target)
            sys.exit()


def add_files(files_list, DOI_NEW, dir_path, total_files):
    print("====================== Loading files... =====================")
    print("--- Dirpath: ", dir_path)
    print("--- Files list: ", files_list)

    for file in files_list:
        logger.info("-----------------------");
        logger.info("==== Starting {0}".format(file["dataFile"]["filename"]))
        try:
            filename_zip = False
            filename = file["dataFile"]["filename"]
            index = file["dataFile"]['storageIdentifier'].rfind('/')
            storageIdentifier = file["dataFile"]['storageIdentifier'][index+1:]
            if 'originalFileFormat' in file["dataFile"]:
                originalFileFormat = file["dataFile"]['originalFileFormat']
                logger.info("Original file format {0}".format(originalFileFormat))
                ext = find_extension(originalFileFormat)
                index = filename.rfind(".")
                filename = filename[0:index] + ext
                typeFile = originalFileFormat
                storageIdentifier = storageIdentifier + ".orig"

            else:
                typeFile = file["dataFile"]["contentType"]
                if typeFile == "application/zip":
                    filename_zip = True
                    f_output = dir_path + '/' + filename
                    f_input = dir_path + '/' +storageIdentifier
                    with zipfile.ZipFile(f_output, 'w') as myzip:
                        myzip.write(f_input, filename)

            df = Datafile()
            logger.info("Type file {0}".format(typeFile))
            df_dict = {
                "pid": DOI_NEW,
                "filename": filename,
                'contentType': typeFile
            }
            if 'categories' in file:
                df_dict['categories'] = file['categories']
            if 'persistentId' in file["dataFile"]:
                df_dict['persistentId'] = file["dataFile"]['persistentId']
            if 'pidURL' in file["dataFile"]:
                df_dict['pidURL'] = file["dataFile"]['pidURL']
            if 'description' in file:
                df_dict['description'] = file['description']
            if 'restricted' in file:
                df_dict['restrict'] = file['restricted']
            if 'directoryLabel' in file:
                df_dict['directoryLabel'] = file['directoryLabel']
            #if 'label' in file:
            #    df_dict['label'] = file['label']
            if 'provFreeform' in file:
                df_dict["provFreeform"] = file['provFreeform']


            df.set(df_dict)
            logger.info(df.json());
            logger.info("It is filename {0}".format(filename))

            # ------ This part was commented 
            #if not filename_zip:
            #    full_filename = dir_path + '/'  + storageIdentifier
            #else:
            #    full_filename = dir_path + '/' + filename
            # ------ Until here
            import os 
            full_filename = os.path.join(dir_path, filename)

            url = config.api_target.base_url_api_native
            url += "/datasets/:persistentId/add?persistentId={0}".format(DOI_NEW)
            files = {'file': (filename, open(full_filename, 'rb'), typeFile)}
            headers = {'X-Dataverse-key': config.api_token_target}
            check = check_lock(DOI_NEW)
            if check == False:
                return check
            resp = requests.post(url, data={"jsonData": df.json()}, files=files, headers=headers)

            if resp.status_code == 503:
                logger.critical("503 - Server {} is unavailable".format(config.base_url_target))
                sys.exit()
            if resp.status_code == 200:
                old_id = file["dataFile"]["id"]

                total_files[old_id] = {
                    'new_id': resp.json()['data']['files'][0]['dataFile']['id'],
                    'file': file
                }
            else:
                logger.error("add_files func: Error adding file. Error {}, filename {}, storageIdentifier {}, directory {}".format(resp.status_code, filename, storageIdentifier, dir_path) )
                return False

        except Exception as e:
            logger.error("add_files error. Error {}, filename {}, storageIdentifier {}, directory {}".format(e, filename, storageIdentifier, dir_path))
            return False

    return True
def clean_version(version):
    print("==== Starting: clean version function...")
    if 'id' in version:
        del version['id']
    if 'datasetId' in version:
        del version['datasetId']
    if 'datasetPersistentId' in version:
        del version['datasetPersistentId']
    if 'storageIdentifier' in version:
        del version['storageIdentifier']
    if 'versionNumber' in version:
        del version['versionNumber']
    if 'versionMinorNumber' in version:
        del version['versionMinorNumber']
    if 'versionState' in version:
        del version['versionState']
    if 'UNF' in version:
        del version['UNF']
    if 'versionNote' in version:
        del version['versionNote']
    if 'releaseTime' in version:
        del version['releaseTime']
    if 'lastUpdateTime' in version:
        del version['lastUpdateTime']

    if 'files' in version:
        del version['files']


    #for 5.4.1 (Producer is mandatory)
    # producer = False
    # if 'metadataBlocks' in version:
    #     if 'citation' in version['metadataBlocks']:
    #         if 'fields' in version['metadataBlocks']['citation']:
    #             fields = version['metadataBlocks']['citation']['fields']
    #             for field in fields:
    #                 if field['typeName'] == 'producer':
    #                     producer = True
    #                     break
    # if not producer:
    #     fieldSubject = {
    #         "typeName": "producer",
    #         "multiple": True,
    #         "typeClass": "compound",
    #         "value": [
    #             {
    #                 "producerName": {
    #                     "typeName": "producerName",
    #                     "multiple": False,
    #                     "typeClass": "primitive",
    #                     "value": "UAL"
    #                 }
    #             }
    #         ]
    #     }
    #     if 'metadataBlocks' in version:
    #         if 'citation' in version['metadataBlocks']:
    #             if 'fields' in version['metadataBlocks']['citation']:
    #                 version['metadataBlocks']['citation']['fields'].append(fieldSubject)


    return version

def check_and_update_subject(version):
    subject = False
    if 'metadataBlocks' in version:
        if 'citation' in version['metadataBlocks']:
            if 'fields' in version['metadataBlocks']['citation']:
                fields = version['metadataBlocks']['citation']['fields']
                for field in fields:
                    if field['typeName'] == 'subject':
                        subject = True
                        break
    if not subject:
        fieldSubject = {
            "typeName": "subject",
            "multiple": True,
            "typeClass": "controlledVocabulary",
            "value": [
                "Other"
            ]
        }
        if 'metadataBlocks' in version:
            if 'citation' in version['metadataBlocks']:
                if 'fields' in  version['metadataBlocks']['citation']:
                    version['metadataBlocks']['citation']['fields'].append(fieldSubject)

    return version

def create_version(version, only, DOI, DOI_NEW, dir_path, total_files, correspondence, first):
    print("==== Starting: Create_version ==============")
    logger.info("==== Starting: Create_version ==============")
    try:
        # Deletes inventory_data from payload since Dataverse api will reject it otherwise
        print("--- Limpiando json ---")
        version.pop('inventory_data', None)
        payload = version

        try:
            if 'datasetVersion' in payload:
                target_version = payload['datasetVersion']
            else:
                target_version = payload

            if 'versionState' in target_version:
                if target_version['versionState'] == 'DEACCESSIONED':
                    return True, correspondence, first
                if target_version['versionState'] == 'DRAFT':
                    v = ':draft'
                    vm = 0
                else:
                    if 'versionNumber' in target_version:
                        v = target_version['versionNumber']
                        vm = target_version['versionMinorNumber']
            else:
                if 'versionNumber' in target_version:
                    print("I found a versionNumber!!! >.<")
                    v = target_version['versionNumber']
                    vm = target_version['versionMinorNumber']
                else:
                    print("Nothing!? 0.0")

            print(f"Running {v}-{vm} version")
            logger.info("--- Current version of dataset is : Major V: %s Minor V: %s", v, vm)

            if 'datasetId' in target_version:
                old_dataset_id = target_version['datasetId']
            else:
                old_dataset_id = 0

            print("Checkpoint 1 - Running as expected... ")

            if 'files' in target_version:
                files_list = target_version['files']

            target_version = clean_version(target_version)

            print("Checkpoint 2 - Running as expected... ")

            payload['datasetVersion'] = target_version

            print("Asking: Is it first version? ---->", first)

            # If it's the first version of the dataset, means the dataset still doesn't exists, it:
            # 1. Creates the dataset
            # 2. Creates a correspondance.json with the new ID and the old ID
            # 3. Add files to version, if it has them.
            # 4. Checks if is a draft or a published version.
            if first:
                print("--- About to upload first version with identifier: ", DOI)
                if (v != ':draft'):
                    print("It's first but is a draft.")
                    resp = config.api_target.create_dataset(config.dv_socioecologico_alias, payload, DOI, False)
                else:
                    print("It's first and NOT a draft.")
                    resp = config.api_target.create_dataset(config.dv_socioecologico_alias, payload)
                    if resp.status_code == 201:
                        ### IMPORTANTE sobre DOI AND DOI_NEW -> En un principio los dos son lo mismo, o 'None' o 'doi.../...'. En este punto
                        # se bifurca la cosa: DOI pasa a ser solo el identificador por ejemplo 5CKICO mientras que DOI_NEW se mantiene o pasa a ser
                        # 'doi.../...'
                        DOI_NEW = resp.json()['data']['persistentId']
                        print("❗ IMPORTANT : THIS IS THE DOI CREATED IN TARGET (should be the original). New is ", DOI_NEW, " original is ", DOI)
                    else:
                        print("❗ Something may have happened. Check response below.")
                        print(resp.json())

                print("UPLOAD of first version is DONE - RESPONSE IS: ", resp.status_code)
                print(resp.json())
                print("Checkpoint 3 - Running as expected... ")

                if resp.status_code == 503:
                    print("❌ Critical error. Check logs.")
                    logger.critical("503 - Server {} is unavailable".format(config.base_url_target))
                    sys.exit()
                if resp.status_code == 200 or resp.status_code == 201:
                    print(" ✅ Creation of dataset's version was sucessfull")

                    first = False
                    new_dataset_id = resp.json()['data']['id']
                    print("The newly created dataset's id  is: ", new_dataset_id)
                    persistentId = resp.json()['data']['persistentId']
                    new_doi = persistentId.split("/")[1]
                    if DOI is None:
                        DOI = new_doi
                        DOI_NEW=persistentId 
                    print("The new DOI is ", new_doi, " and DOI_NEW is ", DOI_NEW)

                    correspondence[old_dataset_id] = new_dataset_id # old dataset id with new one

                    # print(" IMPORTANT!!!!!!!!!!!!!!!!!!! ----> Temporarily commenting add_files(), I need to check this later!!!")

                    print("--- About to add files to newly created dataset", files_list,  DOI_NEW, dir_path, total_files)
                    #status = add_files(files_list,  DOI_NEW, dir_path, total_files)
                    status = True # Setting to True for testing only, this line most be deleted after !!!!!!
                    print("File upload done. Status is ", status)

                    if status == False:
                        return False, correspondence, first, DOI, DOI_NEW
                    if v != ':draft':
                        print("--- I SHOULD BE PUBLISHING!")
                        status = publish_version(vm, DOI_NEW)
                        print("--- And my status isssssssssssssssssssssssss", status)
                        if status == False:
                            return False, correspondence, first, DOI, DOI_NEW
                else:
                    logger.error("create_version func: Create dataset error for {}, status {}".format( DOI, resp.status_code))
                    return False, correspondence, first, DOI, DOI_NEW
            # 5. If it's not a first version, it updated (put_request) metadatablocks and then checks for new/modified/deleted files.
            # 6. If new version is not a draft, then it publishes it.
            else:
                # Update metadata
                payload = check_and_update_subject(payload['datasetVersion'])
                if "datasetVersion" in payload:
                    payload = payload["datasetVersion"]
                else:
                    payload = payload

                # Checks the current dataset's ID
                api_url = "/api/datasets/:persistentId?persistentId={0}".format(DOI_NEW)
                url = config.dv_origin_url + api_url 
                r = config.api_target.get_request(url, auth=True)
                dataset_id = r.json()['data']['id']

                # Uses said ID to send the put_request to update the metadata
                payload['datasetId']=dataset_id
                api_url = "/api/datasets/:persistentId/versions/:draft?persistentId={0}".format(DOI_NEW)
                url = config.dv_origin_url + api_url 
                check_lock(DOI_NEW)
                r = config.api_target.put_request(url, data=json.dumps(payload), auth=True)

                if r.status_code == 503:
                    logger.critical(" ❌ 503 - Server {} is unavailable".format(config.base_url_target))
                    sys.exit()
                if r.status_code != 200:
                    logger.error("❌ create_version func: Update dataset metadata error for {}, status {}".format(DOI, r.status_code) )
                    return False, correspondence, first

                print("Checkpoint 3 (working with a non-first version) - Running as expected... ")
                print("✅ Put request worked correctly. Metadata is updated for new version!")

                # Starting files update
                print("--- Updating files now. Side note: I haven't been able to correctly check the file upload/update yet, so I don't think it's going to work.")

                print("Files list: ", files_list)
                print("Total files: ", total_files)

                # Delete files
                # du_files = check_delete_files(files_list, total_files)
                # print("--- Deleting files ... ", du_files)
                # if len(du_files) > 0:
                #     status = delete_files(du_files, total_files, DOI_NEW)
                #     if status == False:
                #         return False, correspondence, first
                #     r = config.api_target.get_dataset(DOI_NEW, ":latest")
                #     if r.status_code == 503:
                #         logger.critical("503 - Server {} is unavailable".format(config.base_url_target))
                #         sys.exit()
                #     if r.status_code != 200:
                #         logger.error("create_version func: Get dataset metadata error for {}, status {}".format(DOI, r.status_code ))
                #         return False, correspondence, first
                #     fields = r.json()['data']['latestVersion']['metadataBlocks']['citation']['fields']
                #     for field in fields:
                #         if field['typeName'] == 'producer':
                #             fs = payload['metadataBlocks']['citation']['fields']
                #             ex = False
                #             for f in fs:
                #                 if field['typeName'] == 'producer':
                #                     ex = True
                #                     break
                #             if not ex:
                #                 payload['metadataBlocks']['citation']['fields'].append(field)
                #             break

                # # Add files
                # print("--- Adding files ...")
                # a_files = check_add_files(files_list, total_files)
                # print("These are the new files found:", a_files)
                # status = add_files(a_files[0], DOI_NEW, dir_path, total_files)
                # print("Finished adding the new files. Status =>", status)
                # if status == False:
                #     return False, correspondence, first, DOI, DOI_NEW

                # print("I'm about to update files...")
                # update_files(a_files[1], total_files, DOI_NEW)

                print("In this version: ", v)
                if v != ':draft':
                    print("--- All the files were updated and this is NOT a draft. I'm going to publish the new version right now!! ")
                    status = publish_version(vm, DOI_NEW)
                    print("Finished publishing new version. STATUS HERE", status)
                    if status == False:
                        return False, correspondence, first, DOI, DOI_NEW

        except Exception as e:
            logger.error("create_version func: dataset {} Error {}".format(DOI,e))
            return False, correspondence, first, DOI, DOI_NEW

        return True, correspondence, first, DOI, DOI_NEW
    except Exception as e:
        logger.error("An error occured while creating the versions.", e)
        print("ERROR while creating the versions. Check logs!")

def get_datasets(parent, datasets):

    resp = config.api_origin.get_dataverse_contents(parent)
    if resp.status_code == 200:
        dataverses = resp.json()['data']
        if len(dataverses) != 0:
            for elem in dataverses:
                if elem['type'] == 'dataverse':
                    datasets = get_datasets(elem['id'], datasets)

                if elem['type'] == 'dataset':
                    datasets.append(elem['identifier'])

    return  datasets

def main():
    print("==== Starting main...")
    logger.info("==== Starting resources upload to Dataverse version 6.10.1...")
    now = datetime.now()
    logger.info("Program started {}".format(now))
    mapped_datasets = Path(config.dv_data_dir) / "final_mapped"
    logger.info(f"Using {mapped_datasets} as source")
    num_dirs = sum(1 for item in mapped_datasets.iterdir() if item.is_dir())
    logger.info(f"Number of mapped resources to upload: {num_dirs}")
    correspondence = {}
    all_total_files = {}
    for directory in mapped_datasets.iterdir():
        print(f"/////////////// Starting to upload data for {directory.name} ///////////////")
        logger.info(f"/////////////// Starting to upload data for {directory.name} ///////////////")
        try:
            now = datetime.now()
            logger.info("Dataset {} started {} ".format(directory, now))
            total_files = json.loads('{}')

            # Captures DOI (Dataset identifier)
            print("DIRECTORY ", directory, " NAME ", directory.name)
            DOI = config.prefix_DOI + "/" + directory.name
            
            # Path where files are saved
            dir_path = Path(config.dv_data_dir) / "files" / directory.name

            DOI_NEW = DOI

            sorted_versions = sorted(
                [f for f in directory.iterdir() if f.is_file()],
                key=lambda f: take_version(f.stem)
            )

            if len(sorted_versions) == 1:
                only = True
            else:
                only = False

            first = True
            for version in sorted_versions:
                print(f" ----- Working with {version.name} version -------- ")
                logger.info(f" ----- Working with {version.name} version -------- ")
                """ ⚠️⚠️⚠️⚠️⚠️⚠️ ¡¡¡¡¡¡¡¡¡¡¡MUCHO CUIDADO!!!!!!! ¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡¡WARNING EXTREMO!!!!!!!!!!!!!!!!!!!!!!!!!!!!! ⚠️⚠️⚠️⚠️⚠️⚠️⚠️
                Las siguientes lineas comentadas destruirán el dataset en el origen. Este paso será necesario para poder publicar a Crossref los nuevos
                recursos en la instancia final. Esto sólo debe probarse apuntando a un ambiente de origen LOCAL y controlado, de lo contrario podría ocasionar
                pérdidas de información en producción. ¡MUCHA PRECAUCIÓN!"""

                #logger.info("Here the dataset should be destroyed but i wont do that for now.")
                #resp = config.dv_origin_url.destroy_dataset(DOI)
                #if resp.status_code != 200:
                #     logger.warning("main func: Cannot destroy dataset {}, status {} ".format(DOI, resp.status_code))
                """ ----------- ⚠️⚠️⚠️⚠️⚠️⚠️ ----------- """

                # Reads version's stored json                 
                with open(version, 'r', encoding='utf-8') as file:
                    version_data = json.load(file)

                logger.info(f"==== Starting Version creation now for {DOI}")

                cv = create_version(version_data, only, DOI, DOI_NEW, dir_path, total_files, correspondence, first)

                print("--- Final response aster create_version is ", cv)
                correspondence = cv[1]
                cv_status = cv[0]
                first = cv[2]
                print("............ Finishing. correspondance, cv_status, first: ", correspondence, cv_status, first)
                #if cv_status == False:
                #    break
                if cv_status == False:
                    logger.error("main func: Cannot create version for {}".format(DOI))
                    #continue
                    raise RuntimeError(f"Massive error. Can't create {version.name}")
                now = datetime.now()
                logger.info("Dataset {} ended {} ".format(directory, now))
        except Exception as e:
            logger.error("Error with dataset {}, Error {}".format( directory, e))
        try:
            for t in total_files:
                all_total_files[t] = total_files[t]["new_id"]
        except Exception as e:
            print("An exception occured! Check the logs for more info.")
            logger.error(e)
    
    with open('correspondence_old_new.json', 'w') as outfile:
        json.dump(correspondence, outfile, indent=4, sort_keys=True)
    with open('all_data_files.json', 'w') as outfile:
        json.dump(all_total_files, outfile, indent=4, sort_keys=True)
    now = datetime.now()
    logger.info("Program ended {}".format(now))

if __name__ == "__main__":
    main()
