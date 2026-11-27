"""Pruebas sintéticas del mapeo geoespacial de CEIBA y de su curación."""

import pytest


@pytest.fixture
def map_geospatial(mapeo_ceiba, record_ceiba):
    """Mapea un dataset sintético y devuelve sus campos y filas de curación."""
    def map_dataset(dataset):
        curation = []
        fields = mapeo_ceiba.map_geospatial(record_ceiba(dataset), curation)
        return fields, curation

    return map_dataset


def geographic_dataset(geographic_coverage):
    return {"coverage": {"geographicCoverage": geographic_coverage}}


def source_box(coordinates):
    west, east, north, south = coordinates
    sides = {
        "westBoundingCoordinate": west,
        "eastBoundingCoordinate": east,
        "northBoundingCoordinate": north,
        "southBoundingCoordinate": south,
    }
    return {key: value for key, value in sides.items() if value is not None}


def mapped_box(coordinates):
    west, east, north, south = coordinates
    sides = {
        "westLongitude": west,
        "eastLongitude": east,
        "northLatitude": north,
        "southLatitude": south,
    }
    return {key: value for key, value in sides.items() if value is not None}


def curation_row(coordinates, note):
    return {
        "resource": "recurso-sintetico",
        "kind": "bounding_box",
        "field": "geographicBoundingBox",
        "value": " ".join(f"{side}={value}" for side, value in mapped_box(coordinates).items()),
        "note": note,
    }


def test_preserves_one_geographic_description(map_geospatial):
    fields, curation = map_geospatial(geographic_dataset({
        "geographicDescription": "Área sintética de muestreo.",
    }))

    assert fields == {"geographicCoverageDescription": "<p>Área sintética de muestreo.</p>"}
    assert curation == []


def test_combines_descriptions_in_order_and_omits_empty_values(map_geospatial):
    fields, curation = map_geospatial(geographic_dataset([
        {"geographicDescription": "Primera área."},
        {"geographicDescription": ""},
        {},
        {"geographicDescription": {"#text": " \t\n "}},
        {"geographicDescription": {"#text": "Segunda área."}},
    ]))

    assert fields == {"geographicCoverageDescription": "<p>Primera área.</p><p>Segunda área.</p>"}
    assert curation == []


def test_escapes_special_characters_in_geographic_description(map_geospatial):
    fields, curation = map_geospatial(geographic_dataset({
        "geographicDescription": 'Flora & fauna en zonas < A y > B, sector "C".',
    }))

    assert fields == {
        "geographicCoverageDescription": '<p>Flora &amp; fauna en zonas &lt; A y &gt; B, sector "C".</p>',
    }
    assert curation == []


@pytest.mark.parametrize(
    "coordinates",
    [
        pytest.param(("-72.50", "-70.25", "16.40", "12.25"), id="negative-longitudes"),
        pytest.param(("24.20", "29.75", "-10.5", "-14.25"), id="positive-longitudes-preserved"),
        pytest.param(("-15", "42", "4", "-21"), id="crosses-prime-meridian"),
        pytest.param(("-180", "180", "90", "-90"), id="global-limits"),
        pytest.param(("0", "34", "12", "0"), id="zero-west-and-south"),
        pytest.param(("-34", "0", "0", "-12"), id="zero-east-and-north"),
        pytest.param(("50", "55", "24", "19"), id="possible-swapped-axes-preserved"),
    ],
)
def test_maps_valid_box_sides_without_changing_coordinates(map_geospatial, coordinates):
    fields, curation = map_geospatial(geographic_dataset({
        "boundingCoordinates": source_box(coordinates),
    }))

    assert fields == {"geographicBoundingBox": [mapped_box(coordinates)]}
    assert curation == []


