"""Pruebas sintéticas de notesText y su reconstrucción en citation.

El HTML caracteriza el comportamiento actual y queda pendiente de explicitación
en el crosswalk.
"""

import pytest


@pytest.fixture
def map_citation(mapeo_ceiba, record_ceiba):
    """Mapea un registro sintético con el contenido indicado."""
    def map_dataset(dataset):
        return mapeo_ceiba.map_citation(record_ceiba(dataset), tables={}, identifiers={})

    return map_dataset


def test_notes_wrap_additional_info_paragraph_in_html(map_citation):
    citation = map_citation({"additionalInfo": {"para": "Información adicional."}})

    assert citation["notesText"] == "<p>Información adicional.</p>"


def test_notes_are_absent_without_additional_info(map_citation):
    assert "notesText" not in map_citation({})


def test_notes_preserve_multiple_paragraphs_in_order(map_citation):
    citation = map_citation({"additionalInfo": {"para": ["Primer párrafo.", "Segundo párrafo."]}})

    assert citation["notesText"] == "<p>Primer párrafo.</p><p>Segundo párrafo.</p>"


def test_notes_exclude_curatorial_units(map_citation):
    citation = map_citation({"additionalInfo": {
        "para": "Información adicional.",
        "jgtiCuratorialUnit": {
            "beginRange": "731",
            "endRange": "809",
            "unitType": "Unidad sintética reservada para curación",
        },
    }})

    assert citation["notesText"] == "<p>Información adicional.</p>"


def test_reconstructs_notes_as_single_primitive_string(map_citation, reconstruir_dataverse):
    citation = map_citation({"additionalInfo": {"para": "Información adicional."}})
    schema = {
        "title": {"typeClass": "primitive", "multiple": False},
        "subject": {"typeClass": "controlledVocabulary", "multiple": True},
        "notesText": {"typeClass": "primitive", "multiple": False},
    }

    blocks = reconstruir_dataverse({"citation": citation}, schema)
    notes = next(field for field in blocks["citation"]["fields"] if field["typeName"] == "notesText")

    assert notes == {
        "typeName": "notesText",
        "typeClass": "primitive",
        "multiple": False,
        "value": "<p>Información adicional.</p>",
    }


@pytest.mark.parametrize(
    "additional_info",
    [
        pytest.param({}, id="empty-additional-info"),
        pytest.param({"para": []}, id="empty-paragraph-list"),
        pytest.param({"para": ["", " \t\n", None]}, id="blank-paragraphs"),
    ],
)
def test_notes_are_absent_when_additional_info_is_empty(map_citation, additional_info):
    assert "notesText" not in map_citation({"additionalInfo": additional_info})


def test_notes_escape_html_characters(map_citation):
    citation = map_citation({"additionalInfo": {"para": "Flora & fauna: A < B y C > D."}})

    assert citation["notesText"] == "<p>Flora &amp; fauna: A &lt; B y C &gt; D.</p>"


def test_notes_normalize_whitespace(map_citation):
    citation = map_citation({"additionalInfo": {"para": {"#text": "  Nota\t con\n  espacios   extra.  "}}})

    assert citation["notesText"] == "<p>Nota con espacios extra.</p>"


def test_notes_exclude_content_outside_additional_info_paragraphs(map_citation):
    citation = map_citation({
        "abstract": {"para": "Descripción ajena a las notas."},
        "additionalInfo": {
            "para": "Sólo este párrafo va a notas.",
            "#text": "Texto directo fuera del párrafo.",
            "otherElement": {"para": "Párrafo de otro elemento."},
        },
    })

    assert citation["notesText"] == "<p>Sólo este párrafo va a notas.</p>"


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason=(
        "NOTE-H02: la implementación admite texto directo en additionalInfo sin para; "
        "no se identificaron casos reales en los 1107 recursos evaluados. "
        "Interpretación estricta de la fuente del crosswalk pendiente de concertación."
    ),
)
def test_notes_exclude_direct_additional_info_text_without_paragraph(map_citation):
    citation = map_citation({"additionalInfo": "Texto directo sin párrafo."})

    assert "notesText" not in citation, f"notesText={citation.get('notesText')!r}"
