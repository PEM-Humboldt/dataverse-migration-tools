"""Pruebas de integración en memoria de personas y filas de curación."""

import pytest

from src.mapeo.ceiba import ceiba_people


CURATION_FIELDS = {"resource", "kind", "field", "value", "note"}


@pytest.fixture
def curation_tables():
    """Aporta las tablas mínimas para el mapeo de un registro sintético."""
    return {
        "citation_authors_index": {},
        "party_roles": [
            {"party_type": "creator", "role": "", "target_field": "producer", "contributor_type": ""},
            {"party_type": "contact", "role": "", "target_field": "datasetContact", "contributor_type": ""},
            {"party_type": "associatedParty", "role": "pointOfContact",
             "target_field": "datasetContact", "contributor_type": ""},
        ],
        "restriction_reasons": [],
        "vocabularies": [],
    }


@pytest.fixture
def open_record(record_ceiba):
    """Evita generar casos de restricción ajenos a las pruebas de personas."""
    def create_record(dataset):
        return record_ceiba({"intellectualRights": "Libre a nivel interno y externo", **dataset})

    return create_record


@pytest.mark.parametrize(
    "include_contractors",
    [False, True],
    ids=["without-contractor-curation", "with-contractor-curation"],
)
def test_integrates_default_author_contact_recovery_and_unknown_role_notes(
    mapeo_ceiba, open_record, curation_tables, include_contractors
):
    record = open_record({
        "contact": [
            {"organizationName": "Centro Ficticio"},
            {"organizationName": "Laboratorio Ficticio"},
        ],
        "associatedParty": [
            {"organizationName": "CENTRO-FICTICIO", "role": "pointOfContact",
             "electronicMailAddress": "recuperado@example.test"},
            {"organizationName": "Entidad Fuera de Tabla", "role": "rol-ficticio"},
        ],
    })
    record["gbif"] = {"citation": "Cita sintética (2024)."}
    if include_contractors:
        record["inventory"] = {"biologico": {
            "contratista": "Persona Ficticia", "contrato_convenio": "LAB-731PS, LAB-842PS",
        }}

    fields, curation = mapeo_ceiba.dataverse_fields(
        record, curation_tables, identifiers={}, macro_index={}
    )

    default_email = ceiba_people.DEFAULT_CONTACT_EMAIL
    assert fields["citation"]["author"] == [{"authorName": ceiba_people.INSTITUTE_NAME}]
    assert fields["citation"]["datasetContact"] == [
        {"datasetContactName": "Centro Ficticio", "datasetContactEmail": "recuperado@example.test"},
        {"datasetContactName": "Laboratorio Ficticio", "datasetContactEmail": default_email},
    ]
    assert "contributor" not in fields["citation"]
    assert all(case.keys() == CURATION_FIELDS for case in curation)
    [author_case] = [case for case in curation if case["kind"] == "default_author"]
    assert (author_case["resource"], author_case["field"], author_case["value"]) == (
        record["name"], "authorName", "Cita sintética (2024).",
    )
    assert "autor por defecto" in author_case["note"]
    assert len([case for case in curation if case["kind"] == "contractor_association"]) == int(include_contractors)
    assert [case for case in curation if case["kind"] not in {"default_author", "contractor_association"}] == [
        {
            "resource": record["name"], "kind": "contact_email", "field": "contact",
            "value": "Centro Ficticio — recuperado@example.test (otro elemento del EML)", "note": "",
        },
        {
            "resource": record["name"], "kind": "contact_email", "field": "contact",
            "value": f"Laboratorio Ficticio — {default_email} (correo de la I2D)", "note": "",
        },
        {
            "resource": record["name"], "kind": "unknown_role", "field": "associatedParty",
            "value": "Entidad Fuera de Tabla — rol-ficticio", "note": "rol-ficticio",
        },
    ]


def test_integrates_author_review_with_all_curation_fields(
    mapeo_ceiba, open_record, curation_tables
):
    record = open_record({})
    rows = [
        {"resource": record["name"], "author_position": "2", "author_name": "Colectivo B"},
        {"resource": record["name"], "author_position": "1", "author_name": "Autora A",
         "status": "revisar", "note": "Revisar nombre sintético"},
    ]
    curation_tables["citation_authors_index"] = ceiba_people.authors_index(rows)

    fields, curation = mapeo_ceiba.dataverse_fields(
        record, curation_tables, identifiers={}, macro_index={}
    )

    assert fields["citation"]["author"] == [{"authorName": "Autora A"}, {"authorName": "Colectivo B"}]
    assert curation == [{
        "resource": record["name"], "kind": "author_review", "field": "authorName",
        "value": "Autora A | Colectivo B", "note": "Revisar nombre sintético",
    }]


@pytest.mark.parametrize(
    ("name_count", "code_count", "summary"),
    [
        pytest.param(1, 2, "1 nombre; 2 códigos", id="one-name-two-codes"),
        pytest.param(2, 1, "2 nombres; 1 código", id="two-names-one-code"),
        pytest.param(2, 2, "2 nombres; 2 códigos", id="two-names-two-codes"),
        pytest.param(1, 1, None, id="one-to-one"),
        pytest.param(1, 0, None, id="name-only"),
        pytest.param(2, 0, None, id="multiple-names-without-codes"),
        pytest.param(0, 1, None, id="code-only"),
        pytest.param(0, 2, None, id="multiple-codes-without-names"),
        pytest.param(0, 0, None, id="no-contracts"),
    ],
)
def test_records_contractor_association_only_when_ambiguous(
    mapeo_ceiba, open_record, curation_tables, name_count, code_count, summary
):
    people = [
        {"individualName": {"givenName": "Ágata", "surName": "Río-Seco"}, "positionName": "Contratista"},
        {"individualName": {"givenName": "Bruno", "surName": "Costa-Firme"}, "positionName": "Contratista"},
    ]
    names = ["Río-Seco, Ágata", "Costa-Firme, Bruno"][:name_count]
    codes = ["LAB-731PS", "LAB-842PS"][:code_count]
    record = open_record({"creator": people[:name_count]})
    biological = {}
    if names:
        biological["contratista"] = "AGATA RIO SECO"
    if codes:
        record["dataset"]["project"] = {"funding": f"Contrato sintético {codes[0]}."}
        biological["contrato_convenio"] = ", ".join(f"PS {code}" for code in codes)
    record["inventory"] = {"biologico": biological}
    curation_tables["citation_authors_index"] = ceiba_people.authors_index([
        {"resource": record["name"], "author_position": "1", "author_name": "Colectivo Ficticio"},
    ])

    fields, curation = mapeo_ceiba.dataverse_fields(
        record, curation_tables, identifiers={}, macro_index={}
    )

    institutional = fields["institutional"]
    if name_count == code_count == 1:
        assert institutional["contractor"] == [{"contractCode": codes[0], "contractorName": names[0]}]
    elif names or codes:
        assert institutional["contractor"] == (
            [{"contractCode": code} for code in codes] + [{"contractorName": name} for name in names]
        )
    else:
        assert "contractor" not in institutional

    if summary is None:
        assert curation == []
        return

    [case] = curation
    assert case.keys() == CURATION_FIELDS
    assert (case["resource"], case["kind"], case["field"], case["value"]) == (
        record["name"], "contractor_association", "contractor", summary,
    )
    assert "correspondencia inequívoca" in case["note"]
    assert "revisión" in case["note"]
    assert all(value not in case["note"] for value in [*names, *codes])
