"""Pruebas sintéticas del mapeo de contratistas y códigos de contratos."""

import pytest

from src.mapeo.ceiba.ceiba_people import eml_contractors


def contractor(given, surname, position="Contratista"):
    return {
        "individualName": {"givenName": given, "surName": surname},
        "positionName": position,
    }


@pytest.mark.parametrize(
    ("position", "names"),
    [
        ("Contratista", ["Río-Seco, Ágata"]),
        ("Contratosta", ["Río-Seco, Ágata"]),
        ("Supervisor de contratistas", []),
        ("Consultor", []),
    ],
)
def test_eml_contractors_selects_people_by_position(position, names):
    dataset = {"contact": contractor("Ágata", "Río-Seco", position)}

    assert eml_contractors(dataset) == names


def test_eml_contractors_deduplicates_across_sources_and_keeps_first_spelling():
    dataset = {
        "creator": contractor("Ágata", "Río-Seco"),
        "associatedParty": contractor("AGATA", "RIO SECO"),
        "project": {"personnel": [
            contractor("Ágata", "Río Seco"), contractor("Bruno", "Costa-Firme", "Contratosta"),
        ]},
    }

    assert eml_contractors(dataset) == ["Río-Seco, Ágata", "Costa-Firme, Bruno"]


@pytest.mark.parametrize(
    ("funding", "code"),
    [
        ("Financiación por el contrato sintético LAB-731 PS.", "LAB-731PS"),
        ("Financiación por el contrato sintético 79-81-904-667.", "79-81-904-667"),
    ],
    ids=["service-contract", "numeric-contract"],
)
def test_extracts_codes_without_names_from_eml_funding(mapeo_ceiba, record_ceiba, funding, code):
    record = record_ceiba({"project": {"funding": {"para": funding}}})

    assert mapeo_ceiba.map_contractors(record) == [{"contractCode": code}]


def test_merges_eml_and_inventory_codes_without_duplicates(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"project": {"funding": {"para": [
        "Contrato LAB-731 PS.", "Reiteración del código LAB-731PS.",
    ]}}})
    record["inventory"] = {"biologico": {
        "contrato_convenio": "LAB-731PS | N/A; LAB-842PS | 79-81-904-667",
    }}

    assert mapeo_ceiba.map_contractors(record) == [
        {"contractCode": "LAB-731PS"},
        {"contractCode": "LAB-842PS"},
        {"contractCode": "79-81-904-667"},
    ]


def test_appends_distinct_inventory_name_to_eml_names(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"contact": contractor("Ágata", "Río-Seco")})
    record["inventory"] = {"biologico": {"contratista": "Bruno Costa-Firme"}}

    assert mapeo_ceiba.map_contractors(record) == [
        {"contractorName": "Río-Seco, Ágata"},
        {"contractorName": "Bruno Costa-Firme"},
    ]


def test_keeps_eml_spelling_when_inventory_name_matches(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"creator": contractor("Ágata", "Río-Seco")})
    record["inventory"] = {"biologico": {"contratista": "AGATA RIO SECO"}}

    assert mapeo_ceiba.map_contractors(record) == [{"contractorName": "Río-Seco, Ágata"}]


def test_pairs_single_name_and_single_code(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"project": {"funding": "Contrato LAB-731PS."}})
    record["inventory"] = {"biologico": {"contratista": "Bruno Costa-Firme"}}

    assert mapeo_ceiba.map_contractors(record) == [{
        "contractCode": "LAB-731PS", "contractorName": "Bruno Costa-Firme",
    }]


@pytest.mark.parametrize(
    ("name_count", "code_count"),
    [(1, 2), (2, 1), (2, 2)],
    ids=["one-name-many-codes", "many-names-one-code", "many-names-and-codes"],
)
def test_keeps_ambiguous_names_and_codes_in_separate_compounds(
    mapeo_ceiba, record_ceiba, name_count, code_count
):
    people = [contractor("Ágata", "Río-Seco"), contractor("Bruno", "Costa-Firme")]
    names = ["Río-Seco, Ágata", "Costa-Firme, Bruno"][:name_count]
    codes = ["LAB-731PS", "LAB-842PS"][:code_count]
    record = record_ceiba({"creator": people[:name_count], "project": {"funding": " ".join(codes)}})

    assert mapeo_ceiba.map_contractors(record) == (
        [{"contractCode": code} for code in codes] + [{"contractorName": name} for name in names]
    )


def test_keeps_inventory_name_without_code(mapeo_ceiba, record_ceiba):
    record = record_ceiba({})
    record["inventory"] = {"biologico": {"contratista": "Bruno Costa-Firme"}}

    assert mapeo_ceiba.map_contractors(record) == [{"contractorName": "Bruno Costa-Firme"}]


def test_institutional_block_omits_empty_contractor(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"intellectualRights": "Libre a nivel interno y externo"})
    curation = []

    assert mapeo_ceiba.map_contractors(record) == []
    block = mapeo_ceiba.map_institutional(record, tables={}, macro_index={}, curation=curation)

    assert "contractor" not in block
    assert curation == []


