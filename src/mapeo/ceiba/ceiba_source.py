"""Reading of the Ceiba ingest (src/ingest/ceiba_ingest.py) for the mapping.

The ingest writes one resource_metadata.json per IPT resource, in CEIBA_DATA_DIR/METADATA_DIR/<resource>/:

    {"resource": {...resource.xml...},
     "{eml://ecoinformatics.org/eml-2.1.1}eml": {...last published eml-<v>.xml...},   (or eml-2.2.0, or absent)
     "published": true | false,
     "inventory": {...attach_inventory_data()...}}

and CEIBA_DATA_DIR/inventory.csv (resource, latest_version). The XML is already a dictionary
(xml_to_dict_tree() with the LIST_TAGS of the ingest); this module only finds the parts the mapping needs and
offers small helpers for the irregular shapes of that dictionary (one element → dict, several → list).
It does not read the IPT folder again.
"""
import html
import re

from src.utilitarios.files import read_json

EML_ROOT = re.compile(r"^\{(?:eml://ecoinformatics\.org/eml-|https://eml\.ecoinformatics\.org/eml-)([\d.]+)\}eml$")


def as_list(value):
    """The value as a list: [] for None, [value] for a single element, the list itself otherwise."""
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def clean(text):
    """Text with whitespace runs (line breaks included) reduced to one space, stripped."""
    return " ".join(str(text if text is not None else "").split())


def text(value):
    """Text of an element of the dictionary: a string, the «#text» of an element with attributes, or ""."""
    if isinstance(value, dict):
        value = value.get("#text")
    if isinstance(value, list):  # un elemento repetido donde se espera uno: se unen
        return " ".join(t for t in (text(v) for v in value) if t)
    return clean(value) if isinstance(value, str) else ""


# Puntuación que quedó sola al final del texto de un párrafo: el texto que seguía al enlace
LINK_TAIL = re.compile(r"^(.*?)\s*([.;:,!?)]+)$", re.S)


def paragraph_text(para):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, mapear_descripcion()):
    # a paragraph with a <ulink> keeps the text of the link as «title (url)» (the ingest stores it apart from
    # #text), and a single link followed only by punctuation goes back to its place; taking only #text loses
    # the text of the link.
    """Text of one <para>. The ingest flattens the inline tags (<emphasis>…) into the text; a <para> with a
    <ulink> becomes {"#text": text around the link, "ulink": {"@url", "citetitle"}}, without the position of the
    link. Each link is written as «title (url)». With a single link, when the text ends with punctuation left
    alone after a space («… tipos de acceso. .»), the text after the link was only that punctuation: the link
    goes back before it («… tipos de acceso. Restringido temporalmente (url).», Marius, 25/11/2026). Otherwise
    the position cannot be recovered and the links are written after the text."""
    if isinstance(para, dict):
        body = text(para.get("#text"))
        links = []
        for link in as_list(para.get("ulink")):
            title, url = text(link.get("citetitle")), clean(link.get("@url"))
            links.append(f"{title} ({url})" if title and url else title or url)
        links = [l for l in links if l]
        if len(links) == 1:
            tail = LINK_TAIL.match(body)
            if tail and (not tail.group(1) or body[len(tail.group(1)):].startswith((" ", "\n"))):
                return clean(f"{tail.group(1)} {links[0]}{tail.group(2)}")
        return clean(" ".join([body] + links if body else links))
    return text(para)


def paragraphs(element):
    """Paragraphs of a text element (abstract, purpose, methods…): its <para> children, or its own text when it
    has no <para> (EML 2.2.0 allows <purpose>text</purpose>). Empty paragraphs are dropped."""
    if element is None:
        return []
    if isinstance(element, dict) and "para" in element:
        found = [paragraph_text(p) for p in as_list(element["para"])]
    elif isinstance(element, list):
        found = [t for e in element for t in paragraphs(e)]
    else:
        found = [text(element)]
    return [p for p in found if p]


def html_paragraphs(paras):
    """Paragraphs as HTML for a textbox field (destino/textos_html_textbox.md): one <p> per paragraph, with
    & < > escaped. The inline markup (<emphasis> → <em>, <ulink> → <a>) is lost by the ingest before this step."""
    return "".join(f"<p>{html.escape(p, quote=False)}</p>" for p in paras)


def eml_root(data):
    """(EML version, EML root dict) of an ingest dictionary, or (None, None) for a resource never published."""
    for key, value in data.items():
        m = EML_ROOT.match(key)
        if m and isinstance(value, dict):
            return m.group(1), value
    return None, None


def gbif_metadata(eml):
    """additionalMetadata/metadata/gbif of the EML (dict, {} if absent)."""
    for item in as_list(eml.get("additionalMetadata")):
        gbif = ((item or {}).get("metadata") or {}).get("gbif") if isinstance(item, dict) else None
        if isinstance(gbif, dict):
            return gbif
    return {}


def read_record(name, data, latest_version=None):
    # Compared with feature/integracion-ceiba-dataverse-v2 (commit bbdd77d, src/mapeo/ceiba_mapping.py, extraer_dataset()):
    # reads exactly the keys the ingest writes: the EML root under its namespaced key (EML 2.1.1 or 2.2.0) for
    # dataset and @packageId, "resource" (resource.xml) and "inventory" (I2D inventory), which later fields need;
    # it does not try other keys ("eml", "metadata", "eml_data"). A resource without a published EML returns
    # None (not migrated) instead of raising an exception.
    """Source-side record of one resource from its resource_metadata.json dictionary.

    `name`: the resource short name (folder name); `latest_version`: from the ingest inventory.csv.
    Returns None for a resource without a published EML (never published: not migrated).
    """
    eml_version, eml = eml_root(data)
    if eml is None:
        return None
    resource = data.get("resource") or {}
    return {
        "name": name,
        "version": latest_version or "",
        "eml_version": eml_version,
        "package_id": clean(eml.get("@packageId")),
        "dataset": eml.get("dataset") or {},
        "gbif": gbif_metadata(eml),
        "resource": resource,
        "ipt_status": clean(resource.get("status")),  # PUBLIC o PRIVATE (estado de publicación del IPT)
        "inventory": data.get("inventory") or {},
    }


def read_ingest(raw_dir, versions):
    """All ingested resources: {name: record} (records of read_record(); resources never published left out).

    `raw_dir`: CEIBA_DATA_DIR/METADATA_DIR; `versions`: {resource: latest_version} from inventory.csv.
    """
    records = {}
    for path in sorted(raw_dir.glob("*/resource_metadata.json")):
        name = path.parent.name
        record = read_record(name, read_json(path), versions.get(name))
        if record is not None:
            records[name] = record
    return records
