"""Pruebas sintéticas del bloque biologicalMetadata de CEIBA."""

import pytest


DATE_NOTE = "no es una fecha AAAA, AAAA-MM ni AAAA-MM-DD"
ORDER_NOTE = (
    "Fecha inicial posterior a la fecha final para la precisión registrada. "
    "Revisar el intervalo de origen."
)


def curation_row(kind, field, value, note):
    return {
        "resource": "recurso-sintetico",
        "kind": kind,
        "field": field,
        "value": value,
        "note": note,
    }


def source_range(begin, end):
    return {
        key: {"calendarDate": value}
        for key, value in (("beginDate", begin), ("endDate", end))
        if value is not None
    }


def date_range(begin=None, end=None):
    row = {"temporalCoverageType": "Date Range"}
    if begin is not None:
        row["initialCalendarDate"] = begin
    if end is not None:
        row["finalCalendarDate"] = end
    return row


@pytest.mark.parametrize(
    ("begin", "end", "value"),
    [
        pytest.param("2024-05-20", "2023-08-15", '["2024-05-20", "2023-08-15"]', id="days"),
        pytest.param("2025", "2024-12-31", '["2025", "2024-12-31"]', id="year-start"),
        pytest.param("2024-03", "2024-02-29", '["2024-03", "2024-02-29"]', id="month-start"),
        pytest.param("1900-03-01", "1900-02", '["1900-03-01", "1900-02"]', id="non-leap-month-end"),
        pytest.param("0002-01-01", "0001", '["0002-01-01", "0001"]', id="minimum-year-end"),
        pytest.param("2024-05-01", "2024-04", '["2024-05-01", "2024-04"]', id="next-month-day"),
    ],
)
def test_bio_h01_curates_inverted_range(mapeo_ceiba, record_ceiba, begin, end, value):
    record = record_ceiba({"coverage": {"temporalCoverage": {"rangeOfDates": source_range(begin, end)}}})
    curation = []

    assert mapeo_ceiba.map_temporal(record, curation) == [date_range(begin, end)]
    assert curation == [curation_row("temporal_range_order", "temporalCoverage", value, ORDER_NOTE)]


@pytest.mark.parametrize(
    ("begin", "end"),
    [
        pytest.param("2024-04-01", "2024-04-30", id="days-in-order"),
        pytest.param("2024-04-30", "2024-04-30", id="same-day"),
        pytest.param("2023", "2024-01-01", id="earlier-year"),
        pytest.param("2024-04", "2024-05-01", id="earlier-month"),
        pytest.param("2024", "2024-01-10", id="year-overlaps-day"),
        pytest.param("2024-02", "2024-02-02", id="month-overlaps-day"),
        pytest.param("2024-02-29", "2024-02", id="leap-last-day-overlaps-month"),
        pytest.param("1900-02-28", "1900-02", id="non-leap-last-day-overlaps-month"),
        pytest.param("2024", "2024", id="same-year"),
        pytest.param("2024-04", "2024-04", id="same-month"),
        pytest.param("0001", "0001-01-01", id="minimum-year"),
        pytest.param("9999-12-31", "9999", id="maximum-year"),
        pytest.param("9999-12-31", "9999-12", id="maximum-month"),
    ],
)
def test_preserves_ranges_without_unequivocal_inversion(mapeo_ceiba, record_ceiba, begin, end):
    record = record_ceiba({"coverage": {"temporalCoverage": {"rangeOfDates": source_range(begin, end)}}})
    curation = []

    assert mapeo_ceiba.map_temporal(record, curation) == [date_range(begin, end)]
    assert curation == []


@pytest.mark.parametrize(
    ("begin", "end", "rows", "curation"),
    [
        pytest.param("2024-02-30", "2024-03-01", [date_range(end="2024-03-01")],
                     [("initialCalendarDate", "2024-02-30")], id="invalid-start"),
        pytest.param("2024-02-29", "2024-04-31", [date_range(begin="2024-02-29")],
                     [("finalCalendarDate", "2024-04-31")], id="invalid-end"),
        pytest.param(None, "2024-03", [date_range(end="2024-03")], [], id="missing-start"),
        pytest.param("2024", None, [date_range(begin="2024")], [], id="missing-end"),
        pytest.param(None, None, [], [], id="both-missing"),
        pytest.param("0000", "1900-02-29", [],
                     [("initialCalendarDate", "0000"), ("finalCalendarDate", "1900-02-29")],
                     id="both-invalid"),
    ],
)
def test_preserves_unusable_endpoint_handling(mapeo_ceiba, record_ceiba, begin, end, rows, curation):
    record = record_ceiba({"coverage": {"temporalCoverage": {"rangeOfDates": source_range(begin, end)}}})
    notes = []

    assert mapeo_ceiba.map_temporal(record, notes) == rows
    assert notes == [curation_row("date", field, value, DATE_NOTE) for field, value in curation]