@pytest.mark.parametrize(
    "inventory",
    [None, {}, {"biologico": None}],
    ids=["null-inventory", "missing-biological-inventory", "null-biological-inventory"],
)
def test_keeps_eml_contractors_when_biological_inventory_is_absent(
    mapeo_ceiba, record_ceiba, inventory
):
    record = record_ceiba({
        "contact": contractor("Ágata", "Río-Seco"),
        "project": {"funding": "Contrato LAB-731PS."},
    })
    record["inventory"] = inventory

    assert mapeo_ceiba.map_contractors(record) == [{
        "contractCode": "LAB-731PS", "contractorName": "Río-Seco, Ágata",
    }]


@pytest.mark.parametrize("source", ["funding", "inventory"])
def test_characterizes_per_h26_lowercase_ps_suffix(mapeo_ceiba, record_ceiba, source):
    """Registra el tratamiento actual del sufijo ps en ambas fuentes."""
    record = record_ceiba({})
    if source == "funding":
        record["dataset"]["project"] = {"funding": "Contratos LAB-731ps y LAB-842PS."}
    else:
        record["inventory"] = {"biologico": {"contrato_convenio": "LAB-731ps | LAB-842PS"}}

    assert mapeo_ceiba.map_contractors(record) == [{"contractCode": "LAB-842PS"}]


def test_characterizes_per_h28_code_embedded_in_inventory_text(mapeo_ceiba, record_ceiba):
    """Registra que el código se reconoce al ocupar una entrada completa de la celda."""
    record = record_ceiba({})
    record["inventory"] = {"biologico": {
        "contrato_convenio": "Contrato sintético LAB-731PS vigente | LAB-842PS",
    }}

    assert mapeo_ceiba.map_contractors(record) == [{"contractCode": "LAB-842PS"}]


@pytest.mark.parametrize(
    ("cell", "codes"),
    [
        pytest.param(
            "79-81-904-667, 79-81-905-668",
            ["79-81-904-667", "79-81-905-668"],
            id="numeric-comma-list",
        ),
        pytest.param("LAB-731 PS, LAB-842PS", ["LAB-731PS", "LAB-842PS"], id="ps-comma-list"),
        pytest.param("PS   LAB-731PS", ["LAB-731PS"], id="ps-prefix"),
        pytest.param("PS 79-81-904-667", ["79-81-904-667"], id="numeric-code-with-ps-prefix"),
    ],
)
def test_accepts_complete_inventory_contract_codes(mapeo_ceiba, record_ceiba, cell, codes):
    record = record_ceiba({})
    record["inventory"] = {"biologico": {"contrato_convenio": cell}}

    assert mapeo_ceiba.map_contractors(record) == [{"contractCode": code} for code in codes]


def test_deduplicates_mixed_separators_and_keeps_source_order(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"project": {"funding": "Contratos sintéticos LAB-842PS y LAB-953PS."}})
    record["inventory"] = {"biologico": {
        "contrato_convenio": " LAB-731 PS ,  LAB-842PS ; PS LAB-731PS | 79-81-904-667, LAB-764PS ",
    }}

    assert mapeo_ceiba.map_contractors(record) == [
        {"contractCode": "LAB-842PS"},
        {"contractCode": "LAB-953PS"},
        {"contractCode": "LAB-731PS"},
        {"contractCode": "79-81-904-667"},
        {"contractCode": "LAB-764PS"},
    ]


def test_keeps_residual_agreements_and_excludes_recognized_inventory_codes_from_funding(
    mapeo_ceiba, record_ceiba
):
    record = record_ceiba({
        "intellectualRights": "Libre a nivel interno y externo",
        "project": {"funding": "Financiación sintética del EML."},
    })
    record["inventory"] = {"biologico": {
        "contrato_convenio": (
            "LAB-731PS, LAB-842PS | PS LAB-953PS; CONVENIO-SINTETICO "
            "| Nota, alcance adicional | LAB-764PS, Anexo de prueba | LAB-985FN"
        ),
        "proyecto_macro": "MACRO-SINTETICO",
    }}
    macro_index = {"MACRO-SINTETICO": {"suscrito": "Entidad Ficticia"}}
    curation = []

    fields = mapeo_ceiba.map_institutional(record, {}, macro_index, curation)

    assert fields["contractor"] == [
        {"contractCode": "LAB-731PS"}, {"contractCode": "LAB-842PS"}, {"contractCode": "LAB-953PS"},
    ]
    [scientific_project, macro_project] = fields["project"]
    assert scientific_project["projectFunding"] == "<p>Financiación sintética del EML.</p>"
    assert macro_project["projectFunding"] == (
        "<p>Convenio: MACRO-SINTETICO — Entidad Ficticia</p>"
        "<p>Convenio: CONVENIO-SINTETICO</p>"
        "<p>Convenio: Nota, alcance adicional</p>"
        "<p>Convenio: LAB-764PS, Anexo de prueba</p>"
    )
    [case] = curation
    assert (case["resource"], case["kind"], case["field"], case["value"]) == (
        record["name"], "contract_code", "contractCode", "LAB-985FN",
    )
