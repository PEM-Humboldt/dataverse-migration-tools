"""
Mapeo intermedio de metadatos CEIBA hacia Dataverse.

Este módulo transforma los metadatos EML extraídos durante
la ingesta de CEIBA en un diccionario intermedio.

La estructura generada está diseñada para ser procesada
posteriormente por unflatten_dataset() de LIB-1051.

Incluye:
- Extracción del dataset EML.
- Título.
- Descripción.
- Palabras clave.
- Identificador CEIBA.

No incorpora autores ni contactos.
"""

import re


# ============================================================
# 1. FUNCIONES AUXILIARES
# ============================================================

def normalizar_texto(valor):
    """
    Limpia espacios y saltos de línea sin alterar
    el contenido del texto.
    """

    if isinstance(valor, dict):
        valor = valor.get("#text", "")

    if not isinstance(valor, str):
        return ""

    return re.sub(r"\s+", " ", valor).strip()


def extraer_valor(campo):
    """
    Obtiene el valor de un campo Dataverse
    previamente construido.
    """

    if not isinstance(campo, dict):
        return None

    return campo.get("value")


def convertir_compuesto(elementos):
    """
    Convierte campos compuestos de Dataverse
    a una lista de diccionarios simples.
    """

    resultado = []

    for elemento in elementos or []:

        if not isinstance(elemento, dict):
            continue

        compuesto = {}

        for nombre, campo in elemento.items():

            valor = extraer_valor(campo)

            if valor is not None and valor != "":
                compuesto[nombre] = valor

        if compuesto:
            resultado.append(compuesto)

    return resultado


# ============================================================
# 2. EXTRACCIÓN DEL DATASET EML
# ============================================================

def extraer_dataset(datos):
    """
    Identifica y extrae el elemento dataset del JSON
    intermedio de CEIBA.

    Reconoce estructuras EML con y sin namespace.
    """

    if not isinstance(datos, dict):
        raise ValueError(
            "El recurso debe ser un objeto JSON"
        )

    candidatos = [
        datos,
        datos.get("eml"),
        datos.get("resource"),
        datos.get("metadata"),
        datos.get("eml_data")
    ]

    for candidato in candidatos:

        if isinstance(candidato, dict):

            dataset = candidato.get("dataset")

            if isinstance(dataset, dict):
                return dataset

    for clave, contenido in datos.items():

        if not isinstance(clave, str):
            continue

        if not isinstance(contenido, dict):
            continue

        if (
            clave.startswith("{")
            and clave.endswith("}eml")
        ):

            dataset = contenido.get("dataset")

            if isinstance(dataset, dict):
                return dataset

    raise ValueError(
        "No se encontró dataset en la estructura del JSON intermedio"
    )


# ============================================================
# 3. MAPEO DEL TÍTULO
# ============================================================

def mapear_titulo(titulo):
    """
    Transforma el título EML al campo title de Dataverse.
    """

    if isinstance(titulo, dict):
        valor = titulo.get("#text") or ""

    elif isinstance(titulo, str):
        valor = titulo

    else:
        valor = ""

    valor = normalizar_texto(valor)

    if not valor:
        return None

    return {
        "typeName": "title",
        "multiple": False,
        "typeClass": "primitive",
        "value": valor
    }


# ============================================================
# 4. MAPEO DE LA DESCRIPCIÓN
# ============================================================

def mapear_descripcion(abstract):
    """
    Transforma la descripción EML al campo
    dsDescription de Dataverse.
    """

    if not abstract:
        return []

    if isinstance(abstract, dict):
        parrafos = abstract.get("para", [])
    else:
        parrafos = abstract

    if not isinstance(parrafos, list):
        parrafos = [parrafos]

    textos = []

    for parrafo in parrafos:

        if isinstance(parrafo, str):
            texto = parrafo.strip()

        elif isinstance(parrafo, dict):
            texto = str(
                parrafo.get("#text") or ""
            ).strip()

        else:
            continue

        if texto:
            textos.append(texto)

    if not textos:
        return []

    descripcion = "\n\n".join(textos)

    return [
        {
            "dsDescriptionValue": {
                "typeName": "dsDescriptionValue",
                "multiple": False,
                "typeClass": "primitive",
                "value": descripcion
            }
        }
    ]


