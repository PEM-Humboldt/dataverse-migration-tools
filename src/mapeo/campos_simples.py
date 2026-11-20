"""Funciones auxiliares para campos de texto del mapeo CEIBA a Dataverse.

Este módulo trabaja con valores ya extraídos del EML o del JSON intermedio.
No consulta el crosswalk ni modifica los archivos de origen.
La integración de autores y contactos se desarrollará por separado.
"""

import re
from typing import Any


VALORES_SIN_DATO = {"", "N/A", "NA", "NO APLICA"}


def extraer_texto(valor: Any) -> str:
    """Obtengo texto limpio desde un valor simple o una estructura EML.

    - Texto: normalizo espacios, tabulaciones y saltos de línea.
    - Diccionario con '#text': utilizo ese contenido.
    - Lista: uno los textos disponibles con un espacio.
    - Otros valores: no supongo su significado y devuelvo texto vacío.
    """
    if isinstance(valor, str):
        texto = re.sub(r"\s+", " ", valor).strip()
        return "" if texto.upper() in VALORES_SIN_DATO else texto

    if isinstance(valor, dict):
        return extraer_texto(valor.get("#text"))

    if isinstance(valor, list):
        partes = [extraer_texto(elemento) for elemento in valor]
        return " ".join(parte for parte in partes if parte)

    return ""


def mapear_campos_texto(datos: dict, correspondencias: dict[str, str]) -> list[dict]:
    """Construyo campos primitivos de Dataverse a partir de claves directas.

    `correspondencias` relaciona la clave de entrada con el nombre de salida.
    Solo incluyo valores que tengan contenido. No aplico vocabularios
    controlados ni transformaciones que deban validarse en el crosswalk.

    Ejemplo:
        mapear_campos_texto({"title": " Bosques  andinos "},
                            {"title": "title"})
    """
    if not isinstance(datos, dict):
        raise TypeError("datos debe ser un diccionario")
    if not isinstance(correspondencias, dict):
        raise TypeError("correspondencias debe ser un diccionario")

    campos = []
    for clave_origen, nombre_destino in correspondencias.items():
        if not isinstance(nombre_destino, str) or not nombre_destino.strip():
            raise ValueError("Cada campo de destino debe tener un nombre válido")
        texto = extraer_texto(datos.get(clave_origen))
        if texto:
            campos.append({
                "typeName": nombre_destino,
                "multiple": False,
                "typeClass": "primitive",
                "value": texto,
            })
    return campos
