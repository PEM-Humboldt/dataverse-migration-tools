import json
from pathlib import Path
from src.utilitarios.logger import logger

# Raíz del proyecto (3 niveles arriba desde src/utils/storage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def save_json_metadata(data, metadata_directory, filename):
    try:
        raw_dir = BASE_DIR / metadata_directory
        raw_dir.mkdir(parents=True, exist_ok=True)
        raw_filepath = raw_dir / filename

        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise RuntimeError(f"An error ocurred while saving the JSON file in {raw_filepath}") from e

def save_file_as_stream(response, file_directory, folder_name, filename):
    try:
        raw_dir = BASE_DIR / file_directory / folder_name
        raw_dir.mkdir(parents=True, exist_ok=True)
        zip_filepath = raw_dir / filename

        with open(zip_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
    except Exception as e:
        raise IOError(f"An error ocurred while saving the ZIP in {zip_filepath}") from e

def load_json_metadata(file_directory, filename):
    file = BASE_DIR / file_directory / filename
    
    with open(file, "r", encoding='UTF-8') as f:
        metadata_dict = json.load(f)
    return metadata_dict