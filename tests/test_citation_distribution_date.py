"""Validación calendárica y mapeo de dataset/pubDate a citation.distributionDate.

Las fechas parciales válidas y el rechazo de fechas imposibles son criterios
técnicos provisionales, pendientes de contrastar con la tabla de correspondencia.
"""

import pytest


@pytest.mark.parametrize(
    "fecha",
    [
        "2017-05-16",
        "2020-12-31",
        "2024-01-15",
        "2024-02-29",
        "2000-02-29",
        "2026-12-31",
    ],
)
def test_fechas_completas_validas(mapeo_ceiba, fecha):
    assert mapeo_ceiba.iso_date(fecha) == fecha


@pytest.mark.parametrize(
    "fecha",
    ["2017", "2017-05", "2024", "2024-02"],
)
def test_fechas_parciales_validas(mapeo_ceiba, fecha):
    assert mapeo_ceiba.iso_date(fecha) == fecha


@pytest.mark.parametrize(
    "fecha",
    [
        "2017-02-30",
        "2017-13-01",
        "2017-00-10",
        "2023-02-29",
        "1900-02-29",
        "2024-02-30",
        "2024-04-31",
        "2024-13-01",
        "2024-00-15",
        "2024-01-00",
        "2024-13",
        "2024-00",
    ],
)
def test_fechas_calendaricas_invalidas(mapeo_ceiba, fecha):
    assert mapeo_ceiba.iso_date(fecha) is None


@pytest.mark.parametrize(
    ("fecha_hora", "fecha_esperada"),
    [
        ("2024-01-15T10:30:00Z", "2024-01-15"),
        ("2024-01-15T10:30:00-05:00", "2024-01-15"),
    ],
)
def test_normaliza_fecha_y_hora(mapeo_ceiba, fecha_hora, fecha_esperada):
    assert mapeo_ceiba.iso_date(fecha_hora) == fecha_esperada


@pytest.mark.parametrize(
    "valor",
    [
        None,
        pytest.param("", id="cadena-vacia"),
        pytest.param(" \t\n", id="solo-espacios"),
        "NA",
        "N/A",
        "sin fecha registrada",
    ],
)
def test_valores_ausentes_o_invalidos(mapeo_ceiba, valor):
    assert mapeo_ceiba.iso_date(valor) is None


def test_distribution_date_intermedio(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"pubDate": "2017-05-16"})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    assert citation["distributionDate"] == "2017-05-16"


def test_distribution_date_ausente(mapeo_ceiba, record_ceiba):
    citation = mapeo_ceiba.map_citation(record_ceiba({}), tables={}, identifiers={})
    assert "distributionDate" not in citation


def test_distribution_date_parcial(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"pubDate": "2017"})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    assert citation["distributionDate"] == "2017"


def test_distribution_date_invalida_omitida(mapeo_ceiba, record_ceiba):
    record = record_ceiba({"pubDate": "2024-02-30"})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    assert "distributionDate" not in citation, f"distributionDate={citation['distributionDate']!r}"


def test_distribution_date_dataverse(mapeo_ceiba, record_ceiba, reconstruir_dataverse):
    record = record_ceiba({"pubDate": "2017-05-16"})
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    esquema = {
        "title": {"typeClass": "primitive", "multiple": False},
        "subject": {"typeClass": "controlledVocabulary", "multiple": True},
        "distributionDate": {"typeClass": "primitive", "multiple": False},
    }

    final = reconstruir_dataverse({"citation": citation}, esquema)
    campo = next(c for c in final["citation"]["fields"] if c["typeName"] == "distributionDate")
    assert campo == {
        "typeName": "distributionDate",
        "typeClass": "primitive",
        "multiple": False,
        "value": "2017-05-16",
    }


def test_distribution_date_eml_sintetico(mapeo_ceiba, eml_ceiba):
    from src.mapeo.ceiba.ceiba_source import read_record

    datos = eml_ceiba({"pubDate": {"#text": "2017-05-16"}})
    record = read_record("recurso-sintetico", datos, latest_version="1")

    assert record is not None
    citation = mapeo_ceiba.map_citation(record, tables={}, identifiers={})
    assert citation["distributionDate"] == "2017-05-16"


@pytest.mark.parametrize(
    "fecha",
    ["0000", "0000-01", "0000-01-01", "2024-02-30T10:30:00Z"],
)
def test_rechaza_anio_cero_y_fecha_imposible_con_hora(mapeo_ceiba, fecha):
    assert mapeo_ceiba.iso_date(fecha) is None


