"""Pruebas sintéticas de la descripción y su fecha en citation."""

from xml.etree import ElementTree

import pytest


def test_description_wraps_one_paragraph_in_html(mapeo_ceiba):
    dataset = {"abstract": {"para": "Inventario de especies."}}

    assert mapeo_ceiba.map_description(dataset) == [
        {"dsDescriptionValue": "<p>Inventario de especies.</p>"},
    ]


def test_description_preserves_paragraph_count_and_order(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"abstract": {"para": ["Primer párrafo.", "Segundo párrafo."]}})

    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert citation["dsDescription"] == [
        {"dsDescriptionValue": "<p>Primer párrafo.</p><p>Segundo párrafo.</p>"},
    ]


def test_description_escapes_html_characters(mapeo_ceiba):
    dataset = {"abstract": {"para": "Flora & fauna: A < B y C > D."}}

    [description] = mapeo_ceiba.map_description(dataset)

    assert description["dsDescriptionValue"] == "<p>Flora &amp; fauna: A &lt; B y C &gt; D.</p>"


def test_description_is_absent_without_abstract(mapeo_ceiba):
    assert mapeo_ceiba.map_description({"pubDate": "2024-02-29"}) == []


@pytest.mark.parametrize(
    "abstract",
    [
        pytest.param({}, id="empty-abstract"),
        pytest.param({"para": []}, id="empty-paragraph-list"),
        pytest.param({"para": ["", " \t\n", None]}, id="blank-paragraphs"),
    ],
)
def test_description_is_absent_when_empty(mapeo_ceiba, abstract):
    assert mapeo_ceiba.map_description({"abstract": abstract}) == []


def test_description_omits_empty_paragraphs_between_valid_ones(mapeo_ceiba):
    dataset = {"abstract": {"para": [None, "Inicio.", "", " \t\n", "Fin.", None]}}

    [description] = mapeo_ceiba.map_description(dataset)

    assert description["dsDescriptionValue"] == "<p>Inicio.</p><p>Fin.</p>"


def test_description_normalizes_whitespace(mapeo_ceiba):
    dataset = {"abstract": {"para": {"#text": "  Texto\t con\n  espacios   extra.  "}}}

    [description] = mapeo_ceiba.map_description(dataset)

    assert description["dsDescriptionValue"] == "<p>Texto con espacios extra.</p>"


def test_plain_text_description_joins_paragraphs_and_restores_mode(mapeo_ceiba, monkeypatch):
    dataset = {"abstract": {"para": ["Primer párrafo.", "Segundo párrafo."]}}
    original_mode = mapeo_ceiba.DESCRIPTION_AS_HTML
    original_description = mapeo_ceiba.map_description(dataset)

    with monkeypatch.context() as patch:
        patch.setattr(mapeo_ceiba, "DESCRIPTION_AS_HTML", False)
        assert mapeo_ceiba.map_description(dataset) == [
            {"dsDescriptionValue": "Primer párrafo.\nSegundo párrafo."},
        ]

    assert mapeo_ceiba.DESCRIPTION_AS_HTML is original_mode
    assert mapeo_ceiba.map_description(dataset) == original_description


@pytest.mark.parametrize("pub_date", ["2024-02-29", "2018"], ids=["full-date", "year-only"])
def test_reconstruction_preserves_description_and_matching_dates(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, pub_date
):
    record = record_ceiba({"abstract": {"para": "Descripción sintética."}, "pubDate": pub_date})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    assert citation["dsDescription"][0]["dsDescriptionDate"] == citation["distributionDate"] == pub_date

    schema = {
        "title": {"typeClass": "primitive", "multiple": False},
        "subject": {"typeClass": "controlledVocabulary", "multiple": True},
        "distributionDate": {"typeClass": "primitive", "multiple": False},
        "dsDescription": {
            "typeClass": "compound",
            "multiple": True,
            "subfields": {name: {"multiple": False} for name in ("dsDescriptionValue", "dsDescriptionDate")},
        },
    }
    blocks = reconstruir_dataverse({"citation": citation}, schema)
    fields = {field["typeName"]: field for field in blocks["citation"]["fields"]}

    assert fields["dsDescription"] == {
        "typeName": "dsDescription",
        "typeClass": "compound",
        "multiple": True,
        "value": [{
            "dsDescriptionValue": {
                "typeName": "dsDescriptionValue",
                "typeClass": "primitive",
                "multiple": False,
                "value": "<p>Descripción sintética.</p>",
            },
            "dsDescriptionDate": {
                "typeName": "dsDescriptionDate",
                "typeClass": "primitive",
                "multiple": False,
                "value": pub_date,
            },
        }],
    }
    assert fields["distributionDate"]["value"] == pub_date


@pytest.fixture
def mapped_emphasis_paragraph(mapeo_ceiba):
    """Procesa XML en memoria con las opciones pertinentes de la ingesta."""
    from src.ingest.utilitarios.xml_to_dict import xml_to_dict_tree
    from src.mapeo.ceiba.ceiba_source import read_record

    root = ElementTree.fromstring(
        '<eml:eml xmlns:eml="eml://ecoinformatics.org/eml-2.1.1">'
        "<dataset><abstract><para>Texto con <emphasis>énfasis</emphasis> al centro.</para></abstract></dataset>"
        "</eml:eml>"
    )
    ingested = {root.tag: xml_to_dict_tree(root, {"inline_tags": {"emphasis"}, "list_tags": {"para"}})}
    record = read_record("recurso-sintetico", ingested, latest_version="1")
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    [description] = citation["dsDescription"]
    return ElementTree.fromstring(description["dsDescriptionValue"])


def test_description_preserves_text_of_emphasis_through_ingestion(mapped_emphasis_paragraph):
    """Comprueba el contenido textual incluso cuando cambia el formato en línea."""
    assert mapped_emphasis_paragraph.tag == "p"
    assert "".join(mapped_emphasis_paragraph.itertext()) == "Texto con énfasis al centro."


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="DESC-H01: la ingesta aplana emphasis; la decisión del equipo sobre HTML o texto plano sigue pendiente.",
)
def test_description_converts_emphasis_to_em(mapped_emphasis_paragraph):
    """Comprueba que el HTML conserva la marca de énfasis del párrafo original."""
    emphasis = mapped_emphasis_paragraph.find("em")
    assert emphasis is not None, "El texto enfatizado debe quedar dentro de em."
    assert emphasis.text == "énfasis"
