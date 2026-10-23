from src.config import Config
import xmltodict
from src.utilitarios.files import read_csv, write_json
import os
import re
from pathlib import Path
from src.utilitarios.logger import logger

config = Config()
EML_PATTERN = re.compile(r"^eml(?:-(\d+)(?:\.(\d+))?)?\.xml$")
OUTPUT_DIR = f"{config.ceiba_data_dir}/{config.metadata_dir}"

def extract_resource_name(url):
    regex = re.compile(r"[?&]r=([^&]+)")
    match = regex.search(url)
    return match.group(1) if match else ""

def read_resources():
    """Returns the path for each existing resource"""
    base_path = Path(config.ceiba_origin_path)
    return [resource for resource in base_path.iterdir() if resource.is_dir()]

def get_latest_eml(resource_dir):
    """Returns the latest eml file for the given resource"""
    latest_version = None
    latest_filename = None

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

    if latest_filename is None:
        logger.warning(f"No EML file was found for the {resource_dir.name} resource")

    return latest_filename
    
def export_file_references(resource_dir, version = None):
    """Gets files absolute paths and saves them in a dictionary"""

    files_directory = {}

    if version is not None:
        files_directory['zip_filepath'] = f"{resource_dir}/dwca-{version}.zip"
        files_directory['rtf_filepath'] = f"{resource_dir}/{resource_dir.name}-{version}.rtf"
        
    else:
        files_directory['zip_filepath'] = f"{resource_dir}/dwca.zip"
        files_directory['rtf_filepath'] = f"{resource_dir}/{resource_dir.name}.rtf"

    sources_dir = resource_dir / "sources"

    if sources_dir.exists() and sources_dir.is_dir():
        for file in os.listdir(sources_dir):
            if str(file).endswith(".txt"):
                files_directory[file] = f"{resource_dir}/{file}"

    write_json(files_directory, f"{OUTPUT_DIR}/{resource_dir.name}", 'files.json')

def attach_inventory_data(inventory, resource_dict, identifier):
    """Compares current resource identifier to find corresponding row in I2D Inventory"""
    
    target_row = {}
    for row in inventory:
        url = row.get('URL CEIBA')
        if url.startswith(("http://", "https://")):
            extracted_name = extract_resource_name(url)
            if extracted_name == identifier:
                target_row = row
                break
    
    return resource_dict | {"inventory": target_row}

def process_metadata(resource_dir):
    """Transform XML files and inventory record to python dicts to merge them all into a single JSON file
    """
    eml_file = get_latest_eml(resource_dir)

    latest_version = eml_file.split("-")[1] if eml_file and "-" in eml_file else None
    files = ["resource"] if eml_file is None else ["resource", eml_file]
    
    resource_dictionary = {}
    for f in files:
        filepath = resource_dir / f"{f}.xml"

        if not filepath.exists():
            logger.warning(f"File for {resource_dir.name} doesn't exist.")
            continue

        with open(filepath, 'r', encoding="UTF-8") as xml_file:
            data_dict = xmltodict.parse(xml_file.read())
            resource_dictionary = resource_dictionary | data_dict

    return {
        'resource_dict': resource_dictionary,
        'latest_version': latest_version,
        'ceiba_identifier': resource_dir.name
    }

def main():
    logger.info("=============== Ingesting Ceiba resources ===============")
    logger.info("Starting main...")
    resources = read_resources()
    logger.info("All resources fetched!")

    successes = 0
    fails = 0

    inventory = read_csv(config.ceiba_inventory)
    for r in resources:
        try:
            data = process_metadata(r)

            full_dict = attach_inventory_data(inventory, data['resource_dict'], data['ceiba_identifier'])
            write_json(full_dict, f"{OUTPUT_DIR}/{r.name}", "resource_metadata.json")

            export_file_references(r, data['latest_version'])

            successes+=1 
        except Exception as e:
            logger.exception(f"Failed to process resource {r} - ERROR")
            fails += 1

    logger.info(f"Ceiba ingest finished - Number of SUCCESS: {successes} | Number of FAILS: {fails}")

if __name__ == '__main__':
    main()