# Dataverse Migration Tools

Este repositorio recopila los scripts para la migración de datos para la integración de los catálogos del Instituto en una instancia de Dataverse 6.10.

## Estructura del repositorio
El repositorio se estructura de la siguiente manera:
- **Ingesta:** Scripts necesarios para la conexión a los catálogos originales y la lectura e importación de sus datos.
- **Formateo:** Scripts para la recepción de los datos en sus formatos originales, simplificación de estructuras y su transformación a diccionarios de python.
- **Mapeo:**  Scripts para mapear los metadatos originales de cada catálogo a los metadatos establecidos para la instancia de de dataverse 6.10.1.
- **Operaciones:** Scripts de creación de los datasets, carga de sus metadatos en formato JSON, archivos y configuraciones.
- **Utilitarios:** Funciones y módulos auxiliares reutilizables.
- **Logs:** Directorio para el almacenamiento de logs.

## Pre-requisitos

### Ambiente virtual
Para correr los scripts de este repositorio es necesario generar un ambiente virtual de python:
```sh
python3 -m venv <nombre_ambiente>
```

Actívelo con:
```sh
# En Linux
. <nombre_ambiente>/bin/activate

# En Windows
.\<nombre_ambiente>\Scripts\Activate.ps1
```

Instale las librerías necesarias con:
```sh
pip install -r requirements.txt
```

### Archivo de configuración
Se tiene un archivo de configuración [config.json](/src/config.json):
```sh
    "biocultural": {
        "origin_url": "http://dataverse.localhost", # URL de instancia de BioCultural de donde se descargarán los datos
        "origin_api_token": "", # Token de usuario administrador de instancia de BioCultural de origen
        "dataverse_names": [":root", "iavh_i2d_biocultural"], # Nombres de dataversos desde los que se necesitan hacer las descargas de los datos
        "doi_prefix": "doi:10.21068", # Prefijo de DOI
        "metadata_directory": "data/biocultural/raw/", # Ruta donde se almacenarán los metadatos
        "files_directory": "data/biocultural/files/" # Ruta donde se almacenarán los archivos
    }  
```

## Ingesta de datos

### Biocultural
Para obtener todos los metadatos y archivos de los datasets de BioCultural ejecute el script [biocultural_ingest.py](/src/ingest/biocultural_ingest.py):
```sh
python3 -m src.ingest.biocultural_ingest
```

Los metadatos se almacenarán en la ruta establecida en el atributo `metadata_directory` del [config.json](/src/config.json). Si se mantiene la ruta definida, se recomienda crear la carpeta `data` al mismo nivel del directorio `src`.
Los archivos se almacenarán en la ruta establecida en el atributo `files_directory` del [config.json](/src/config.json), dentro de una subcarpeta para cada DOI. Si se mantiene la ruta definida, se recomienda crear la carpeta `data` al mismo nivel del directorio `src`.

## Logs
Podrá encontrar los archivos de logs en la carpeta [logs](/src/logs/).