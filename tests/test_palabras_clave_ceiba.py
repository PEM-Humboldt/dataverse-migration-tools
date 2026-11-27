"""Pruebas sintéticas de las palabras clave y los tesauros de CEIBA."""

import pytest


GBIF_TYPE = "GBIF Dataset Type Vocabulary"
GBIF_SUBTYPE = "GBIF Dataset Subtype Vocabulary"
GBIF_TYPE_URI = "http://rs.gbif.org/vocabulary/gbif/dataset_type.xml"
GBIF_TYPE_2015_URI = "http://rs.gbif.org/vocabulary/gbif/dataset_type_2015-07-10.xml"
GBIF_SUBTYPE_URI = "http://rs.gbif.org/vocabulary/gbif/dataset_subtype.xml"
THESAURUS_URI = "https://example.test/tesauro"


def keyword_set(words, thesaurus=None):
    return {"keyword": words, "keywordThesaurus": thesaurus}


def test_gbif_type_keeps_recognized_and_free_keywords(mapeo_ceiba):
    dataset = {"keywordSet": [
        keyword_set(["Occurrence", "aves", "sitio de prueba"], f"{GBIF_TYPE}: {GBIF_TYPE_URI}"),
    ]}

    result = mapeo_ceiba.map_keywords(dataset)

    assert sorted(result, key=lambda entry: entry["keywordValue"]) == [
        {
            "keywordValue": "Occurrence",
            "keywordVocabulary": GBIF_TYPE,
            "keywordVocabularyURI": GBIF_TYPE_URI,
        },
        {"keywordValue": "aves"},
        {"keywordValue": "sitio de prueba"},
    ]


@pytest.mark.parametrize(
    ("words", "expected"),
    [
        pytest.param("Árboles, Aves", ["Árboles", "Aves"], id="comma"),
        pytest.param("Árboles; Aves", ["Árboles", "Aves"], id="semicolon"),
        pytest.param("Biodiversidad; Flora, Fauna", ["Biodiversidad", "Flora", "Fauna"], id="mixed"),
    ],
)
def test_splits_keywords_and_preserves_spelling(mapeo_ceiba, words, expected):
    dataset = {"keywordSet": keyword_set([words], "n/a")}

    result = mapeo_ceiba.map_keywords(dataset)

    assert sorted(entry["keywordValue"] for entry in result) == sorted(expected)


@pytest.mark.parametrize(
    ("first", "duplicate"),
    [
        pytest.param("Aves", "Aves", id="exact"),
        pytest.param("Aves", "AVES", id="case"),
        pytest.param("Árboles", "Arboles", id="accented-first"),
        pytest.param("Arboles", "Árboles", id="unaccented-first"),
    ],
)
def test_deduplicates_free_keywords_and_keeps_first_spelling(mapeo_ceiba, first, duplicate):
    dataset = {"keywordSet": [keyword_set([first, duplicate]), keyword_set(duplicate)]}

    assert mapeo_ceiba.map_keywords(dataset) == [{"keywordValue": first}]


def test_deduplicates_across_different_thesauri(mapeo_ceiba):
    first_uri = f"{THESAURUS_URI}/a"
    second_uri = f"{THESAURUS_URI}/b"
    dataset = {"keywordSet": [
        keyword_set("Biodiversidad", f"Tesauro A: {first_uri}"),
        keyword_set("Biodiversidad", f"Tesauro B: {second_uri}"),
        keyword_set("BIODIVERSIDAD", "n/a"),
    ]}

    [result] = mapeo_ceiba.map_keywords(dataset)

    assert result["keywordValue"] == "Biodiversidad"
    # Ambos tesauros son admisibles. El nombre y la URI deben corresponder al mismo.
    assert (result["keywordVocabulary"], result["keywordVocabularyURI"]) in {
        ("Tesauro A", first_uri),
        ("Tesauro B", second_uri),
    }


