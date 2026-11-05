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
    CEIBA_DATA_DIR="data/ceiba" # Ruta relativa donde se almacenarán los datos de Ceiba
    
    # Geonetwork
    GN_URL=https://geonetwork.humboldt.org.co/geonetwork/srv
    GN_USER= # Nombre de usuario administrador
    GN_PASSWORD= # Contraseña de usuario administrador
    GN_DATA_DIR="" # Ruta relativa donde se almacenarán los datos de Geonetwork

    INVENTORY_PATH="/ruta/inventario/i2d" # Ruta absoluta al inventario I2D
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

Los metadatos se almacenarán en la ruta establecida en el atributo `BIOCULTURAL_DATA_DIR/METADATA_DIR` del [.env](.env.example). Si se mantiene la ruta por defecto, se recomienda crear la carpeta `data` al mismo nivel del directorio `src`.
Los archivos se almacenarán en la ruta establecida en el atributo `BIOCULTURAL_DATA_DIR/FILES_DIR` del [.env](.env.example). Si se mantiene la ruta por defecto, se recomienda crear la carpeta `data` al mismo nivel del directorio `src`.

La estructura final se verá así:
- Carpeta `collections`: Almacena un json de cada uno de los dataversos existentes con información sobre sus datasets y dataversos hijos.
- Carpeta `files`: Almacena los archivos de cada versión de cada dataset en subcarpetas nombradas como [IDENTIFICADOR_DOI]-[VERSIÓN]
- Carpeta `metadatablocks`: Almacena un json por cada bloque de metadatos existente en la instancia.
- Carpeta `raw`: Almacena los metadatos de cada versión de cada dataset en jsons nombrados como [IDENTIFICADOR_DOI]-[VERSIÓN].json
- Archivo `inventory.csv`: Genera un inventario de todos los datasets presentes en la instancia.
- Archivo `version.json`: Almacena un resumen de la versión de la instancia de BioCultural.

### Ceiba
Para obtener todos los metadatos y archivos de los datasets de Ceiba ejecute el script [ceiba_ingest.py](/src/ingest/ceiba_ingest.py):
```sh
python3 -m src.ingest.ceiba_ingest
```
Los metadatos se almacenarán en la ruta establecida en el atributo `CEIBA_DATA_DIR/METADATA_DIR` del [.env](.env.example). Si se mantiene la ruta por defecto, se recomienda crear la carpeta `data` al mismo nivel del directorio `src`.

Se creará una carpeta para cada recurso, donde dentro se almacenará:
- `files.json` para la ruta absoluta de los archivos del recurso.
- `resource_metadata.json` que contiene la data del `eml.xml` de la última versión disponible, unido con la data almacenada en `resources.xml`.

### GeoNetwork
Para obtener todos los metadatos y las referencias de los archivos adjuntos a cada uno de los recursos de GeoNetwork, ejecute el script [geonetwork_ingest.py](/src/ingest/geonetwork_ingest.py):
```sh
python3 -m src.ingest.geonetwork_ingest
```

Se generará la siguiente estructura:
- **attachements**: Almacena un JSON por cada recurso, usando su ID como nombre de archivo. Dentro se referencian los archivos adjuntos, con su url, tamaño y tipo de adjunto.
- **inventory**: Contiene un archivo de inventario de archivos para todos los recursos (`files_inventory.csv`), un inventario de metadatos generales (`inventory.csv`) y un resumen de todos los recursos (+6000) separándolos en varios archivos, cada uno conteniendo lotes de 100.
- **sharing**: Almacena un JSON por cada recurso, usando su ID como nombre de archivo. Dentro se referencian los privilegios de cada recurso.
- **xml**: Almacena un JSON por cada recurso, usando su ID como nombre de archivo. Dentro se almacenan los metadatos completos de cada recurso.
- `groups.json`: Grupos de GeoNetwork
- `site.json`: Información de la instancia de GeoNetwork

## Logs
Podrá encontrar los archivos de logs en la carpeta [logs](/src/logs/).