def test_preserves_coordinate_text_after_whitespace_normalization(map_geospatial):
    fields, curation = map_geospatial(geographic_dataset({
        "boundingCoordinates": {
            "westBoundingCoordinate": {"#text": " \n-1.2500\t "},
            "eastBoundingCoordinate": " +02.500 ",
            "northBoundingCoordinate": " 1.5e1 ",
            "southBoundingCoordinate": " -0.000 ",
        },
    }))

    assert fields == {"geographicBoundingBox": [{
        "westLongitude": "-1.2500",
        "eastLongitude": "+02.500",
        "northLatitude": "1.5e1",
        "southLatitude": "-0.000",
    }]}
    assert curation == []


@pytest.mark.parametrize(
    "coordinates",
    [
        pytest.param((None, "-12", "40", "22"), id="missing-west"),
        pytest.param(("-36", None, "40", "22"), id="missing-east"),
        pytest.param(("-36", "-12", None, "22"), id="missing-north"),
        pytest.param(("-36", "-12", "40", None), id="missing-south"),
    ],
)
def test_records_only_available_coordinates_when_one_side_is_missing(map_geospatial, coordinates):
    fields, curation = map_geospatial(geographic_dataset({
        "boundingCoordinates": source_box(coordinates),
    }))

    assert fields == {}
    assert curation == [curation_row(coordinates, "faltan lados")]


@pytest.mark.parametrize(
    ("coordinates", "reason"),
    [
        pytest.param(("-72", "no numérico", "16", "8"), "un lado no es un número", id="non-numeric"),
        pytest.param(("-180.1", "24", "16", "8"), "fuera de rango", id="west-below-minimum"),
        pytest.param(("180.1", "24", "16", "8"), "fuera de rango", id="west-above-maximum"),
        pytest.param(("-24", "-180.1", "16", "8"), "fuera de rango", id="east-below-minimum"),
        pytest.param(("-24", "180.1", "16", "8"), "fuera de rango", id="east-above-maximum"),
        pytest.param(("-24", "24", "-90.1", "8"), "fuera de rango", id="north-below-minimum"),
        pytest.param(("-24", "24", "90.1", "8"), "fuera de rango", id="north-above-maximum"),
        pytest.param(("-24", "24", "16", "-90.1"), "fuera de rango", id="south-below-minimum"),
        pytest.param(("-24", "24", "16", "90.1"), "fuera de rango", id="south-above-maximum"),
        pytest.param(("-24", "NaN", "16", "8"), "fuera de rango", id="nan"),
        pytest.param(("-24", "24", "inf", "8"), "fuera de rango", id="positive-infinity"),
        pytest.param(("-inf", "24", "16", "8"), "fuera de rango", id="negative-infinity"),
        pytest.param(("-12", "-36", "40", "22"), "oeste ≥ este", id="inverted-longitudes"),
        pytest.param(("-36", "-12", "22", "40"), "sur ≥ norte", id="inverted-latitudes"),
        pytest.param(("-12", "-36", "22", "40"), "oeste ≥ este; sur ≥ norte", id="both-axes-inverted"),
        pytest.param(("-36.00", "-36", "40", "22"), "oeste ≥ este", id="zero-width"),
        pytest.param(("-36", "-12", "22.00", "22"), "sur ≥ norte", id="zero-height"),
        pytest.param(("-36", "-36", "22", "22"), "oeste ≥ este; sur ≥ norte", id="point"),
    ],
)
def test_rejects_invalid_boxes_without_losing_description(map_geospatial, coordinates, reason):
    fields, curation = map_geospatial(geographic_dataset({
        "geographicDescription": "Descripción conservada.",
        "boundingCoordinates": source_box(coordinates),
    }))

    assert fields == {"geographicCoverageDescription": "<p>Descripción conservada.</p>"}
    assert curation == [curation_row(coordinates, reason)]


FIRST_VALID_BOX = ("25", "34", "48", "34")
SECOND_VALID_BOX = ("-48", "-35", "-12", "-19")
ZERO_WIDTH_BOX = ("33", "33", "18", "12")
INVERTED_LATITUDE_BOX = ("-70", "-55", "-18", "-10")