@pytest.mark.parametrize(
    "controlled_first",
    [pytest.param(False, id="free-first"), pytest.param(True, id="controlled-first")],
)
def test_prefers_vocabulary_in_either_order(mapeo_ceiba, controlled_first):
    free = keyword_set(["Áves", "Fauna"], "n/a")
    controlled = keyword_set("aves", f"Tesauro de biodiversidad: {THESAURUS_URI}")
    groups = [controlled, free] if controlled_first else [free, controlled]

    result = mapeo_ceiba.map_keywords({"keywordSet": groups})

    assert sorted(result, key=lambda entry: entry["keywordValue"]) == [
        {"keywordValue": "Fauna"},
        {
            "keywordValue": "aves",
            "keywordVocabulary": "Tesauro de biodiversidad",
            "keywordVocabularyURI": THESAURUS_URI,
        },
    ]


@pytest.mark.parametrize(
    "dataset",
    [
        pytest.param({}, id="missing-keyword-set"),
        pytest.param({"keywordSet": {"keywordThesaurus": "n/a"}}, id="missing-keyword"),
        pytest.param({"keywordSet": keyword_set(["", " ", None, " , ; "], "n/a")}, id="blank-keywords"),
    ],
)
def test_ignores_empty_keywords(mapeo_ceiba, dataset):
    assert mapeo_ceiba.map_keywords(dataset) == []


@pytest.mark.usefixtures("reconstruir_dataverse")
def test_reconstructs_keywords_in_dataverse(mapeo_ceiba, record_ceiba):
    """Verifica las palabras y sus vocabularios en el registro JSON de Dataverse."""
    from src.mapeo.geonetwork.dataverse_payload import version_record

    record = record_ceiba({"keywordSet": [
        keyword_set(["Checklist", "Bosque ficticio", "Fauna"], f"{GBIF_TYPE}: {GBIF_TYPE_URI}"),
        keyword_set(
            ["Inventoryregional", "páramo", "zona de prueba"],
            f"{GBIF_SUBTYPE}: {GBIF_SUBTYPE_URI}",
        ),
    ]})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    schema = {
        "title": {"multiple": False, "typeClass": "primitive"},
        "subject": {"multiple": True, "typeClass": "controlledVocabulary"},
        "keyword": {
            "multiple": True,
            "typeClass": "compound",
            "subfields": {
                name: {"multiple": False}
                for name in ("keywordValue", "keywordVocabulary", "keywordVocabularyURI", "keywordTermURI")
            },
        },
    }

    payload = version_record({"citation": citation}, {}, schema, record, record["inventory"])

    fields = payload["datasetVersion"]["metadataBlocks"]["citation"]["fields"]
    keyword_field = next(field for field in fields if field["typeName"] == "keyword")
    assert keyword_field["typeClass"] == "compound"
    assert keyword_field["multiple"] is True
    assert len(keyword_field["value"]) == 6
    values = {}
    for entry in keyword_field["value"]:
        for name, child in entry.items():
            assert child["typeName"] == name
            assert child["typeClass"] == "primitive"
            assert child["multiple"] is False
        values[entry["keywordValue"]["value"]] = {
            name: child["value"] for name, child in entry.items() if name != "keywordValue"
        }
    assert values == {
        "Checklist": {"keywordVocabulary": GBIF_TYPE, "keywordVocabularyURI": GBIF_TYPE_URI},
        "Bosque ficticio": {},
        "Fauna": {},
        "Inventoryregional": {"keywordVocabulary": GBIF_SUBTYPE, "keywordVocabularyURI": GBIF_SUBTYPE_URI},
        "páramo": {},
        "zona de prueba": {},
    }


@pytest.mark.parametrize(
    "uri",
    [pytest.param(None, id="without-uri"), pytest.param(THESAURUS_URI, id="with-uri")],
)
def test_maps_named_thesaurus_with_optional_uri(mapeo_ceiba, uri):
    name = "Tesauro de fauna"
    label = f"{name}: {uri}" if uri else name
    dataset = {"keywordSet": keyword_set({"#text": "Mamíferos"}, label)}
    expected = {"keywordValue": "Mamíferos", "keywordVocabulary": name}
    if uri:
        expected["keywordVocabularyURI"] = uri

    assert mapeo_ceiba.map_keywords(dataset) == [expected]


@pytest.mark.parametrize("filler", ["N/A", "'n/a'", "NA", "No aplica", "Otro", ""])
def test_omits_filler_thesauri(mapeo_ceiba, filler):
    dataset = {"keywordSet": keyword_set("Mariposas", filler)}

    assert mapeo_ceiba.map_keywords(dataset) == [{"keywordValue": "Mariposas"}]


