"""
Pruebas del mapeo intermedio CEIBA hacia Dataverse.
"""

from src.mapeo.ceiba_mapping import (
    construir_citation_intermedio
)


def test_mapeo_intermedio():

    dataset = {
        "title": {
            "#text": "Biodiversidad de Colombia"
        },
        "abstract": {
            "para": [
                "Inventario de especies",
                "Registros de biodiversidad"
            ]
        },
        "keywordSet": {
            "keyword": [
                "Biodiversidad",
                "Colombia"
            ],
            "keywordThesaurus": "N/A"
        }
    }

    resultado = construir_citation_intermedio(
        dataset,
        identificador_ceiba="recurso_001"
    )

    citation = resultado["citation"]

    # Título
    assert (
        citation["title"]
        == "Biodiversidad de Colombia"
    )

    # Descripción
    assert (
        citation["dsDescription"][0]["dsDescriptionValue"]
        == "Inventario de especies\n\nRegistros de biodiversidad"
    )

    # Palabras clave
    assert (
        citation["keyword"][0]["keywordValue"]
        == "Biodiversidad"
    )

    assert (
        citation["keyword"][1]["keywordValue"]
        == "Colombia"
    )

    # Identificador
    assert (
        citation["otherId"][0]["otherIdAgency"]
        == "IPT Ceiba (I2D)"
    )

    assert (
        citation["otherId"][0]["otherIdValue"]
        == "recurso_001"
    )


def test_sin_autores_contactos():

    dataset = {
        "title": "Recurso de prueba",
        "creator": [
            {
                "individualName": {
                    "givenName": "Ana"
                }
            }
        ],
        "contact": [
            {
                "organizationName": "Entidad"
            }
        ]
    }

    resultado = construir_citation_intermedio(
        dataset
    )

    citation = resultado["citation"]

    assert citation["title"] == "Recurso de prueba"

    assert "author" not in citation

    assert "datasetContact" not in citation


def test_dataset_vacio():

    resultado = construir_citation_intermedio({})

    assert resultado == {
        "citation": {
            "subject": ["Earth and Environmental Sciences"]
        }
    }