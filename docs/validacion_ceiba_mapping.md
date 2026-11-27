# Validación parcial del mapeo CEIBA–Dataverse

Este informe acompaña el Draft Pull Request de `feature/validacion-ceiba-mapping` a `marbotte/ceiba-mapping-example`. Presenta la evidencia disponible al 26 de noviembre de 2026, las correcciones aplicadas y las decisiones pendientes para continuar la validación.

## Índice

1. [Contexto y alcance](#contexto-y-alcance)
2. [Arquitectura evaluada](#arquitectura-evaluada)
3. [Metodología](#metodología)
4. [Caracterización de los datos](#caracterización-de-los-datos)
5. [Resultados de citation](#resultados-de-citation)
6. [Personas e instituciones](#personas-e-instituciones)
7. [Correcciones implementadas](#correcciones-implementadas)
8. [Regresión y reporte de curación](#regresión-y-reporte-de-curación)
9. [Pruebas unitarias](#pruebas-unitarias)
10. [Herramienta de comparación de regresiones](#herramienta-de-comparación-de-regresiones)
11. [Matriz de hallazgos pendientes](#matriz-de-hallazgos-pendientes)
12. [Preguntas para Marius y el equipo](#preguntas-para-marius-y-el-equipo)
13. [Próximas actividades](#próximas-actividades)

## Contexto y alcance

| Referencia | Valor |
|---|---|
| Repositorio | `PEM-Humboldt/dataverse-migration-tools` |
| Rama de trabajo | `feature/validacion-ceiba-mapping` |
| Rama base | `marbotte/ceiba-mapping-example` |
| Commit base | `449385271f8efd92894ba70785e95c2bead70ecd` |
| Commit de los esquemas Dataverse | `ab2841405a24f149ff7fdb6264f179ede27c6e7c` |
| Crosswalk de referencia | `MigracionCeiba_20261125.xlsx` |
| Fecha de corte | 26 de noviembre de 2026 |

La evaluación fortalece la implementación desarrollada por Marius y conserva su arquitectura. Cubre el bloque `citation` y los elementos relacionados con personas, instituciones y contratistas. Quedan pendientes las evaluaciones específicas de `geospatial`, los elementos restantes de `institutional`, `externalReferences` y `biologicalMetadata`. El alcance se limita a la entrega parcial y no se ha realizado carga de datos en Dataverse.

Los resultados cuantitativos proceden de las evaluaciones suministradas para esta fase. La FASE 11 consistió en una auditoría estática de solo lectura. Las cifras de pytest corresponden a la última ejecución informada, anterior a esa auditoría.

## Arquitectura evaluada

```text
EML original → ingesta → JSON intermedio → transformación de metadatos
             → validación estructural contra esquemas Dataverse → JSON finales y reportes
```

| Componente | Responsabilidad |
|---|---|
| [`ceiba_source.py`](../src/mapeo/ceiba/ceiba_source.py) | Lee los registros de la ingesta en su representación intermedia, extrae `dataset` y `packageId`, y normaliza las formas de texto y las listas procedentes del EML. |
| [`ceiba_people.py`](../src/mapeo/ceiba/ceiba_people.py) | Mapea autores, apariciones de personas y organizaciones, roles, correos y datos institucionales. Detecta nombres de contratistas en el EML y genera notas de curación de personas cuando corresponde. |
| [`ceiba_fields.py`](../src/mapeo/ceiba/ceiba_fields.py) | Aplica las reglas de transformación y compone los bloques de metadatos. Integra códigos y nombres de contratistas, y consolida los casos de curación por registro. |
| [`ceiba_metadata_mapping.py`](../src/mapeo/ceiba_metadata_mapping.py) | Orquesta el mapeo por lotes, la comprobación de los campos contra los esquemas, la generación de los JSON finales y la escritura de los reportes. |
| [`compare_ceiba_mapping.py`](../scripts/compare_ceiba_mapping.py) | Compara dos salidas locales de mapeo y resume diferencias de JSON y reportes para revisar regresiones. |

La **validación estructural** verifica campos, tipos, multiplicidad, obligatoriedad y vocabularios según los esquemas. La **validación semántica** compara lo que se documenta en el EML con lo que se conserva en la ingesta y en los JSON finales, atendiendo a significado, identidad y contexto. El **cumplimiento del crosswalk** comprueba que se usen las fuentes, destinos y transformaciones acordados. Un resultado estructural correcto puede contener una asignación semántica dudosa o una decisión pendiente del crosswalk.

## Metodología

1. Revisar las reglas del crosswalk actualizado.
2. Inspeccionar la implementación existente y sus dependencias.
3. Generar una línea base sin las correcciones.
4. Evaluar los casos reales dentro del alcance.
5. Comparar el XML original, el JSON de ingesta y el JSON final.
6. Construir y adaptar pruebas sintéticas reproducibles.
7. Identificar y clasificar los hallazgos.
8. Aplicar correcciones justificadas por la evidencia.
9. Comparar las salidas posteriores a cada corrección. PER-H16 y PER-H28 se revisaron conjuntamente en la regresión contractual.
10. Consolidar los resultados y las decisiones pendientes.

Se priorizaron los problemas con impacto real y se limitaron los cambios preventivos. DATE-01 fue la excepción, dirigida a evitar la aceptación de fechas calendáricamente imposibles detectada con pruebas sintéticas.

## Caracterización de los datos

| Indicador | Cantidad |
|---|---:|
| Recursos ingresados | 1191 |
| Recursos publicados en CEIBA | 1107 |
| Recursos no publicados | 84 |
| EML 2.1.1 publicados | 1032 |
| EML 2.2.0 publicados | 75 |
| JSON finales generados | 1107 |
| Recursos previstos como borradores | 27 |
| Recursos previstos para liberación | 1080 |
| Problemas estructurales de mapeo reportados | 0 |

El conteo de problemas estructurales cubre las verificaciones del esquema. La evaluación semántica y la curación se contabilizan por separado.

## Resultados de citation

### Elementos simples

Se evaluaron `title`, `alternativeTitle`, `otherIdAgency`, `otherIdValue`, `subject`, `language` y `distributionDate` en los 1107 recursos publicados.

| Indicador | Cantidad |
|---|---:|
| Evaluaciones de elementos | 7749 |
| Valores presentes | 6648 |
| Ausencias justificadas | 1101 |
| Diferencias respecto a las reglas evaluadas | 0 |

- **ALT-H01.** El código carece de una restricción explícita de versión EML para `shortName`. En los recursos evaluados no se encontraron casos fuera de EML 2.2.0.
- **LANG-H02.** Un recurso documenta `oci`, correspondiente a `Occitan`. Se conservó la equivalencia y se propone revisar el valor de origen.
- **LANG-H03.** Una fila del vocabulario de idiomas carece de identificador, sin impacto observado.

### Descripción y notas

| Indicador | Cantidad |
|---|---:|
| Descripciones (`dsDescriptionValue`) | 1107 |
| Fechas de descripción (`dsDescriptionDate`) | 1107 |
| Notas adicionales (`notesText`) | 462 |
| Párrafos evaluados | 1631 |
| Caracteres de texto evaluados | 1174492 |

No se identificó pérdida de contenido textual. **DESC-H01** registra la pérdida de ocho etiquetas de énfasis en cuatro párrafos de tres recursos. **DESC-H02** y **DESC-H03** identifican limitaciones potenciales para enlaces y contenido XML mixto, sin casos reales identificados en las descripciones evaluadas. **DESC-H04** recoge la decisión pendiente sobre HTML o texto plano para `dsDescriptionValue`.

**NOTE-H01** identifica que el crosswalk no explicita el tratamiento HTML de `notesText`. **NOTE-H02** documenta que la implementación admite texto directo en `additionalInfo` sin `para`. No se identificaron casos reales y una prueba sintética conserva la discrepancia para revisión. **CUR-H01** registra 42 recursos con `jgtiCuratorialUnit`. Está pendiente verificar integralmente su exclusión del mapeo y definir su conservación en un archivo externo de curación.

### Palabras clave

| Indicador | Cantidad |
|---|---:|
| Recursos evaluados | 1107 |
| Conjuntos de palabras clave | 3244 |
| Valores originales no vacíos | 10005 |
| Valores después de la separación | 10165 |
| Duplicados eliminados | 305 |
| Palabras clave finales | 9860 |
| Valores de `keywordVocabulary` después de la corrección | 2061 |
| Valores de `keywordVocabularyURI` después de la corrección | 2056 |

**KW-001** incorporó `nomenclator authority` y `ejemplar`, dos términos del vocabulario oficial de subtipo GBIF ausentes del conjunto utilizado por el mapeador. Se conservaron las entradas previas. La regresión dejó 1105 JSON idénticos y modificó 2, con 2 valores adicionales de `keywordVocabulary` y 2 de `keywordVocabularyURI`. Los demás elementos y los reportes permanecieron idénticos en esa comparación.

## Personas e instituciones

### Validación de las fuentes

| Indicador | Cantidad |
|---|---:|
| Recursos evaluados | 1107 |
| Apariciones de personas y organizaciones | 11804 |
| Comparaciones de atributos entre EML e ingesta | 70824 |
| Valores presentes | 57209 |
| Ausencias | 13615 |
| Diferencias en los atributos evaluados | 0 |

### Elementos finales

| Elemento | Entradas |
|---|---:|
| `author` | 2045 |
| `datasetContact` | 1426 |
| `producer` | 3660 |
| `distributor` | 1216 |
| `contributor` | 5515 |
| `contractor` | 1327 |
| `depositor` | 0 |
| **Total** | **15189** |

Las cifras cuentan entradas de destino. Una misma persona u organización puede aparecer en varios recursos o roles. Los 2045 nombres de `author` y su orden se conservaron al contrastarlos con la tabla de correspondencia suministrada. El cotejo valida la transferencia desde esa fuente y la certificación bibliográfica de las autorías queda fuera del alcance.

| Indicador de contactos | Cantidad |
|---|---:|
| Candidatos | 1474 |
| Entradas finales | 1426 |
| Duplicados eliminados | 48 |
| Correos propios | 1395 |
| Correos recuperados de otras apariciones | 6 |
| Correos institucionales asignados por ausencia de correo | 25 |
| Registros de curación relacionados con correos | 31 |

| Elemento | Candidatos | Entradas finales |
|---|---:|---:|
| `producer` | 4122 | 3660 |
| `distributor` | 1306 | 1216 |
| `contributor` | 5615 | 5515 |

Se contabilizaron 1207 asignaciones de `Project Member`. No se encontraron roles desconocidos en los recursos evaluados.

### Deduplicación

| Indicador | Cantidad |
|---|---:|
| Asignaciones candidatas de contactos, productores, distribuidores y colaboradores | 12517 |
| Asignaciones conservadas | 11817 |
| Asignaciones duplicadas eliminadas | 700 |
| Casos sin conflictos relevantes para los campos de destino | 663 |
| Casos que requieren revisión semántica | 37 |
| Conflictos de afiliación | 36 |
| Conflictos de correo electrónico | 2 |
| Casos con ambos tipos de conflicto | 1 |
| Recursos únicos involucrados | 36 |

No se identificó pérdida de atributos exclusivos del destino en la evaluación realizada. La regla de primera aparición determina qué valor se conserva técnicamente. Los conflictos de afiliación o correo requieren decidir si las apariciones corresponden a la misma identidad y si el valor retenido es el adecuado.

### Contratistas

Después de las correcciones se contabilizaron 1004 nombres, 590 códigos contractuales, 1327 entradas compuestas y 680 recursos con información contractual.

| Situación | Recursos |
|---|---:|
| Asociación directa uno a uno | 267 |
| Asociación indeterminada | 187 |
| Sólo nombres | 221 |
| Sólo códigos | 5 |
| Sin nombres ni códigos | 427 |

No se establecieron asociaciones arbitrarias entre nombres y códigos. En los casos indeterminados ambos se conservaron en entradas separadas.

## Correcciones implementadas

### DATE-01

`iso_date()` valida la parte calendárica mediante `datetime.date`, conserva la precisión de las fechas parciales y retiene el día de origen sin convertir la zona horaria a UTC. El patrón heredado todavía admite determinados sufijos libres después de un espacio o `T`, por lo que su alcance es distinto del de un validador integral de fechas y horas ISO 8601. En la regresión real, los 1107 JSON y los cuatro reportes permanecieron idénticos.

### KW-001

Se añadieron los dos términos de subtipo GBIF a `GBIF_SUBTYPE_VALUES`, preservando los términos existentes y la lógica de `map_keywords()`. La regresión real confirmó dos recursos corregidos, sin cambios adicionales en los elementos o reportes comparados.

### PER-H16

`map_contractors()` genera una fila `contractor_association` en la curación cuando, después de deduplicar, existen nombres y códigos y no se puede establecer una relación uno a uno. La fila identifica el recurso e incluye un resumen de cantidades. Los nombres y códigos individuales quedan en las entradas de metadatos separadas.

| Comprobación posterior a la corrección | Resultado |
|---|---:|
| Recursos con asociación indeterminada | 187 |
| Registros de curación del tipo `contractor_association` | 187 |
| Conteos numéricamente correctos | 187 |
| Registros duplicados | 0 |
| Recursos con asociación indeterminada sin curación | 0 |
| Asociaciones arbitrarias | 0 |

Una primera comprobación literal encontró 144 diferencias debidas exclusivamente al uso de singular o plural. La comprobación numérica independiente confirmó la corrección de todos los conteos. La categoría usada queda abierta a aprobación institucional.

### PER-H28

Se recuperaron códigos del inventario separados por comas o precedidos por el prefijo redundante `PS`. La separación con comas se aplica cuando todos los fragmentos del tramo son códigos completos válidos según `PS_CODE.fullmatch()`. La clasificación compartida entre `map_contractors()` y `map_projects()` evita trasladar esos códigos a `projectFunding` como convenios. Los tramos mixtos conservan su tratamiento anterior.

| Comprobación posterior a la corrección | Resultado |
|---|---:|
| Códigos recuperados | 10 |
| Recursos corregidos | 3 |
| Códigos inesperados | 0 |
| Códigos eliminados | 0 |
| Cambios en nombres | 0 |
| Valores de `projectFunding` corregidos | 3 |

Se conservaron los textos de financiación y los convenios legítimos en los casos evaluados.

## Regresión y reporte de curación

La regresión usó la línea base posterior a KW-001 para comparar la salida posterior a PER-H16 y PER-H28.

| Indicador | Resultado |
|---|---:|
| JSON comparados | 1107 |
| JSON idénticos | 1104 |
| JSON modificados | 3 |
| Recursos añadidos o eliminados | 0 |
| Valores añadidos en `contractor` | 10 |
| Valores modificados en `projectFunding` | 3 |

Los cambios de metadatos se limitaron a `institutional`. Los reportes `load_plan.csv`, `version_dates.csv` y `mapping_problems.json` permanecieron idénticos. En `curation.csv` se conservaron los 1163 registros anteriores y se añadieron exclusivamente 187 registros `contractor_association`.

| Indicador de curación | Inicial | Actual |
|---|---:|---:|
| Registros | 1163 | 1350 |
| Recursos únicos | 865 | 910 |
| Recursos sin curación | 242 | 197 |

Las filas de curación hacen trazables decisiones pendientes, valores de respaldo y casos que requieren revisión. El total de filas mide la carga de revisión y no equivale a un conteo de errores de implementación. La cantidad de filas puede exceder la de recursos únicos porque un recurso puede requerir más de una revisión.

## Pruebas unitarias

La última ejecución informada en macOS con Python 3.13.2 abarcó doce suites seleccionadas. El resultado fue de **230 casos ejecutados, 228 aprobados, 2 `xfail` estrictos y 0 fallos inesperados**. Los `xfail` corresponden a DESC-H01 y NOTE-H02. Esta selección representa el conjunto adaptado; los módulos heredados pendientes quedaron fuera.

`pytest` requiere instalación adicional a las dependencias declaradas del proyecto. Se recomienda ejecutar la selección en un proceso dedicado, dado que las fixtures aíslan dependencias de importación para estas pruebas. El comparador requiere Python 3.10 o posterior. La ejecución informada sólo acredita el entorno macOS indicado.

El comando se ejecuta desde la raíz del repositorio con el entorno virtual preparado.

```bash
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
.venv/bin/python -m pytest \
tests/test_citation_title_subject.py \
tests/test_citation_nivel1.py \
tests/test_citation_language.py \
tests/test_citation_other_id.py \
tests/test_citation_distribution_date.py \
tests/test_palabras_clave_ceiba.py \
tests/test_citation_description.py \
tests/test_citation_notes.py \
tests/test_compare_ceiba_mapping.py \
tests/test_ceiba_people.py \
tests/test_ceiba_contractors.py \
tests/test_ceiba_people_curation.py \
-v --tb=short -p no:cacheprovider
```

## Herramienta de comparación de regresiones

[`scripts/compare_ceiba_mapping.py`](../scripts/compare_ceiba_mapping.py) recibe como argumentos posicionales el directorio de línea base, el de resultados actuales y el de reportes, en ese orden. Cada entrada debe contener `load_plan.csv`, `version_dates.csv`, `curation.csv` y `mapping_problems.json` en su raíz. Por defecto busca los registros `*-1.0.json` en `metadata/`. `--metadata-subdir` permite indicar un subdirectorio relativo común a ambas entradas, o `.` cuando los JSON están en la raíz.

```bash
.venv/bin/python scripts/compare_ceiba_mapping.py \
  /ruta/linea-base /ruta/resultados-actuales /ruta/privada/reporte-agregado

.venv/bin/python scripts/compare_ceiba_mapping.py \
  /ruta/linea-base /ruta/resultados-actuales /ruta/privada/reporte-detallado \
  --metadata-subdir metadata --detailed
```

El script empareja los JSON por nombre de recurso, compara valores interpretados e ignora diferencias de indentación, orden de claves y orden de campos Dataverse emparejados por `typeName`. Respeta el orden de las demás listas. Compara las filas CSV y los mensajes de `mapping_problems.json` preservando su multiplicidad, e informa diferencias y ausencias. `summary.json` contiene conteos agrupados. `--detailed` escribe además `details.json` con valores y filas individuales. La salida debe estar fuera de ambos directorios de entrada. El script protege de sobrescritura los reportes existentes.

El código de salida `0` indica que la comparación se completó, incluso si encontró diferencias. `2` indica una comparación incompleta o un error. Para aceptar una regresión, se deben revisar el universo esperado, la completitud de los reportes, los conteos y la justificación de las diferencias. Las salidas detalladas deben mantenerse **fuera del repositorio y bajo acceso restringido**. El resumen también requiere revisión antes de compartirse porque puede incorporar etiquetas procedentes de la entrada.

## Matriz de hallazgos pendientes

La prioridad es una propuesta para organizar la revisión. **Alta** identifica decisiones que condicionan una operación, la aceptación de una regresión o la protección de información. **Media** identifica posibles efectos en la calidad o la trazabilidad. **Baja** identifica límites documentales o casos sin afectación observada. Los estados distinguen evidencia confirmada, limitaciones potenciales y decisiones institucionales abiertas.

| ID | Descripción | Evidencia | Impacto | Prioridad | Estado | Recomendación |
|---|---|---|---|---|---|---|
| ALT-H01 | Falta una comprobación explícita de versión EML para `shortName`. | No se encontraron casos reales fuera de EML 2.2.0. | Una entrada fuera de la versión prevista podría generar `alternativeTitle`. | Baja | Confirmado por inspección, sin impacto observado. | Acordar si la versión debe exigirse en el mapeo o en la validación de origen. |
| LANG-H02 | Un recurso documenta `oci` y se conserva `Occitan`. | 1 recurso con ese código. | Puede requerir confirmar el idioma declarado en la fuente. | Media | Confirmado, pendiente de curación. | Revisar la fuente y conservar la equivalencia mientras se verifica. |
| LANG-H03 | Hay una fila del vocabulario sin identificador. | 1 fila, sin impacto observado. | La fila carece de una clave para la búsqueda por identificador. | Baja | Confirmado. | Revisar la fila con el responsable del vocabulario. |
| DESC-H01 | Se pierde el marcado de énfasis. | 3 recursos, 4 párrafos y 8 etiquetas. El texto se conserva y el caso sintético tiene `xfail` estricto. | Pérdida de formato en las descripciones afectadas. | Media | Confirmado, pendiente de decisión. | Acordar qué marcado debe preservarse y revisar su paso por la ingesta. |
| DESC-H02 | Posible pérdida o transformación incompleta de enlaces. | Sin casos reales en las descripciones evaluadas. | Podría cambiar la representación de los enlaces de futuros recursos. | Baja | Limitación potencial. | Definir la regla y cubrirla con casos sintéticos si se aprueba. |
| DESC-H03 | El XML mixto puede requerir tratamiento adicional. | Sin casos reales en las descripciones evaluadas. | Podría afectar el orden o el marcado en otras formas de XML. | Baja | Limitación potencial. | Caracterizar las formas necesarias antes de ampliar la transformación. |
| DESC-H04 | Formato de `dsDescriptionValue` pendiente de acuerdo. | La ruta evaluada usa HTML. | Afecta presentación y conservación del marcado. | Media | Decisión institucional pendiente. | Resolver si se conserva HTML o se usa texto plano. |
| NOTE-H01 | La regla de HTML para `notesText` carece de explicitación en el crosswalk. | La implementación usa HTML. | La expectativa documental puede diferir de la salida. | Media | Confirmado, pendiente de decisión. | Acordar y documentar el formato en la fila correspondiente. |
| NOTE-H02 | Se admite texto directo en `additionalInfo` sin `para`. | Sin casos reales identificados. Se conserva un caso sintético con `xfail` estricto. | Una entrada de esa forma podría generar `notesText`. | Baja | Confirmado con evidencia sintética, pendiente de decisión. | Acordar si se admite el texto directo. |
| CUR-H01 | Tratamiento externo de `jgtiCuratorialUnit` pendiente. | 42 recursos identificados. | Se requiere una vía para conservar la información y verificar su exclusión del mapeo. | Alta | Presencia confirmada, verificación integral pendiente. | Definir el archivo externo y comprobar su cobertura. |
| PER-H01 | El crosswalk y el código nombran de forma distinta la tabla de roles. | `contributor_roles.csv` frente a `party_roles.csv`. | Dificulta identificar la tabla que gobierna el mapeo. | Baja | Diferencia documental confirmada. | Concertar la denominación y alinear la documentación. |
| PER-H02/H03 | Faltan tablas de autoridades de personas y organizaciones. | Ausencia observada de `people.csv` y `organisations.csv` en el flujo evaluado. | La identificación depende de las fuentes disponibles y sus reglas de comparación. | Media | Confirmado para el flujo evaluado. | Definir si se incorporan autoridades y quién las mantiene. |
| PER-H11 | La reparación de `@humboldt.org` se extiende a otros correos institucionales. | 14 contactos finales no correspondientes al correo I2D. | Puede cambiar direcciones distintas del contacto institucional de respaldo. | Media | Confirmado, política pendiente. | Validar el alcance de la reparación con el equipo. |
| PER-H22 | Una organización quedó excluida como contratista. | 1 organización. | Su información contractual puede requerir un tratamiento distinto. | Media | Confirmado, admisión pendiente de decisión. | Acordar si el destino debe admitir organizaciones como contratistas. |
| PER-H24 | La equivalencia de nombres usa subconjuntos de palabras. | 92 coincidencias por subconjuntos y 35 casos con múltiples coincidencias posibles. | Una equivalencia textual puede ser ambigua como identificación. | Media | Confirmado, revisión semántica pendiente. | Revisar coincidencias múltiples y acordar criterios de identidad o curación. |
| PER-H25 | Faltan datos del inventario biológico en recursos publicados. | 80 recursos. | Limita el enriquecimiento cuya única fuente es ese inventario. | Media | Confirmado. | Verificar la cobertura del inventario y determinar qué ausencias requieren curación. |
| PER-H26 | El reconocimiento de códigos distingue mayúsculas y minúsculas. | Comportamiento caracterizado, sin pérdida real identificada. | Podría excluir variantes de capitalización en otros datos. | Baja | Limitación potencial, sin pérdida observada. | Mantener la regla hasta contar con evidencia de impacto y una decisión. |
| PER-H27 | Hay información residual del inventario sin proyecto macro asociado. | 265 recursos. | Puede quedar información sin un destino acordado. Los valores residuales pueden incluir textos que no sean convenios válidos. | Media | Confirmado, destino pendiente de decisión. | Clasificar los valores y definir un destino sólo para la información pertinente. |
| PER-H29 | Los nombres de contratistas del inventario contienen separadores. | 27 recursos. | La separación podría cambiar el conteo de nombres y el resultado de la asociación con códigos. | Media | Confirmado, regla pendiente de decisión. | Distinguir delimitadores de personas de signos propios de un nombre antes de separar. |
| PER-H36 | Algunas apariciones institucionales se clasificaron internamente como personas. | 3 apariciones en 2 recursos. | Puede requerir revisar el reconocimiento de instituciones. | Media | Confirmado. | Revisar los casos y definir si se necesita una regla particular o una autoridad. |
| PER-H37 | Se generaron afiliaciones redundantes. | 2 afiliaciones en 1 recurso. | Añade información repetida al destino. | Baja | Confirmado. | Revisar el origen de la redundancia antes de modificar la regla. |
| PER-H38 | Hay diferencias de afiliación entre apariciones deduplicadas. | 36 conflictos. | La primera aparición puede conservar una afiliación distinta de otra fuente. | Media | Confirmado, revisión semántica pendiente. | Acordar si se mantiene la precedencia o se envían los conflictos a curación. |
| PER-H39 | Hay diferencias de correo entre apariciones deduplicadas. | 2 conflictos. Uno coincide con un conflicto de afiliación. | Puede prevalecer un correo distinto del que corresponda usar. | Media | Confirmado, revisión semántica pendiente. | Revisar las fuentes y acordar precedencia o curación. |

### Hallazgos de auditoría previa a publicación

| ID | Descripción | Evidencia | Impacto | Prioridad | Estado | Recomendación |
|---|---|---|---|---|---|---|
| REG-H01 | El comparador admite entradas idénticas o vacías y no exige todas las columnas de curación. | La revisión estática identificó que puede aceptar la misma carpeta en ambos lados y que `value` y `note` no son obligatorios al leer `curation.csv`. | Una ejecución completa puede dar falsa confianza sobre el universo o las columnas comparadas. | Alta | Confirmado por inspección. | Validar entradas distintas, universo esperado y las cinco columnas de curación antes de automatizar la aceptación. |
| REG-H02 | El reporte detallado puede contener información sensible y quedar dentro del repositorio. | `--detailed` conserva valores y filas individuales. El destino se comprueba respecto a las entradas y puede quedar dentro del árbol de Git. | Riesgo de incorporación accidental a la publicación. | Alta | Riesgo confirmado por inspección. | Escribir los reportes fuera del repositorio y mantener acceso restringido a los detalles. |
| REG-H03 | Las etiquetas del resumen pueden proceder de valores de entrada. | Los nombres de campos y valores de `kind` y `field` se usan como claves de agrupación. | Una etiqueta libre o mal formada puede exponer contenido sensible en un agregado. | Media | Riesgo potencial identificado por inspección. | Revisar el resumen antes de compartirlo y evaluar la validación o anonimización de etiquetas. |
| REG-H04 | La escritura de los reportes puede completarse sólo en parte. | El resumen y el detalle se escriben en secuencia. | Puede quedar una salida parcial que bloquee un reintento en el mismo destino. | Baja | Limitación potencial identificada por inspección. | Usar otro directorio al reintentar y evaluar la publicación conjunta de las salidas. |
| TEST-H01 | `pytest` no está declarado como dependencia. | Las pruebas lo importan y las dependencias del proyecto no lo incluyen. | Un entorno nuevo requiere preparación adicional. | Media | Confirmado por inspección. | Considerar una dependencia de desarrollo y documentar su instalación. |
| TEST-H02 | Las fixtures pueden dejar módulos importados en el mismo proceso. | Se sustituyen dependencias temporalmente y los módulos importados pueden quedar en caché. | Una suite futura que use configuración real podría recibir referencias sintéticas. | Media | Limitación potencial identificada por inspección. | Ejecutar la selección en un proceso dedicado y revisar el aislamiento al ampliar la suite. |
| TEST-H03 | Una prueba de permisos depende de POSIX. | La aserción comprueba bits de permisos del archivo detallado. | La portabilidad de esa prueba queda por verificar en otros sistemas. | Media | Supuesto confirmado por inspección. | Documentar el entorno verificado y revisar la aserción antes de ampliar plataformas. |
| DATE-H01 | La validación de fechas tiene alcance calendárico. | `datetime.date` comprueba el calendario y la expresión heredada admite determinados sufijos libres. | El resultado válido no certifica una fecha y hora ISO 8601 completa. | Baja | Alcance confirmado por inspección. | Describir el alcance y acordar por separado cualquier validación adicional de hora o zona. |
| DOC-H01 | DATE-01 redujo parte de la explicación heredada sobre fechas parciales. | Observación del diff de `iso_date()`. | Puede perderse el contexto de la decisión de conservar precisión parcial. | Baja | Confirmado por inspección. | Conservar esa justificación en la documentación técnica acordada. |
| DOC-H02 | Hay ejemplos heredados de procedencia no verificada. | La auditoría localizó ejemplos nominales y contractuales presentes en el commit base. | Su publicación requiere confirmar que sean adecuados como ejemplos. | Baja | Procedencia pendiente de verificar. | Revisar con el equipo si deben sustituirse por valores inequívocamente ficticios. |

## Preguntas para Marius y el equipo

1. ¿Se mantiene HTML para `dsDescriptionValue` o se adopta texto plano? La evaluación cubrió 1107 descripciones y no detectó pérdida de contenido textual.
2. ¿Debemos conservar las etiquetas de énfasis y enlaces originales del EML? Se perdieron ocho etiquetas de énfasis en cuatro párrafos de tres recursos. No se identificaron casos reales de enlaces en las descripciones evaluadas.
3. ¿Se admite texto directo de `additionalInfo` sin `para`? El comportamiento se reprodujo con una prueba sintética y no se encontraron casos reales en la evaluación.
4. ¿Se contempla incorporar tablas de autoridades de personas y organizaciones? La revisión de fuentes incluyó 11804 apariciones y el flujo evaluado carece de `people.csv` y `organisations.csv`.
5. ¿Debemos actualizar la denominación de la tabla de roles en el crosswalk? La referencia documental usa `contributor_roles.csv` y el código consume `party_roles.csv`.
6. ¿Es correcto extender la reparación del dominio de correo a todas las direcciones institucionales afectadas? Se identificaron 14 contactos finales no correspondientes al correo I2D.
7. ¿Se mantiene la primera aparición cuando existen afiliaciones o correos diferentes para una misma identidad? Se identificaron 36 conflictos de afiliación y dos de correo, con un caso que presenta ambas diferencias.
8. ¿Es suficiente la comparación de nombres de contratistas mediante subconjuntos de palabras? Se observaron 92 coincidencias por subconjuntos y 35 casos con múltiples coincidencias posibles.
9. ¿Se aprueba `contractor_association` como categoría de curación? Los 187 recursos ambiguos tienen una fila cada uno con conteos numéricamente correctos.
10. ¿Se deben admitir organizaciones como contratistas? La evaluación identificó una organización excluida.
11. ¿Cómo tratar los convenios del inventario cuando no existe un proyecto macro asociado? Hay 265 recursos con información residual sin proyecto macro. La clasificación de esa información queda pendiente.
12. ¿Deben separarse los nombres de contratistas que contienen delimitadores? Se identificaron 27 recursos con separadores en los nombres del inventario.
13. ¿Cómo se realizará la conservación externa de las unidades curatoriales? Se identificaron 42 recursos con `jgtiCuratorialUnit` y queda pendiente verificar el tratamiento completo.
14. ¿Se deben fortalecer los controles del comparador antes de utilizarlo como criterio automático de aceptación? La auditoría detectó casos de entradas incompletas y riesgos de exposición de reportes.
15. ¿Conviene declarar dependencias de desarrollo y mejorar el aislamiento de las fixtures? `pytest` requiere instalación adicional y la selección actual se recomienda en un proceso dedicado.

Estas preguntas quedan abiertas para concertación. Las recomendaciones de la matriz orientan la revisión y no constituyen autorizaciones de cambio.

## Próximas actividades

1. Validar `geospatial`.
2. Validar los elementos restantes de `institutional`.
3. Validar `externalReferences`.
4. Validar `biologicalMetadata`.
5. Ejecutar la regresión integral cuando los bloques pendientes cuenten con criterios acordados y cobertura.
6. Consolidar las pruebas y la documentación final.
7. Realizar la entrega técnica al equipo.
