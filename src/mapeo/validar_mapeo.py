"""Prueba local del mapeo CEIBA sin escribir sobre los recursos originales."""
import argparse
import json
from collections import Counter
from pathlib import Path

from ceiba_to_dataverse import construir_citation_basico, extraer_dataset


def ejecutar(origen, salida):
    archivos = sorted(origen.rglob('resource_metadata.json'))
    conteo = Counter()
    ejemplos = []
    for archivo in archivos:
        try:
            with archivo.open(encoding='utf-8') as f:
                recurso = json.load(f)
            dataset = extraer_dataset(recurso)
            identificador = archivo.parent.name
            resultado = construir_citation_basico(dataset, identificador)
            campos = resultado['citation']['fields']
            conteo['procesados'] += 1
            for campo in campos:
                conteo[f"campo_{campo['typeName']}"] += 1
            if len(ejemplos) < 5:
                ejemplos.append({'recurso': identificador, 'resultado': resultado})
        except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
            conteo['errores'] += 1
            if len(ejemplos) < 5:
                ejemplos.append({'archivo': str(archivo), 'error': str(error)})
    reporte = {'archivos_encontrados': len(archivos),
               'conteos': dict(conteo), 'ejemplos': ejemplos,
               'nota': 'Prueba local. No se envían metadatos a Dataverse.'}
    salida.parent.mkdir(parents=True, exist_ok=True)
    salida.write_text(json.dumps(reporte, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'archivos': len(archivos), 'conteos': dict(conteo)},
                     ensure_ascii=False, indent=2))
    print(f'Reporte: {salida}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--origen', type=Path, default=Path('data/ceiba/raw'))
    parser.add_argument('--salida', type=Path, default=Path('data/ceiba/reporte_mapeo_local.json'))
    args = parser.parse_args()
    ejecutar(args.origen, args.salida)
