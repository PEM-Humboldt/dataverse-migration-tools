"""Pruebas sintéticas del bloque externalReferences de CEIBA."""

from xml.etree import ElementTree

import pytest


COPY = "External Copy of the dataset"
BIBLIOGRAPHY = "This dataset references"
SOURCE_URL = "https://i2d.humboldt.org.co/ceiba/resource"
BAD_URL_NOTE = "URL mal escrita: no migrada"
REPAIRED_URL_NOTE = (
    "URL escrita sin https://: añadido en la migración; comprobar que el enlace funciona"
)


def bibliography_row(text, **identifier):
    return {"externalReferenceType": BIBLIOGRAPHY, "citationText": text, **identifier}


def source_row(name="recurso-sintetico", version="1"):
    return {
        "externalReferenceType": COPY,
        "citationText": "IPT Ceiba (I2D)",
        "externalReferenceURL": f"{SOURCE_URL}?r={name}&v={version}",
        "externalReferenceOtherId": name,
        "externalReferenceNote": "Migrado desde IPT Ceiba (I2D)",
    }


def url_curation(identifier, note=BAD_URL_NOTE):
    return {
        "resource": "recurso-sintetico",
        "kind": "reference_url",
        "field": "externalReferenceURL",
        "value": identifier,
        "note": note,
    }


def mapped_references(mapeo, record):
    curation = []
    references = mapeo.map_external_references(record, curation)
    return mapeo.quote_urls(references), curation


def test_source_reference_uses_directory_name_and_source_version(mapeo_ceiba, eml_ceiba):
    from src.mapeo.ceiba.ceiba_source import read_record

    ingested = eml_ceiba({})
    root = next(iter(ingested.values()))
    root["@packageId"] = "https://example.test/resource?r=clave-anterior&v=1"
    ingested["resource"] = {"shortName": "nombre-del-ipt"}
    record = read_record("recurso-sintetico", ingested, latest_version="9.2")
    record["gbif"] = {"bibliography": {"citation": "Cita posterior"}}

    rows, curation = mapped_references(mapeo_ceiba, record)

    assert rows == [source_row(version="9.2"), bibliography_row("<p>Cita posterior</p>")]
    assert curation == []


@pytest.mark.parametrize(
    ("name", "version", "query"),
    [
        ("muestra con espacio", "1 2", "r=muestra%20con%20espacio&v=1%202"),
        ("muestra-á", "1", "r=muestra-%C3%A1&v=1"),
        ("muestra%2Funo&parte#fragmento", "1", "r=muestra%2Funo&parte#fragmento&v=1"),
    ],
    ids=["spaces", "unicode", "reserved-and-already-encoded"],
)
def test_source_reference_characterizes_existing_url_encoding(
    mapeo_ceiba, record_ceiba, name, version, query
):
    """Caracteriza la codificación actual, incluidos los delimitadores reservados."""
    record = record_ceiba({})
    record.update(name=name, version=version)

    rows, curation = mapped_references(mapeo_ceiba, record)

    expected = source_row(name, version)
    expected["externalReferenceURL"] = f"{SOURCE_URL}?{query}"
    assert rows == [expected]
    assert curation == []


