import json

from unittest.mock import patch

from src.mapeo.validar_integracion_ceiba import (
    validar_recurso,
)
from src.mapeo.reconstruct_mapping import (
    load_dv_schemas,
)


def crear_recurso(tmp_path):
    directorio = tmp_path / "recurso_prueba"
    directorio.mkdir()

    ruta = directorio / "resource_metadata.json"

    datos = {
        "dataset": {
            "title": "Biodiversidad de Colombia",
            "abstract": {
                "para": "Inventario de biodiversidad"
            },
            "keywordSet": {
                "keyword": ["Biodiversidad", "Colombia"]
            }
        }
    }

    ruta.write_text(
        json.dumps(datos),
        encoding="utf-8"
    )

    return ruta


def test_recurso_correcto(tmp_path):
    ruta = crear_recurso(tmp_path)
    schema = load_dv_schemas()

    resultado = validar_recurso(ruta, schema)

    assert resultado["estado"] == "CORRECTO"
    assert resultado["campos_dataverse"] == 4


def test_recurso_sin_eml(tmp_path):
    ruta = crear_recurso(tmp_path)
    schema = load_dv_schemas()

    with patch(
        "src.mapeo.validar_integracion_ceiba.extraer_dataset",
        side_effect=ValueError(
            "No se encontró dataset en la estructura del JSON intermedio"
        ),
    ):
        resultado = validar_recurso(ruta, schema)

    assert resultado["estado"] == "SIN_EML"


def test_campo_faltante(tmp_path):
    ruta = crear_recurso(tmp_path)
    schema = load_dv_schemas()

    from src.mapeo.validar_integracion_ceiba import (
        unflatten_dataset,
    )

    def reconstruccion_incompleta(intermedio, schema):
        resultado = unflatten_dataset(intermedio, schema)

        resultado["citation"]["fields"] = [
            campo
            for campo in resultado["citation"]["fields"]
            if campo["typeName"] != "keyword"
        ]

        return resultado

    with patch(
        "src.mapeo.validar_integracion_ceiba.unflatten_dataset",
        side_effect=reconstruccion_incompleta,
    ):
        resultado = validar_recurso(ruta, schema)

    assert resultado["estado"] == "INCOMPLETO"
    assert "keyword" in resultado["error"]


def test_valor_diferente(tmp_path):
    ruta = crear_recurso(tmp_path)
    schema = load_dv_schemas()

    from src.mapeo.validar_integracion_ceiba import (
        unflatten_dataset,
    )

    def reconstruccion_modificada(intermedio, schema):
        resultado = unflatten_dataset(intermedio, schema)

        for campo in resultado["citation"]["fields"]:
            if campo["typeName"] == "title":
                campo["value"] = "Título modificado"

        return resultado

    with patch(
        "src.mapeo.validar_integracion_ceiba.unflatten_dataset",
        side_effect=reconstruccion_modificada,
    ):
        resultado = validar_recurso(ruta, schema)

    assert resultado["estado"] == "INCOMPLETO"
    assert "title" in resultado["error"]
