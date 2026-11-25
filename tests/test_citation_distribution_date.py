"""
Pruebas permanentes de distributionDate.

Origen:
    CEIBA EML dataset/pubDate

Destino:
    Dataverse citation.distributionDate

Regla:
    Conservar únicamente fechas históricas completas
    y válidas con formato YYYY-MM-DD.
"""

from pathlib import Path

import pytest
import xmltodict

from src.mapeo.ceiba_mapping import (
    construir_citation_intermedio,
    mapear_fecha_publicacion,
)

from src.mapeo.reconstruct_mapping import (
    load_dv_schemas,
    unflatten_dataset,
)


@pytest.mark.parametrize(
    "fecha",
    [
        "2017-05-16",
        "2020-12-31",
        "2024-02-29",
    ],
)
def test_fechas_validas(fecha):
    assert mapear_fecha_publicacion(fecha) == fecha


@pytest.mark.parametrize(
    "fecha",
    [
        "2017",
        "2017-05",
        "2017-02-30",
        "2023-02-29",
        "2017-13-01",
        "2017-00-10",
        "",
        None,
    ],
)
def test_fechas_invalidas_o_incompletas(fecha):
    assert mapear_fecha_publicacion(fecha) is None


def test_distribution_date_intermedio():
    dataset = {
        "title": "Recurso de prueba",
        "pubDate": "2017-05-16",
    }

    resultado = construir_citation_intermedio(dataset)

    assert resultado["citation"]["distributionDate"] == (
        "2017-05-16"
    )


def test_distribution_date_ausente():
    dataset = {
        "title": "Recurso sin fecha",
    }

    resultado = construir_citation_intermedio(dataset)

    assert "distributionDate" not in resultado["citation"]


def test_distribution_date_incompleta():
    dataset = {
        "title": "Recurso con fecha incompleta",
        "pubDate": "2017",
    }

    resultado = construir_citation_intermedio(dataset)

    assert "distributionDate" not in resultado["citation"]


def test_distribution_date_dataverse():
    dataset = {
        "title": "Recurso de prueba",
        "pubDate": "2017-05-16",
    }

    intermedio = construir_citation_intermedio(dataset)

    final = unflatten_dataset(
        intermedio,
        load_dv_schemas(),
    )

    campo = next(
        campo
        for campo in final["citation"]["fields"]
        if campo["typeName"] == "distributionDate"
    )

    assert campo["typeClass"] == "primitive"
    assert campo["multiple"] is False
    assert campo["value"] == "2017-05-16"


def test_distribution_date_eml_real():
    ruta = Path("../dataDir/ivi-paramoguerrero/eml-5.xml")

    if not ruta.exists():
        pytest.skip("EML real no disponible en este equipo")

    assert ruta.exists(), (
        f"No se encontró el EML de prueba: {ruta}"
    )

    with ruta.open("rb") as archivo:
        datos = xmltodict.parse(archivo)

    dataset = datos["eml:eml"]["dataset"]

    assert dataset["pubDate"] == "2017-05-16"

    resultado = construir_citation_intermedio(dataset)

    assert resultado["citation"]["distributionDate"] == (
        "2017-05-16"
    )