# ============================================================
# 5. MAPEO DE PALABRAS CLAVE
# ============================================================

def mapear_palabras_clave(keyword_sets):
    """
    Transforma las palabras clave EML al formato
    de Dataverse.

    Conserva cada palabra clave y su vocabulario.
    """

    if isinstance(keyword_sets, dict):
        keyword_sets = [keyword_sets]

    palabras_dataverse = []

    for grupo in keyword_sets or []:

        if not isinstance(grupo, dict):
            continue

        tesauro = str(
            grupo.get("keywordThesaurus") or ""
        ).strip()

        palabras = grupo.get("keyword", [])

        if not isinstance(palabras, list):
            palabras = [palabras]

        for palabra in palabras:

            if isinstance(palabra, dict):
                valor = str(
                    palabra.get("#text") or ""
                ).strip()

            elif isinstance(palabra, str):
                valor = palabra.strip()

            else:
                continue

            if not valor:
                continue

            palabra_dv = {
                "keywordValue": {
                    "typeName": "keywordValue",
                    "multiple": False,
                    "typeClass": "primitive",
                    "value": valor
                }
            }

            if tesauro and tesauro.upper() not in {
                "N/A", "NA", "NO APLICA"
            }:

                palabra_dv["keywordVocabulary"] = {
                    "typeName": "keywordVocabulary",
                    "multiple": False,
                    "typeClass": "primitive",
                    "value": tesauro
                }

            palabras_dataverse.append(palabra_dv)

    return palabras_dataverse


# ============================================================
# 6. MAPEO DEL IDENTIFICADOR CEIBA
# ============================================================

def mapear_identificador_ceiba(identificador):
    """
    Transforma el identificador original de CEIBA
    al campo otherId de Dataverse.
    """

    if not identificador:
        return []

    identificador = str(identificador).strip()

    if identificador.upper() in {
        "NA", "N/A", "NO APLICA"
    }:
        return []

    return [
        {
            "otherIdAgency": {
                "typeName": "otherIdAgency",
                "multiple": False,
                "typeClass": "primitive",
                "value": "CEIBA"
            },
            "otherIdValue": {
                "typeName": "otherIdValue",
                "multiple": False,
                "typeClass": "primitive",
                "value": identificador
            }
        }
    ]


# ============================================================
# 7. CONSTRUCCIÓN DEL BLOQUE CITATION INTERMEDIO
# ============================================================

def construir_citation_intermedio(
    dataset,
    identificador_ceiba=None
):
    """
    Construye el bloque citation en formato intermedio.

    El resultado puede ser procesado posteriormente
    por unflatten_dataset() de LIB-1051.

    No incorpora autores ni contactos.
    """

    if not isinstance(dataset, dict):
        raise TypeError(
            "dataset debe ser un diccionario"
        )

    citation = {}

    # --------------------------------------------------------
    # Título
    # --------------------------------------------------------

    titulo = mapear_titulo(
        dataset.get("title")
    )

    valor_titulo = extraer_valor(titulo)

    if valor_titulo:
        citation["title"] = valor_titulo

    # --------------------------------------------------------
    # Descripción
    # --------------------------------------------------------

    descripcion = mapear_descripcion(
        dataset.get("abstract")
    )

    descripcion_intermedia = convertir_compuesto(
        descripcion
    )

    if descripcion_intermedia:
        citation["dsDescription"] = (
            descripcion_intermedia
        )

    # --------------------------------------------------------
    # Palabras clave
    # --------------------------------------------------------

    palabras = mapear_palabras_clave(
        dataset.get("keywordSet")
    )

    palabras_intermedias = convertir_compuesto(
        palabras
    )

    if palabras_intermedias:
        citation["keyword"] = (
            palabras_intermedias
        )

    # --------------------------------------------------------
    # Identificador CEIBA
    # --------------------------------------------------------

    identificadores = mapear_identificador_ceiba(
        identificador_ceiba
    )

    identificadores_intermedios = convertir_compuesto(
        identificadores
    )

    if identificadores_intermedios:
        citation["otherId"] = (
            identificadores_intermedios
        )

    # --------------------------------------------------------
    # Resultado
    # --------------------------------------------------------

    if not citation:
        return {}

    return {
        "citation": citation
    }