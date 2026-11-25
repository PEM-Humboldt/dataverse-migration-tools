from datetime import date
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

import csv
import re
from functools import lru_cache
from pathlib import Path
import unicodedata


@lru_cache(maxsize=1)
def cargar_vocabulario_idiomas():
    """
    Obtiene equivalencias ISO 639-2 -> valor Dataverse
    desde metadata_dataverse/citation.tsv.
    """
    ruta_tsv = (
        Path(__file__).resolve().parents[2]
        / "metadata_dataverse"
        / "citation.tsv"
    )

    equivalencias = {}

    with ruta_tsv.open(
        encoding="utf-8-sig",
        newline=""
    ) as archivo:
        lector = csv.reader(archivo, delimiter="\t")
        encabezados = None
        leyendo_vocabulario = False

        for fila in lector:
            if not fila:
                continue

            primera = fila[0].strip()

            if primera == "#controlledVocabulary":
                encabezados = [valor.strip() for valor in fila]
                leyendo_vocabulario = True
                continue

            if primera.startswith("#"):
                leyendo_vocabulario = False
                continue

            if not leyendo_vocabulario or not encabezados:
                continue

            registro = dict(zip(encabezados, fila))

            if registro.get("DatasetField", "").strip() != "language":
                continue

            codigo = registro.get("identifier", "").strip().lower()
            valor = registro.get("Value", "").strip()

            if codigo and valor:
                equivalencias[codigo] = valor

    return equivalencias


def mapear_idioma(valor):
    """
    Transforma el código ISO del EML al vocabulario Dataverse.
    """
    codigo = normalizar_texto(valor)

    if not codigo:
        return None

    equivalencias = cargar_vocabulario_idiomas()

    return equivalencias.get(codigo.lower())


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
def separar_tesauro_uri(keyword_thesaurus):
    """
    Separa el nombre del tesauro y su URI cuando
    ambos están documentados en keywordThesaurus.

    No asigna vocabularios a palabras clave.
    """

    texto = normalizar_texto(keyword_thesaurus)

    if not texto or texto.upper() in {
        "N/A", "NA", "NO APLICA"
    }:
        return "", ""

    coincidencia = re.search(
        r"https?://[^\s]+",
        texto
    )

    if not coincidencia:
        return texto, ""

    uri = coincidencia.group(0).rstrip(".,;")

    nombre = normalizar_texto(
        texto[:coincidencia.start()].rstrip(" :")
    )

    return nombre, uri

def es_palabra_clave_gbif(termino, tesauro):
    """
    Identifica términos reconocidos de los vocabularios
    GBIF de tipo y subtipo de conjunto de datos.

    No modifica keywordValue ni completa coreType/subtype.
    """

    termino_normalizado = normalizar_texto(termino).lower()
    tesauro_normalizado = normalizar_texto(tesauro).lower()

    tipos_gbif = {
        "occurrence",
        "checklist",
        "samplingevent",
        "metadata",
        "other"
    }

    subtipos_gbif = {
        "specimen",
        "observation",
        "inventoryregional",
        "inventorythematic",
        "derivedfromoccurrence",
        "taxonomicauthority",
        "nomenclatorauthority"
    }

    if tesauro_normalizado == "gbif dataset type vocabulary":
        return termino_normalizado in tipos_gbif

    if tesauro_normalizado == "gbif dataset subtype vocabulary":
        return termino_normalizado in subtipos_gbif

    return False

def normalizar_identificador_palabra(valor):
    """
    Normaliza una palabra clave exclusivamente para
    identificar duplicados.

    Ignora mayúsculas, tildes y puntuación.
    No modifica el valor original publicado.
    """

    texto = normalizar_texto(valor).lower()

    texto = unicodedata.normalize("NFKD", texto)

    texto = "".join(
        caracter
        for caracter in texto
        if not unicodedata.combining(caracter)
    )

    texto = "".join(
        caracter if caracter.isalnum() or caracter.isspace()
        else " "
        for caracter in texto
    )

    return " ".join(texto.split())