def test_bio_h01_preserves_occurrences_and_temporal_order(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"coverage": {"temporalCoverage": [
        {
            "singleDateTime": {"calendarDate": "2024-02-29"},
            "rangeOfDates": [
                source_range("2024-02", "2024-04"),
                source_range("2024-02-30", "2024-04"),
                source_range("2025-02", "2024"),
            ],
        },
        {
            "singleDateTime": {"calendarDate": "2025"},
            "rangeOfDates": [
                source_range("2025-02", "2024"),
                source_range("2025-05-01", "2025-04-31"),
            ],
        },
    ]}})
    record["gbif"] = {"formationPeriod": "Etapa  sintética"}
    notes = []

    assert mapeo_ceiba.map_temporal(record, notes) == [
        {"temporalCoverageType": "Date", "simpleCalendarDate": "2024-02-29"},
        date_range("2024-02", "2024-04"),
        date_range(end="2024-04"),
        date_range("2025-02", "2024"),
        {"temporalCoverageType": "Date", "simpleCalendarDate": "2025"},
        date_range("2025-02", "2024"),
        date_range(begin="2025-05-01"),
        {"temporalCoverageType": "Formation period", "formationPeriod": "<p>Etapa sintética</p>"},
    ]
    inverted = curation_row("temporal_range_order", "temporalCoverage", '["2025-02", "2024"]', ORDER_NOTE)
    assert notes == [
        curation_row("date", "initialCalendarDate", "2024-02-30", DATE_NOTE),
        inverted,
        inverted,
        curation_row("date", "finalCalendarDate", "2025-04-31", DATE_NOTE),
    ]


@pytest.fixture
def biological_tables():
    """Equivalencias ficticias con destinos del vocabulario de biologicalMetadata."""
    return {"vocabularies": [
        {"field": field, "source": source, "source_value": value, "dataverse_value": target}
        for field, source, value, target in [
            ("coreType", "resource.xml", "registro sintético", "Occurrence"),
            ("coreType", "resource.xml", "checklist", "Checklist"),
            ("subtype", "resource.xml", "ficha", "Specimen"),
            ("subtype", "resource.xml", "observation", "Observation"),
            ("taxonRankName", "eml", "especie", "species"),
            ("taxonRankName", "eml", "familia", "family"),
            ("specimenPreservationMethod", "eml", "en seco", "Dried"),
            ("specimenPreservationMethod", "eml", "desecado", "Dried"),
            ("specimenPreservationMethod", "eml", "alcohol", "Alcohol"),
        ]
    ]}


def test_short_name_comes_from_directory(mapeo_ceiba, eml_ceiba, biological_tables):
    from src.mapeo.ceiba.ceiba_source import read_record

    ingested = eml_ceiba({"shortName": "nombre descriptivo"})
    ingested["resource"] = {"shortName": "otro nombre corto"}
    record = read_record("clave-de-directorio", ingested)
    notes = []

    assert mapeo_ceiba.map_biological(record, biological_tables, notes) == {
        "emlShortName": "clave-de-directorio",
    }
    assert notes == []


@pytest.mark.parametrize("subtype", [" FICHA ", None], ids=["xml-subtype", "no-keyword-fallback"])
def test_resource_xml_types_take_precedence(mapeo_ceiba, record_ceiba, biological_tables, subtype):
    record = record_ceiba({"keywordSet": [
        {"keywordThesaurus": "GBIF Dataset Type Vocabulary", "keyword": ["Checklist"]},
        {"keywordThesaurus": "GBIF Dataset Subtype Vocabulary", "keyword": ["Observation"]},
    ]})
    record["resource"]["coreType"] = " \tREGISTRO  SINTÉTICO "
    expected = {"emlShortName": "recurso-sintetico", "coreType": "Occurrence"}
    if subtype is not None:
        record["resource"]["subtype"] = subtype
        expected["subtype"] = "Specimen"
    notes = []

    assert mapeo_ceiba.map_biological(record, biological_tables, notes) == expected
    assert notes == []


