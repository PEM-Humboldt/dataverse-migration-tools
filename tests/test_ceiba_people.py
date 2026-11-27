"""Pruebas unitarias de autores, personas y organizaciones de CEIBA."""

import pytest

from src.mapeo.ceiba import ceiba_people


def person(given, surname, *, affiliation="", email=""):
    entry = {"individualName": {"givenName": given, "surName": surname}}
    if affiliation:
        entry["organizationName"] = affiliation
    if email:
        entry["electronicMailAddress"] = email
    return entry


def role_row(source, target, *, role="", contributor_type=""):
    return {"party_type": source, "role": role, "target_field": target, "contributor_type": contributor_type}


def test_authors_follow_numeric_position_and_keep_table_names(record_ceiba):
    record = record_ceiba({"creator": person("Nombre", "Del EML", affiliation="Entidad ficticia")})
    rows = [
        {"resource": record["name"], "author_position": "10", "author_name": "Colectivo Ficticio"},
        {"resource": record["name"], "author_position": "2", "author_name": "B. Río-Seco"},
        {"resource": "otro-recurso-sintetico", "author_position": "1", "author_name": "Autor ajeno"},
        {"resource": record["name"], "author_position": "1", "author_name": "Ágata de Prueba"},
    ]
    curation = []

    authors = ceiba_people.map_authors(record, ceiba_people.authors_index(rows), curation)

    assert authors == [
        {"authorName": "Ágata de Prueba"},
        {"authorName": "B. Río-Seco"},
        {"authorName": "Colectivo Ficticio"},
    ]
    assert curation == []


def test_default_author_records_source_citation_when_table_has_no_match(record_ceiba):
    record = record_ceiba({})
    record["gbif"] = {"citation": {"#text": "Cita sintética (2024).", "@identifier": "cita-ficticia"}}
    curation = []

    authors = ceiba_people.map_authors(record, {}, curation)

    assert authors == [{"authorName": ceiba_people.INSTITUTE_NAME}]
    [case] = curation
    assert (case["resource"], case["kind"], case["field"], case["value"]) == (
        record["name"], "default_author", "authorName", "Cita sintética (2024).",
    )
    assert "autor por defecto" in case["note"]


def test_author_review_preserves_authors_and_creates_one_curation_entry(record_ceiba):
    record = record_ceiba({})
    rows = [
        {"resource": record["name"], "author_position": "2", "author_name": "Colectivo B", "status": "revisar"},
        {"resource": record["name"], "author_position": "1", "author_name": "Autora A",
         "status": "revisar", "note": "Verificar grafía sintética"},
    ]
    curation = []

    authors = ceiba_people.map_authors(record, ceiba_people.authors_index(rows), curation)

    assert authors == [{"authorName": "Autora A"}, {"authorName": "Colectivo B"}]
    assert curation == [{
        "resource": record["name"], "kind": "author_review", "field": "authorName",
        "value": "Autora A | Colectivo B", "note": "Verificar grafía sintética",
    }]


@pytest.mark.parametrize(
    ("element", "name", "is_person", "affiliation"),
    [
        pytest.param(person("Ágata", "Río-Seco"), "Río-Seco, Ágata", True, "", id="person"),
        pytest.param(
            person("Ágata", "Río-Seco", affiliation="Laboratorio Ficticio"),
            "Río-Seco, Ágata", True, "Laboratorio Ficticio", id="affiliated-person",
        ),
        pytest.param(
            {"organizationName": "Organización de Prueba"},
            "Organización de Prueba", False, "", id="organization",
        ),
        pytest.param(
            {"individualName": {"surName": "   CENTRO   DE-PRUEBA "}, "organizationName": "Céntro de Prueba"},
            "Céntro de Prueba", False, "", id="equivalent-surname-and-organization",
        ),
    ],
)
def test_party_classification_preserves_source_spelling(element, name, is_person, affiliation):
    result = ceiba_people.party(element, "creator")

    assert (result["name"], result["is_person"], result["affiliation"]) == (name, is_person, affiliation)


def test_comparison_key_normalizes_case_accents_whitespace_and_punctuation():
    variants = ("  ÁGATA\t RÍO-SECO ", "Ágata, Río Seco.", "agata rio seco")

    assert {ceiba_people.norm_key(name) for name in variants} == {"agata rio seco"}


