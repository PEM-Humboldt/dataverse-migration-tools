import json
from pathlib import Path

import requests
from src.formato.biocultural_format import extract_pid_identifier
from src.utilitarios.files import read_csv, load_json_metadata
from src.config import Config

config = Config()

def load():
    datasets = read_csv(Path(config.dv_data_dir) / "inventory.csv")
    for d in datasets:
        pid = d['persistent_id']
        identifier = extract_pid_identifier(pid)

        files_metadata = (Path(config.dv_data_dir)/config.metadata_dir).glob(f"{identifier}-*.json")

        for file in files_metadata:

            version_folder = file.stem
            versions_files_path = Path(config.dv_data_dir) / config.files_dir / version_folder

            if not versions_files_path.exists():
                print(f"No existe la carpeta: {versions_files_path}")
                continue

            json = load_json_metadata(Path(config.dv_data_dir)/config.metadata_dir, file.name)

            for file_metadata in json.get("datasetVersion").get("files", []):
                data_file = file_metadata["dataFile"]

                file_path = versions_files_path / data_file['filename']

                if not file_path.exists():
                    print(f"No existe el archivo {file_path}")
                    continue

                file_data = {
                    'pid': pid,
                    'version': version_folder,
                    'label': file_path.name,
                    'id': data_file['id'],
                    'checksum': data_file['checksum']['value'],
                    'size': data_file['filesize']
                }
                print("=========================================================")
                print(file_data)

                storage_id = direct_upload(file_data, file_path)
                generate_json_data(pid, file_metadata, storage_id)

def direct_upload(data, file_path):
    pid = data['pid']
    size = data['size']

    api_url = f"/api/datasets/:persistentId/uploadurls"
    url = config.dv_target_url + api_url 
    params = {
        "persistentId": pid,
        "size": size
    }

    response = requests.get(
        url=url,
        params=params,
        headers={"X-Dataverse-key": config.dv_target_api_token},
    )

    r = response.json()
    if r.get("status") != "OK":
        raise RuntimeError(r.get("message", "Error requesting upload URLs"))

    response_data = r["data"]
    data_storage_identifier = response_data.get('storageIdentifier')

    # Obtener todas las URLs
    if "url" in response_data:
        urls = {"1": response_data["url"]}
    else:
        urls = response_data["urls"]
    print("OBTUVE LAS URLS!!!!!!!!!!!!!!!!!! V", urls)

    if len(urls) > 1:
        etags = {}
        part_size = response_data["partSize"]

        for part_number, url in urls.items():

            chunk = file.read(part_size)
            response = requests.put(
                        url=url,
                        data=chunk,
                        headers={"x-amz-tagging": "dv-state=temp"},
                    )
            if response.status_code != 200:
                raise RuntimeError(
                    f"Error subiendo archivo a S3: {response.status_code} - {response.text}"
                )
            
            print("Status:", response.status_code)
            print("Headers:", response.headers)
            print("Body:", response.text)
            
            etag = response.headers.get("ETag")

            if not etag:
                raise RuntimeError(f"No se recibió ETag para la parte {part_number}")
            etags[part_number] = etag

        response = requests.put(
            config.dv_target_url + response_data["complete"],
            json=etags,
            headers={"X-Dataverse-key": config.dv_target_api_token}
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"Error completando carga multipart: "
                f"{response.status_code} - {response.text}"
            )

    else:
        with open(file_path, "rb") as file:
            response = requests.put(
                url=urls["1"],
                data=file,
                headers={"x-amz-tagging": "dv-state=temp"},
            )

            if response.status_code != 200:
                raise RuntimeError(
                    f"Error subiendo archivo a S3: {response.status_code} - {response.text}"
                )

            print("Status:", response.status_code)
            print("Headers:", response.headers)
            print("Body:", response.text)

    return data_storage_identifier

def generate_json_data(pid, data, storage_id):
    print(data)
    json_data = {
        'description': data.get('description', ""),
        'categories':data.get('categories', []), 
        'restrict':data.get('restricted', False), 
        'storageIdentifier': storage_id,
        'fileName':data.get('dataFile').get('filename', ""), 
        'mimeType':data.get('dataFile').get('contentType'), 
        'checksum': {'@type': data['dataFile']['checksum']['type'], '@value': data['dataFile']['checksum']['value']}
    }

    api_url = "/api/datasets/:persistentId/add"
    url = config.dv_target_url + api_url
    params = {
        "persistentId": pid
    }
    r = requests.post(
        files={
        "jsonData": (None, json.dumps(json_data))
        },
        url=url,
        params=params,
        headers={"X-Dataverse-key": config.dv_target_api_token},
    )

    print("MY FINAL RESPONSE IS ====>>>>>>>>>>>>>>>>>>>>>>>")
    print(r.json())
    
def main():
    load()

if __name__ == '__main__':
    main()