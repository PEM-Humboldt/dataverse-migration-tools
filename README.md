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
    VOCABULARIES_PATH="/ruta/a/vocabularies.xlsx" # Ruta absoluta al libro de equivalencias de vocabularios de Biocultural (hoja `vocabularies`)
    TSV_FILES_PATH="/ruta/a/metadata_dataverse" # Ruta a la carpeta con las definiciones de los bloques de metadatos (<bloque>.tsv)

    # Dataverse 6.10.1 Instance
    DV_TARGET_URL = "http://dataverse.localhost" # URL de la instancia final de Dataverse
    DV_TARGET_API_TOKEN="" # Token de usuario administrador de instancia final de Dataverse
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

> Nota: Tenga presente que GeoNetwork maneja más de 6000 recursos. La ejecución completa del script puede tomar varios minutos. Si desea hacer una prueba controlada, puede descomentar la línea 191 del script `geonetwork_ingest.py`

Los datos se almacenarán en la ruta `GN_DATA_DIR` del [.env](.env.example). Si se mantiene la ruta por defecto, se recomienda crear la carpeta `data` al mismo nivel del directorio `src`.

La estructura final se verá así:
- Carpeta `attachements`: Almacena un JSON por cada recurso, usando su ID como nombre de archivo. Dentro se referencian los archivos adjuntos, con su url, tamaño y tipo de adjunto.
- Carpeta `inventory`: Contiene un inventario de metadatos generales (`inventory.csv`) y un resumen de todos los recursos separándolos en varios archivos, cada uno conteniendo lotes de 100.
- Carpeta `sharing`: Almacena un JSON por cada recurso, usando su ID como nombre de archivo. Dentro se referencian los privilegios de cada recurso.
- Carpeta `xml`: Almacena un JSON por cada recurso, usando su ID como nombre de archivo. Dentro se almacenan los metadatos completos de cada recurso.
- `groups.json`: Grupos de GeoNetwork
- `site.json`: Información de la instancia de GeoNetwork

## Mapeo de metadatos

### GeoNetwork
Para convertir la cosecha de GeoNetwork en registros de versión de Dataverse ejecute el script [geonetwork_mapping.py](/src/mapeo/geonetwork_mapping.py) después de la ingesta:
```sh
python3 -m src.mapeo.geonetwork_mapping
```

El script lee la cosecha (`GN_DATA_DIR`) y el inventario de la I2D (`INVENTORY_PATH`, hoja `Geográfico`, unida por el «ID GeoNetwork»), aplica la tabla de correspondencia y comprueba cada registro frente a las definiciones de los bloques de metadatos (`TSV_FILES_PATH`, leídas por `load_dv_schemas()`). Solo se migran los registros de datos: no los servicios web (`hierarchyLevel` = `service`), cuyos puntos de acceso pasan a los conjuntos de datos que sirven, ni los registros de `tablas/excluded_records.csv`.

En la primera versión de la migración solo se transfieren los metadatos. Con la opción `--with-files`, el script prepara también los archivos de datos (adjuntos de GeoNetwork):
```sh
python3 -m src.mapeo.geonetwork_mapping --with-files
```

Los resultados se almacenarán en la ruta `GN_DATA_DIR`:
- Carpeta `raw` (`METADATA_DIR`): un JSON por registro migrado, nombrado como [UUID]-1.0.json, con la forma `{"metadataLanguage", "datasetVersion", "inventory_data"}`. Los registros de GeoNetwork no tienen DOI: cada uno será un conjunto de datos nuevo con una sola versión.
- `load_plan.csv`: una fila por registro: archivo de versión, si se publica después de la carga (`release` = `no` para los borradores), tipo de acceso y licencia; con `--with-files`, número de archivos, archivos restringidos y carpeta de los archivos.
- `version_dates.csv`: las fechas originales de cada versión (`createDate` y `changeDate` de GeoNetwork), para restituirlas después de la carga. Las filas de los borradores (`draft` = `True`) no se aplican.
- `mapping_problems.json`: los registros que no pasan la comprobación frente a los bloques; no reciben registro de versión.
- `files_to_download.csv` (solo con `--with-files`): los adjuntos por descargar, con su URL, tamaño y carpeta de destino.

Las tablas que usa el mapeo (correspondencia, variables de GeoNetwork, roles, organizaciones, personas, equivalencias, créditos, registros excluidos) son tablas revisadas a mano que contienen datos de los registros: nombres de personas, títulos, registros privados. Por eso **no se publican en este repositorio**: cada persona que ejecuta el mapeo las copia en [src/mapeo/geonetwork/tablas](/src/mapeo/geonetwork/tablas), donde git las ignora (regla `*.csv`). Su contenido, sus columnas y de dónde obtenerlas se describen en [tablas/README.md](/src/mapeo/geonetwork/tablas/README.md). El script se detiene si falta alguna. Un cambio de regla se hace en ellas o en las funciones de `src/mapeo/geonetwork/`.

## Logs
Podrá encontrar los archivos de logs en la carpeta [logs](/src/logs/).