def test_contact_keeps_its_own_email_over_an_earlier_appearance(record_ceiba):
    record = record_ceiba({
        "creator": person("Ágata", "Río-Seco", email="alterno@example.test"),
        "contact": person("Ágata", "Río-Seco", email="original@example.test"),
    })
    roles = [role_row("creator", "producer"), role_row("contact", "datasetContact")]

    fields, curation = ceiba_people.map_parties(record, roles)

    assert fields["datasetContact"] == [{
        "datasetContactName": "Río-Seco, Ágata", "datasetContactEmail": "original@example.test",
    }]
    assert curation == []


def test_contact_keeps_priority_and_affiliation_when_borrowing_associated_email(record_ceiba):
    record = record_ceiba({
        "contact": person("Ágata", "Río-Seco", affiliation="Primera afiliación"),
        "associatedParty": {
            **person("AGATA", "RIO SECO", affiliation="Otra afiliación", email="recuperado@example.test"),
            "role": "pointOfContact",
        },
    })
    roles = [
        role_row("contact", "datasetContact"),
        role_row("associatedParty", "datasetContact", role="pointOfContact"),
    ]

    fields, curation = ceiba_people.map_parties(record, roles)

    assert fields["datasetContact"] == [{
        "datasetContactName": "Río-Seco, Ágata",
        "datasetContactAffiliation": "Primera afiliación",
        "datasetContactEmail": "recuperado@example.test",
    }]
    assert curation == [{
        "resource": record["name"], "kind": "contact_email", "element": "contact", "role": "",
        "name": "Río-Seco, Ágata", "value": "recuperado@example.test (otro elemento del EML)",
    }]


def test_contact_uses_institutional_default_and_records_curation(record_ceiba):
    record = record_ceiba({"contact": {"organizationName": "Centro Ficticio"}})
    default_email = ceiba_people.DEFAULT_CONTACT_EMAIL

    fields, curation = ceiba_people.map_parties(record, [role_row("contact", "datasetContact")])

    assert fields["datasetContact"] == [{
        "datasetContactName": "Centro Ficticio", "datasetContactEmail": default_email,
    }]
    assert curation == [{
        "resource": record["name"], "kind": "contact_email", "element": "contact", "role": "",
        "name": "Centro Ficticio", "value": f"{default_email} (correo de la I2D)",
    }]


def test_contact_repairs_incomplete_institutional_domain(record_ceiba):
    record = record_ceiba({
        "contact": person("Ágata", "Río-Seco", email="fixture-sintetico@HUMBOLDT.ORG"),
    })

    fields, curation = ceiba_people.map_parties(record, [role_row("contact", "datasetContact")])

    assert fields["datasetContact"][0]["datasetContactEmail"] == "fixture-sintetico@humboldt.org.co"
    assert curation == []


@pytest.mark.parametrize(
    ("source", "role", "target"),
    [
        ("creator", "", "producer"),
        ("metadataProvider", "", "distributor"),
        ("associatedParty", "originator", "producer"),
        ("associatedParty", "distributor", "distributor"),
        ("personnel", "originator", "producer"),
        ("personnel", "distributor", "distributor"),
    ],
)
def test_maps_producers_and_distributors_from_synthetic_roles(record_ceiba, source, role, target):
    entry = person("Ágata", "Río-Seco", affiliation="Laboratorio Ficticio")
    if role:
        entry["role"] = role
    dataset = {"project": {"personnel": entry}} if source == "personnel" else {source: entry}

    fields, curation = ceiba_people.map_parties(
        record_ceiba(dataset), [role_row(source, target, role=role)]
    )

    assert fields == {target: [{
        f"{target}Name": "Río-Seco, Ágata", f"{target}Affiliation": "Laboratorio Ficticio",
    }]}
    assert curation == []


