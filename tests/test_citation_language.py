"""
Pruebas permanentes del elemento language.

Mapeo:
CEIBA EML dataset/language
    -> ISO 639-2
    -> vocabulario Dataverse citation.tsv
    -> citation.language
"""

from pathlib import Path

import pytest
import xmltodict

from src.mapeo.ceiba_mapping import (
    construir_citation_intermedio,
    cargar_vocabulario_idiomas,
)

from src.mapeo.reconstruct_mapping import (
    load_dv_schemas,
    unflatten_dataset,
)


@pytest.mark.parametrize(
    "codigo, esperado",
    [
        ("spa", "Spanish, Castilian"),
        ("eng", "English"),
        ("oci", "Occitan"),
    ],
)
def test_equivalencias_iso(codigo, esperado):
    resultado = construir_citation_intermedio({
        "title": "Recurso de prueba",
        "language": codigo,
    })

    assert resultado["citation"]["language"] == [esperado]


def test_language_ausente():
    resultado = construir_citation_intermedio({
        "title": "Recurso sin idioma",
    })

    assert "language" not in resultado["citation"]


def test_language_desconocido():
    resultado = construir_citation_intermedio({
        "title": "Recurso de prueba",
        "language": "zzz",
    })

    assert "language" not in resultado["citation"]


def test_language_mayusculas():
    resultado = construir_citation_intermedio({
        "title": "Recurso de prueba",
        "language": "SPA",
    })

    assert resultado["citation"]["language"] == [
        "Spanish, Castilian"
    ]


def test_language_dataverse():
    intermedio = construir_citation_intermedio({
        "title": "Recurso de prueba",
        "language": "spa",
    })

    final = unflatten_dataset(
        intermedio,
        load_dv_schemas(),
    )

    campo = next(
        campo
        for campo in final["citation"]["fields"]
        if campo["typeName"] == "language"
    )

    assert campo["typeClass"] == "controlledVocabulary"
    assert campo["multiple"] is True
    assert campo["value"] == ["Spanish, Castilian"]


def test_vocabulario_original():
    equivalencias = cargar_vocabulario_idiomas()

    assert equivalencias["spa"] == "Spanish, Castilian"
    assert equivalencias["eng"] == "English"
    assert equivalencias["oci"] == "Occitan"


def test_language_eml_real():
    ruta = Path("../dataDir/ivi-paramoguerrero/eml-5.xml")

    if not ruta.exists():
        pytest.skip("EML real no disponible en este equipo")

    assert ruta.exists(), (
        f"No se encontró el EML de prueba: {ruta}"
    )

    with ruta.open("rb") as archivo:
        datos = xmltodict.parse(archivo)

    dataset = datos["eml:eml"]["dataset"]

    assert dataset["language"] == "spa"

    resultado = construir_citation_intermedio(dataset)

    assert resultado["citation"]["language"] == [
        "Spanish, Castilian"
    ]
