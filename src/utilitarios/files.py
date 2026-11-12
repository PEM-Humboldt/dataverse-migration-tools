import json
import csv
import io
import os
from pathlib import Path
import openpyxl

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
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
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

def save_file_as_stream(response, file_directory, folder_name, filename):
    try:
        raw_dir = BASE_DIR / file_directory / folder_name
        raw_dir.mkdir(parents=True, exist_ok=True)

        final_filepath = raw_dir / filename
        part_filepath = raw_dir / f"{filename}.part"

        with open(part_filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)

        if part_filepath.stat().st_size == 0:
            raise IOError("File downloaded is 0 bytes.")

        part_filepath.replace(final_filepath)

    except Exception as e:
        if part_filepath.exists():
            part_filepath.unlink()

        raise IOError(f"An error ocurred while saving the ZIP in {final_filepath}") from e
    
def read_xlsx(wb, sheet_name):
    """Reads an Excel's sheet of a file"""
    
    if sheet_name not in wb.sheetnames:
        raise ValueError(f"La hoja {sheet_name} no existe.")
        
    sheet = wb[sheet_name]
    
    headers = [cell.value for cell in sheet[1]]
    
    rows = []
    for row in sheet.iter_rows(min_row=2, values_only=True):
        if any(row):
            rows.append(dict(zip(headers, row)))
            
    return rows

def write_bytes(content, path, filename):
    """Write `content` (bytes) to `path` unchanged, atomically (`<name>.part`, then renamed).

    For responses saved exactly as the source gave them (XML, JSON not re-encoded).
    """
    aw_dirpath = BASE_DIR / path / filename
    write_path = Path(aw_dirpath)
    write_path.parent.mkdir(parents=True, exist_ok=True)
    tmp = write_path.with_name(write_path.name + ".part")
    tmp.write_bytes(content)
    os.replace(tmp, write_path)