@pytest.mark.parametrize(
    ("coordinates", "valid_boxes", "rejected_boxes"),
    [
        pytest.param(
            (FIRST_VALID_BOX, SECOND_VALID_BOX),
            (FIRST_VALID_BOX, SECOND_VALID_BOX),
            (),
            id="two-valid-boxes-in-source-order",
        ),
        pytest.param(
            (ZERO_WIDTH_BOX, SECOND_VALID_BOX),
            (SECOND_VALID_BOX,),
            ((ZERO_WIDTH_BOX, "oeste ≥ este"),),
            id="one-invalid-and-one-valid",
        ),
        pytest.param(
            (ZERO_WIDTH_BOX, INVERTED_LATITUDE_BOX),
            (),
            ((ZERO_WIDTH_BOX, "oeste ≥ este"), (INVERTED_LATITUDE_BOX, "sur ≥ norte")),
            id="two-invalid-boxes",
        ),
    ],
)
def test_maps_multiple_coverages_in_source_order(map_geospatial, coordinates, valid_boxes, rejected_boxes):
    fields, curation = map_geospatial(geographic_dataset([
        {"geographicDescription": "Primera área.", "boundingCoordinates": source_box(coordinates[0])},
        {"geographicDescription": "Segunda área.", "boundingCoordinates": source_box(coordinates[1])},
    ]))

    assert fields["geographicCoverageDescription"] == "<p>Primera área.</p><p>Segunda área.</p>"
    if valid_boxes:
        assert fields["geographicBoundingBox"] == [mapped_box(box) for box in valid_boxes]
    else:
        assert "geographicBoundingBox" not in fields
    assert curation == [curation_row(box, note) for box, note in rejected_boxes]


@pytest.mark.parametrize(
    "dataset",
    [
        pytest.param({}, id="no-coverage"),
        pytest.param({"coverage": {"temporalCoverage": {}}}, id="no-geographic-coverage"),
        pytest.param(geographic_dataset({"geographicDescription": " \t "}), id="blank-description"),
    ],
)
def test_omits_geospatial_fields_without_geographic_information(map_geospatial, dataset):
    fields, curation = map_geospatial(dataset)

    assert fields == {}
    assert curation == []


@pytest.mark.parametrize(
    "coordinate_element",
    [
        pytest.param({}, id="no-bounding-coordinates"),
        pytest.param({"boundingCoordinates": {}}, id="empty-bounding-coordinates"),
        pytest.param(
            {"boundingCoordinates": source_box(("", " ", "\t", "\n"))},
            id="all-coordinate-values-blank",
        ),
    ],
)
def test_omits_absent_or_completely_empty_boxes_without_curation(map_geospatial, coordinate_element):
    """Un rectángulo sin ningún lado informado se omite sin registrar curación."""
    fields, curation = map_geospatial(geographic_dataset({
        "geographicDescription": "Área sin coordenadas.",
        **coordinate_element,
    }))

    assert fields == {"geographicCoverageDescription": "<p>Área sin coordenadas.</p>"}
    assert curation == []


def test_does_not_derive_other_geographic_fields(map_geospatial):
    fields, curation = map_geospatial(geographic_dataset({
        "geographicDescription": "Ciudad, estado y país ficticios a una altitud de 100 a 200 m.",
        "boundingCoordinates": {
            **source_box(FIRST_VALID_BOX),
            "boundingAltitudes": {"altitudeMinimum": "100", "altitudeMaximum": "200", "altitudeUnits": "m"},
        },
    }))

    assert fields.keys().isdisjoint({
        "country", "state", "city", "otherGeographicCoverage", "geographicUnit",
        "altitudeRange", "minimumAltitude", "maximumAltitude", "wkt",
    })
    assert fields["geographicBoundingBox"] == [mapped_box(FIRST_VALID_BOX)]
    assert curation == []
