import openpyxl
import xmltodict
import re

from src.formato.utilitarios.map_inventory import map_full_inventory
from src.utilitarios.files import read_xlsx

RESOURCE_PATTERN_NAME = re.compile(r"[?&]r=([^&]+)")

def xml_to_dict(filepath):
    with open(filepath, 'r', encoding="UTF-8") as xml_file:
        return xmltodict.parse(xml_file.read())

def extract_resource_name(url):
    regex = RESOURCE_PATTERN_NAME
    match = regex.search(url)
    return match.group(1) if match else ""

def map_biologico_inventory(excel_file):
    """
    Fetches biological data from I2D Inventory 
    """
    wb = openpyxl.load_workbook(excel_file, data_only=True)

    rows_biologico = read_xlsx(wb, "Biológico")

    biologico_index = {}
    for row in rows_biologico:
        url = row.get('URL CEIBA')

        if url and url.strip().lower().startswith(("http://", "https://")):
            resource_name = extract_resource_name(url)
            biologico_index[resource_name] = {
                'acceso_recurso': row.get('Acceso al recurso'),
                'fecha_liberacion': row.get('Fecha liberación'),
                'objeto_restriccion': row.get('Objeto de la restricción'),
                'proyecto': row.get('Proyecto'),
                'proyecto_macro': str(row.get('Proyecto Macro')).strip(),
                'contrato_convenio': row.get('Contrato/Convenio'),
                'doi': row.get('DOI'),
                'gbif_key': row.get('GBIF DATASET KEY'),
                'url': url
            }

    incoming_index = map_full_inventory(wb)
    incoming_index['biologico'] = biologico_index

    return incoming_index
