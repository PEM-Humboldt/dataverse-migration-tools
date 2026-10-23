import json
import csv
import io
from pathlib import Path
from src.utilitarios.logger import logger


# Raíz del proyecto (3 niveles arriba desde src/utils/storage.py)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

def read_json(file_directory, filename):
    file = BASE_DIR / file_directory / filename
    
    with open(file, "r", encoding='UTF-8') as f:
        metadata_dict = json.load(f)
    return metadata_dict

def write_json(data, path, filename):
    try:
        raw_dirpath = BASE_DIR / path
        raw_dirpath.mkdir(parents=True, exist_ok=True)
        raw_filepath = raw_dirpath / filename

        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        raise RuntimeError(f"An error ocurred while saving the JSON file in {raw_filepath}") from e

def read_csv(path):
    """Read a UTF-8 CSV file with a header row; return a list of dictionaries."""
    return list(csv.DictReader(io.StringIO(Path(path).read_text(encoding="utf-8"))))

def write_csv(rows, path, filename, fieldnames=None):
    try:
        raw_dirpath = BASE_DIR / path
        raw_dirpath.mkdir(parents=True, exist_ok=True)
        raw_filepath = raw_dirpath / filename

        fieldnames = fieldnames or (list(rows[0]) if rows else [])
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
        raw_filepath.write_text(buf.getvalue(), encoding="utf-8")
    except Exception as e:
        raise RuntimeError(f"An error occured while writing the CSV in {raw_dirpath}") from e

def read_csv(path):
    """Read a UTF-8 CSV file with a header row; return a list of dictionaries."""
    return list(csv.DictReader(io.StringIO(Path(path).read_text(encoding="utf-8"))))

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