def test_unknown_independent_vocabularies_keep_curation_order(
    mapeo_ceiba, record_ceiba, biological_tables
):
    record = record_ceiba({})
    record["resource"].update(coreType="tipo  de prueba", subtype="subtipo de prueba")
    record["gbif"]["specimenPreservationMethod"] = ["técnica de prueba", " alcohol "]
    notes = []

    assert mapeo_ceiba.map_biological(record, biological_tables, notes) == {
        "emlShortName": "recurso-sintetico",
        "specimenPreservationMethod": ["Alcohol"],
    }
    note = "valor sin equivalencia en tablas/vocabularies.csv"
    assert notes == [
        curation_row("vocabulary", "coreType", "tipo de prueba", note),
        curation_row("vocabulary", "subtype", "subtipo de prueba", note),
        curation_row("vocabulary", "specimenPreservationMethod", "técnica de prueba", note),
    ]


def test_independent_prose_preserves_paragraphs_and_escapes(
    mapeo_ceiba, record_ceiba, biological_tables
):
    record = record_ceiba({
        "purpose": " Observaciones \t & análisis ",
        "introduction": {"para": ["Primero < Segundo", " ", " Último > Inicio "]},
        "gettingStarted": {"para": " Consulta  inicial. "},
        "biologicalBiases": "Dato sin fuente aprobada",
        "coverage": {"taxonomicCoverage": [
            {"generalTaxonomicCoverage": " Primer \n grupo. "},
            {"generalTaxonomicCoverage": " "},
            {"generalTaxonomicCoverage": "Segundo & último."},
        ]},
    })
    notes = []

    assert mapeo_ceiba.map_biological(record, biological_tables, notes) == {
        "emlShortName": "recurso-sintetico",
        "purpose": "<p>Observaciones &amp; análisis</p>",
        "introduction": "<p>Primero &lt; Segundo</p><p>Último &gt; Inicio</p>",
        "gettingStarted": "<p>Consulta inicial.</p>",
        "taxonomicCoverageDescription": ["<p>Primer grupo.</p>", "<p>Segundo &amp; último.</p>"],
    }
    assert notes == []


def test_preservation_deduplicates_equivalences_in_source_order(
    mapeo_ceiba, record_ceiba, biological_tables
):
    record = record_ceiba({})
    record["gbif"]["specimenPreservationMethod"] = [" EN SECO ", "alcohol", "desecado", " alcohol "]
    notes = []

    assert mapeo_ceiba.map_biological(record, biological_tables, notes) == {
        "emlShortName": "recurso-sintetico",
        "specimenPreservationMethod": ["Dried", "Alcohol"],
    }
    assert notes == []


def test_taxonomy_maps_available_fields_and_omits_empty_rows(
    mapeo_ceiba, record_ceiba, biological_tables
):
    record = record_ceiba({"coverage": {"taxonomicCoverage": {"taxonomicClassification": [
        {"taxonRankName": " ESPECIE ", "taxonRankValue": "Taxón  Uno",
         "commonName": ["Nombre A", {"#text": " Nombre B "}], "taxonId": "urn:example:taxon"},
        {"taxonRankValue": "Taxón Dos", "commonName": "Nombre C"},
        {"taxonRankName": "familia", "taxonRankValue": "Taxón Tres"},
        {"taxonRankName": "", "taxonRankValue": " ", "commonName": None},
    ]}}})
    notes = []

    assert mapeo_ceiba.map_taxonomic(record, biological_tables, notes) == {
        "taxonomicClassification": [
            {"taxonRankName": "species", "taxonRankValue": "Taxón Uno", "commonName": "Nombre A Nombre B"},
            {"taxonRankValue": "Taxón Dos", "commonName": "Nombre C"},
            {"taxonRankName": "family", "taxonRankValue": "Taxón Tres"},
        ],
    }
    assert notes == []


