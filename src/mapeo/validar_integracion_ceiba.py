"""
Validación por lotes de la integración CEIBA → Dataverse.

Lee los archivos resource_metadata.json generados por
la ingesta CEIBA y comprueba su transformación mediante
el constructor intermedio y LIB-1051.

No modifica los archivos originales.
No realiza solicitudes a la API de Dataverse.
"""

import csv
import json
import os

from pathlib import Path

from src.mapeo.ceiba_mapping import (
    extraer_dataset,
    construir_citation_intermedio,
)

from src.mapeo.reconstruct_mapping import (
    load_dv_schemas,
    unflatten_dataset,
)


DIRECTORIO_ENTRADA = Path(
    os.getenv(
        "CEIBA_DATA_DIR",
        "../dataverse-migration-tools/data/ceiba/raw"
    )
)

DIRECTORIO_SALIDA = Path(
    os.getenv(
        "CEIBA_REPORT_DIR",
        "data/ceiba/reportes"
    )
)

ARCHIVO_REPORTE = (
    DIRECTORIO_SALIDA / "validacion_integracion_ceiba.csv"
)



def recuperar_valor(campo):
    """
    Recupera los valores de un campo reconstruido
    para compararlos con el diccionario intermedio.
    """

    if campo["typeClass"] != "compound":
        return campo["value"]

    elementos = campo["value"]

    if not isinstance(elementos, list):
        elementos = [elementos]

    recuperados = []

    for elemento in elementos:
        recuperados.append({
            nombre: subcampo["value"]
            for nombre, subcampo in elemento.items()
        })

    return recuperados


def validar_recurso(ruta, schema):
    """
    Procesa un recurso individual y devuelve
    los resultados de validación.
    """

    identificador = ruta.parent.name

    reporte = {
        "recurso": identificador,
        "dataset_eml": False,
        "titulo": False,
        "descripcion": False,
        "palabras_clave": 0,
        "identificador_ceiba": False,
        "campos_dataverse": 0,
        "estado": "",
        "error": "",
    }

    try:

        # 1. Leer JSON
        with ruta.open(encoding="utf-8") as archivo:
            datos = json.load(archivo)

        # 2. Extraer dataset EML
        dataset = extraer_dataset(datos)

        if not isinstance(dataset, dict):
            reporte["estado"] = "SIN_EML"
            return reporte

        reporte["dataset_eml"] = True

        # 3. Recuperar el identificador original del EML
        # Se conserva completo, incluida la versión publicada.
        raiz_eml = next(
            (
                contenido
                for clave, contenido in datos.items()
                if isinstance(clave, str)
                and (
                    clave == "eml"
                    or clave == "eml:eml"
                    or clave.endswith("}eml")
                )
                and isinstance(contenido, dict)
            ),
            None,
        )

        identificador_eml = (
            raiz_eml.get("@packageId")
            if raiz_eml is not None
            else None
        )

        # 4. Construir diccionario intermedio
        intermedio = construir_citation_intermedio(
            dataset,
            identificador_ceiba=identificador_eml,
        )

        citation = intermedio.get("citation", {})

        reporte["titulo"] = bool(
            citation.get("title")
        )

        reporte["descripcion"] = bool(
            citation.get("dsDescription")
        )

        reporte["palabras_clave"] = len(
            citation.get("keyword", [])
        )

        reporte["identificador_ceiba"] = bool(
            citation.get("otherId")
        )

        # 4. Reconstruir Dataverse
        resultado = unflatten_dataset(
            intermedio,
            schema,
        )

        campos = resultado.get(
            "citation", {}
        ).get("fields", [])

        reporte["campos_dataverse"] = len(campos)

        # 5. Verificar campos y conservación de valores
        campos_esperados = {
            "title",
            "dsDescription",
            "keyword",
            "otherId",
        }

        campos_reconstruidos = {
            campo["typeName"]: campo
            for campo in campos
        }

        faltantes = (
            campos_esperados - campos_reconstruidos.keys()
        )

        diferencias = []

        for nombre in sorted(
            campos_esperados & campos_reconstruidos.keys()
        ):
            original = citation.get(nombre)
            recuperado = recuperar_valor(
                campos_reconstruidos[nombre]
            )

            if original != recuperado:
                diferencias.append(nombre)

        if faltantes or diferencias:
            reporte["estado"] = "INCOMPLETO"

            detalles = []

            if faltantes:
                detalles.append(
                    f"Campos faltantes: {sorted(faltantes)}"
                )

            if diferencias:
                detalles.append(
                    f"Valores diferentes: {diferencias}"
                )

            reporte["error"] = "; ".join(detalles)

        else:
            reporte["estado"] = "CORRECTO"

    #except Exception as error:

    #    reporte["estado"] = "ERROR"

    #    reporte["error"] = (
    #        f"{type(error).__name__}: {error}"
    #    )
    except ValueError as error:

        if str(error) == (
            "No se encontró dataset en la estructura del JSON intermedio"
        ):
            reporte["estado"] = "SIN_EML"
            reporte["error"] = ""
        else:
            reporte["estado"] = "ERROR"
            reporte["error"] = (
                f"{type(error).__name__}: {error}"
            )

    except Exception as error:

        reporte["estado"] = "ERROR"

        reporte["error"] = (
            f"{type(error).__name__}: {error}"
        )


    return reporte


def ejecutar_validacion():

    if not DIRECTORIO_ENTRADA.is_dir():
        raise FileNotFoundError(
            f"No existe: {DIRECTORIO_ENTRADA}"
        )

    rutas = sorted(
        DIRECTORIO_ENTRADA.glob(
            "*/resource_metadata.json"
        )
    )

    print(f"Recursos encontrados: {len(rutas)}")

    schema = load_dv_schemas()

    resultados = []

    for numero, ruta in enumerate(rutas, start=1):

        resultado = validar_recurso(
            ruta,
            schema,
        )

        resultados.append(resultado)

        if numero % 100 == 0:
            print(
                f"Procesados: {numero}/{len(rutas)}"
            )

    # Crear directorio de salida
    DIRECTORIO_SALIDA.mkdir(
        parents=True,
        exist_ok=True,
    )

    columnas = [
        "recurso",
        "dataset_eml",
        "titulo",
        "descripcion",
        "palabras_clave",
        "identificador_ceiba",
        "campos_dataverse",
        "estado",
        "error",
    ]

    with ARCHIVO_REPORTE.open(
        "w",
        newline="",
        encoding="utf-8-sig",
    ) as archivo:

        escritor = csv.DictWriter(
            archivo,
            fieldnames=columnas,
        )

        escritor.writeheader()
        escritor.writerows(resultados)

    # Resumen
    conteos = {}

    for resultado in resultados:

        estado = resultado["estado"]

        conteos[estado] = (
            conteos.get(estado, 0) + 1
        )

    print("\nRESULTADOS DE VALIDACIÓN")

    for estado, cantidad in sorted(
        conteos.items()
    ):
        print(f"{estado}: {cantidad}")

    print(
        f"\nReporte generado: {ARCHIVO_REPORTE}"
    )


if __name__ == "__main__":
    ejecutar_validacion()