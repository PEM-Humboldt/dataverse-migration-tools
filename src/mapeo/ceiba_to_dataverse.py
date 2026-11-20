"""
Mapeo de metadatos CEIBA hacia Dataverse.

Entrada:
    Diccionario enriquecido generado por la ingesta CEIBA.

Salida:
    Estructuras de metadatos compatibles con Dataverse.
"""


def mapear_autores(creadores):
    """
    Transforma los creadores EML al formato de autores de Dataverse.
    """

    if isinstance(creadores, dict):
        creadores = [creadores]

    autores = []

    for creador in creadores or []:

        if not isinstance(creador, dict):
            continue

        nombre = creador.get("individualName") or {}

        if not isinstance(nombre, dict):
            nombre = {}

        nombres = nombre.get("givenName") or ""
        apellidos = nombre.get("surName") or ""

        nombres = str(nombres).strip()
        apellidos = str(apellidos).strip()

        if nombres and apellidos:
            nombre_completo = f"{apellidos}, {nombres}"
        else:
            nombre_completo = apellidos or nombres

        organizacion = creador.get("organizationName") or ""
        organizacion = str(organizacion).strip()

        # Si no hay nombre individual, utilizar la organización.
        if not nombre_completo:
            nombre_completo = organizacion

        if not nombre_completo:
            continue

        autor = {
            "authorName": {
                "typeName": "authorName",
                "multiple": False,
                "typeClass": "primitive",
                "value": nombre_completo
            }
        }

        if organizacion:
            autor["authorAffiliation"] = {
                "typeName": "authorAffiliation",
                "multiple": False,
                "typeClass": "primitive",
                "value": organizacion
            }

        autores.append(autor)

    return autores

def mapear_contactos(contactos):
    """
    Transforma los contactos EML al formato de Dataverse.
    """

    if isinstance(contactos, dict):
        contactos = [contactos]

    contactos_dataverse = []

    for contacto in contactos or []:

        if not isinstance(contacto, dict):
            continue

        nombre = contacto.get("individualName") or {}

        if not isinstance(nombre, dict):
            nombre = {}

        nombres = str(nombre.get("givenName") or "").strip()
        apellidos = str(nombre.get("surName") or "").strip()

        if nombres and apellidos:
            nombre_completo = f"{apellidos}, {nombres}"
        else:
            nombre_completo = apellidos or nombres

        organizacion = str(
            contacto.get("organizationName") or ""
        ).strip()

        correo = str(
            contacto.get("electronicMailAddress") or ""
        ).strip()

        if not nombre_completo:
            nombre_completo = organizacion

        if not nombre_completo:
            continue

        contacto_dv = {
            "datasetContactName": {
                "typeName": "datasetContactName",
                "multiple": False,
                "typeClass": "primitive",
                "value": nombre_completo
            }
        }

        if organizacion:
            contacto_dv["datasetContactAffiliation"] = {
                "typeName": "datasetContactAffiliation",
                "multiple": False,
                "typeClass": "primitive",
                "value": organizacion
            }

        if correo:
            contacto_dv["datasetContactEmail"] = {
                "typeName": "datasetContactEmail",
                "multiple": False,
                "typeClass": "primitive",
                "value": correo
            }

        contactos_dataverse.append(contacto_dv)

    return contactos_dataverse

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

def mapear_descripcion(abstract):
    """
    Transforma la descripción EML al campo dsDescription
    de Dataverse.
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
            texto = str(parrafo.get("#text") or "").strip()

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

def mapear_palabras_clave(keyword_sets):
    """
    Transforma las palabras clave EML al formato de Dataverse.

    Conserva cada palabra clave y su vocabulario asociado.
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
                valor = str(palabra.get("#text") or "").strip()
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

def construir_citation(dataset, identificador_ceiba=None):
    """
    Integra los metadatos EML en el bloque citation de Dataverse.

    Recibe:
        dataset: diccionario EML del conjunto de datos.

    Devuelve:
        Diccionario con los campos de citation.
    """

    fields = []

    # Título
    titulo = mapear_titulo(dataset.get("title"))

    if titulo:
        fields.append(titulo)

    # La integración de autores queda pendiente para una etapa posterior.
    # No se ejecuta el mapeo de creator ni associatedParty en este avance.

    # Contactos
    contactos = mapear_contactos(dataset.get("contact", []))

    if contactos:
        fields.append({
            "typeName": "datasetContact",
            "multiple": True,
            "typeClass": "compound",
            "value": contactos
        })

    # Descripción
    descripcion = mapear_descripcion(dataset.get("abstract"))

    if descripcion:
        fields.append({
            "typeName": "dsDescription",
            "multiple": True,
            "typeClass": "compound",
            "value": descripcion
        })

    # Palabras clave
    palabras = mapear_palabras_clave(
        dataset.get("keywordSet", [])
    )

    if palabras:
        fields.append({
            "typeName": "keyword",
            "multiple": True,
            "typeClass": "compound",
            "value": palabras
        })

    # Identificador original de CEIBA
    identificadores = mapear_identificador_ceiba(
        identificador_ceiba
    )

    if identificadores:
        fields.append({
            "typeName": "otherId",
            "multiple": True,
            "typeClass": "compound",
            "value": identificadores
        })

    return {
        "citation": {
            "fields": fields
        }
    }

