"""Pruebas sintéticas del título alternativo de citation."""

from xml.etree import ElementTree


def test_alternative_title_from_short_name_in_eml_220(mapeo_ceiba):
    from src.ingest.utilitarios.xml_to_dict import xml_to_dict_tree
    from src.mapeo.ceiba.ceiba_source import read_record

    root = ElementTree.fromstring(
        '<eml:eml xmlns:eml="https://eml.ecoinformatics.org/eml-2.2.0">'
        "<dataset><title>Inventario de prueba</title>"
        "<shortName>Inventario del bosque</shortName></dataset></eml:eml>"
    )
    record = read_record("carpeta-ficticia", {root.tag: xml_to_dict_tree(root)})
    assert record["eml_version"] == "2.2.0"

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert citation["alternativeTitle"] == ["Inventario del bosque"]


def test_missing_short_name_does_not_use_folder_name(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"title": "Inventario de prueba"})
    record["name"] = "carpeta-ficticia"
    record["eml_version"] = "2.2.0"

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert "alternativeTitle" not in citation


def test_reconstructs_alternative_title_as_repeatable_primitive(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse
):
    record = record_ceiba({"shortName": "Inventario del bosque"})
    record["eml_version"] = "2.2.0"
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    schema = {
        "title": {"typeClass": "primitive", "multiple": False},
        "subject": {"typeClass": "controlledVocabulary", "multiple": True},
        "alternativeTitle": {"typeClass": "primitive", "multiple": True},
    }

    blocks = reconstruir_dataverse({"citation": citation}, schema)
    field = next(
        field for field in blocks["citation"]["fields"] if field["typeName"] == "alternativeTitle"
    )

    assert field == {
        "typeName": "alternativeTitle",
        "typeClass": "primitive",
        "multiple": True,
        "value": ["Inventario del bosque"],
    }


def test_characterizes_alt_h01_short_name_in_eml_211(mapeo_ceiba, eml_ceiba):
    """Caracteriza ALT-H01. La regla institucional asigna shortName a EML 2.2.0."""
    from src.mapeo.ceiba.ceiba_source import read_record

    record = read_record("carpeta-ficticia", eml_ceiba({"shortName": "Nombre sintético"}))
    assert record["eml_version"] == "2.1.1"

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert citation["alternativeTitle"] == ["Nombre sintético"]
