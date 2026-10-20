from src.config import Config
import xmltodict
from src.utilitarios.storage import save_json_metadata
import os
import re
import json
from pathlib import Path
from src.utilitarios.logger import logger


config = Config()
EML_PATTERN = re.compile(r"^eml(?:-(\d+)(?:\.(\d+))?)?\.xml$")

def read_resources():
    base_path = Path(config.ceiba_origin_path)
    return [resource for resource in base_path.iterdir() if resource.is_dir()]

# Compares all eml's files and returns latest
def get_latest_eml_version(resource_dir):

    latest_version = None
    latest_filename = None

    try:
        for file in os.listdir(resource_dir):

            match = EML_PATTERN.match(file)
            if match:
                v_major_str, v_minor_str = match.groups()

                if v_major_str is None:
                    version_tuple = (0, 0, False)
                else:
                    major = int(v_major_str)
                    has_minor = v_minor_str is not None
                    minor = int(v_minor_str) if has_minor else 0

                    version_tuple = (major, minor, has_minor)

                if latest_version is None or version_tuple > latest_version:
                    latest_version = version_tuple
                    latest_filename = os.path.splitext(file)[0]
    
        return latest_filename
    except Exception as e:
        logger.exception(f"An exception occured while getting latest eml version for {resource_dir.name} - {e}")

def save_files_path(resource_dir, write_dir, version = None):
    filespath = {}
    try:
        if version is not None:
            filespath['zip_filepath'] = f"dwca-{version}.zip"
            filespath['rtf_filepath'] = f"{resource_dir.name}-{version}.rtf"
            
        else:
            filespath['zip_filepath'] = f"dwca.zip"
            filespath['rtf_filepath'] = f"{resource_dir.name}.rtf"

        sources_dir = resource_dir / "sources"

        if sources_dir.exists() and sources_dir.is_dir():
            for file in os.listdir(sources_dir):
                if str(file).endswith(".txt"):
                    filespath[file] = f"{file}"

        output_filepath = f"{write_dir}/files.json"
        with open(output_filepath, 'w', encoding='UTF-8') as jf:
            json.dump(filespath, jf, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.exception(f"An exception occured while saving file references for {resource_dir.name} - {e}")

def read_xml(resource_dir):
    resource_name = get_latest_eml_version(resource_dir)

    if resource_name is None:
        files = ["resource"]
    else:
        files = ["resource", resource_name]

    write_dir = f"{config.ceiba_metadata_directory}/{resource_dir.name}"
    try:
        for f in files:
            filepath = resource_dir / f"{f}.xml"

            if not filepath.exists():
                print("El archivo no existe")
                continue

            with open(filepath, 'r', encoding="UTF-8") as xml_file:
                data_dict = xmltodict.parse(xml_file.read())

            save_json_metadata(data_dict, write_dir, f, "")

        if resource_name and "-" in resource_name:
            save_files_path(resource_dir, write_dir, resource_name.split("-")[1])
        else:
            save_files_path(resource_dir, write_dir, None)

        return True
    except Exception as e:
        logger.exception(f"An exception occured while parsing XML to JSON in {resource_dir.name} - {e}")
        return False

def main():
    logger.info("=============== Ingesting Ceiba resources ===============")
    logger.info("Starting main...")
    resources = read_resources()
    logger.info("All resources fetched!")

    successes = 0
    fails = 0
    for r in resources:
        response = read_xml(r)

        if response == True:
            successes+=1 
        else:
            fails += 1

    logger.info(f"Ceiba ingest finished - Number of SUCCESS: {successes} | Number of FAILS: {fails}")

if __name__ == '__main__':
    main()