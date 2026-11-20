# Avance del mapeo CEIBA → Dataverse

## Alcance

Este avance implementa y prueba campos de tratamiento directo del bloque `citation`:

- `title`: copia del título y normalización de espacios y saltos de línea.
- `dsDescription`: extracción de párrafos del resumen EML.
- `keyword`: palabras clave y tesauro cuando se encuentra documentado.
- `otherId`: identificador original del recurso CEIBA, cuando se suministra.

Las funciones originales de contactos y autores se conservan en el archivo por compatibilidad, **pero no se ejecutan en `construir_citation_basico`**. La integración de autores solicitada por Marius queda fuera de este avance. Tampoco se incorporan datos de personas.

## Archivos

- `src/mapeo/ceiba_to_dataverse.py`: funciones del mapeo.
- `src/mapeo/validar_mapeo.py`: revisión local de recursos y reporte de cobertura.
- `tests/test_mapeo_basico.py`: pruebas unitarias.

## Ejecución

Desde la raíz del repositorio, con el entorno virtual activo:

```bash
python -m pip install pytest
PYTHONPATH=src/mapeo python -m pytest -q tests/test_mapeo_basico.py
PYTHONPATH=src/mapeo python src/mapeo/validar_mapeo.py --origen data/ceiba/raw --salida data/ceiba/reporte_mapeo_local.json
```


## Registro de trabajo

| Actividad | Estado | Evidencia |
| --- | --- | --- |
| Revisar código previo | Realizado | `ceiba_to_dataverse.py` original |
| Normalizar título | Implementado | `test_titulo` |
| Mapeo de descripción | Conservado y probado | `test_descripcion` |
| Mapeo de palabras clave | Conservado y probado | `test_palabras_clave` |
| Identificador CEIBA | Conservado y probado | `test_identificador` |
| Excluir autores del nuevo constructor | Implementado | `test_sin_autores` |
| Validar con JSON reales | Pendiente | Reporte local |
