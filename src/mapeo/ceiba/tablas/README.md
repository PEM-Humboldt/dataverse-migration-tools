# Tablas del mapeo de Ceiba

El mapeo de Ceiba ([`ceiba_metadata_mapping.py`](/src/mapeo/ceiba_metadata_mapping.py) y los módulos de [`src/mapeo/ceiba/`](/src/mapeo/ceiba)) usa cuatro tablas CSV revisadas a mano. Tienen que estar en esta carpeta, pero **no se publican en este repositorio**, como las de GeoNetwork:

- `restriction_reasons.csv` contiene los textos del inventario de la I2D sobre la restricción de recursos (nombres de convenios, de comunidades y de financiadores), y `citation_authors.csv` los nombres de personas de las citas;
- el repositorio es público, y git las ignora por la regla `*.csv` del [`.gitignore`](/.gitignore).

Solo este archivo, que las describe, está en el repositorio.

## Cómo obtenerlas

1. Pedir al equipo de la línea de integración de datos la copia vigente de las cuatro tablas. Las prepara el proyecto prototipo de Ceiba (`testCeiba`), que valida las reglas con el equipo, y se comparten por la carpeta compartida del proyecto, fuera de GitHub.
2. Copiarlas en esta carpeta (`src/mapeo/ceiba/tablas/`), sin cambiar sus nombres.
3. Comprobar que git no las ve: `git status --short src/mapeo/ceiba/tablas/` no muestra ningún CSV.
4. Nunca añadirlas con `git add -f`, ni quitar la regla `*.csv` del `.gitignore`.

El script se detiene con un mensaje si falta alguna de las tablas.

## Las tablas

En las columnas, **en negrita** las que lee el código; las demás documentan la regla (cifras, notas, validación). Las cifras son de las plantillas del prototipo (todas las versiones de la copia del IPT del 29/10/2026).

| Tabla | Qué es | Filas (24/11/2026) | Columnas |
|---|---|---|---|
| `party_roles.csv` | Personas y organizaciones: elemento del EML × rol → campo de Dataverse y tipo de colaborador (correspondencia del equipo del 05/11/2026, `ceiba/personas_roles_dataverse.md`). El personal del proyecto con rol tiene dos filas: Miembro del proyecto y el destino de su rol | 48 | **`party_type`** (`creator`, `contact`, `metadataProvider`, `associatedParty`, `personnel`), **`role`** (rol del EML; vacío para los tres primeros y para las apariciones sin rol), **`target_field`** (`producer`, `datasetContact`, `distributor`, `contributor`), **`contributor_type`**; `n_parties`, `n_resources`, `note`; `validated` |
| `vocabularies.csv` | Valores de la fuente → valor del vocabulario de Dataverse, para `coreType` y `subtype` (de `resource.xml`), `taxonRankName` y `specimenPreservationMethod` (del EML) | 52 | **`field`**, **`source`** (`resource.xml` o `eml`), **`source_value`** (comparado sin mayúsculas), **`dataverse_value`**; `match` (`exacta` o `equivalencia`), `n_resources`; `validated` |
| `restriction_reasons.csv` | Textos de «Objeto de la restricción» del inventario → razón del vocabulario `restrictionJustification` (8 razones). El código usa `reason_code` (lo decide el equipo) y, mientras esté vacío, `proposed_reason`; si la fila no está validada (`validated` vacío), el conjunto de datos va también a la lista de curación (*actualizado el 25/11/2026*) | 18 | **`restriction_text`** (texto del inventario, comparado sin espacios de más), **`reason_code`** (valor exacto del vocabulario, por llenar); `n_datasets`, `proposed_codes` (códigos de la regla de palabras clave de `03_mapping.qmd`), **`proposed_reason`** (razón propuesta, valor exacto del vocabulario, por validar), **`validated`**, `note` |
| `citation_authors.csv` | Autores de Dataverse (`authorName`): los nombres escritos antes del año en la cita de Ceiba, en el orden de la cita, tal como están escritos. Extraída una vez de la copia del IPT del 24/11/2026 (regla del bloque `citation-authors-check` de `testCeiba/03_mapping.qmd`) y revisada a mano (*25/11/2026*); **el código no extrae autores: solo lee esta tabla**. Un conjunto de datos sin filas recibe el Instituto como autor por defecto y va a la lista de curación: si se añaden conjuntos de datos a Ceiba antes de la migración final, hay que añadir sus filas a mano. Las filas en estado `revisar` van también a la lista de curación | 2.045 (1.107 conjuntos de datos) | **`resource`**, `source_version`, **`author_position`**, **`author_name`**, **`status`** (`ok`, `corregido` a mano, `revisar`), **`note`**, `citation` (texto completo de la cita, como ayuda); `validated` |
