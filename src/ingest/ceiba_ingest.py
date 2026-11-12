from pathlib import Path
import os
import re
import xml.etree.ElementTree as ET
from src.formato.utilitarios.map_inventory import attach_inventory_data
from src.config import Config
from src.utilitarios.files import write_csv, write_json
from src.formato.ceiba_format import map_biologico_inventory
from src.utilitarios.logger import logger

config = Config()
EML_PATTERN = re.compile(r"^eml-(\d+)(?:\.(\d+))?\.xml$")
OUTPUT_DIR = f"{config.ceiba_data_dir}/{config.metadata_dir}"
INLINE_TAGS = {"emphasis", "subscript", "superscript", "i", "b", "u"}
LIST_TAGS = {"creator", "contact", "keyword", "keywordSet", "personnel", "associatedParty", "taxonClassification", "para"}

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
        logger.warning(f"No published EML file was found for the {resource_dir.name} resource")

    return latest_filename
    
def export_file_references(resource_dir, version = None):
    """Gets files absolute paths and saves them in a dictionary"""

    files_directory = {}
    suffix = f"-{version}" if version is not None else ""

    zip_path = resource_dir / f"dwca{suffix}.zip"
    rtf_file = resource_dir / f"{resource_dir.name}{suffix}.rtf"

    files_directory['zip_filepath'] = str(zip_path) if zip_path.exists() else ""
    files_directory['rtf_filepath'] = str(rtf_file) if rtf_file.exists() else ""
    
    sources_dir = resource_dir / "sources"

    if sources_dir.exists() and sources_dir.is_dir():
        for file in os.listdir(sources_dir):
            if not str(file).endswith(".log"):
                files_directory[file] = f"{sources_dir}/{file}"

    write_json(files_directory, f"{OUTPUT_DIR}/{resource_dir.name}", 'files.json')

def process_metadata(resource_dir):
    """Transform XML files and inventory record to python dicts to merge them all into a single JSON file
    """
    eml_file = get_latest_eml(resource_dir)
    published = eml_file is not None
    latest_version = eml_file.split("-")[1] if published else None

    if not published:
        logger.info(f"{resource_dir.name}: never published, only resource.xml is read")
    files = ["resource", eml_file] if published else ["resource"]

    resource_dictionary = {}
    for f in files:
        filepath = resource_dir / f"{f}.xml"

        if not filepath.exists():
            logger.warning(f"File for {resource_dir.name} doesn't exist.")
            continue

        tree = ET.parse(filepath)
        root = tree.getroot()
        data_dict = {root.tag: xml_to_dict_tree(root)}

        resource_dictionary = resource_dictionary | data_dict
    return {
        'resource_dict': resource_dictionary | {"published": published},
        'latest_version': latest_version,
        'ceiba_identifier': resource_dir.name
    }

def clean_inline_text(element):
    return " ".join("".join(element.itertext()).split())

def validate_inline_tags_only(element):
    """Return True if the element has children, and ALL of them are formatting tags."""
    hijos = list(element)
    if not hijos:
        return False

    # Checks all children for formatting tags, if any has other tags that are not inline, it returns False
    for desc in element.iter():
        if desc is element:
            continue
        if desc.tag not in INLINE_TAGS:
            return False

    return True

def xml_to_dict_tree(element):
    """Turns XML to a dictionary"""

    # If the element has no children, then checks attributes and text only.
    if len(element) == 0:
        text = element.text.strip() if element.text else None
        if not element.attrib:
            return text
        res = {f"@{k}": v for k, v in element.attrib.items()}
        if text:
            res["#text"] = text
        return res

    # Checks if the element contains only formatting tags (e.g. <emphasis>) and returns the full text
    if validate_inline_tags_only(element):
        return clean_inline_text(element)

    # Keeps the hierarchical tags
    data = {}
    if element.attrib:
        data.update({f"@{k}": v for k, v in element.attrib.items()})

    text_fragments = []
    if element.text and element.text.strip():
        text_fragments.append(element.text.strip())

    # Loops over every child tag of current element
    for child in element:
        child_val = xml_to_dict_tree(child)

        # If the tag is in LIST_TAGS it sets the data in a list (always)
        if child.tag in data or child.tag in LIST_TAGS:
            if child.tag not in data:
                data[child.tag] = []
            elif not isinstance(data[child.tag], list):
                data[child.tag] = [data[child.tag]]
            data[child.tag].append(child_val)
        else:
            data[child.tag] = child_val

        if child.tail and child.tail.strip():
            text_fragments.append(child.tail.strip())

    if text_fragments:
        data["#text"] = " ".join(text_fragments)

    return data

def main():
    logger.info("=============== Ingesting Ceiba resources ===============")
    logger.info("Starting main...")
    resources = read_resources()
    logger.info("All resources fetched!")

    successes = 0
    fails = 0

    full_index = map_biologico_inventory(config.i2d_inventory)

    inventory_mapping = []
    for r in resources:
        try:
            data = process_metadata(r)

            full_dict = attach_inventory_data(full_index, data['ceiba_identifier'], 'biologico', data['resource_dict'])
            write_json(full_dict, f"{OUTPUT_DIR}/{r.name}", "resource_metadata.json")

            export_file_references(r, data['latest_version'])
            inventory_mapping.append({'resource': r.name, 'latest_version': data['latest_version']})
            successes+=1 
        except Exception as e:
            logger.exception(f"Failed to process resource {r} - ERROR")
            fails += 1

    write_csv(inventory_mapping, Path(config.ceiba_data_dir), 'inventory.csv')
    logger.info(f"Ceiba ingest finished - Number of SUCCESS: {successes} | Number of FAILS: {fails}")

if __name__ == '__main__':
    main()