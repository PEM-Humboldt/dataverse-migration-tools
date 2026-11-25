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
        "{eml://ecoinformatics.org/eml-2.1.1}eml": {
            "@packageId": (
                "http://i2d.humboldt.org.co/ceiba/"
                "resource.do?id=recurso_prueba/v5"
            ),
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
    assert resultado["campos_dataverse"] == 5


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


def test_identificador_completo_desde_eml(tmp_path):
    """
    Comprueba que el identificador procede de @packageId
    y conserva la versión publicada del recurso.
    """
    ruta = crear_recurso(tmp_path)
    schema = load_dv_schemas()

    resultado = validar_recurso(ruta, schema)

    assert resultado["estado"] == "CORRECTO"
    assert resultado["identificador_ceiba"] is True

    # Verificar también el valor que llega al mapeador.
    with patch(
        "src.mapeo.validar_integracion_ceiba."
        "construir_citation_intermedio",
        wraps=__import__(
            "src.mapeo.ceiba_mapping",
            fromlist=["construir_citation_intermedio"]
        ).construir_citation_intermedio,
    ) as mapeador:

        validar_recurso(ruta, schema)

        identificador = (
            mapeador.call_args.kwargs["identificador_ceiba"]
        )

    assert identificador == (
        "http://i2d.humboldt.org.co/ceiba/"
        "resource.do?id=recurso_prueba/v5"
    )

    assert identificador != ruta.parent.name
