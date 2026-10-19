import json
from pathlib import Path
from src.utilitarios.logger import logger

# Raíz del proyecto (3 niveles arriba desde src/utils/storage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def save_json_metadata(data, metadata_directory, id, current_v):
    raw_dir = BASE_DIR / metadata_directory
    raw_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{id}_{current_v}.json"
    raw_filepath = raw_dir / filename

    with open(raw_filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_file(response, file_directory, id, current_v, filename):
    folder_name = id + '_' + current_v
    raw_dir = BASE_DIR / file_directory / folder_name
    raw_dir.mkdir(parents=True, exist_ok=True)
    zip_filepath = raw_dir / filename

    if response.status_code == 200:
        with open(zip_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        print(f"ZIP de {id}_{current_v} descargado exitosamente en: {zip_filepath}")
    else:
        print(f"Error {response.status_code} al descargar el ZIP de {id}_{current_v} - ERROR: {response.text}")
        logger.error(f"ERROR getting files for {id}_{current_v}")

def load_json_metadata(file_directory, filename):
    file = BASE_DIR / file_directory / filename
    
    with open(file, "r", encoding='UTF-8') as f:
        metadata_dict = json.load(f)
    return metadata_dict