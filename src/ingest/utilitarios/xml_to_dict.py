
import xml.etree.ElementTree as ET
import io

def parse_xml_with_prefixes(xml_bytes):
    """Parsea el XML reemplazando las URLs {http://...} por sus prefijos originales (gmd:, gco:, etc.)."""
    events = ("start", "start-ns")
    ns_map = {}
    root = None

    for event, elem in ET.iterparse(io.BytesIO(xml_bytes), events):
        if event == "start-ns":
            prefix, uri = elem
            ns_map[uri] = prefix
        elif event == "start":
            if root is None:
                root = elem
            # Si la etiqueta tiene {uri}nombre, la regresamos a prefijo:nombre
            if elem.tag.startswith("{"):
                uri, tag_name = elem.tag[1:].split("}", 1)
                prefix = ns_map.get(uri)
                elem.tag = f"{prefix}:{tag_name}" if prefix else tag_name

    return root

def clean_inline_text(element):
    return " ".join("".join(element.itertext()).split())

def validate_inline_tags_only(element, INLINE_TAGS):
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

def xml_to_dict_tree(element, INLINE_TAGS = {}, LIST_TAGS = {}, STRING_TAGS = {}, DICT_TAGS = {}):
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
    if validate_inline_tags_only(element, INLINE_TAGS):
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
        child_val = xml_to_dict_tree(child, INLINE_TAGS, LIST_TAGS, STRING_TAGS, DICT_TAGS)

        # If the tag is in LIST_TAGS it sets the data in a list (always)
        if child.tag in data or child.tag in LIST_TAGS:
            if child.tag not in data:
                data[child.tag] = []
            elif not isinstance(data[child.tag], list):
                data[child.tag] = [data[child.tag]]
            data[child.tag].append(child_val)
        elif child.tag in data or child.tag in STRING_TAGS:
            data[child.tag] = "" if child_val is None else child_val
        elif child.tag in data or child.tag in DICT_TAGS:
            data[child.tag] = {} if child_val is None else child_val
        else:
            data[child.tag] = child_val

        if child.tail and child.tail.strip():
            text_fragments.append(child.tail.strip())

    if text_fragments:
        data["#text"] = " ".join(text_fragments)

    return data