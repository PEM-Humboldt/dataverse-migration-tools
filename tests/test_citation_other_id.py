"""
Pruebas del mapeo de identificadores CEIBA hacia
citation/otherId de Dataverse.
"""

from pathlib import Path
import xml.etree.ElementTree as ET

import pytest

from src.ingest.utilitarios.xml_to_dict import xml_to_dict_tree
from src.mapeo.ceiba_mapping import (
    extraer_dataset,
    construir_citation_intermedio,
)
from src.mapeo.reconstruct_mapping import (
    load_dv_schemas,
    unflatten_dataset,
)


IDENTIFICADOR = (
    "http://i2d.humboldt.org.co/ceiba/"
    "resource.do?id=ivi-paramoguerrero/v5"
)


def crear_dataset():
    return {
        "title": "Biodiversidad de Colombia",
        "abstract": {
            "para": "Inventario de biodiversidad"
        },
        "keywordSet": {
            "keyword": ["Biodiversidad"]
        },
    }


def obtener_other_id_dataverse(identificador):
    intermedio = construir_citation_intermedio(
        crear_dataset(),
        identificador_ceiba=identificador,
    )

    resultado = unflatten_dataset(
        intermedio,
        load_dv_schemas(),
    )

    return next(
        campo
        for campo in resultado["citation"]["fields"]
        if campo["typeName"] == "otherId"
    )


def test_other_id_agency():
    intermedio = construir_citation_intermedio(
        crear_dataset(),
        identificador_ceiba=IDENTIFICADOR,
    )

    assert (
        intermedio["citation"]["otherId"][0]["otherIdAgency"]
        == "IPT Ceiba (I2D)"
    )


def test_other_id_value_completo():
    intermedio = construir_citation_intermedio(
        crear_dataset(),
        identificador_ceiba=IDENTIFICADOR,
    )

    assert (
        intermedio["citation"]["otherId"][0]["otherIdValue"]
        == IDENTIFICADOR
    )


def test_other_id_conserva_version():
    campo = obtener_other_id_dataverse(IDENTIFICADOR)

    valor = campo["value"][0]["otherIdValue"]["value"]

    assert valor.endswith("/v5")
    assert valor == IDENTIFICADOR


def test_other_id_estructura_compuesta():
    campo = obtener_other_id_dataverse(IDENTIFICADOR)

    assert campo["typeName"] == "otherId"
    assert campo["typeClass"] == "compound"
    assert campo["multiple"] is True
    assert len(campo["value"]) == 1

    subcampos = campo["value"][0]

    assert (
        subcampos["otherIdAgency"]["value"]
        == "IPT Ceiba (I2D)"
    )

    assert (
        subcampos["otherIdValue"]["value"]
        == IDENTIFICADOR
    )

    for nombre in ("otherIdAgency", "otherIdValue"):
        assert subcampos[nombre]["typeName"] == nombre
        assert subcampos[nombre]["typeClass"] == "primitive"
        assert subcampos[nombre]["multiple"] is False


def test_other_id_sin_identificador():
    intermedio = construir_citation_intermedio(
        crear_dataset(),
        identificador_ceiba=None,
    )

    assert not intermedio["citation"].get("otherId")


@pytest.mark.parametrize(
    "identificador",
    ["", "   ", "NA", "N/A", "NO APLICA"],
)
def test_other_id_valores_no_aplicables(identificador):
    intermedio = construir_citation_intermedio(
        crear_dataset(),
        identificador_ceiba=identificador,
    )

    assert not intermedio["citation"].get("otherId")


def test_other_id_eml_real():
    ruta = Path("../dataDir/ivi-paramoguerrero/eml-5.xml")

    if not ruta.exists():
        pytest.skip("EML real no disponible en este equipo")

    root = ET.parse(ruta).getroot()

    tags = {
        "inline_tags": {
            "emphasis", "subscript", "superscript",
            "i", "b", "u"
        },
        "list_tags": {
            "creator", "contact", "keyword",
            "keywordSet", "personnel",
            "associatedParty", "taxonClassification",
            "para"
        },
    }

    datos = {
        root.tag: xml_to_dict_tree(root, tags)
    }

    dataset = extraer_dataset(datos)

    identificador = datos[root.tag]["@packageId"]

    assert identificador == root.attrib["packageId"]

    intermedio = construir_citation_intermedio(
        dataset,
        identificador_ceiba=identificador,
    )

    resultado = unflatten_dataset(
        intermedio,
        load_dv_schemas(),
    )

    campo = next(
        campo
        for campo in resultado["citation"]["fields"]
        if campo["typeName"] == "otherId"
    )

    assert (
        campo["value"][0]["otherIdAgency"]["value"]
        == "IPT Ceiba (I2D)"
    )

    assert (
        campo["value"][0]["otherIdValue"]["value"]
        == identificador
    )

    assert identificador.endswith("/v5")
