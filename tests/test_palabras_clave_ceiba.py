from src.mapeo.ceiba_mapping import mapear_palabras_clave


def extraer_resultados(datos):
    """
    Convierte la salida del mapeador en una estructura
    sencilla para facilitar las pruebas.
    """
    resultado = mapear_palabras_clave(datos)

    return [
        {
            "valor": elemento["keywordValue"]["value"],
            "vocabulario": elemento.get(
                "keywordVocabulary", {}
            ).get("value"),
            "uri": elemento.get(
                "keywordVocabularyURI", {}
            ).get("value"),
        }
        for elemento in resultado
    ]


def test_palabras_clave_gbif():
    datos = [
        {
            "keywordThesaurus": (
                "GBIF Dataset Type Vocabulary: "
                "http://rs.gbif.org/vocabulary/gbif/dataset_type.xml"
            ),
            "keyword": [
                "Occurrence",
                "Antioquia",
                "aves",
            ],
        }
    ]

    resultado = extraer_resultados(datos)

    assert len(resultado) == 3

    assert resultado[0] == {
        "valor": "Occurrence",
        "vocabulario": "GBIF Dataset Type Vocabulary",
        "uri": (
            "http://rs.gbif.org/vocabulary/gbif/dataset_type.xml"
        ),
    }

    assert resultado[1] == {
        "valor": "Antioquia",
        "vocabulario": None,
        "uri": None,
    }

    assert resultado[2] == {
        "valor": "aves",
        "vocabulario": None,
        "uri": None,
    }


def test_separacion_de_palabras_clave():
    datos = [
        {
            "keywordThesaurus": "n/a",
            "keyword": [
                "Biodiversidad; Flora, Fauna"
            ],
        }
    ]

    resultado = extraer_resultados(datos)

    assert [
        elemento["valor"] for elemento in resultado
    ] == [
        "Biodiversidad",
        "Flora",
        "Fauna",
    ]


def test_duplicados_mayusculas_tildes():
    datos = [
        {
            "keywordThesaurus": "n/a",
            "keyword": [
                "Antioquia",
                "ANTIOQUIA",
                "aves",
                "Áves",
            ],
        }
    ]

    resultado = extraer_resultados(datos)

    assert [
        elemento["valor"] for elemento in resultado
    ] == [
        "Antioquia",
        "aves",
    ]


def test_conservar_tesauros_diferentes():
    datos = [
        {
            "keywordThesaurus": "Tesauro A",
            "keyword": ["Biodiversidad"],
        },
        {
            "keywordThesaurus": "Tesauro B",
            "keyword": ["Biodiversidad"],
        },
        {
            "keywordThesaurus": "n/a",
            "keyword": ["BIODIVERSIDAD"],
        },
    ]

    resultado = extraer_resultados(datos)

    assert len(resultado) == 2

    assert [
        elemento["vocabulario"] for elemento in resultado
    ] == [
        "Tesauro A",
        "Tesauro B",
    ]


def test_priorizar_palabra_con_tesauro():
    datos = [
        {
            "keywordThesaurus": "n/a",
            "keyword": ["Áves", "Fauna"],
        },
        {
            "keywordThesaurus": "Tesauro de biodiversidad",
            "keyword": ["aves"],
        },
    ]

    resultado = extraer_resultados(datos)

    assert resultado == [
        {
            "valor": "Fauna",
            "vocabulario": None,
            "uri": None,
        },
        {
            "valor": "aves",
            "vocabulario": "Tesauro de biodiversidad",
            "uri": None,
        },
    ]


def test_palabras_clave_vacias():
    datos = [
        {
            "keywordThesaurus": "n/a",
            "keyword": ["", " ", None],
        }
    ]

    resultado = extraer_resultados(datos)

    assert resultado == []


def test_integracion_palabras_clave_dataverse():
    """
    Verifica que las palabras clave y sus vocabularios
    se conserven después de reconstruir el bloque
    citation en el formato final de Dataverse.
    """
    from src.mapeo.ceiba_mapping import (
        construir_citation_intermedio,
    )
    from src.mapeo.reconstruct_mapping import (
        load_dv_schemas,
        unflatten_dataset,
    )

    dataset = {
        "keywordSet": [
            {
                "keywordThesaurus": (
                    "GBIF Dataset Type Vocabulary: "
                    "http://rs.gbif.org/vocabulary/gbif/dataset_type.xml"
                ),
                "keyword": [
                    "Checklist",
                    "IVI",
                    "Coberturas vegetales",
                ],
            },
            {
                "keywordThesaurus": (
                    "GBIF Dataset Subtype Vocabulary: "
                    "http://rs.gbif.org/vocabulary/gbif/dataset_subtype.xml"
                ),
                "keyword": [
                    "Inventoryregional",
                    "páramo",
                    "páramo Guerrero",
                ],
            },
        ]
    }

    intermedio = construir_citation_intermedio(dataset)

    schema = load_dv_schemas()

    resultado = unflatten_dataset(
        intermedio,
        schema,
    )

    campos = resultado["citation"]["fields"]

    campo_keyword = next(
        campo
        for campo in campos
        if campo["typeName"] == "keyword"
    )

    palabras = campo_keyword["value"]

    assert len(palabras) == 6

    valores = [
        palabra["keywordValue"]["value"]
        for palabra in palabras
    ]

    assert valores == [
        "Checklist",
        "IVI",
        "Coberturas vegetales",
        "Inventoryregional",
        "páramo",
        "páramo Guerrero",
    ]

    checklist = palabras[0]

    assert (
        checklist["keywordVocabulary"]["value"]
        == "GBIF Dataset Type Vocabulary"
    )

    assert (
        checklist["keywordVocabularyURI"]["value"]
        == "http://rs.gbif.org/vocabulary/gbif/dataset_type.xml"
    )

    inventoryregional = palabras[3]

    assert (
        inventoryregional["keywordVocabulary"]["value"]
        == "GBIF Dataset Subtype Vocabulary"
    )

    assert (
        inventoryregional["keywordVocabularyURI"]["value"]
        == "http://rs.gbif.org/vocabulary/gbif/dataset_subtype.xml"
    )

    for indice in [1, 2, 4, 5]:
        assert "keywordVocabulary" not in palabras[indice]
        assert "keywordVocabularyURI" not in palabras[indice]