def mapear_palabras_clave(keyword_sets):
    """
    Transforma las palabras clave EML al formato
    intermedio de Dataverse.

    Conserva los valores originales y los vocabularios
    reales, evitando duplicados equivalentes.
    """

    if isinstance(keyword_sets, dict):
        keyword_sets = [keyword_sets]

    palabras_dataverse = []
    identificadores = set()

    for grupo in keyword_sets or []:

        if not isinstance(grupo, dict):
            continue

        tesauro, tesauro_uri = separar_tesauro_uri(
            grupo.get("keywordThesaurus")
        )

        palabras = grupo.get("keyword", [])

        if not isinstance(palabras, list):
            palabras = [palabras]

        for palabra in palabras:

            valor = normalizar_texto(palabra)

            if not valor:
                continue

            terminos = re.split(r"[,;]", valor)

            for termino in terminos:

                termino = normalizar_texto(termino)

                if not termino:
                    continue

                identificador = normalizar_identificador_palabra(
                    termino
                )

                if not identificador:
                    continue

                # Determinar si el vocabulario corresponde
                # realmente a la palabra clave.
                es_tesauro_gbif = tesauro.lower() in {
                    "gbif dataset type vocabulary",
                    "gbif dataset subtype vocabulary",
                }

                asignar_tesauro = bool(tesauro)

                if es_tesauro_gbif:
                    asignar_tesauro = es_palabra_clave_gbif(
                        termino,
                        tesauro,
                    )

                vocabulario = tesauro if asignar_tesauro else ""

                # La comparación utiliza únicamente
                # vocabularios efectivamente asignados.
                clave = (
                    identificador,
                    vocabulario.lower(),
                )

                if clave in identificadores:
                    continue

                clave_sin_tesauro = (
                    identificador,
                    "",
                )

                if vocabulario:

                    # Priorizar la aparición con vocabulario.
                    if clave_sin_tesauro in identificadores:

                        palabras_dataverse = [
                            elemento
                            for elemento in palabras_dataverse
                            if not (
                                normalizar_identificador_palabra(
                                    elemento["keywordValue"]["value"]
                                ) == identificador
                                and "keywordVocabulary" not in elemento
                            )
                        ]

                        identificadores.discard(
                            clave_sin_tesauro
                        )

                else:

                    # No duplicar una palabra libre cuando
                    # ya existe con un vocabulario real.
                    existe_con_tesauro = any(
                        clave_existente[0] == identificador
                        and clave_existente[1]
                        for clave_existente in identificadores
                    )

                    if existe_con_tesauro:
                        continue

                palabra_dv = {
                    "keywordValue": {
                        "typeName": "keywordValue",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": termino,
                    }
                }

                if vocabulario:
                    palabra_dv["keywordVocabulary"] = {
                        "typeName": "keywordVocabulary",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": vocabulario,
                    }

                if vocabulario and tesauro_uri:
                    palabra_dv["keywordVocabularyURI"] = {
                        "typeName": "keywordVocabularyURI",
                        "multiple": False,
                        "typeClass": "primitive",
                        "value": tesauro_uri,
                    }

                palabras_dataverse.append(palabra_dv)
                identificadores.add(clave)

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

    if not identificador:
        return []

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
                "value": "IPT Ceiba (I2D)"
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


def mapear_fecha_publicacion(valor):
    """
    Valida dataset/pubDate para distributionDate.

    Acepta únicamente fechas completas YYYY-MM-DD.
    No completa fechas parciales ni reemplaza fechas históricas.
    """
    import re

    fecha = normalizar_texto(valor)

    if not fecha:
        return None

    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fecha):
        return None

    try:
        date.fromisoformat(fecha)
    except ValueError:
        return None

    return fecha


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
    # Título alternativo (EML 2.2.0)
    # --------------------------------------------------------

    nombre_corto = normalizar_texto(
        dataset.get("shortName")
    )

    if nombre_corto:
        citation["alternativeTitle"] = [nombre_corto]

    # --------------------------------------------------------
    # Área temática (valor institucional constante)
    # --------------------------------------------------------

    citation["subject"] = [
        "Earth and Environmental Sciences"
    ]

    # --------------------------------------------------------
    # Idioma (ISO 639-2 -> vocabulario Dataverse)
    # --------------------------------------------------------

    idioma = mapear_idioma(dataset.get("language"))

    if idioma:
        citation["language"] = [idioma]

    # --------------------------------------------------------
    # Fecha histórica de distribución (CEIBA pubDate)
    # --------------------------------------------------------

    fecha_distribucion = mapear_fecha_publicacion(
        dataset.get("pubDate")
    )

    if fecha_distribucion:
        citation["distributionDate"] = fecha_distribucion

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
    # Información adicional (notesText)
    # --------------------------------------------------------

    additional_info = dataset.get("additionalInfo")

    if isinstance(additional_info, dict):
        parrafos = additional_info.get("para")
    else:
        parrafos = None

    if parrafos is not None:
        if not isinstance(parrafos, list):
            parrafos = [parrafos]

        textos = []

        for parrafo in parrafos:
            texto = normalizar_texto(parrafo)

            if texto:
                textos.append(texto)

        if textos:
            citation["notesText"] = "\n".join(textos)

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