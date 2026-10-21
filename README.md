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
python3 -m venv .venv
```

> Nota: Es posible cambiar el nombre del ambiente si se prefiere. En caso de que lo haga, ubique el ambiente fuera de la carpeta del repositorio o agregue el nombre del ambiente al archivo .gitignore para evitar versionarlo por error.

Actívelo con:
```sh
# En Linux
. .venv/bin/activate

# En Windows
.\.venv\Scripts\Activate.ps1
```

Instale las librerías necesarias con:
```sh
pip install -r requirements.txt
```

### Archivo de configuración
Se tiene un archivo de variables de ambiente [.env.example](/.env.example):
```sh
    # Biocultural
    BIOCULTURAL_ORIGIN_URL="http://dataverse.localhost" # URL de instancia de BioCultural de donde se descargarán los datos
    BIOCULTURAL_ORIGIN_API_TOKEN="" # Token de usuario administrador de instancia de BioCultural de origen
    BIOCULTURAL_DATA_DIR="" # Ruta relativa donde se almacenarán los datos de biocultural

    # Ceiba
    CEIBA_ORIGIN_PATH="/ruta/a/carpeta/resources" # Ruta absoluta a la carpeta con los recursos

    METADATA_DIR="raw" # Nombre de la carpeta donde se almacenarán los metadatos
    FILES_DIR="files"  # Nombre de la carpeta donde se almacenarán los archivos
```

Genere su archivo `.env` copiando el `env.example`:
```sh
cp .env.example .env
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