def mapear_identificador_ceiba(identificador):
    """
    Transforma el identificador original de CEIBA
    al campo otherId de Dataverse.
    """

    if not identificador:
        return []

    identificador = str(identificador).strip()

    if identificador.upper() in {"NA", "N/A", "NO APLICA"}:
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

    

# ------------------------------------------------------------
# Avance de mapeos directos (sin extracción de autores)
# ------------------------------------------------------------

import re


def normalizar_texto(valor):
    """Limpia espacios y saltos de línea sin alterar el contenido del texto."""
    if isinstance(valor, dict):
        valor = valor.get("#text", "")
    if not isinstance(valor, str):
        return ""
    return re.sub(r"\s+", " ", valor).strip()


def campo_simple(nombre, valor):
    """Genera un campo primitivo de Dataverse cuando existe un valor válido."""
    texto = normalizar_texto(valor)
    if not texto or texto.upper() in {"N/A", "NA", "NO APLICA"}:
        return None
    return {"typeName": nombre, "multiple": False,
            "typeClass": "primitive", "value": texto}


def valores_texto(valor):
    """Convierte un valor EML simple o repetido en una lista de textos."""
    elementos = valor if isinstance(valor, list) else [valor]
    resultado = []
    for elemento in elementos:
        texto = normalizar_texto(elemento)
        if texto and texto.upper() not in {"N/A", "NA", "NO APLICA"}:
            resultado.append(texto)
    return resultado


def mapear_idioma(dataset):
    """Mapea dataset/language a language (campo repetible de citation)."""
    idiomas = valores_texto(dataset.get("language"))
    # Evito duplicados conservando el orden de aparición.
    idiomas = list(dict.fromkeys(idiomas))
    if not idiomas:
        return None
    return {"typeName": "language", "multiple": True,
            "typeClass": "controlledVocabulary", "value": idiomas}


def mapear_subtitulo(dataset):
    """Mapea dataset/alternateIdentifier solo si NO es un identificador.

    No se implementa aquí: el nombre de la fuente no garantiza que sea
    un subtítulo. Se mantiene esta función explícita para evitar un
    mapeo incorrecto por similitud de nombres.
    """
    return None


def mapear_distribucion_temporal(dataset):
    """Extrae fechas EML candidatas; no genera campos Dataverse todavía.

    Las fechas EML pueden estar expresadas como rangos o fechas únicas.
    Requieren una revisión específica antes de mapearlas.
    """
    cobertura = dataset.get("coverage")
    if not isinstance(cobertura, dict):
        return []
    temporal = cobertura.get("temporalCoverage")
    return temporal if isinstance(temporal, list) else ([temporal] if temporal else [])


def construir_citation_basico(dataset, identificador_ceiba=None):
    """Construye citation con los campos directos revisados en este avance.

    Este constructor evita incluir autores y contactos, porque su
    correspondencia con personas/roles se evaluará posteriormente.
    Las palabras clave y la descripción conservan las funciones existentes.
    """
    if not isinstance(dataset, dict):
        raise TypeError("dataset debe ser un diccionario")

    campos = []
    titulo = mapear_titulo(dataset.get("title"))
    if titulo:
        campos.append(titulo)

    descripcion = mapear_descripcion(dataset.get("abstract"))
    if descripcion:
        campos.append({"typeName": "dsDescription", "multiple": True,
                       "typeClass": "compound", "value": descripcion})

    palabras = mapear_palabras_clave(dataset.get("keywordSet"))
    if palabras:
        campos.append({"typeName": "keyword", "multiple": True,
                       "typeClass": "compound", "value": palabras})

    identificadores = mapear_identificador_ceiba(identificador_ceiba)
    if identificadores:
        campos.append({"typeName": "otherId", "multiple": True,
                       "typeClass": "compound", "value": identificadores})

    # language se mantiene fuera de la salida hasta contrastar los
    # valores EML reales con el vocabulario de la instalación Dataverse.
    return {"citation": {"fields": campos}}

def extraer_dataset(datos):
    """
    Identifica y extrae el elemento dataset del JSON intermedio de CEIBA.

    Los archivos generados durante la ingesta conservan la estructura
    original del EML, incluyendo el namespace de su versión.

    Esta función permite identificar dataset en archivos EML 2.1.1,
    EML 2.2.0 y otras versiones que mantengan la misma estructura.
    """

    if not isinstance(datos, dict):
        raise ValueError("El recurso debe ser un objeto JSON")

    # Primero reviso las estructuras que no tienen namespace.
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

    # Identifico el elemento EML cuando conserva el namespace.
    # Esto ocurre en los JSON generados durante la ingesta CEIBA.
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

    # Si no encuentro dataset, informo el problema para su revisión.
    raise ValueError(
        "No se encontró dataset en la estructura del JSON intermedio"
    )

