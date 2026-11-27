"""Pruebas sintéticas del idioma de citation."""

from xml.etree import ElementTree

import pytest


@pytest.fixture
def language_identifiers():
    """Proporciona equivalencias sintéticas de los identificadores de idioma."""
    return {
        ("language", "spa"): "Spanish, Castilian",
        ("language", "eng"): "English",
        ("language", "oci"): "Occitan",
    }


@pytest.fixture
def language_schema():
    """Define un esquema sintético de Dataverse para un citation mínimo."""
    return {
        "title": {"typeClass": "primitive", "multiple": False},
        "subject": {"typeClass": "controlledVocabulary", "multiple": True},
        "language": {"typeClass": "controlledVocabulary", "multiple": True},
    }


@pytest.mark.parametrize(
    ("code", "expected"),
    [("spa", "Spanish, Castilian"), ("eng", "English"), ("oci", "Occitan")],
)
def test_maps_iso_language_code(mapeo_ceiba, language_identifiers, code, expected):
    assert mapeo_ceiba.map_language({"language": code}, language_identifiers) == [expected]


def test_language_normalizes_case_and_whitespace(mapeo_ceiba, language_identifiers):
    dataset = {"language": {"#text": " \t SPA  \n"}}

    assert mapeo_ceiba.map_language(dataset, language_identifiers) == ["Spanish, Castilian"]


def test_language_deduplicates_labels_and_preserves_distinct_languages(
    mapeo_ceiba, language_identifiers
):
    dataset = {"language": ["eng", "ENG", "spa", {"#text": " oci "}, "OCI", "spa"]}

    values = mapeo_ceiba.map_language(dataset, language_identifiers)

    assert sorted(values) == ["English", "Occitan", "Spanish, Castilian"]


def test_reconstructs_language_as_repeatable_controlled_vocabulary(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, language_identifiers, language_schema
):
    record = record_ceiba({"language": ["spa", "eng"]})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers=language_identifiers)

    blocks = reconstruir_dataverse({"citation": citation}, language_schema)
    field = next(field for field in blocks["citation"]["fields"] if field["typeName"] == "language")

    assert field == {
        "typeName": "language",
        "typeClass": "controlledVocabulary",
        "multiple": True,
        "value": ["Spanish, Castilian", "English"],
    }


@pytest.mark.parametrize(
    "dataset",
    [pytest.param({}, id="absent"), pytest.param({"language": "zzz"}, id="unknown-code")],
)
def test_omits_missing_or_unknown_language_from_dataverse(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, language_identifiers, language_schema, dataset
):
    """Caracteriza también LANG-H01, la omisión actual de códigos desconocidos."""
    citation = mapeo_ceiba.map_citation(
        record_ceiba(dataset), tables={}, identifiers=language_identifiers
    )

    blocks = reconstruir_dataverse({"citation": citation}, language_schema)

    assert citation["language"] == []
    assert all(field["typeName"] != "language" for field in blocks["citation"]["fields"])


def test_reads_language_identifiers_from_synthetic_tsv(mapeo_ceiba, language_identifiers, tmp_path):
    (tmp_path / "citation.tsv").write_text(
        "#controlledVocabulary\tDatasetField\tValue\tidentifier\n"
        "\tlanguage\tSpanish, Castilian\t SPA \n"
        "\tlanguage\tEnglish\teng\n"
        "\tlanguage\tOccitan\toci\n",
        encoding="utf-8",
    )

    assert mapeo_ceiba.vocabulary_identifiers(tmp_path) == language_identifiers


def test_language_from_synthetic_eml(mapeo_ceiba, language_identifiers):
    from src.ingest.utilitarios.xml_to_dict import xml_to_dict_tree
    from src.mapeo.ceiba.ceiba_source import read_record

    root = ElementTree.fromstring(
        '<eml:eml xmlns:eml="eml://ecoinformatics.org/eml-2.1.1">'
        "<dataset><title>Recurso sintético</title><language>oci</language></dataset></eml:eml>"
    )
    record = read_record("carpeta-ficticia", {root.tag: xml_to_dict_tree(root)})

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers=language_identifiers)

    assert citation["language"] == ["Occitan"]