@pytest.mark.parametrize(
    ("word", "vocabulary", "uri"),
    [
        ("Registro biológico", GBIF_TYPE, GBIF_TYPE_URI),
        ("Evento de muestreo", GBIF_TYPE, GBIF_TYPE_URI),
        ("Espécimen", GBIF_SUBTYPE, GBIF_SUBTYPE_URI),
        ("Inventario regional", GBIF_SUBTYPE, GBIF_SUBTYPE_URI),
    ],
)
def test_recognizes_spanish_gbif_terms(mapeo_ceiba, word, vocabulary, uri):
    dataset = {"keywordSet": keyword_set([word, "musgos"], f"{vocabulary}: {uri}")}

    result = mapeo_ceiba.map_keywords(dataset)

    assert sorted(result, key=lambda entry: entry["keywordValue"]) == [
        {"keywordValue": word, "keywordVocabulary": vocabulary, "keywordVocabularyURI": uri},
        {"keywordValue": "musgos"},
    ]


def test_does_not_generate_keyword_term_uri(mapeo_ceiba):
    dataset = {"keywordSet": [
        keyword_set("Bosque", f"Tesauro de hábitat: {THESAURUS_URI}"),
        keyword_set("Rana"),
    ]}

    result = mapeo_ceiba.map_keywords(dataset)

    assert len(result) == 2
    assert all("keywordTermURI" not in entry for entry in result)
    assert any(entry.get("keywordVocabularyURI") == THESAURUS_URI for entry in result)


@pytest.mark.parametrize(
    ("first", "duplicate"),
    [
        ("naidí", "naidí."),
        ("naidí.", "naidí"),
        ("Craugastoridae", "Craugastoridae."),
        ("Craugastoridae.", "Craugastoridae"),
    ],
)
def test_characterizes_punctuation_in_duplicate_key(mapeo_ceiba, first, duplicate):
    """Registra la equivalencia por puntuación del código actual para su revisión."""
    dataset = {"keywordSet": [keyword_set(first), keyword_set(duplicate)]}

    assert mapeo_ceiba.map_keywords(dataset) == [{"keywordValue": first}]


@pytest.mark.parametrize(
    ("first_uri", "later_uri"),
    [
        pytest.param(GBIF_TYPE_URI, GBIF_TYPE_2015_URI, id="unversioned-first"),
        pytest.param(GBIF_TYPE_2015_URI, GBIF_TYPE_URI, id="versioned-first"),
    ],
)
def test_characterizes_first_controlled_entry_across_gbif_versions(
    mapeo_ceiba, first_uri, later_uri
):
    """Registra el desempate actual entre URL de versiones equivalentes de GBIF."""
    dataset = {"keywordSet": [
        keyword_set("Occurrence", f"{GBIF_TYPE}: {first_uri}"),
        keyword_set("OCCURRENCE", f"{GBIF_TYPE}: {later_uri}"),
    ]}

    assert mapeo_ceiba.map_keywords(dataset) == [{
        "keywordValue": "Occurrence",
        "keywordVocabulary": GBIF_TYPE,
        "keywordVocabularyURI": first_uri,
    }]


def test_kw001_nomenclator_authority_maps_to_gbif_subtype(mapeo_ceiba):
    dataset = {"keywordSet": keyword_set("Nomenclator authority", f"{GBIF_SUBTYPE}: {GBIF_SUBTYPE_URI}")}

    assert mapeo_ceiba.map_keywords(dataset) == [{
        "keywordValue": "Nomenclator authority",
        "keywordVocabulary": GBIF_SUBTYPE,
        "keywordVocabularyURI": GBIF_SUBTYPE_URI,
    }]


def test_kw001_spanish_specimen_alias_maps_to_gbif_subtype(mapeo_ceiba):
    dataset = {"keywordSet": keyword_set("Ejemplar", f"{GBIF_SUBTYPE}: {GBIF_SUBTYPE_URI}")}

    assert mapeo_ceiba.map_keywords(dataset) == [{
        "keywordValue": "Ejemplar",
        "keywordVocabulary": GBIF_SUBTYPE,
        "keywordVocabularyURI": GBIF_SUBTYPE_URI,
    }]
