
import xml.etree.ElementTree as ET
import io

def parse_xml_with_prefixes(xml_bytes):
    """Parsing returns original prefixes instead of full url (gmd:, gco:, etc.)."""
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
            # If tag is {uri}name, returns only prefix:name as the original xml
            if elem.tag.startswith("{"):
                uri, tag_name = elem.tag[1:].split("}", 1)
                prefix = ns_map.get(uri)
                elem.tag = f"{prefix}:{tag_name}" if prefix else tag_name

    return root

def clean_inline_text(element):
    return " ".join("".join(element.itertext()).split())

def validate_inline_tags_only(element, inline_tags):
    """Return True if the element has children, and ALL of them are formatting tags."""
    hijos = list(element)
    if not hijos:
        return False

    # Checks all children for formatting tags, if any has other tags that are not inline, it returns False
    for desc in element.iter():
        if desc is element:
            continue
        if desc.tag not in inline_tags:
            return False

    return True

def xml_to_dict_tree(element, tags = {}):
    """Turns XML to a dictionary"""

    inline_tags = tags.get("inline_tags") or {}
    list_tags = tags.get("list_tags") or {}
    string_tags = tags.get("string_tags") or {}
    dict_tags = tags.get("dict_tags") or {}

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
    if validate_inline_tags_only(element, inline_tags):
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
        child_val = xml_to_dict_tree(child, tags)

        # If the tag is in list_tags it sets the data in a list (always)
        if child.tag in data or child.tag in list_tags:
            if child.tag not in data:
                data[child.tag] = []
            elif not isinstance(data[child.tag], list):
                data[child.tag] = [data[child.tag]]
            data[child.tag].append(child_val)
        elif child.tag in data or child.tag in string_tags:
            data[child.tag] = "" if child_val is None else child_val
        elif child.tag in data or child.tag in dict_tags:
            data[child.tag] = {} if child_val is None else child_val
        else:
            data[child.tag] = child_val

        if child.tail and child.tail.strip():
            text_fragments.append(child.tail.strip())

    if text_fragments:
        data["#text"] = " ".join(text_fragments)

    return data