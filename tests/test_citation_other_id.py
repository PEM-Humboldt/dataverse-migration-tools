"""Pruebas sintéticas del identificador de origen en citation."""

from xml.etree import ElementTree

import pytest


AGENCY = "IPT Ceiba (I2D)"


@pytest.mark.parametrize(
    ("base_url", "query_key"),
    [
        pytest.param("http://example.test/ceiba/resource.do", "id", id="historical-http"),
        pytest.param("https://example.test/ceiba/resource", "r", id="ceiba-https"),
        pytest.param("https://example.test/resource", "r", id="root-https"),
    ],
)
@pytest.mark.parametrize("version", ["v3", "v3.0", "v5.2"])
def test_other_id_preserves_agency_and_exact_package_id(
    mapeo_ceiba, eml_ceiba, base_url, query_key, version
):
    from src.mapeo.ceiba.ceiba_source import read_record

    package_id = f"{base_url}?{query_key}=recurso-ficticio/{version}"
    ingested = eml_ceiba({})
    next(iter(ingested.values()))["@packageId"] = package_id
    record = read_record("carpeta-ficticia", ingested, latest_version="99")

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert record["package_id"] == package_id
    assert citation["otherId"] == [{"otherIdAgency": AGENCY, "otherIdValue": package_id}]


@pytest.mark.parametrize("package_id", [None, "", "  \t "], ids=["absent", "empty", "whitespace"])
def test_missing_package_id_does_not_generate_other_id(mapeo_ceiba, eml_ceiba, package_id):
    from src.mapeo.ceiba.ceiba_source import read_record

    ingested = eml_ceiba({})
    root = next(iter(ingested.values()))
    if package_id is None:
        del root["@packageId"]
    else:
        root["@packageId"] = package_id
    record = read_record("carpeta-ficticia", ingested, latest_version="3")

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert record["package_id"] == ""
    assert "otherId" not in citation


def test_inventory_doi_stays_in_external_references(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["package_id"] = "https://example.test/resource?r=recurso-ficticio/v3"
    doi = "10.1234/recurso-sintetico"
    record["inventory"] = {"biologico": {"doi": f"https://doi.org/{doi}"}}

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    references = mapeo_ceiba.map_external_references(record, curation=[])

    assert citation["otherId"] == [{"otherIdAgency": AGENCY, "otherIdValue": record["package_id"]}]
    assert [ref["externalReferenceDOI"] for ref in references if "externalReferenceDOI" in ref] == [doi]


def test_reconstructs_other_id_as_compound_with_single_primitive_children(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse
):
    record = record_ceiba({})
    package_id = "https://example.test/ceiba/resource?r=recurso-ficticio/v3.0"
    record["package_id"] = package_id
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    schema = {
        "title": {"typeClass": "primitive", "multiple": False},
        "subject": {"typeClass": "controlledVocabulary", "multiple": True},
        "otherId": {
            "typeClass": "compound",
            "multiple": True,
            "subfields": {
                "otherIdAgency": {"multiple": False},
                "otherIdValue": {"multiple": False},
            },
        },
    }

    blocks = reconstruir_dataverse({"citation": citation}, schema)
    field = next(field for field in blocks["citation"]["fields"] if field["typeName"] == "otherId")

    assert field == {
        "typeName": "otherId",
        "typeClass": "compound",
        "multiple": True,
        "value": [{
            "otherIdAgency": {
                "typeName": "otherIdAgency", "typeClass": "primitive", "multiple": False, "value": AGENCY,
            },
            "otherIdValue": {
                "typeName": "otherIdValue", "typeClass": "primitive", "multiple": False, "value": package_id,
            },
        }],
    }


def test_other_id_from_synthetic_eml_package_id_attribute(mapeo_ceiba):
    from src.ingest.utilitarios.xml_to_dict import xml_to_dict_tree
    from src.mapeo.ceiba.ceiba_source import read_record

    root = ElementTree.fromstring(
        '<eml:eml xmlns:eml="eml://ecoinformatics.org/eml-2.1.1" '
        'packageId="https://example.test/ceiba/resource?r=recurso-ficticio&amp;v=3.0">'
        "<dataset><title>Recurso sintético</title></dataset></eml:eml>"
    )
    package_id = "https://example.test/ceiba/resource?r=recurso-ficticio&v=3.0"
    ingested = {root.tag: xml_to_dict_tree(root)}
    record = read_record("carpeta-ficticia", ingested, latest_version="7")

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert root.attrib["packageId"] == record["package_id"] == package_id
    assert citation["otherId"] == [{"otherIdAgency": AGENCY, "otherIdValue": package_id}]
