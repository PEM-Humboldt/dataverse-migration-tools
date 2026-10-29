
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
    """Creates two inventories of resources (one per row), one for general metadata and one for files."""
    info = rec["geonet:info"]
    user = (rec.get("userinfo") or "").split("|")
    link = rec.get('link') or []
    files = link if isinstance(link, list) else [link]
    ff = []

    for f in files:
        ff.append(strip_link_data(f))

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

    files_data = {
        "uuid": info["uuid"],
        "files_urls": ff
    }

    return inventory_data, files_data
