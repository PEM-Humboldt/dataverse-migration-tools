import logging
import sys
from types import ModuleType, SimpleNamespace

import pytest


@pytest.fixture
def record_ceiba():
    """Construye un record sintético para probar el mapeo en memoria."""
    def crear(dataset):
        return {
            "name": "recurso-sintetico",
            "version": "1",
            "eml_version": "2.1.1",
            "package_id": "",
            "dataset": {"title": "Recurso sintético", **dataset},
            "gbif": {},
            "resource": {"status": "PUBLIC"},
            "ipt_status": "PUBLIC",
            "inventory": {},
        }

    return crear


@pytest.fixture
def eml_ceiba():
    """Representa en memoria la entrada EML serializada por la ingesta."""
    def crear(dataset):
        return {
            "{eml://ecoinformatics.org/eml-2.1.1}eml": {
                "@packageId": "urn:example:recurso-sintetico:1",
                "dataset": {"title": "Recurso sintético", **dataset},
            },
        }

    return crear


@pytest.fixture
def mapeo_ceiba(monkeypatch):
    # El logger de producción abre un archivo bajo src/logs al importarse.
    logger_modulo = ModuleType("src.utilitarios.logger")
    logger_modulo.logger = logging.getLogger("tests.ceiba")
    with monkeypatch.context() as entorno:
        entorno.setitem(sys.modules, "src.utilitarios.logger", logger_modulo)
        from src.mapeo.ceiba import ceiba_fields

    return ceiba_fields


@pytest.fixture
def reconstruir_dataverse(monkeypatch, tmp_path):
    # El reconstructor instancia Config al importarse. La prueba aporta su esquema en memoria.
    config_modulo = ModuleType("src.config")
    config_modulo.Config = lambda: SimpleNamespace(tsv_files=tmp_path)
    with monkeypatch.context() as entorno:
        entorno.setitem(sys.modules, "src.config", config_modulo)
        from src.mapeo.reconstruct_mapping import unflatten_dataset

    return unflatten_dataset