def test_bibliography_preserves_order_and_normalized_text(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["gbif"] = {
        "bibliography": {
            "citation": [
                "  Primera\t cita\ncon   espacios. ",
                {"#text": "  Segunda & <tercera> y \"cuarta\". ", "@identifier": "ISSN 0000-0000"},
            ],
        },
    }

    rows, curation = mapped_references(mapeo_ceiba, record)

    assert rows == [
        source_row(),
        bibliography_row("<p>Primera cita con espacios.</p>"),
        bibliography_row(
            '<p>Segunda &amp; &lt;tercera&gt; y "cuarta".</p>',
            externalReferenceOtherId="ISSN 0000-0000",
        ),
    ]
    assert ["".join(ElementTree.fromstring(row["citationText"]).itertext()) for row in rows[1:]] == [
        "Primera cita con espacios.",
        'Segunda & <tercera> y "cuarta".',
    ]
    assert curation == []


@pytest.mark.parametrize(
    "gbif",
    [
        {},
        {"bibliography": {}},
        {"bibliography": {"citation": " \n "}},
        {"bibliography": {"citation": {"@identifier": "https://example.test/ruta con espacios"}}},
    ],
    ids=["missing-bibliography", "missing-citation", "blank-text", "identifier-without-text"],
)
def test_bibliography_without_text_has_no_reference_or_curation(mapeo_ceiba, record_ceiba, gbif):
    record = record_ceiba({})
    record["gbif"] = gbif

    assert mapped_references(mapeo_ceiba, record) == ([source_row()], [])


@pytest.mark.parametrize(
    "citations",
    [
        ["Texto de la cita", "Texto de la cita"],
        ["Texto  de la cita", " Texto de la cita\n"],
        [
            {"#text": "Texto de la cita", "@identifier": "etiqueta local uno"},
            {"#text": "Texto de la cita", "@identifier": "etiqueta local dos"},
        ],
    ],
    ids=["identical", "equal-after-normalization", "different-source-identifiers"],
)
def test_bibliography_preserves_repeated_occurrences(mapeo_ceiba, record_ceiba, citations):
    record = record_ceiba({})
    record["gbif"] = {"bibliography": {"citation": citations}}

    rows, curation = mapped_references(mapeo_ceiba, record)

    expected = bibliography_row("<p>Texto de la cita</p>")
    assert rows == [source_row(), expected, expected]
    assert curation == []


def test_bibliography_characterizes_nested_text_in_synthetic_ingest(mapeo_ceiba, record_ceiba):
    """Documenta una forma sintética ausente de la ingesta auditada."""
    record = record_ceiba({})
    record["gbif"] = {
        "bibliography": {
            "citation": [
                {"#text": "Texto disponible", "emphasis": "Texto anidado"},
                {"emphasis": "Sin texto directo"},
            ],
        },
    }

    assert mapped_references(mapeo_ceiba, record) == (
        [source_row(), bibliography_row("<p>Texto disponible</p>")],
        [],
    )


@pytest.mark.parametrize(
    ("identifier", "field", "value", "note"),
    [
        pytest.param("10.0000/sintetico", "externalReferenceDOI", "10.0000/sintetico", None, id="bare-doi"),
        pytest.param("https://doi.org/10.0000/sintetico", "externalReferenceDOI",
                     "10.0000/sintetico", None, id="doi-before-url"),
        pytest.param("DOI : 10.0000/sintetico", "externalReferenceDOI", "10.0000/sintetico", None, id="doi-label"),
        pytest.param("10.0000/sintetico...", "externalReferenceDOI", "10.0000/sintetico", None, id="doi-punctuation"),
        pytest.param("https://doi.org/10.0000/sintetico  anotación", "externalReferenceDOI",
                     "10.0000/sintetico", None, id="doi-before-malformed-url"),
        pytest.param("http://example.test/ruta", "externalReferenceURL", "http://example.test/ruta", None, id="http"),
        pytest.param("https://example.test/ISBN/ruta", "externalReferenceURL",
                     "https://example.test/ISBN/ruta", None, id="https-before-isbn"),
        pytest.param("https://example.test/a%2Fb", "externalReferenceURL",
                     "https://example.test/a%2Fb", None, id="already-encoded"),
        pytest.param("www.example.test/ruta", "externalReferenceURL", "https://www.example.test/ruta",
                     REPAIRED_URL_NOTE, id="www-repaired"),
        pytest.param("www.example.test/ruta ISSN", None, None, BAD_URL_NOTE, id="malformed-www-before-issn"),
        pytest.param("ISBN 0000000000000", "externalReferenceOtherId", "ISBN 0000000000000", None, id="isbn"),
        pytest.param("ISSN 0000-0000", "externalReferenceOtherId", "ISSN 0000-0000", None, id="issn"),
        pytest.param("etiqueta local", None, None, None, id="other-identifier"),
        pytest.param(None, None, None, None, id="absent-identifier"),
    ],
)
def test_classifies_bibliographic_identifiers(mapeo_ceiba, record_ceiba, identifier, field, value, note):
    record = record_ceiba({})
    citation = {"#text": "Cita sintética"}
    if identifier is not None:
        citation["@identifier"] = identifier
    record["gbif"] = {"bibliography": {"citation": citation}}

    rows, curation = mapped_references(mapeo_ceiba, record)

    expected = {} if field is None else {field: value}
    assert rows == [source_row(), bibliography_row("<p>Cita sintética</p>", **expected)]
    assert curation == ([url_curation(identifier, note)] if note else [])


@pytest.mark.parametrize(
    ("identifier", "cleaned"),
    [
        ("http://exam ple.test/ruta", "http://exam ple.test/ruta"),
        ("https://exam ple.test/ruta", "https://exam ple.test/ruta"),
        ("https://  example.test/ruta", "https:// example.test/ruta"),
        ("https://example.test/una ruta", "https://example.test/una ruta"),
        (" https://example.test/?q=uno\t  dos ", "https://example.test/?q=uno dos"),
        ("https://example.test/a https://example.test/b", "https://example.test/a https://example.test/b"),
        ("HTTP://example.test/ruta", "HTTP://example.test/ruta"),
        ("HtTpS://example.test/ruta", "HtTpS://example.test/ruta"),
    ],
    ids=["http-authority", "https-authority", "after-scheme", "path", "query", "two-links", "uppercase", "mixed-case"],
)
def test_ext_h02_curates_http_not_admitted_as_url(mapeo_ceiba, record_ceiba, identifier, cleaned):
    record = record_ceiba({})
    record["gbif"] = {"bibliography": {"citation": {"#text": "Cita & enlace", "@identifier": identifier}}}

    rows, curation = mapped_references(mapeo_ceiba, record)

    assert rows == [source_row(), bibliography_row("<p>Cita &amp; enlace</p>")]
    assert curation == [url_curation(cleaned)]


def test_ext_h02_preserves_multiplicity_and_unrelated_references(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    bad = "https://example.test/ruta malformada"
    malformed = {"#text": "Cita repetida", "@identifier": bad}
    good = "https://example.test/ruta"
    record["gbif"] = {
        "bibliography": {"citation": [malformed, {"#text": "Cita válida", "@identifier": good}, malformed]},
    }

    rows, curation = mapped_references(mapeo_ceiba, record)

    assert rows == [
        source_row(),
        bibliography_row("<p>Cita repetida</p>"),
        bibliography_row("<p>Cita válida</p>", externalReferenceURL=good),
        bibliography_row("<p>Cita repetida</p>"),
    ]
    assert curation == [url_curation(bad), url_curation(bad)]


@pytest.mark.parametrize("label", ["ISBN", "ISSN"])
def test_ext_h02_does_not_reclassify_existing_isbn_or_issn(mapeo_ceiba, record_ceiba, label):
    record = record_ceiba({})
    identifier = f"https://example.test/ruta {label} 0000"
    record["gbif"] = {"bibliography": {"citation": {"#text": "Cita híbrida", "@identifier": identifier}}}

    assert mapped_references(mapeo_ceiba, record) == (
        [source_row(), bibliography_row("<p>Cita híbrida</p>", externalReferenceOtherId=identifier)],
        [],
    )


@pytest.mark.parametrize(
    ("inventory", "doi"),
    [
        ({"biologico": {"doi": "10.0000/copia-sintetica"}}, "10.0000/copia-sintetica"),
        ({"biologico": {"doi": "https://doi.org/10.0000/copia-sintetica"}}, "10.0000/copia-sintetica"),
        ({"biologico": {"doi": "N/A"}}, None),
        ({"biologico": {"doi": "identificador local"}}, None),
        ({}, None),
    ],
    ids=["doi", "prefixed-doi", "marker", "not-recognized", "missing-inventory"],
)
def test_appends_one_inventory_doi_copy_only_if_recognized(mapeo_ceiba, record_ceiba, inventory, doi):
    record = record_ceiba({})
    record["inventory"] = inventory
    record["gbif"] = {"bibliography": {"citation": "Cita previa a la copia"}}

    expected = [source_row(), bibliography_row("<p>Cita previa a la copia</p>")]
    if doi:
        expected.append({"externalReferenceType": COPY, "externalReferenceDOI": doi})
    assert mapped_references(mapeo_ceiba, record) == (expected, [])


def test_preserves_same_doi_in_two_roles_without_adding_citation_other_id(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["package_id"] = "urn:example:recurso-sintetico:1"
    doi = "10.0000/ambas-funciones"
    record["gbif"] = {"bibliography": {"citation": {"#text": "Cita", "@identifier": doi}}}
    record["inventory"] = {"biologico": {"doi": f"doi:{doi}"}}

    rows, curation = mapped_references(mapeo_ceiba, record)
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})

    assert rows == [
        source_row(),
        bibliography_row("<p>Cita</p>", externalReferenceDOI=doi),
        {"externalReferenceType": COPY, "externalReferenceDOI": doi},
    ]
    assert citation["otherId"] == [
        {"otherIdAgency": "IPT Ceiba (I2D)", "otherIdValue": "urn:example:recurso-sintetico:1"},
    ]
    assert curation == []


def test_reconstructs_complete_external_reference_compound(
    mapeo_ceiba, eml_ceiba, reconstruir_dataverse
):
    from src.mapeo.ceiba.ceiba_source import read_record

    doi, copy_doi = "10.0000/cita", "10.0000/copia"
    good, bare = "https://example.test/valida", "www.example.test/reconstruible"
    malformed, isbn = "https://example.test/ruta malformada", "ISBN 0000000000000"
    ingested = eml_ceiba({})
    root = next(iter(ingested.values()))
    root["additionalMetadata"] = {"metadata": {"gbif": {"bibliography": {"citation": [
        {"#text": "DOI bibliográfico", "@identifier": doi},
        {"#text": "Enlace válido", "@identifier": good},
        {"#text": "Enlace reconstruible", "@identifier": bare},
        {"#text": "Enlace malformado", "@identifier": malformed},
        {"#text": "Libro sintético", "@identifier": isbn},
    ]}}}}
    ingested["inventory"] = {"biologico": {"doi": copy_doi, "gbif_key": "00000000-0000-4000-8000-000000000001"}}
    record = read_record("recurso-sintetico", ingested, latest_version="1")
    expected = [
        source_row(),
        bibliography_row("<p>DOI bibliográfico</p>", externalReferenceDOI=doi),
        bibliography_row("<p>Enlace válido</p>", externalReferenceURL=good),
        bibliography_row("<p>Enlace reconstruible</p>", externalReferenceURL=f"https://{bare}"),
        bibliography_row("<p>Enlace malformado</p>"),
        bibliography_row("<p>Libro sintético</p>", externalReferenceOtherId=isbn),
        {"externalReferenceType": COPY, "externalReferenceDOI": copy_doi},
    ]
    schema = {
        "externalReference": {
            "typeClass": "compound",
            "multiple": True,
            "controlled_subfields": {"externalReferenceType"},
            "subfields": {
                name: {"multiple": False} for name in (
                    "externalReferenceType", "citationText", "externalReferenceURL",
                    "externalReferenceDOI", "externalReferenceOtherId", "externalReferenceNote",
                    "externalEncoding", "externalFileFormat", "externalFileFormatVersion",
                )
            },
        },
    }

    rows, curation = mapped_references(mapeo_ceiba, record)
    payload = reconstruir_dataverse({"externalReferences": {"externalReference": rows}}, schema)

    assert payload == {
        "externalReferences": {
            "name": "externalReferences",
            "fields": [{
                "typeName": "externalReference",
                "typeClass": "compound",
                "multiple": True,
                "value": [{
                    key: {
                        "typeName": key,
                        "typeClass": "controlledVocabulary" if key == "externalReferenceType" else "primitive",
                        "multiple": False,
                        "value": value,
                    }
                    for key, value in row.items()
                } for row in expected],
            }],
        },
    }
    assert curation == [url_curation(bare, REPAIRED_URL_NOTE), url_curation(malformed)]
