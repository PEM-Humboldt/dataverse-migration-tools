import openpyxl
from src.formato.utilitarios.map_inventory import map_full_inventory
from src.utilitarios.files import read_xlsx

def as_text(value):
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(v) for v in value)
    return str(value)

def strip_link_data(link):
    parts = [p.strip() for p in link.split("|")]

    if "/attachments/" in link:
        return {
            'type': 'attachment',
            'name': parts[0],
            'description': parts[1],
            'protocol': parts[3],
            'mime_type': parts[4],
            'order': parts[5],
            'file_name': link.split("/attachments/", 1)[1]
        }
    else:
        return {
            'type': 'external',
            'name': parts[0],
            'description': parts[1],
            'protocol': parts[3],
            'mime_type': parts[4],
            'order': parts[5]
        }

def inventory_row(rec):
    """Creates an inventory of resources with general metadata"""
    info = rec["geonet:info"]
    user = (rec.get("userinfo") or "").split("|")
    link = rec.get('link') or []
    files = link if isinstance(link, list) else [link]
    inventory_data = {
        "uuid": info["uuid"],
        "id": info["id"],
        "schema": info["schema"],
        "title": rec.get("defaultTitle", ""),
        "type": as_text(rec.get("type")),
        "is_template": as_text(rec.get("isTemplate")),
        "is_harvested": as_text(rec.get("isHarvested")),
        "is_public": info.get("isPublishedToAll", ""),
        "source": info.get("source", ""),
        "number_files": len(files),
        "owner_id": as_text(rec.get("owner")),
        "owner_username": user[0],
        "owner_profile": user[3] if len(user) > 3 else "",
        "group_owner": as_text(rec.get("groupOwner")),
        "published_for_group": as_text(rec.get("publishedForGroup")),
        "category": as_text(rec.get("category")),
        "language": as_text(rec.get("docLocale")),
        "standard_name": as_text(rec.get("standardName")),
        "valid": as_text(rec.get("valid")),
        "create_date": info.get("createDate", ""),
        "change_date": info.get("changeDate", ""),
    }

    return inventory_data

def inventory_text(value):
    """Cell value of the I2D inventory as stripped text ('' for an empty cell), with as_text()."""
    return as_text(value).strip()

def map_geografico_inventory(excel_file):
    """
    Reads the I2D Inventory with the sheet «Geográfico» indexed by GeoNetwork UUID under «geografico»,
    so that attach_inventory_data(full_index, uuid, "geografico") gives each GeoNetwork record its inventory data.
    """
    wb = openpyxl.load_workbook(excel_file, data_only=True)

    geografico_index = {}
    for row in read_xlsx(wb, "Geográfico"):
        uuid = inventory_text(row.get('ID GeoNetwork'))
        if not uuid or uuid == "-":
            continue
        geografico_index[uuid] = {
            'id_geonetwork': uuid,
            'tipo_acceso': inventory_text(row.get('Tipo de acceso')),
            'estado': inventory_text(row.get('Estado')),
            'metadato_privado': inventory_text(row.get('(TEMPORAL) Metadato finalizado pero privado')),
            'proyecto': inventory_text(row.get('Proyecto')),
            'proyecto_macro': inventory_text(row.get('Proyecto Macro')),
            'contrato_convenio': inventory_text(row.get('Contrato/Convenio')),
            'contratista': inventory_text(row.get('Contratista')),
            'objeto_restriccion': inventory_text(row.get('Objeto de la restricción')),
            'fecha_liberacion': inventory_text(row.get('Fecha liberación I2D')),
        }

    incoming_index = map_full_inventory(wb)
    incoming_index['geografico'] = geografico_index

    return incoming_index
