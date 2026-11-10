import openpyxl
import xmltodict
import re

from src.utilitarios.logger import logger
from src.utilitarios.files import read_xlsx

RESOURCE_PATTERN_NAME = re.compile(r"[?&]r=([^&]+)")

def xml_to_dict(filepath):
    with open(filepath, 'r', encoding="UTF-8") as xml_file:
        return xmltodict.parse(xml_file.read())

def extract_resource_name(url):
    regex = RESOURCE_PATTERN_NAME
    match = regex.search(url)
    return match.group(1) if match else ""

def attach_inventory_data(full_index, resource_dict, identifier):
    """Compares current resource identifier to find corresponding row in I2D Inventory"""
    
    target_row = {}

    biologico_data = full_index['biologico'].get(identifier)

    if not biologico_data:
        logger.warning(f"No se encontró coincidencia en el inventario para el recurso: {identifier}")
        return resource_dict | {"inventory": {}}

    cod_macro = biologico_data.get('proyecto_macro')
    macro_data = full_index['proyecto_macro'].get(cod_macro, {})

    general_data = full_index['general'].get(identifier, {})

    target_row = {
        'biologico': biologico_data,
        'proyecto_macro_detalle': macro_data,
        'general': general_data
    }

    if not target_row:
        logger.warning(f"No se encontró coincidencia en el inventario para el recurso: {identifier}")
    return resource_dict | {"inventory": target_row}

def map_full_inventory(excel_file):
    wb = openpyxl.load_workbook(excel_file, data_only=True)

    rows_biologico = read_xlsx(wb, "Biológico")
    rows_macro = read_xlsx(wb, "Proyectos Macro")
    rows_general = read_xlsx(wb, "GENERAL")

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

    macro_index = {}
    for row in rows_macro:
        val = str(row.get('NO. PROYECTO'))
        proyecto_macro = str(val).strip() if val is not None else None

        if proyecto_macro:
            macro_index[proyecto_macro] = {
                'objeto': row.get('OBJETO'),
                'nombre_corto': row.get('NOMBRE CORTO'),
                'fecha_inicio': row.get('FECHA DE INICIO'),
                'fecha_final': row.get('FECHA FINAL')
            }

    general_index = {}
    for row in rows_general:
        enlace = row.get('ENLACE')

        if enlace and enlace.strip().lower().startswith(("http://", "https://")):
            resource_name = extract_resource_name(enlace)

            general_index[resource_name] = {
                'accion': row.get('ACCIÓN'),
                'mes': row.get('MES'),
                'anio': row.get('AÑO')
            }

    full_index = {
        'biologico': biologico_index,
        'proyecto_macro': macro_index,
        'general': general_index
    }
    return full_index

