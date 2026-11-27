"""Pruebas sintéticas del título y el tema de citation."""

import pytest


SUBJECT_VALUE = "Earth and Environmental Sciences"


@pytest.fixture
def citation_schema():
    """Define el esquema y el vocabulario sintéticos para title y subject."""
    return {
        "title": {"typeClass": "primitive", "multiple": False, "required": True},
        "subject": {
            "typeClass": "controlledVocabulary",
            "multiple": True,
            "required": True,
            "vocabulary": ["Arts and Humanities", "Earth and Environmental Sciences"],
        },
    }


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        pytest.param("Biodiversidad de prueba", "Biodiversidad de prueba", id="plain-text"),
        pytest.param(
            {"#text": "Árboles y fauna: observaciones (2024).", "@xml:lang": "es"},
            "Árboles y fauna: observaciones (2024).",
            id="text-with-attributes",
        ),
        pytest.param(
            "  Flora\t y  fauna\r\n del bosque  ",
            "Flora y fauna del bosque",
            id="normalized-whitespace",
        ),
    ],
)
def test_title_comes_from_dataset_and_preserves_text(mapeo_ceiba, record_ceiba, source, expected):
    record = record_ceiba({"title": source})
    record["name"] = "carpeta-ficticia"

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert citation["title"] == expected


def test_missing_title_is_not_invented(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, citation_schema
):
    record = record_ceiba({"shortName": "Otro nombre"})
    record["name"] = "carpeta-ficticia"
    record["eml_version"] = "2.2.0"
    del record["dataset"]["title"]

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    blocks = reconstruir_dataverse(
        {"citation": {"title": citation["title"], "subject": citation["subject"]}},
        citation_schema,
    )

    assert citation["title"] == ""
    assert all(field["typeName"] != "title" for field in blocks["citation"]["fields"])


def test_reconstructs_title_as_single_primitive(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, citation_schema
):
    record = record_ceiba({"title": "Título sintético"})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    blocks = reconstruir_dataverse({"citation": citation}, citation_schema)
    field = next(field for field in blocks["citation"]["fields"] if field["typeName"] == "title")

    assert field == {
        "typeName": "title",
        "typeClass": "primitive",
        "multiple": False,
        "value": "Título sintético",
    }


def test_subject_is_constant_for_empty_dataset(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["dataset"].clear()

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert citation["subject"] == [SUBJECT_VALUE]


def test_subject_is_independent_of_eml_topics(mapeo_ceiba, record_ceiba):
    record = record_ceiba({
        "subject": ["Arts and Humanities"],
        "keywordSet": {"keyword": ["Arte", "Historia"]},
        "coverage": {"taxonomicCoverage": {"generalTaxonomicCoverage": "Plantas"}},
    })

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert citation["subject"] == [SUBJECT_VALUE]


def test_reconstructs_subject_as_repeatable_controlled_vocabulary(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, citation_schema
):
    citation = mapeo_ceiba.map_citation(record_ceiba({}), tables={}, identifiers={})

    blocks = reconstruir_dataverse({"citation": citation}, citation_schema)
    field = next(field for field in blocks["citation"]["fields"] if field["typeName"] == "subject")

    assert field == {
        "typeName": "subject",
        "typeClass": "controlledVocabulary",
        "multiple": True,
        "value": [SUBJECT_VALUE],
    }


def test_subject_belongs_to_synthetic_reference_vocabulary(mapeo_ceiba, record_ceiba, citation_schema):
    from src.mapeo.geonetwork.dataverse_check import check_fields

    citation = mapeo_ceiba.map_citation(record_ceiba({}), tables={}, identifiers={})
    fields = {"citation": {"subject": citation["subject"]}}

    assert check_fields(fields, {"subject": citation_schema["subject"]}, ["citation"]) == []
