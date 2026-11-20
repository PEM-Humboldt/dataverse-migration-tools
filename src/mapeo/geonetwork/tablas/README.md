# Tablas del mapeo de GeoNetwork

El mapeo de GeoNetwork ([`geonetwork_mapping.py`](/src/mapeo/geonetwork_mapping.py) y los módulos de [`src/mapeo/geonetwork/`](/src/mapeo/geonetwork)) usa nueve tablas CSV revisadas a mano. Tienen que estar en esta carpeta, pero **no se publican en este repositorio**:

- contienen datos de los registros de GeoNetwork: nombres de personas, títulos y textos de créditos, registros privados o de acceso restringido;
- el repositorio es público, y git las ignora por la regla `*.csv` del [`.gitignore`](/.gitignore).

Solo este archivo, que las describe, está en el repositorio.

## Cómo obtenerlas

1. Pedir al equipo de la línea de integración de datos la copia vigente de las nueve tablas. Las prepara el proyecto prototipo de GeoNetwork, que valida las reglas con el equipo, y se comparten por la carpeta compartida del proyecto, fuera de GitHub.
2. Copiarlas en esta carpeta (`src/mapeo/geonetwork/tablas/`), sin cambiar sus nombres.
3. Comprobar que git no las ve:
   - `git status --short src/mapeo/geonetwork/tablas/` no muestra ningún CSV;
   - `git check-ignore -v src/mapeo/geonetwork/tablas/people.csv` muestra la regla `*.csv`.
4. Nunca añadirlas con `git add -f`, ni quitar la regla `*.csv` del `.gitignore`.

El script se detiene con un mensaje si falta alguna de las tablas que lee.


## Las tablas

En las columnas, **en negrita** las que lee el código; las demás documentan la regla (cifras de la cosecha, notas, validación).

| Tabla | Qué es | Filas (20/11/2026) | Columnas |
|---|---|---|---|
| `crosswalk.csv` | Tabla de correspondencia ISO 19139 → campos de Dataverse: para cada campo de destino, las variables de GeoNetwork que lo alimentan y el tratamiento. Es la referencia de las reglas que aplican las funciones de `gn_mapping.py`; ninguna función la lee | 135 (85 con una regla, 50 sin fuente en GeoNetwork) | `block`, `field`, `parent` (campo de destino); `source_vars`, `check_vars` (variables de `gn_variables.csv`); `treatment`; `quality_notes`; `status` (`propuesta` o `sin fuente`); `validated`, `review` |
| `gn_variables.csv` | Variables de GeoNetwork: un nombre por ruta XML del registro ISO 19139 | 138 | **`name`**, `path` (ruta corta), **`full_path`** (ruta completa desde `gmd:MD_Metadata`), `description`, `same_info_as`, `same_info_note` (variables con la misma información). Las variables `api_…` no vienen del XML y no se leen del registro |
| `party_roles.csv` | Responsables: lugar en el registro × rol ISO → campo de Dataverse y tipo de contribuidor | 47 | **`section`** (lugar: contacto del registro, cita, distribución…), **`role`** (código `CI_RoleCode`), **`dv_field`** (`datasetContact`, `producer`, `contributor`, `distributor`), **`contributor_type`**; `appearances`, `records`; `validated`, `review` |
| `organisations.csv` | Formas de escribir las organizaciones en GeoNetwork, con su nombre normalizado | 182 | **`organisation_name`** (como aparece en GeoNetwork), **`canonical_name`** (nombre normalizado: el del Instituto identifica al Instituto en todas sus formas), **`ror`** (identificador ROR, si se conoce); `n_parties`, `n_records`, `department`, `not_organisation`, `note` |
| `people.csv` | Nombres de personas de GeoNetwork y si de verdad son personas | 709 | **`individual_name`** (como aparece en `gmd:individualName`), **`not_person`** (`TRUE` cuando el «nombre» es una función o una organización: entonces se usa el nombre de la organización) |
| `citation_mentions.csv` | Personas e instituciones acreditadas en los textos de créditos de cada registro: de aquí salen los autores (`citation/author`). Se prepara fuera del proceso de migración y se revisa a mano antes de la carga | 1.003 (645 registros) | **`uuid`** (registro), `title`, **`field`** (texto de origen: solo se usan las filas de `credit`), `raw_text`, **`author_name`** (persona), **`institution`** (institución, si no hay persona), `part` (parte del texto donde se encontró el nombre) |
| `srs_equivalences.csv` | Sistemas de referencia: texto de GeoNetwork → código EPSG | 45 | **`code`** (texto de `srs_code` en GeoNetwork), **`epsg`** (uno o varios códigos separados por «;»; vacío: no se migra); `n_records`, `code_spaces`, `uuids` (registros donde aparece), `rule`, `check`; `validated`, `review` |
| `format_equivalences.csv` | Formatos: texto de GeoNetwork → valor del vocabulario `geographic/distributionFormat` | 71 | **`text`** (nombre del formato en GeoNetwork), **`format`** (uno o varios valores separados por «;»; vacío: no se migra); `n_records`, `variables`, `uuids` (registros donde aparece), `rule`, `check`; `validated`, `review` |
| `excluded_records.csv` | Registros que no se migran aunque sean conjuntos de datos: plantillas y registros de prueba sin marcar, recursos eliminados en el inventario de la I2D | 9 | **`uuid`**, `title`, `reason`, `decided` (fecha de la decisión) |

Cómo se comparan los textos de las tablas con los de GeoNetwork:
- en `srs_equivalences.csv`, `format_equivalences.csv` y `people.csv`, el texto tiene que ser el de GeoNetwork tal como aparece, salvo los espacios de más y los saltos de línea;
- en `organisations.csv`, la comparación ignora además mayúsculas, tildes y signos de puntuación.