def test_taxonomy_curates_unknown_rank_and_keeps_name(mapeo_ceiba, record_ceiba, biological_tables):
    record = record_ceiba({"coverage": {"taxonomicCoverage": {"taxonomicClassification": {
        "taxonRankName": " Rango  sin equivalencia ", "taxonRankValue": "Taxón A",
    }}}})
    notes = []

    assert mapeo_ceiba.map_taxonomic(record, biological_tables, notes) == {
        "taxonomicClassification": [{"taxonRankValue": "Taxón A"}],
    }
    assert notes == [curation_row(
        "vocabulary", "taxonRankName", "Rango sin equivalencia",
        "rango sin equivalencia en tablas/vocabularies.csv",
    )]


def test_taxonomy_keeps_row_multiplicity_and_order(mapeo_ceiba, record_ceiba, biological_tables):
    first = {"taxonRankValue": "Taxón A"}
    second = {"taxonRankValue": "Taxón B"}
    record = record_ceiba({"coverage": {"taxonomicCoverage": [
        {"taxonomicClassification": [first, second, first.copy()]},
        {"taxonomicClassification": {"taxonRankValue": " Taxón \t A "}},
    ]}})
    notes = []

    assert mapeo_ceiba.map_taxonomic(record, biological_tables, notes) == {
        "taxonomicClassification": [first, second, first, first],
    }
    assert notes == []


@pytest.mark.parametrize(
    ("node", "rows"),
    [
        pytest.param(
            {"taxonRankValue": "Padre", "taxonomicClassification": {"taxonRankValue": "Hijo"}},
            [{"taxonRankValue": "Padre"}], id="one-nested-level",
        ),
        pytest.param(
            {"taxonRankValue": "Padre", "taxonomicClassification": {
                "taxonRankValue": "Hijo", "taxonomicClassification": {"taxonRankValue": "Nieto"},
            }},
            [{"taxonRankValue": "Padre"}], id="multiple-nested-levels",
        ),
        pytest.param(
            {"taxonomicClassification": {"taxonRankName": "especie", "taxonRankValue": "Hijo"}},
            [], id="usable-child-under-empty-parent",
        ),
    ],
)
def test_characterizes_non_recursive_taxonomy(
    mapeo_ceiba, record_ceiba, biological_tables, node, rows
):
    """Documenta la limitación conocida de jerarquías, pendiente de aprobación institucional."""
    record = record_ceiba({"coverage": {"taxonomicCoverage": {"taxonomicClassification": node}}})
    notes = []

    assert mapeo_ceiba.map_taxonomic(record, biological_tables, notes) == (
        {"taxonomicClassification": rows} if rows else {}
    )
    assert notes == []


def test_methods_group_area_sampling_and_quality(mapeo_ceiba):
    dataset = {"methods": {
        "sampling": {
            "studyExtent": {"description": {"para": [" Cuenca < umbral ", " Sector & ribera "]}},
            "samplingDescription": " Muestreo \t en parcelas. ",
        },
        "qualityControl": {"description": {"para": ["Primera revisión.", "Segunda revisión."]}},
    }}

    assert mapeo_ceiba.map_methods(dataset) == {"emlMethod": [{
        "emlMethodStudyArea": "<p>Cuenca &lt; umbral</p><p>Sector &amp; ribera</p>",
        "emlMethodSampling": "<p>Muestreo en parcelas.</p>",
        "emlMethodQualityControl": "<p>Primera revisión.</p><p>Segunda revisión.</p>",
    }]}


def test_empty_optional_method_descriptions_are_omitted(mapeo_ceiba):
    dataset = {"methods": {
        "sampling": {"studyExtent": {}, "samplingDescription": {"para": "Único"}},
        "qualityControl": {"description": {"para": [" ", ""]}},
    }}

    assert mapeo_ceiba.map_methods(dataset) == {"emlMethod": [{"emlMethodSampling": "<p>Único</p>"}]}


def test_method_steps_keep_order_and_renumber_after_empty_steps(mapeo_ceiba):
    dataset = {"methods": {"methodStep": [
        {}, {"description": "Preparación."}, {"description": {"para": " "}},
        {"description": [{"para": "Lectura."}, {"para": "Registro."}]},
        {"description": "Preparación."}, {"description": ""},
    ]}}

    assert mapeo_ceiba.map_methods(dataset) == {"emlMethodStep": [
        {"emlMethodStepNumber": "1", "emlMethodStepDescription": "<p>Preparación.</p>"},
        {"emlMethodStepNumber": "2", "emlMethodStepDescription": "<p>Lectura.</p><p>Registro.</p>"},
        {"emlMethodStepNumber": "3", "emlMethodStepDescription": "<p>Preparación.</p>"},
    ]}