def test_fecha_hora_conserva_el_dia_escrito(mapeo_ceiba):
    assert mapeo_ceiba.iso_date("2024-01-01T23:30:00-05:00") == "2024-01-01"


@pytest.mark.parametrize(
    ("fecha", "esperada"),
    [
        ("2024-02-29", "2024-02-29"),
        ("2024-02", "2024-02"),
        ("2024-02-30", None),
        (None, None),
    ],
)
def test_ds_description_date(mapeo_ceiba, fecha, esperada):
    dataset = {"abstract": {"para": "Descripción sintética."}, "pubDate": fecha}

    [descripcion] = mapeo_ceiba.map_description(dataset)

    assert descripcion["dsDescriptionValue"]
    if esperada is None:
        assert "dsDescriptionDate" not in descripcion
    else:
        assert descripcion["dsDescriptionDate"] == esperada


@pytest.mark.parametrize(
    ("fecha", "esperada", "curacion_esperada"),
    [
        ("2024-02-29", "2024-02-29", []),
        ("2024-02-30", None, [("date", "simpleCalendarDate", "2024-02-30")]),
        (None, None, []),
    ],
)
def test_cobertura_temporal_fecha_unica(
    mapeo_ceiba, record_ceiba, fecha, esperada, curacion_esperada
):
    cobertura = {"temporalCoverage": {"singleDateTime": {"calendarDate": fecha}}}
    curacion = []

    resultado = mapeo_ceiba.map_temporal(record_ceiba({"coverage": cobertura}), curacion)

    if esperada is None:
        assert resultado == []
    else:
        assert resultado == [{"temporalCoverageType": "Date", "simpleCalendarDate": esperada}]
    assert [(caso["kind"], caso["field"], caso["value"]) for caso in curacion] == curacion_esperada


@pytest.mark.parametrize(
    ("inicio", "fin", "limites_esperados", "curacion_esperada"),
    [
        ("2024-02", "2024-03-01", {"initialCalendarDate": "2024-02", "finalCalendarDate": "2024-03-01"}, []),
        (
            "2024-02-30",
            "2024-03-01",
            {"finalCalendarDate": "2024-03-01"},
            [("date", "initialCalendarDate", "2024-02-30")],
        ),
        (
            "2024-02-29",
            "2024-04-31",
            {"initialCalendarDate": "2024-02-29"},
            [("date", "finalCalendarDate", "2024-04-31")],
        ),
        (
            "0000-01-01",
            "2024-04-31",
            {},
            [("date", "initialCalendarDate", "0000-01-01"), ("date", "finalCalendarDate", "2024-04-31")],
        ),
    ],
)
def test_cobertura_temporal_rango(
    mapeo_ceiba, record_ceiba, inicio, fin, limites_esperados, curacion_esperada
):
    rango = {"beginDate": {"calendarDate": inicio}, "endDate": {"calendarDate": fin}}
    cobertura = {"temporalCoverage": {"rangeOfDates": rango}}
    curacion = []

    resultado = mapeo_ceiba.map_temporal(record_ceiba({"coverage": cobertura}), curacion)

    if limites_esperados:
        assert resultado == [{"temporalCoverageType": "Date Range", **limites_esperados}]
    else:
        assert resultado == []
    assert [(caso["kind"], caso["field"], caso["value"]) for caso in curacion] == curacion_esperada


@pytest.mark.parametrize(
    ("fecha", "esperada"),
    [
        ("2024-02-29", "2024-02-29"),
        ("2024-02", None),
        ("2024-02-30", None),
        (None, None),
    ],
)
def test_restricted_until(mapeo_ceiba, record_ceiba, fecha, esperada):
    record = record_ceiba({"intellectualRights": "Restringido temporalmente"})
    record["inventory"] = {
        "biologico": {"fecha_liberacion": fecha, "objeto_restriccion": "Motivo sintético"}
    }
    tablas = {
        "restriction_reasons": [
            {"restriction_text": "Motivo sintético", "reason_code": "motivo-sintetico", "validated": "sí"}
        ]
    }
    curacion = []

    acceso = mapeo_ceiba.map_access(record, tablas, curacion)

    if esperada is None:
        assert "restrictedUntil" not in acceso
        assert [(caso["kind"], caso["field"], caso["value"]) for caso in curacion] == [
            ("restricted_until", "restrictedUntil", fecha or "")
        ]
    else:
        assert acceso["restrictedUntil"] == esperada
        assert curacion == []
