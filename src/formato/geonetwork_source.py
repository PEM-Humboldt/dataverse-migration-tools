"""Interpretation of the saved GeoNetwork responses (offline: no network, no reading of files).

Adapted from testGeonetwork/01_inventory.qmd (chunk inventory-table), 03_profile.qmd
(chunk profile-related), the preview analysis of 2026-10-09 and the comparison of 2026-10-21
between /related and the relations read from the XML.
"""
import re
import xml.etree.ElementTree as ET
from urllib.parse import unquote, urlsplit

NS = {"gmd": "http://www.isotc211.org/2005/gmd", "gco": "http://www.isotc211.org/2005/gco"}

# Columns of inventory.csv, in order (same as testGeonetwork/data/inventory.csv).
INVENTORY_COLUMNS = [
    "uuid", "id", "schema", "title", "type", "is_template", "is_harvested", "is_public",
    "source", "owner_id", "owner_username", "owner_profile", "group_owner",
    "published_for_group", "category", "language", "standard_name", "valid",
    "create_date", "change_date",
]


def _as_text(value):
    """Join multiple values with '|'; None becomes an empty string.

    Some index fields of the q service (type, publishedForGroup, category) are sometimes
    a string and sometimes a list.
    """
    if value is None:
        return ""
    if isinstance(value, list):
        return "|".join(str(v) for v in value)
    return str(value)


def q_records(page):
    """Records of one page of the q service: `metadata` is a list, or a dict when the page has one record."""
    records = page.get("metadata", [])
    return [records] if isinstance(records, dict) else records


def q_count(page):
    """Total number of records, from the summary of a page requested with buildSummary=true."""
    return int(page["summary"]["@count"])


def inventory_row(rec):
    """One row of inventory.csv from one record of the q service (flattened index values)."""
    info = rec["geonet:info"]
    user = (rec.get("userinfo") or "").split("|")      # user|surname|name|profile
    return {
        "uuid": info["uuid"],
        "id": info["id"],
        "schema": info["schema"],
        "title": rec.get("defaultTitle", ""),           # `title` is almost always empty
        "type": _as_text(rec.get("type")),
        "is_template": _as_text(rec.get("isTemplate")),
        "is_harvested": _as_text(rec.get("isHarvested")),
        "is_public": info.get("isPublishedToAll", ""),
        "source": info.get("source", ""),
        "owner_id": _as_text(rec.get("owner")),
        "owner_username": user[0],
        "owner_profile": user[3] if len(user) > 3 else "",
        "group_owner": _as_text(rec.get("groupOwner")),
        "published_for_group": _as_text(rec.get("publishedForGroup")),
        "category": _as_text(rec.get("category")),
        "language": _as_text(rec.get("docLocale")),
        "standard_name": _as_text(rec.get("standardName")),
        "valid": _as_text(rec.get("valid")),
        "create_date": info.get("createDate", ""),
        "change_date": info.get("changeDate", ""),
    }


def graphic_overviews(xml_bytes):
    """URLs of the preview images of an ISO 19139 record (gmd:graphicOverview/…/gmd:fileName), in order.

    Not used by the harvest: with `attachment_ref`, it tells which attachments are preview
    images, for the transfer of the attachments and for the `illustration` field.
    """
    root = ET.fromstring(xml_bytes)
    path = ".//gmd:graphicOverview/gmd:MD_BrowseGraphic/gmd:fileName/gco:CharacterString"
    return [e.text.strip() for e in root.findall(path, NS) if e.text and e.text.strip()]


_ATTACHMENT_PATH = re.compile(r"/api/records/([^/]+)/attachments/(.+)$")


def attachment_ref(url):
    """(record identifier, file name) of a GeoNetwork attachment URL, or None for any other URL.

    Only the path is used, so the host does not matter: previews written with
    http://, with :80, or with the old internal address 192.168.11.70:8080 all point
    to the same attachment of the current catalogue. The record identifier may be
    another record's (16 previews on 2026-10-09) and is not always a UUID.
    """
    m = _ATTACHMENT_PATH.search(urlsplit(url).path)
    return (m.group(1), unquote(m.group(2))) if m else None
