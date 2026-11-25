"""
Pruebas permanentes del Nivel 1 del bloque citation.

Elementos:
- alternativeTitle
- subject
- notesText
"""

from src.mapeo.ceiba_mapping import construir_citation_intermedio
from src.mapeo.reconstruct_mapping import load_dv_schemas, unflatten_dataset


def obtener_campo(resultado, nombre):
    campos = resultado["citation"]["fields"]

    return next(
        campo for campo in campos
        if campo["typeName"] == nombre
    )


def test_alternative_title_presente():
    resultado = construir_citation_intermedio({
        "title": "Biodiversidad",
        "shortName": "Sonópolis"
    })

    assert resultado["citation"]["alternativeTitle"] == ["Sonópolis"]


def test_alternative_title_ausente():
    resultado = construir_citation_intermedio({
        "title": "Biodiversidad"
    })

    assert "alternativeTitle" not in resultado["citation"]


def test_alternative_title_dataverse():
    intermedio = construir_citation_intermedio({
        "title": "Biodiversidad",
        "shortName": "Sonópolis"
    })

    final = unflatten_dataset(intermedio, load_dv_schemas())
    campo = obtener_campo(final, "alternativeTitle")

    assert campo["multiple"] is True
    assert campo["typeClass"] == "primitive"
    assert campo["value"] == ["Sonópolis"]


def test_notes_text_presente():
    resultado = construir_citation_intermedio({
        "additionalInfo": {
            "para": "Información adicional"
        }
    })

    assert resultado["citation"]["notesText"] == "Información adicional"


def test_notes_text_ausente():
    resultado = construir_citation_intermedio({})

    assert "notesText" not in resultado["citation"]


def test_notes_text_varios_parrafos():
    resultado = construir_citation_intermedio({
        "additionalInfo": {
            "para": [
                "Primer párrafo",
                "Segundo párrafo"
            ]
        }
    })

    assert resultado["citation"]["notesText"] == (
        "Primer párrafo\nSegundo párrafo"
    )


def test_notes_text_excluye_unidades_curatoriales():
    resultado = construir_citation_intermedio({
        "additionalInfo": {
            "para": "Información adicional",
            "jgtiCuratorialUnit": {
                "beginRange": "100"
            }
        }
    })

    assert resultado["citation"]["notesText"] == "Información adicional"
    assert "jgtiCuratorialUnit" not in str(resultado)


def test_notes_text_dataverse():
    intermedio = construir_citation_intermedio({
        "additionalInfo": {
            "para": "Información adicional"
        }
    })

    final = unflatten_dataset(intermedio, load_dv_schemas())
    campo = obtener_campo(final, "notesText")

    assert campo["multiple"] is False
    assert campo["typeClass"] == "primitive"
    assert campo["value"] == "Información adicional"
