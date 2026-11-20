"""Pruebas del avance de mapeo: campos directos y casos incompletos."""
import pytest
from src.mapeo.ceiba_to_dataverse import (
    construir_citation_basico, extraer_dataset, mapear_titulo,
    mapear_descripcion, mapear_palabras_clave, normalizar_texto,
    mapear_identificador_ceiba,
)


def test_normalizacion():
    assert normalizar_texto('  Un  título\n con\t espacios ') == 'Un título con espacios'


def test_titulo():
    assert mapear_titulo({'#text': '  Prueba\n  CEIBA  '})['value'] == 'Prueba CEIBA'
    assert mapear_titulo(None) is None


def test_descripcion():
    resultado = mapear_descripcion({'para': ['Uno', {'#text': 'Dos'}]})
    assert resultado[0]['dsDescriptionValue']['value'] == 'Uno\n\nDos'


def test_palabras_clave():
    resultado = mapear_palabras_clave({'keyword': ['bosque', 'fauna'], 'keywordThesaurus': 'N/A'})
    assert len(resultado) == 2
    assert 'keywordVocabulary' not in resultado[0]


def test_identificador():
    assert mapear_identificador_ceiba(' ABC ')[0]['otherIdValue']['value'] == 'ABC'
    assert mapear_identificador_ceiba('NO APLICA') == []


def test_sin_autores():
    dataset = {'title': 'Mi recurso', 'creator': [{'individualName': {'givenName': 'Ana'}}],
               'contact': [{'organizationName': 'Entidad'}]}
    campos = construir_citation_basico(dataset)['citation']['fields']
    assert [campo['typeName'] for campo in campos] == ['title']


def test_dataset_directo():
    assert extraer_dataset({'dataset': {'title': 'A'}})['title'] == 'A'


def test_dataset_eml():
    assert extraer_dataset({'eml': {'dataset': {'title': 'B'}}})['title'] == 'B'


def test_dataset_desconocido():
    with pytest.raises(ValueError):
        extraer_dataset({'resource_metadata': {'dataset': {'title': 'C'}}})