def test_absent_methods_are_omitted(mapeo_ceiba):
    assert mapeo_ceiba.map_methods({}) == {}


@pytest.mark.parametrize(
    ("description", "html"),
    [
        pytest.param({"para": {"#text": "Inicio", "itemizedlist": {"listitem": "Detalle"}}},
                     "<p>Inicio</p>", id="list"),
        pytest.param({"para": {"#text": "Inicio", "emphasis": "Detalle"}}, "<p>Inicio</p>", id="emphasis"),
        pytest.param({"para": {"#text": "Consultar .", "ulink": {
            "@url": "https://example.test", "citetitle": "Ficha",
        }}}, "<p>Consultar Ficha (https://example.test).</p>", id="link"),
        pytest.param({"#text": "Preámbulo", "para": "Párrafo"}, "<p>Párrafo</p>", id="mixed-content"),
        pytest.param({"para": {"emphasis": "Solo en nodo estructurado"}}, None, id="structured-only"),
    ],
)
def test_characterizes_method_markup_limits(mapeo_ceiba, description, html):
    """Registra límites del texto mixto y del marcado, pendientes de decisión institucional."""
    dataset = {"methods": {"methodStep": {"description": description}}}
    expected = {"emlMethodStep": [
        {"emlMethodStepNumber": "1", "emlMethodStepDescription": html},
    ]} if html else {}

    assert mapeo_ceiba.map_methods(dataset) == expected


COLLECTION_CODES_NOTE = (
    "lista de códigos separada en entradas: nombre y colección madre solo en la primera; "
    "asignar a cada código su nombre"
)
COLLECTION_IDENTIFIER_NOTE = (
    "identificador de colección que no es un código, un URI ni un texto del RNC: "
    "copiado como código; revisar qué es"
)
COLLECTION = {"collectionName": "Colección de prueba", "parentCollectionIdentifier": "Colección matriz"}


@pytest.mark.parametrize(
    ("identifier", "field", "value"),
    [
        pytest.param("http://example.test/a,b", "collectionIdentifier", ["http://example.test/a,b"], id="http"),
        pytest.param("https://example.test/a", "collectionIdentifier", ["https://example.test/a"], id="https"),
        pytest.param("urn:lsid:example.test:collection:a", "collectionIdentifier",
                     ["urn:lsid:example.test:collection:a"], id="lsid"),
        pytest.param("RNC: 0000", "collectionIdentifier", ["RNC: 0000"], id="rnc"),
        pytest.param(" CAT-1 ", "collectionCode", "CAT-1", id="code"),
        pytest.param(" CAT/1 ", "collectionCode", "CAT/1", id="slash-in-code"),
    ],
)
def test_classifies_collection_identifier(mapeo_ceiba, record_ceiba, identifier, field, value):
    record = record_ceiba({})
    record["gbif"]["collection"] = COLLECTION | {"collectionIdentifier": identifier}
    notes = []

    assert mapeo_ceiba.map_collections(record, notes) == [COLLECTION | {field: value}]
    assert notes == []


@pytest.mark.parametrize(
    ("identifier", "codes"),
    [
        pytest.param("A, B", ["A", "B"], id="comma"),
        pytest.param("A; B", ["A", "B"], id="semicolon"),
        pytest.param("A | B", ["A", "B"], id="vertical-bar"),
        pytest.param("A, B; | C", ["A", "B", "C"], id="combined-with-empty-segment"),
        pytest.param("A ; ;", ["A"], id="one-usable-segment"),
        pytest.param("A, A; B", ["A", "A", "B"], id="repeated-code"),
    ],
)
def test_collection_code_expansion_keeps_order_and_association(
    mapeo_ceiba, record_ceiba, identifier, codes
):
    record = record_ceiba({})
    record["gbif"]["collection"] = COLLECTION | {"collectionIdentifier": identifier}
    notes = []

    assert mapeo_ceiba.map_collections(record, notes) == [
        COLLECTION | {"collectionCode": codes[0]}, *({"collectionCode": code} for code in codes[1:]),
    ]
    expected = [curation_row("collection_codes", "collectionName", identifier, COLLECTION_CODES_NOTE)]
    assert notes == (expected if len(codes) > 1 else [])


