"""
Pruebas de integración del mapeo CEIBA con LIB-1051.

Verifica que el diccionario intermedio producido por
ceiba_mapping.py pueda reconstruirse correctamente
utilizando los esquemas de Dataverse.

Campos evaluados:
- title
- dsDescription
- keyword
- otherId

No se integran autores ni contactos.
"""

import pytest

from src.mapeo.ceiba_mapping import (
    construir_citation_intermedio,
)

from src.mapeo.reconstruct_mapping import (
    load_dv_schemas,
    unflatten_dataset,
)


@pytest.fixture
def dataset_prueba():
    """
    Metadatos EML simulados para las pruebas.
    """

    return {
        "title": {
            "#text": "Biodiversidad de Colombia"
        },
        "abstract": {
            "para": [
                "Inventario de especies",
                "Registros de biodiversidad",
            ]
        },
        "keywordSet": {
            "keyword": [
                "Biodiversidad",
                "Colombia",
            ],
            "keywordThesaurus": "N/A",
        },
    }


@pytest.fixture
def resultado_dataverse(dataset_prueba):
    """
    Ejecuta el flujo completo de integración.
    """

    intermedio = construir_citation_intermedio(
        dataset_prueba,
        identificador_ceiba="recurso_001",
    )

    schema = load_dv_schemas()

    campos_requeridos = {
        "title",
        "dsDescription",
        "keyword",
        "otherId",
    }

    faltantes = campos_requeridos - schema.keys()

    if faltantes:
        pytest.fail(
            f"El esquema no contiene estos campos: {faltantes}"
        )

    return unflatten_dataset(
        intermedio,
        schema,
    )


def obtener_campo(resultado, nombre):
    """
    Busca un campo dentro del bloque citation.
    """

    campos = resultado["citation"]["fields"]

    for campo in campos:
        if campo["typeName"] == nombre:
            return campo

    raise AssertionError(
        f"No se encontró el campo: {nombre}"
    )


def test_bloque_citation(resultado_dataverse):
    """
    Comprueba la estructura general del bloque.
    """

    assert "citation" in resultado_dataverse

    citation = resultado_dataverse["citation"]

    assert citation["name"] == "citation"

    assert isinstance(citation["fields"], list)

    assert len(citation["fields"]) == 4


def test_titulo(resultado_dataverse):
    """
    Comprueba el título y sus propiedades.
    """

    campo = obtener_campo(
        resultado_dataverse,
        "title",
    )

    assert campo["typeClass"] == "primitive"

    assert campo["multiple"] is False

    assert campo["value"] == "Biodiversidad de Colombia"


def test_descripcion(resultado_dataverse):
    """
    Comprueba la descripción y su subcampo.
    """

    campo = obtener_campo(
        resultado_dataverse,
        "dsDescription",
    )

    assert campo["typeClass"] == "compound"

    assert campo["multiple"] is True

    assert len(campo["value"]) == 1

    subcampo = campo["value"][0]["dsDescriptionValue"]

    assert subcampo["typeName"] == "dsDescriptionValue"

    assert subcampo["typeClass"] == "primitive"

    assert subcampo["multiple"] is False

    assert subcampo["value"] == (
        "Inventario de especies\n\n"
        "Registros de biodiversidad"
    )


def test_palabras_clave(resultado_dataverse):
    """
    Comprueba las palabras clave y su multiplicidad.
    """

    campo = obtener_campo(
        resultado_dataverse,
        "keyword",
    )

    assert campo["typeClass"] == "compound"

    assert campo["multiple"] is True

    assert len(campo["value"]) == 2

    valores = [
        elemento["keywordValue"]["value"]
        for elemento in campo["value"]
    ]

    assert valores == [
        "Biodiversidad",
        "Colombia",
    ]


def test_identificador_ceiba(resultado_dataverse):
    """
    Comprueba el identificador de procedencia CEIBA.
    """

    campo = obtener_campo(
        resultado_dataverse,
        "otherId",
    )

    assert campo["typeClass"] == "compound"

    assert campo["multiple"] is True

    assert len(campo["value"]) == 1

    identificador = campo["value"][0]

    assert (
        identificador["otherIdAgency"]["value"]
        == "CEIBA"
    )

    assert (
        identificador["otherIdValue"]["value"]
        == "recurso_001"
    )


def test_sin_autores_contactos(resultado_dataverse):
    """
    Comprueba que no se incorporan autores
    ni contactos en esta etapa.
    """

    nombres = {
        campo["typeName"]
        for campo in resultado_dataverse["citation"]["fields"]
    }

    assert "author" not in nombres

    assert "datasetContact" not in nombres