def test_party_deduplication_is_per_normalized_name_and_target(record_ceiba):
    record = record_ceiba({
        "creator": person("Ágata", "Río-Seco", affiliation="Primera afiliación de producción"),
        "metadataProvider": person("AGATA", "RIO SECO", affiliation="Primera afiliación de distribución"),
        "associatedParty": {
            **person("agata", "rio seco", affiliation="Afiliación posterior"), "role": "publisher",
        },
    })
    roles = [
        role_row("creator", "producer"),
        role_row("metadataProvider", "distributor"),
        role_row("associatedParty", "producer", role="publisher"),
        role_row("associatedParty", "distributor", role="publisher"),
    ]

    fields, curation = ceiba_people.map_parties(record, roles)

    assert fields == {
        "producer": [{"producerName": "Río-Seco, Ágata", "producerAffiliation": "Primera afiliación de producción"}],
        "distributor": [{
            "distributorName": "RIO SECO, AGATA", "distributorAffiliation": "Primera afiliación de distribución",
        }],
    }
    assert curation == []


@pytest.mark.parametrize("name", [ceiba_people.INSTITUTE_NAME, "IAvH"], ids=["institute-name", "abbreviation"])
def test_institute_producer_and_distributor_have_all_three_attributes(record_ceiba, name):
    record = record_ceiba({
        "creator": {"organizationName": name}, "metadataProvider": {"organizationName": name},
    })
    roles = [role_row("creator", "producer"), role_row("metadataProvider", "distributor")]

    fields, curation = ceiba_people.map_parties(record, roles)

    for target in ("producer", "distributor"):
        assert fields[target] == [{
            f"{target}Name": name,
            f"{target}Abbreviation": ceiba_people.INSTITUTE_ABBREVIATION,
            f"{target}URL": ceiba_people.INSTITUTE_URL,
            f"{target}LogoURL": ceiba_people.INSTITUTE_LOGO,
        }]
    assert curation == []


def test_institute_affiliation_does_not_add_organization_attributes_to_person(record_ceiba):
    entry = person("Ágata", "Río-Seco", affiliation=ceiba_people.INSTITUTE_NAME)
    record = record_ceiba({"creator": entry, "metadataProvider": entry})
    roles = [role_row("creator", "producer"), role_row("metadataProvider", "distributor")]

    fields, curation = ceiba_people.map_parties(record, roles)

    for target in ("producer", "distributor"):
        assert fields[target] == [{
            f"{target}Name": "Río-Seco, Ágata", f"{target}Affiliation": ceiba_people.INSTITUTE_NAME,
        }]
    assert curation == []


def test_personnel_gets_project_member_and_configured_role(record_ceiba):
    record = record_ceiba({"project": {"personnel": {
        **person("Ágata", "Río-Seco"), "role": "principalInvestigator",
    }}})
    roles = [
        role_row("personnel", "contributor", role="principalInvestigator", contributor_type="Project Member"),
        role_row("personnel", "contributor", role="principalInvestigator", contributor_type="Researcher"),
    ]

    fields, curation = ceiba_people.map_parties(record, roles)

    assert fields["contributor"] == [
        {"contributorType": "Project Member", "contributorName": "Río-Seco, Ágata"},
        {"contributorType": "Researcher", "contributorName": "Río-Seco, Ágata"},
    ]
    assert curation == []


def test_contributor_keeps_distinct_roles_and_deduplicates_each_type(record_ceiba):
    record = record_ceiba({"associatedParty": [
        {**person("Ágata", "Río-Seco"), "role": "custodian"},
        {**person("AGATA", "RIO SECO"), "role": "custodian"},
        {**person("Ágata", "Río-Seco"), "role": "editor"},
    ]})
    roles = [
        role_row("associatedParty", "contributor", role="custodian", contributor_type="Data Curator"),
        role_row("associatedParty", "contributor", role="editor", contributor_type="Editor"),
    ]

    fields, curation = ceiba_people.map_parties(record, roles)

    assert fields["contributor"] == [
        {"contributorType": "Data Curator", "contributorName": "Río-Seco, Ágata"},
        {"contributorType": "Editor", "contributorName": "Río-Seco, Ágata"},
    ]
    assert curation == []


def test_unknown_contributor_role_is_reported_without_mapping_it(record_ceiba):
    record = record_ceiba({
        "associatedParty": {**person("Ágata", "Río-Seco"), "role": "rol-ficticio"},
    })

    fields, curation = ceiba_people.map_parties(record, [])

    assert fields == {}
    assert curation == [{
        "resource": record["name"], "kind": "unknown_role", "element": "associatedParty",
        "role": "rol-ficticio", "name": "Río-Seco, Ágata", "value": "",
    }]
