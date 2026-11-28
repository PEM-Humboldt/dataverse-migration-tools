import openpyxl
import xmltodict
import re
from collections import Counter, defaultdict

from src.formato.utilitarios.map_inventory import map_full_inventory
from src.utilitarios.files import read_xlsx

RESOURCE_PATTERN_NAME = re.compile(r"[?&]r=([^&]+)")

def extract_resource_name(url):
    regex = RESOURCE_PATTERN_NAME
    match = regex.search(url)
    return match.group(1) if match else ""

def map_biologico_inventory(excel_file, *, biological_identifiers=None):
    """
    Fetches biological data from I2D Inventory 

    Si se proporciona una lista de identificadores, añade una entrada por fila
    indexada para conservar los duplicados antes de resolver correspondencias.
    """
    wb = openpyxl.load_workbook(excel_file, data_only=True)

    rows_biologico = read_xlsx(wb, "Biológico")

    biologico_index = {}
    for row in rows_biologico:
        url = row.get('URL CEIBA')

        if url and url.strip().lower().startswith(("http://", "https://")):
            resource_name = extract_resource_name(url)
            if biological_identifiers is not None:
                biological_identifiers.append(resource_name)
            biologico_index[resource_name] = {
                'acceso_recurso': row.get('Acceso al recurso'),
                'fecha_liberacion': row.get('Fecha liberación'),
                'objeto_restriccion': row.get('Objeto de la restricción'),
                'proyecto': row.get('Proyecto'),
                'proyecto_macro': str(row.get('Proyecto Macro')).strip(),
                'contrato_convenio': row.get('Contrato/Convenio'),
                'doi': row.get('DOI'),
                'gbif_key': row.get('GBIF DATASET KEY'),
                'url': url,
                'contratista': row.get('Contratista'),
                'metadato_privado': row.get('(TEMPORAL) Metadato finalizado pero privado')
            }

    incoming_index = map_full_inventory(wb)
    incoming_index['biologico'] = biologico_index

    return incoming_index


def normalize_ceiba_identifier(identifier):
    """Quita los espacios en blanco y convierte a minúsculas para comparar claves."""
    return "".join(identifier.split()).lower()


def resolve_ceiba_inventory(full_index, ceiba_identifiers, biological_identifiers):
    """Devuelve una vista de Biológico para la ingesta CEIBA y sus conteos.

    La recuperación exige una fila biológica y un identificador CEIBA únicos.
    Los conteos de ambigüedad pueden coincidir para un mismo recurso.
    """
    biological_groups = defaultdict(list)
    for identifier in biological_identifiers:
        key = normalize_ceiba_identifier(identifier)
        if key:
            biological_groups[key].append(identifier)

    ceiba_keys = [(identifier, normalize_ceiba_identifier(identifier)) for identifier in ceiba_identifiers]
    ceiba_counts = Counter(key for _, key in ceiba_keys if key)
    biological_index = full_index["biologico"]
    recovered = {}
    counts = dict.fromkeys(("exact", "normalized", "missing", "ambiguous_inventory", "ambiguous_ceiba"), 0)
    for identifier, key in ceiba_keys:
        if identifier in biological_index:
            counts["exact"] += 1
            continue
        candidates = biological_groups.get(key)
        if not candidates:
            counts["missing"] += 1
            continue
        inventory_collision = len(candidates) > 1
        ceiba_collision = ceiba_counts[key] > 1
        if inventory_collision or ceiba_collision:
            counts["ambiguous_inventory"] += int(inventory_collision)
            counts["ambiguous_ceiba"] += int(ceiba_collision)
            continue
        recovered[identifier] = biological_index[candidates[0]]
        counts["normalized"] += 1

    return full_index | {"biologico": biological_index | recovered}, counts
