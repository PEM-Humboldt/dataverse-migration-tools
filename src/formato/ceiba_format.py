import xmltodict
import re

def xml_to_dict(filepath):
    with open(filepath, 'r', encoding="UTF-8") as xml_file:
        return xmltodict.parse(xml_file.read())

def extract_resource_name(url):
    regex = re.compile(r"[?&]r=([^&]+)")
    match = regex.search(url)
    return match.group(1) if match else ""

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