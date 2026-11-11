from src.utilitarios.files import read_xlsx
from src.utilitarios.logger import logger

def map_full_inventory(wb):
    """
    Reads I2D Inventory and returns formatted rows
    """
    rows_macro = read_xlsx(wb, "Proyectos Macro")
    rows_general = read_xlsx(wb, "GENERAL")

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

        if enlace:
            if enlace.strip().lower().startswith(("http://i2d.humboldt", "https://i2d.humboldt")):
                from src.formato.ceiba_format import extract_resource_name
                resource_name = extract_resource_name(enlace)
            elif enlace.strip().lower().startswith(("http://doi", "https://doi")):
                resource_name = enlace.split("://")[-1]
            else:
                resource_name = enlace

            general_index[resource_name] = {
                'accion': row.get('ACCIÓN'),
                'mes': row.get('MES'),
                'anio': row.get('AÑO')
            }

    full_index = {
        'proyecto_macro': macro_index,
        'general': general_index
    }
    return full_index

def attach_inventory_data(full_index, identifier, inventory_type, resource_dict=None):
    """
    Compares current resource identifier to find corresponding row in I2D Inventory.
    """
    if not resource_dict:
        resource_dict = {}

    type_data = full_index.get(inventory_type, {}).get(identifier)

    if not type_data:
        logger.warning(f"No se encontró coincidencia para el recurso: {identifier}")
        return resource_dict | {"inventory": {}}

    # Compara contra "Proyecto macro" y "General"
    cod_macro = type_data.get('proyecto_macro')
    macro_data = full_index.get('proyecto_macro', {}).get(cod_macro, {})
    general_data = full_index.get('general', {}).get(identifier, {})

    target_row = {
        inventory_type: type_data,
        'proyecto_macro_detalle': macro_data,
        'general': general_data
    }

    return resource_dict | {"inventory": target_row}