@pytest.mark.parametrize("identifier", [None, " N/A ", " no aplica "], ids=["absent", "na", "not-applicable"])
def test_collection_markers_leave_only_useful_fields(mapeo_ceiba, record_ceiba, identifier):
    record = record_ceiba({})
    collection = {"collectionName": "Colección de prueba", "parentCollectionIdentifier": " Ninguno "}
    if identifier is not None:
        collection["collectionIdentifier"] = identifier
    record["gbif"]["collection"] = collection
    notes = []

    assert mapeo_ceiba.map_collections(record, notes) == [{"collectionName": "Colección de prueba"}]
    assert notes == []


def test_collection_curates_free_text_and_keeps_objects_in_order(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["gbif"]["collection"] = [
        {"collectionName": " Primera ", "collectionIdentifier": " Texto   descriptivo "},
        {"collectionName": " Segunda ", "parentCollectionIdentifier": " Otra  matriz ",
         "collectionIdentifier": "SEC"},
    ]
    notes = []

    assert mapeo_ceiba.map_collections(record, notes) == [
        {"collectionName": "Primera", "collectionCode": "Texto descriptivo"},
        {"collectionName": "Segunda", "parentCollectionIdentifier": "Otra matriz", "collectionCode": "SEC"},
    ]
    assert notes == [curation_row(
        "collection_identifier", "collectionCode", "Texto descriptivo", COLLECTION_IDENTIFIER_NOTE,
    )]


def test_omits_empty_collection_rows(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["gbif"]["collection"] = [{}, {"collectionName": " ", "collectionIdentifier": "N/A"}]
    notes = []

    assert mapeo_ceiba.map_collections(record, notes) == []
    assert notes == []


@pytest.fixture
def biological_schema():
    """Esquema sintético con las cardinalidades y tipos efectivos del bloque."""
    controlled = {"coreType": ["Occurrence"], "subtype": ["Specimen"],
                  "specimenPreservationMethod": ["Dried", "Alcohol"]}
    schema = {
        field: {"typeClass": "controlledVocabulary" if field in controlled else "primitive",
                "multiple": field in {"taxonomicCoverageDescription", "specimenPreservationMethod"},
                "required": False}
        for field in (
            "emlShortName", "coreType", "subtype", "purpose", "introduction", "gettingStarted",
            "taxonomicCoverageDescription", "specimenPreservationMethod", "biologicalBiases",
        )
    }
    for key, values in controlled.items():
        schema[key]["vocabulary"] = values

    subfields = {
        "taxonomicClassification": ("taxonRankName", "taxonRankValue", "commonName", "taxonId"),
        "temporalCoverage": ("temporalCoverageType", "simpleCalendarDate", "initialCalendarDate",
                             "finalCalendarDate", "formationPeriod"),
        "emlMethod": ("emlMethodStudyArea", "emlMethodSampling", "emlMethodQualityControl"),
        "emlMethodStep": ("emlMethodStepNumber", "emlMethodStepDescription"),
        "collectionData": ("collectionName", "parentCollectionIdentifier", "collectionIdentifier",
                           "collectionCode"),
    }
    child_vocabularies = {
        "taxonomicClassification": {"taxonRankName": ["species"]},
        "temporalCoverage": {"temporalCoverageType": ["Date", "Date Range", "Formation period"]},
    }
    for parent, children in subfields.items():
        child_vocabulary = child_vocabularies.get(parent, {})
        schema[parent] = {
            "typeClass": "compound", "multiple": True, "required": False,
            "controlled_subfields": set(child_vocabulary), "subfields_vocabulary": child_vocabulary,
            "subfields": {name: {"multiple": name == "collectionIdentifier", "required": False}
                          for name in children},
        }
    return schema


def dv_field(name, value, field_type="primitive", *, multiple=False):
    return {"typeName": name, "typeClass": field_type, "multiple": multiple, "value": value}


def test_biological_block_reconstruction(
    mapeo_ceiba, record_ceiba, reconstruir_dataverse, biological_tables, biological_schema
):
    from src.mapeo.geonetwork.dataverse_check import check_fields

    record = record_ceiba({
        "purpose": "Propósito",
        "introduction": {"para": "Introducción"},
        "gettingStarted": "Inicio",
        "coverage": {
            "taxonomicCoverage": {"generalTaxonomicCoverage": "Cobertura", "taxonomicClassification": {
                "taxonRankName": "especie", "taxonRankValue": "Taxón A", "commonName": "Nombre A",
            }},
            "temporalCoverage": {"rangeOfDates": source_range("2025", "2024-12-31")},
        },
        "methods": {
            "sampling": {"studyExtent": {"description": "Área"}, "samplingDescription": "Muestra"},
            "qualityControl": {"description": "Control"},
            "methodStep": {"description": "Paso"},
        },
    })
    record["resource"].update(coreType="registro sintético", subtype="ficha")
    record["gbif"] = {
        "collection": [
            COLLECTION | {"collectionIdentifier": "https://example.test/collection"},
            {"collectionName": "Otra colección", "collectionIdentifier": "A | B"},
        ],
        "specimenPreservationMethod": ["desecado", "alcohol"],
    }
    name = "biologicalMetadata"
    notes = []
    flat = {name: mapeo_ceiba.map_biological(record, biological_tables, notes)}
    assert check_fields(flat, biological_schema, [name]) == []

    expected_fields = [
        dv_field("emlShortName", "recurso-sintetico"),
        dv_field("coreType", "Occurrence", "controlledVocabulary"),
        dv_field("subtype", "Specimen", "controlledVocabulary"),
        dv_field("purpose", "<p>Propósito</p>"),
        dv_field("introduction", "<p>Introducción</p>"),
        dv_field("gettingStarted", "<p>Inicio</p>"),
        dv_field("taxonomicCoverageDescription", ["<p>Cobertura</p>"], multiple=True),
        dv_field("taxonomicClassification", [{
            "taxonRankName": dv_field("taxonRankName", "species", "controlledVocabulary"),
            "taxonRankValue": dv_field("taxonRankValue", "Taxón A"),
            "commonName": dv_field("commonName", "Nombre A"),
        }], "compound", multiple=True),
        dv_field("temporalCoverage", [{
            "temporalCoverageType": dv_field("temporalCoverageType", "Date Range", "controlledVocabulary"),
            "initialCalendarDate": dv_field("initialCalendarDate", "2025"),
            "finalCalendarDate": dv_field("finalCalendarDate", "2024-12-31"),
        }], "compound", multiple=True),
        dv_field("emlMethod", [{
            "emlMethodStudyArea": dv_field("emlMethodStudyArea", "<p>Área</p>"),
            "emlMethodSampling": dv_field("emlMethodSampling", "<p>Muestra</p>"),
            "emlMethodQualityControl": dv_field("emlMethodQualityControl", "<p>Control</p>"),
        }], "compound", multiple=True),
        dv_field("emlMethodStep", [{
            "emlMethodStepNumber": dv_field("emlMethodStepNumber", "1"),
            "emlMethodStepDescription": dv_field("emlMethodStepDescription", "<p>Paso</p>"),
        }], "compound", multiple=True),
        dv_field("collectionData", [
            {"collectionName": dv_field("collectionName", "Colección de prueba"),
             "parentCollectionIdentifier": dv_field("parentCollectionIdentifier", "Colección matriz"),
             "collectionIdentifier": dv_field("collectionIdentifier", ["https://example.test/collection"],
                                              multiple=True)},
            {"collectionName": dv_field("collectionName", "Otra colección"),
             "collectionCode": dv_field("collectionCode", "A")},
            {"collectionCode": dv_field("collectionCode", "B")},
        ], "compound", multiple=True),
        dv_field("specimenPreservationMethod", ["Dried", "Alcohol"], "controlledVocabulary", multiple=True),
    ]
    assert reconstruir_dataverse(flat, biological_schema) == {name: {"name": name, "fields": expected_fields}}
    assert notes == [
        curation_row("temporal_range_order", "temporalCoverage", '["2025", "2024-12-31"]', ORDER_NOTE),
        curation_row("collection_codes", "collectionName", "A | B", COLLECTION_CODES_NOTE),
    ]
