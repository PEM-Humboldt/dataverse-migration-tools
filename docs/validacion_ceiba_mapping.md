# Validación parcial del mapeo CEIBA–Dataverse

Este informe acompaña el Draft Pull Request #13 de `feature/validacion-ceiba-mapping` a `develop`, según la auditoría previa del PR. Consolida la evaluación inicial, la validación de `geospatial`, la corrección INS-H20 y la validación de `externalReferences` hasta la regresión de EXT-H02.

## Índice

1. [Contexto y alcance](#contexto-y-alcance)
2. [Arquitectura evaluada](#arquitectura-evaluada)
3. [Metodología](#metodología)
4. [Caracterización de los datos](#caracterización-de-los-datos)
5. [Resultados de citation](#resultados-de-citation)
6. [Resultados de geospatial](#resultados-de-geospatial)
7. [Personas e instituciones](#personas-e-instituciones)
8. [Resultados de externalReferences](#resultados-de-externalreferences)
9. [Correcciones implementadas](#correcciones-implementadas)
10. [Regresión y reporte de curación](#regresión-y-reporte-de-curación)
11. [Pruebas unitarias](#pruebas-unitarias)
12. [Herramienta de comparación de regresiones](#herramienta-de-comparación-de-regresiones)
13. [Matriz de hallazgos pendientes](#matriz-de-hallazgos-pendientes)
14. [Preguntas para Marius y el equipo](#preguntas-para-marius-y-el-equipo)
15. [Próximas actividades](#próximas-actividades)

## Contexto y alcance

| Referencia | Valor |
|---|---|
| Repositorio | `PEM-Humboldt/dataverse-migration-tools` |
| Rama de trabajo | `feature/validacion-ceiba-mapping` |
| Rama de partida del desarrollo | `marbotte/ceiba-mapping-example` |
| Base efectiva del PR según la auditoría previa | `develop` |
| Draft Pull Request | [#13](https://github.com/PEM-Humboldt/dataverse-migration-tools/pull/13) |
| Commit histórico de partida | `449385271f8efd92894ba70785e95c2bead70ecd` |
| Commit de referencia de INS-H20 | `7d1e26204688569b88c0fab5b8627e752807deef` |
| HEAD de referencia para la validación de `externalReferences` | `1c6148804f10ded29c99d751320baf530cf44150` |
| Commit de los esquemas Dataverse | `ab2841405a24f149ff7fdb6264f179ede27c6e7c` |
| Crosswalk de referencia | `MigracionCeiba_20261125.xlsx` |
| Fecha de corte de la evaluación inicial | 26 de noviembre de 2026 |
| Actualización de la documentación geográfica | 27 de noviembre de 2026 |
| Corte documental anterior | 27 de noviembre de 2026 |
| Fecha de corte de esta actualización | 28 de noviembre de 2026 |

La evaluación fortalece la implementación desarrollada por Marius y conserva su arquitectura. Cubre `citation`, `geospatial`, `externalReferences` y los elementos relacionados con personas, instituciones y contratistas. Se completó la validación funcional de `geospatial` y `externalReferences` en los alcances documentados. Quedan pendientes los indicadores de coherencia geográfica, los elementos restantes de `institutional` y la validación funcional de `biologicalMetadata`. La carga efectiva en Dataverse queda fuera de esta entrega parcial.

INS-H20 se validó en el árbol de trabajo local sobre su commit de referencia. En ese corte, dos archivos de producción estaban modificados y la suite específica aún no estaba rastreada. Los cuatro archivos no rastreados ajenos al trabajo quedaron fuera de la entrega. La regresión diferencial abarcó los cinco bloques y el PASO 10.12.2.13.5.2.7 consolidó los resultados técnicos. Los cambios de INS-H20 quedaron registrados en el commit `1c6148804f10ded29c99d751320baf530cf44150`, que sirve como referencia para EXT-H02.

En el corte del PASO 11.6, `externalReferences` cuenta con validación funcional completa, EXT-H02 corregido, regresión transversal aprobada y línea base consolidada. Se aprobaron **1381 controles obligatorios acumulados**. La suite automatizada cuenta por separado **343 casos**, con **341 aprobados y 2 `xfail` históricos**. Esta actualización prepara el cierre documental. La publicación conjunta del bloque en el Draft PR #13 y la aprobación institucional siguen pendientes. La base del PR se documenta según la auditoría previa.

Los resultados cuantitativos proceden de las evaluaciones informadas. La FASE 11 consistió en una auditoría estática de solo lectura. Las cifras de pytest corresponden a las ejecuciones de pruebas sintéticas descritas en la sección de pruebas unitarias.

## Arquitectura evaluada

```text
EML original → ingesta → JSON intermedio → transformación de metadatos
             → validación estructural contra esquemas Dataverse → JSON finales y reportes
```

| Componente | Responsabilidad |
|---|---|
| [`ceiba_format.py`](../src/formato/ceiba_format.py) | `map_biologico_inventory()` carga el inventario y puede conservar los identificadores por fila. `normalize_ceiba_identifier()` genera la clave auxiliar y `resolve_ceiba_inventory()` prepara una vista específica para CEIBA. |
| [`ceiba_ingest.py`](../src/ingest/ceiba_ingest.py) | `read_resources()` enumera los directorios. `main()` resuelve las asociaciones, llama a `process_metadata()` y aplica `attach_inventory_data()` antes de escribir `resource_metadata.json`. |
| [`ceiba_source.py`](../src/mapeo/ceiba/ceiba_source.py) | Lee los registros de la ingesta en su representación intermedia, extrae `dataset` y `packageId`, y normaliza las formas de texto y las listas procedentes del EML. |
| [`ceiba_people.py`](../src/mapeo/ceiba/ceiba_people.py) | Mapea autores, apariciones de personas y organizaciones, roles, correos y datos institucionales. Detecta nombres de contratistas en el EML y genera notas de curación de personas cuando corresponde. |
| [`ceiba_fields.py`](../src/mapeo/ceiba/ceiba_fields.py) | Aplica las reglas de transformación y compone los bloques de metadatos. Integra códigos y nombres de contratistas, y consolida los casos de curación por registro. |
| [`ceiba_metadata_mapping.py`](../src/mapeo/ceiba_metadata_mapping.py) | Orquesta el mapeo por lotes, la comprobación de los campos contra los esquemas, la generación de los JSON finales y la escritura de los reportes. |
| [`compare_ceiba_mapping.py`](../scripts/compare_ceiba_mapping.py) | Compara dos salidas locales de mapeo y resume diferencias de JSON y reportes para revisar regresiones. |
| [`test_ceiba_inventory_resolution.py`](../tests/test_ceiba_inventory_resolution.py) | Verifica la resolución, el adjunto del inventario y su integración en la ingesta mediante datos sintéticos. |

`read_record()` consume el inventario adjunto en el JSON de ingesta. Las funciones existentes de `institutional` usan sus datos para acceso, proyectos y contratistas. `map_external_references()` puede añadir una copia externa a partir del DOI del inventario. Así, la recuperación de una fila biológica alimenta ambos bloques sin cambiar las funciones del mapeador. El JSON final también conserva el inventario en `inventory_data`.

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

Para INS-H20 se compararon las asociaciones de inventario en todo el universo de ingesta y se verificó por separado el efecto sobre los recursos con JSON final. El diferencial se cotejó semánticamente por recurso, bloque y campo. La curación y los valores hijos se compararon con multiconjuntos para conservar las repeticiones. Se construyó una línea base posterior y se auditó contra sus archivos, el estado del código y las referencias previas.

Para `externalReferences` se caracterizaron el TSV, el crosswalk y las salidas en el PASO 11.2. En el PASO 11.3 se reconstruyó el bloque a partir de los JSON de ingesta y del inventario adjunto. Los PASOS 11.4 y 11.5 aislaron el cambio de curación y lo comprobaron con pruebas sintéticas y una comparación en memoria. El PASO 11.6 regeneró únicamente las salidas de mapeo. Su resumen de validación, el comparador y el manifiesto documentan la regresión y la nueva línea base. La caracterización funcional y el ciclo sintético previo se citan como resultados de sus respectivos pasos.

Las reevaluaciones conservan los antecedentes históricos y explicitan el universo, el criterio y la unidad de las mediciones posteriores. La [reconciliación de I03](#reconciliación-de-i03-en-projectfunding) distingue celdas fuente, ocurrencias de segmentos, recursos, valores Dataverse y párrafos HTML. Las cifras de esta actualización proceden de las ejecuciones y conciliaciones acreditadas. La edición fue documental.

## Caracterización de los datos

| Indicador | Cantidad |
|---|---:|
| Recursos ingresados | 1191 |
| Recursos con `published=True` en la ingesta | 1107 |
| Recursos con `published=False` en la ingesta | 84 |
| EML 2.1.1 publicados | 1032 |
| EML 2.2.0 publicados | 75 |
| JSON finales generados | 1107 |
| Recursos previstos como borradores | 27 |
| Recursos previstos para liberación | 1080 |
| Problemas estructurales de mapeo reportados | 0 |

El conteo de problemas estructurales cubre las verificaciones del esquema. La evaluación semántica y la curación se contabilizan por separado.

El indicador `published` registra si la ingesta encontró un archivo EML publicado para el recurso. El reconocimiento de la raíz EML por el mapeador se verifica por separado. En este universo, los 1107 recursos con `published=True` disponían de EML con raíz reconocida, fueron elegibles y generaron un JSON final. Los otros 84 carecían de un JSON final.

El estado del IPT era `PUBLIC` para 1080 recursos y `PRIVATE` para 111. El plan de carga prevé liberar los 1080 recursos `PUBLIC` y mantener como borradores los 27 `PRIVATE` que tienen JSON final. Los otros 84 `PRIVATE` carecen de JSON final. La disponibilidad de un JSON final y su destino previsto corresponden a etapas previas a la publicación efectiva en Dataverse.

### Cobertura del inventario biológico antes y después de INS-H20

| Universo | Total | Asociados antes | Asociados después | Ausencias antes | Ausencias después | Recuperaciones |
|---|---:|---:|---:|---:|---:|---:|
| Ingesta completa | 1191 | 1088 | 1153 | 103 | 38 | 65 |
| Con JSON final | 1107 | 1027 | 1091 | 80 | 16 | 64 |
| Sin JSON final | 84 | 61 | 62 | 23 | 22 | 1 |

La cobertura global pasó de **91,35 % a 96,81 %**, un incremento de **5,46 puntos porcentuales**. Las ausencias disminuyeron **63,11 %** respecto a las 103 de partida. Se conservaron las 1088 asociaciones originales, sin ambigüedades detectadas en la ejecución real. Se verificaron 1114 valores terminales del inventario recuperado y los 1191 archivos `files.json` se conservaron byte a byte.

De las 65 recuperaciones, 64 fueron elegibles para el mapeo. La restante carecía de una raíz EML reconocida. Los 1043 JSON finales fuera de la cohorte recuperada se conservaron. Los dos escenarios produjeron 1107 JSON finales y registraron cero problemas de mapeo. El balance de curación y los cambios por bloque se detallan en la [regresión transversal de INS-H20](#regresión-transversal-de-ins-h20). PER-H25 distingue las 16 ausencias elegibles de las 22 correspondientes a recursos sin JSON final.

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

## Resultados de geospatial

### Alcance del crosswalk y reglas de mapeo

Se evaluaron las filas 67 a 79 del crosswalk actualizado el 25 de noviembre de 2026. Cinco elementos tienen fuente directa bajo `dataset/coverage/geographicCoverage`.

| Elemento de destino | Elemento EML relativo a la cobertura |
|---|---|
| `geographicCoverageDescription` | `geographicDescription` |
| `westLongitude` | `boundingCoordinates/westBoundingCoordinate` |
| `eastLongitude` | `boundingCoordinates/eastBoundingCoordinate` |
| `northLatitude` | `boundingCoordinates/northBoundingCoordinate` |
| `southLatitude` | `boundingCoordinates/southBoundingCoordinate` |

`map_geospatial()` asigna los cuatro lados de `geographicBoundingBox` por nombre del elemento EML, con independencia del orden de aparición y de las descripciones traducidas del esquema. `box_problem()` comprueba que los cuatro valores sean numéricos, se encuentren dentro de los límites globales y cumplan oeste < este y sur < norte. El mapeo conserva las coordenadas aceptadas y excluye los rectángulos rechazados de los JSON finales. [Mapeo CEIBA](../src/mapeo/ceiba/ceiba_fields.py) · [Validación de rectángulos](../src/mapeo/geonetwork/gn_mapping.py)

Ocho elementos carecen de fuente definida en la migración actual. Son `country`, `state`, `city`, `otherGeographicCoverage`, `geographicUnit`, `minimumAltitude`, `maximumAltitude` y `wkt`. La regla vigente descarta la derivación automática de divisiones administrativas, altitudes y geometrías WKT.

### Caracterización de las coberturas originales

La evaluación abarcó los 1107 recursos publicados de la población caracterizada arriba, con 1032 registros EML 2.1.1 y 75 EML 2.2.0.

| Indicador | Cantidad |
|---|---:|
| Coberturas geográficas | 1107 |
| Descripciones no vacías | 1107 |
| Caracteres normalizados en las descripciones | 305287 |
| Rectángulos completos | 1107 |
| Rectángulos con coordenadas numéricas y finitas | 1107 |
| Rectángulos aceptados por las reglas actuales | 1070 |
| Rectángulos rechazados | 37 |
| Rectángulos completamente vacíos | 0 |
| Coordenadas fuera de los límites globales | 0 |
| Coberturas con altitudes | 0 |

Cada recurso tenía una sola cobertura geográfica.

| Geometría rechazada | Motivo registrado en curación | Cantidad |
|---|---|---:|
| Punto | `oeste ≥ este; sur ≥ norte` | 26 |
| Ancho cero y altura positiva | `oeste ≥ este` | 7 |
| Alto cero y ancho positivo | `sur ≥ norte` | 3 |
| Inversión real de longitud | `oeste ≥ este` | 1 |
| **Total** | | **37** |

Por motivo registrado, hubo 26 casos con ambas condiciones, ocho con `oeste ≥ este` y tres con `sur ≥ norte`. Los comparadores incluyen tanto la igualdad como la inversión. En 36 casos se observó igualdad entre lados en uno o ambos ejes. Estas coberturas puntuales o lineales pueden representar geometrías legítimas de origen y su tratamiento queda pendiente de concertación.

### Validación EML → ingesta

| Indicador | Resultado |
|---|---:|
| Recursos evaluados | 1107 |
| Coberturas en XML y en JSON de ingesta, por etapa | 1107 |
| Rectángulos en XML y en JSON de ingesta, por etapa | 1107 |
| Comparaciones por cada uno de los cinco elementos | 1107 |
| Comparaciones totales | 5535 |
| Coincidencias | 5535 |
| Diferencias | 0 |
| Recursos afectados por diferencias | 0 |
| Caracteres normalizados de las descripciones, por etapa | 305287 |

El cotejo no identificó pérdida de información en los cinco elementos durante la ingesta.

### Validación ingesta → JSON final de Dataverse

| Verificación | Resultado |
|---|---:|
| Descripciones geográficas conservadas y transformadas a HTML | 1107 |
| Rectángulos aceptados y conservados exactamente | 1070 |
| Coordenadas individuales conservadas en los rectángulos aceptados | 4280 |
| Rectángulos rechazados correctamente omitidos | 37 |
| Verificaciones de ausencia de los ocho elementos sin fuente | 8856 |
| Verificaciones de ausencia de los compuestos `geographicCoverage` y `altitudeRange` | 2214 |
| **Comparaciones totales** | **17564** |

Las 17564 comparaciones fueron correctas, con cero diferencias. Los 305287 caracteres de las descripciones se conservaron tras normalizar el contenido textual del HTML. La presentación visual quedó fuera del cotejo. Se verificó que el JSON final no incluyera ninguno de los 37 rectángulos rechazados.

### Validación de curación y balance del bloque

Se cotejaron las filas de tipo `bounding_box` por identificador del recurso, campo `geographicBoundingBox`, motivo y concordancia con los cuatro valores originales de las coordenadas.

| Resultado del cotejo de curación | Filas |
|---|---:|
| Esperadas | 37 |
| Observadas | 37 |
| Coincidencias completas | 37 |
| Faltantes | 0 |
| Inesperadas | 0 |

El balance suma **23136 verificaciones sin diferencias**. Incluye 5535 verificaciones EML → ingesta, 17564 ingesta → JSON final y 37 cotejos completos de filas de curación. El total acumula pasos de verificación sobre los mismos recursos, incluidos cotejos de rectángulos completos y de sus lados individuales.

### Evaluación complementaria de coherencia geográfica

Se empleó una referencia rectangular aproximada para Colombia, con latitudes de −4,5 a 13,5 y longitudes de −82 a −66. La referencia sirve exclusivamente para formular hipótesis de revisión. El mapeo conserva sus reglas de aceptación globales y la referencia carece de valor como frontera oficial.

| Relación con la referencia | Rectángulos aceptados |
|---|---:|
| Completamente dentro | 973 |
| Intersectan sin estar completamente contenidos | 93 |
| Fuera | 4 |
| **Total** | **1070** |

El indicador de contención de la referencia completa se cumple en 26 rectángulos. Se superpone con la clasificación anterior. De los cuatro rectángulos fuera de la referencia, uno menciona Colombia en la descripción.

| Indicador sobre longitudes y ejes | Recursos |
|---|---:|
| Con longitudes positivas | 20 |
| Con oeste negativo y este positivo | 18 |
| Con ambas longitudes positivas | 2 |
| Con longitudes positivas y mención de Colombia | 5 |
| Con longitudes positivas sin mención de Colombia | 15 |
| Compatibles con la referencia mediante la heurística de cambio de signo aplicada | 0 |
| Con posible intercambio de latitud y longitud | 1 |
| **Recursos únicos entre longitudes positivas y posible intercambio** | **20** |

La descripción del posible intercambio menciona Colombia y el caso pertenece al grupo con longitudes positivas. Entre las 26 coberturas puntuales, 25 están dentro de la referencia y una está fuera. Ninguna coincide con el origen (0, 0). Los indicadores señalan casos para revisión. Su confirmación requiere un cotejo individual con la cobertura real, que aún no se ha realizado.

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

La tabla corresponde a la salida posterior a PER-H16 y PER-H28, antes de INS-H20.

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

Después de PER-H16 y PER-H28, antes de INS-H20, se contabilizaron 1004 nombres, 590 códigos contractuales, 1327 entradas compuestas y 680 recursos con información contractual.

| Situación | Recursos |
|---|---:|
| Asociación directa uno a uno | 267 |
| Asociación indeterminada | 187 |
| Sólo nombres | 221 |
| Sólo códigos | 5 |
| Sin nombres ni códigos | 427 |

No se establecieron asociaciones arbitrarias entre nombres y códigos. En los casos indeterminados ambos se conservaron en entradas separadas.

El efecto posterior de INS-H20 se documenta en la [regresión transversal](#regresión-transversal-de-ins-h20) y en la [matriz de hallazgos](#matriz-de-hallazgos-pendientes).

## Resultados de externalReferences

### Alcance, fuentes y esquema del bloque 4

Se evaluaron los 1191 recursos de ingesta, de los cuales 1107 eran elegibles y 84 carecían de JSON final. El alcance comprende las filas 95 a 103 del crosswalk `MigracionCeiba_20261125.xlsx` y el esquema `externalReferences.tsv` del commit indicado en el contexto. La huella SHA-256 del TSV es `22019abe2e490d7d24cf8fe7956bf99bc0f20c996cb25125f6571ac5a9f4666a`.

El padre `externalReference` es compuesto, opcional y repetible (`0..n`). Cada fila tiene nueve hijos posibles, opcionales y de cardinalidad `0..1`. En la tabla, «bibliografía» designa `additionalMetadata/metadata/gbif/bibliography/citation`. Sus identificadores proceden de `@identifier`.

| Campo | Fuente | Regla de transformación | Cardinalidad por fila | Valores | Observaciones |
|---|---|---|---|---:|---|
| `externalReferenceType` | Procedencia de la fila | La referencia de origen y la copia DOI usan `External Copy of the dataset`. Las citas usan `This dataset references`. | `0..1` | 11077 | Único hijo con vocabulario controlado. |
| `citationText` | Etiqueta fija de origen o texto de la bibliografía | Conserva la etiqueta de origen. Para citas, normaliza espacios, escapa el texto y lo envuelve en un párrafo HTML. | `0..1` | 10395 | La copia DOI del inventario carece de texto de cita. |
| `externalReferenceURL` | Clave CEIBA y versión de origen, o identificador bibliográfico | Genera la URL de origen. Conserva las URL bibliográficas admitidas y añade `https://` a las formas `www.` reconstruibles. Aplica la codificación porcentual vigente. | `0..1` | 1559 | Las URL malformadas del alcance quedan en curación. |
| `externalReferenceDOI` | Identificador bibliográfico o `inventory.biologico.doi` | Reconoce el patrón DOI y retira el prefijo del resolutor o de la etiqueta, y los puntos finales. | `0..1` | 1032 | 350 DOI bibliográficos y 682 de copia. |
| `externalReferenceOtherId` | Clave del directorio CEIBA o identificador bibliográfico ISBN/ISSN | Conserva la clave de origen y los ISBN/ISSN con espacios normalizados. | `0..1` | 1176 | 1107 claves de origen y 69 ISBN/ISSN. |
| `externalReferenceNote` | Texto fijo de origen | Indica que el recurso se migró desde el IPT CEIBA. | `0..1` | 1107 | La curación de URL se registra en el reporte separado. |
| `externalEncoding` | Sin fuente aprobada | Se omite. | `0..1` | 0 | Información de archivos internos fuera de este campo. |
| `externalFileFormat` | Sin fuente aprobada | Se omite. | `0..1` | 0 | El formato de archivo necesita corresponder a la referencia externa concreta. |
| `externalFileFormatVersion` | Sin fuente aprobada | Se omite. | `0..1` | 0 | La versión del formato requiere la misma correspondencia. |

`read_record()` y `gbif_metadata()` obtienen las fuentes. `source_reference()` genera la fila de origen, `map_external_references()` incorpora la bibliografía y la copia del inventario, y `doi_of()` reconoce y limpia los DOI. Se aplican `quote_urls()` y `drop_empty()` antes de reconstruir el compuesto para Dataverse. Los metadatos de archivos o distribuciones presentes en EML y GBIF se evaluaron por separado. Las filas 101 a 103 del crosswalk carecen de una fuente aprobada para describir el formato, su versión o la codificación de una referencia externa. [Fuentes CEIBA](../src/mapeo/ceiba/ceiba_source.py) · [Transformación](../src/mapeo/ceiba/ceiba_fields.py) · [Codificación de URL](../src/mapeo/geonetwork/gn_mapping.py) · [Reconstrucción](../src/mapeo/reconstruct_mapping.py)

### Validación funcional y referencia de origen

En el PASO 11.3 se reconstruyeron de manera independiente las **1107 listas** desde los JSON de ingesta, el inventario adjunto, las versiones de origen de `inventory.csv` y las reglas del TSV y del crosswalk. Se cotejaron la secuencia, el multiconjunto y la estructura nativa por recurso. Coincidieron **11077 referencias** y **26346 valores hijos**, con cero diferencias estructurales. El orden fue **1107 referencias de origen** en primera posición, **9288 citas bibliográficas** en su orden de ingesta y **682 copias DOI** en última posición cuando correspondía. Hubo 703 recursos con bibliografía y 404 sin bibliografía utilizable.

Cada referencia de origen incluye el tipo fijo `External Copy of the dataset`, `citationText` igual a `IPT Ceiba (I2D)`, la URL de la página CEIBA con la clave del directorio y la versión de `inventory.csv`, esa misma clave en `externalReferenceOtherId` y la nota `Migrado desde IPT Ceiba (I2D)`. La versión de `inventory.csv` coincide con `source_version` de `load_plan.csv` en los 1107 recursos. La versión extraída de `@packageId` difirió textualmente de `inventory.csv` en **593** casos tras retirar el prefijo `v` cuando estaba presente. La diferencia documenta la procedencia de cada valor. La URL sigue la versión de `inventory.csv`, que es la fuente de la implementación vigente. El sufijo de versión del JSON pertenece al destino Dataverse.

La sintaxis básica y los parámetros de las URL de origen se verificaron localmente. La resolución efectiva de URL y DOI queda fuera del alcance. La coincidencia con la implementación, el cumplimiento del crosswalk y la conservación de la fuente se comprobaron por separado. Esa distinción permitió identificar EXT-H02 aunque el JSON final coincidiera con la reconstrucción de la regla vigente.

### Identificadores y multiplicidad bibliográfica

| Identificadores presentes | Ocurrencias |
|---|---:|
| DOI | 350 |
| URL HTTP/HTTPS admitidas | 450 |
| URL `www.` reconstruidas | 2 |
| URL `www.` malformada | 1 |
| ISBN | 65 |
| ISSN | 4 |
| Identificadores HTTP/HTTPS omitidos | 4 |
| Otra clase | 1099 |
| **Total presente** | **1975** |

Las otras **7313 citas** carecían de identificador. La clasificación aplica primero DOI, luego URL HTTP/HTTPS admitidas, formas `www.` reconstruibles o malformadas e ISBN/ISSN. Antes de EXT-H02, cuatro identificadores HTTP/HTTPS con espacios internos quedaban fuera del JSON y de la curación. La [corrección EXT-H02](#ext-h02) mantiene la omisión del campo URL y registra las cuatro ocurrencias para revisión.

**EXT-H01.** Se encontraron **28 repeticiones adicionales en 20 recursos**. Veinticinco ya eran repeticiones exactas en la ingesta y tres resultaron de la normalización. En dos grupos los identificadores de origen eran distintos. Todas las ocurrencias finales tienen contraparte en la fuente. Se conserva el orden y la multiplicidad mientras se acuerda una política institucional de deduplicación.

**EXT-H04.** Se cotejó el HTML esperado y, mediante extracción de su contenido, el texto normalizado de las **9288 citas**. Todas conservaron el texto disponible en el JSON de ingesta. El hallazgo queda técnicamente cerrado para JSON de ingesta CEIBA → JSON final Dataverse. El XML original queda fuera de ese cotejo. Los casos sintéticos de texto anidado y delimitadores reservados caracterizan el comportamiento vigente para formas fuera de las observadas, con alcance distinto de las reglas institucionales.

### DOI del inventario y GBIF dataset key

De **1046** valores no vacíos en el campo DOI del inventario se reconocieron **682**, cada uno en una copia de tipo `External Copy of the dataset` al final del compuesto. Entre los **364** valores no reconocidos, **353** coincidieron con la lista léxica estricta de marcadores y **11** quedaron fuera de esa clasificación. Los once incluyen diez textos libres o etiquetas y un token con apariencia DOI en un contexto distinto. La clasificación de marcadores es léxica. La ausencia semántica y el valor con apariencia DOI requieren revisión de fuente. El antecedente de los siete DOI no reconocidos de INS-H20 corresponde a un subconjunto y se conserva en su corte histórico.

**EXT-H03.** `gbif_key` tiene 1045 valores con contenido y 682 con forma UUID. Por recurso, **681** presentan DOI reconocido y UUID, **1** solo DOI reconocido, **1** solo UUID y **424** ninguno de esos dos valores reconocidos. Un UUID y un DOI pueden coexistir sin acreditar la misma identidad. El inventario adjunto conserva los valores en `inventory_data`. La fila 99 del crosswalk deja la asignación como opción no decidida y el destino institucional permanece abierto.

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

### INS-H20

La ingesta vinculaba las filas biológicas a los directorios CEIBA mediante una búsqueda literal de la clave extraída del parámetro `r` de la URL del inventario. Las diferencias de espacios y capitalización impedían que una fila existente se adjuntara. La corrección se aplica antes de escribir los metadatos de ingesta y mantiene como primera opción la coincidencia exacta.

`map_biologico_inventory()` incorpora el parámetro opcional `biological_identifiers`. Cuando se suministra una lista, agrega una entrada por fila antes de asignarla al diccionario. Esto preserva la multiplicidad aunque el índice por clave literal retenga la última fila ante duplicados exactos. Ese comportamiento histórico se conserva para búsquedas exactas. El diccionario de retorno mantiene su estructura.

```python
def normalize_ceiba_identifier(identifier):
    """Quita los espacios en blanco y convierte a minúsculas para comparar claves."""
    return "".join(identifier.split()).lower()
```

La clave auxiliar elimina espacios en blanco, incluidas tabulaciones y saltos de línea. Conserva tildes y puntuación. Las secuencias URL permanecen codificadas. `resolve_ceiba_inventory()` agrupa las filas biológicas y cuenta las claves de todos los directorios CEIBA, incluidos los nunca publicados. Revisa primero la clave literal. En su ausencia, recupera una fila solo si la clave normalizada es no vacía y corresponde a una sola fila biológica y a una sola entrada CEIBA. Si hay candidatas y alguna de las dos agrupaciones es ambigua, rechaza la recuperación. Los contadores de ambas fuentes de ambigüedad pueden aumentar para un mismo recurso.

En `main()` se resuelve una vez el inventario antes del bucle de procesamiento.

```python
    biological_identifiers = []
    full_index = map_biologico_inventory(config.i2d_inventory, biological_identifiers=biological_identifiers)
    ceiba_index, counts = resolve_ceiba_inventory(full_index, (r.name for r in resources), biological_identifiers)
```

La vista usa el identificador original del directorio para adjuntar la fila recuperada y conserva los valores de la fila, incluida su URL. GENERAL sigue consultándose por la clave original CEIBA y Proyectos Macro por el código de la fila biológica. El mensaje nuevo registra conteos agregados. Las pruebas y el impacto observado se detallan en [Suite INS-H20](#suite-ins-h20) y [Regresión transversal de INS-H20](#regresión-transversal-de-ins-h20).

| Archivo | Cambio verificado | Inserciones | Eliminaciones |
|---|---|---:|---:|
| `src/formato/ceiba_format.py` | Ajusta `map_biologico_inventory()` y añade `normalize_ceiba_identifier()` y `resolve_ceiba_inventory()`. | 49 | 1 |
| `src/ingest/ceiba_ingest.py` | Integra la resolución y los conteos en `main()`. El diff incluye un salto de línea final. | 12 | 4 |
| **Total de archivos de producción rastreados** | **Diff de INS-H20** | **61** | **5** |

`tests/test_ceiba_inventory_resolution.py` es un módulo nuevo de **355 líneas, 9 funciones y 25 casos**. Su copia no rastreada se verificó por separado del diff.

Los cambios de producción de INS-H20 se limitaron a `src/formato/ceiba_format.py` y `src/ingest/ceiba_ingest.py`. El cambio directo ocurre en la asociación del inventario durante la ingesta. Los proyectos, contratistas, condiciones de acceso y referencias externas cambian como efecto de las filas biológicas recuperadas que consume el mapeador vigente. La huella de `src/mapeo/ceiba/ceiba_fields.py` se conservó durante la evaluación de INS-H20.

### EXT-H02

La fila 97 del crosswalk establece que una URL mal escrita se omite y se registra para curación. La rama anterior solo generaba ese registro para formas malformadas que comenzaban por `www.`. En el universo evaluado, cuatro identificadores con prefijo HTTP/HTTPS y espacios internos quedaban fuera de la regla de admisión y de la curación.

La corrección añade este fragmento al final de la clasificación de identificadores en `map_external_references()`. Así preserva la precedencia de DOI, URL admitidas, `www.` e ISBN/ISSN, incluida la clasificación previa de identificadores híbridos. Conserva `citationText` y la omisión de `externalReferenceURL`. Registra una fila por ocurrencia con el valor normalizado por la regla existente. La reparación del destino y la separación de enlaces quedan para revisión. [Código del mapeo CEIBA](../src/mapeo/ceiba/ceiba_fields.py)

```python
        elif re.match(r"^https?://", identifier, re.IGNORECASE):
            curation.append({"resource": record["name"], "kind": "reference_url", "field": "externalReferenceURL",
                             "value": identifier, "note": "URL mal escrita: no migrada"})
```

La comparación en memoria preservó las tres filas históricas de `reference_url` y añadió cuatro en tres recursos. El balance de siete filas incluye dos reparaciones y cinco omisiones. La [regresión transversal](#regresión-transversal-de-ext-h02) reprodujo las cuatro adiciones exactas y verificó cero cambios en las referencias migradas. **EXT-H02 queda técnicamente cerrado** con esa regresión aprobada.

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

| Indicador de curación | Línea base posterior a KW-001 | Salida posterior a PER-H16 y PER-H28 |
|---|---:|---:|
| Registros | 1163 | 1350 |
| Recursos únicos | 865 | 910 |
| Recursos sin curación | 242 | 197 |

Las filas de curación hacen trazables decisiones pendientes, valores de respaldo y casos que requieren revisión. El total de filas mide la carga de revisión y no equivale a un conteo de errores de implementación. La cantidad de filas puede exceder la de recursos únicos porque un recurso puede requerir más de una revisión.

### Integridad de la línea base usada para geospatial

Se verificó el conjunto de archivos de la línea base posterior a PER-H16 y PER-H28 contra su manifiesto.

| Indicador | Resultado |
|---|---:|
| JSON de metadatos | 1107 |
| Reportes de migración | 4 |
| Archivos registrados | 1111 |
| Archivos encontrados | 1111 |
| Huellas SHA-256 coincidentes | 1111 |
| Huellas diferentes | 0 |
| Archivos faltantes | 0 |
| Archivos no registrados | 0 |
| Registros inesperados | 0 |

El SHA-256 de `src/mapeo/ceiba/ceiba_fields.py` es `dc09979bd912208a3aefc50c34df0242d8cf2c26f7f21079e5d073aade5ce99f` y coincide con el consignado en el manifiesto. El commit `449385271f8efd92894ba70785e95c2bead70ecd` registrado en el manifiesto corresponde al estado anterior a la publicación de las correcciones. La huella identifica el contenido del mapeador empleado para la línea base posterior a las correcciones.

Esta verificación acredita la integridad de los artefactos existentes frente a su manifiesto. La validación geográfica conservó el código de producción, por lo que se utilizaron esos artefactos sin ejecutar nuevamente la ingesta ni el mapeo completo. Una regresión por regeneración requeriría producir otra salida y compararla con la línea base.

### Regresión transversal de INS-H20

Los 1107 JSON finales conservaron sus identificadores. Se conservaron semánticamente 1043 y se modificaron los 64 correspondientes a las recuperaciones elegibles. Los 64 cambiaron en `inventory_data` y 63 en `datasetVersion`. Los cambios de bloque se distribuyeron así.

| Bloque | Recursos modificados |
|---|---:|
| `citation` | 0 |
| `geospatial` | 0 |
| `institutional` | 57 |
| `externalReferences` | 50 |
| `biologicalMetadata` | 0 |

De 5535 comparaciones recurso-bloque, 5428 se conservaron y 107 cambiaron. Entre los 64 recursos modificados, 44 cambiaron en ambos bloques, 13 solo en `institutional`, 6 solo en `externalReferences` y 1 solo en `inventory_data`. Los conteos por bloque se superponen. La estabilidad observada se refiere al efecto de INS-H20 y la validación semántica integral mantiene su propio alcance.

| Elemento compuesto | Recursos modificados |
|---|---:|
| `project` | 55 |
| `contractor` | 9 |
| `access` | 7 |
| `externalReference` | 50 |

La suma de la tabla corresponde a **121 incidencias recurso–campo**. Un mismo recurso puede tener cambios en más de un campo. Los subtotales de valores hijos incorporados fueron los siguientes.

| Campo compuesto | Valores nuevos |
|---|---:|
| `project` | 208 |
| `contractor` | 11 |
| `access` | 14 |
| `externalReference` | 100 |
| **Total** | **333** |

Los tres compuestos de `institutional` suman **233 valores hijos**. Los otros **100** pertenecen a `externalReferences`.

| Elemento hijo | Valores incorporados |
|---|---:|
| `projectFunding` | 55 |
| `projectID` | 55 |
| `projectShortName` | 55 |
| `projectName` | 43 |
| `contractCode` | 9 |
| `contractorName` | 2 |
| `restrictedUntil` | 7 |
| `restrictionJustification` | 7 |
| `externalReferenceDOI` | 50 |
| `externalReferenceType` | 50 |
| **Total** | **333** |

La comparación preservó las multiplicidades y registró **cero bajas de valores hijos**. Las filas de `contractor` se compararon por separado. Se incorporaron 15 y se retiraron 5 como parte del diferencial de filas compuestas. Se conservaron los nombres y códigos anteriores, las referencias externas y los valores de `accessType`.

### Reconciliación de I03 en projectFunding

El control I03 de PER-H27 quedó registrado como **13 esperados, 0 observados, REVISAR**. La reconciliación del PASO 10.12.2.13.5.2.5.1 aprobó sus 24 controles. El estado original queda como antecedente. El procedimiento histórico que atribuyó a los 13 segmentos el significado de incorporaciones no se recuperó.

| Indicador | Cantidad |
|---|---:|
| Segmentos residuales recuperados | 17 |
| Segmentos distintos de FN/OS | 13 |
| Iguales al código Macro | 7 |
| Sin código Macro | 6 |
| Códigos FN | 4 |
| Códigos OS | 0 |
| Valores nuevos de `projectFunding` | 55 |
| Párrafos base Macro incorporados | 55 |
| Párrafos con contraparte | 44 |
| Párrafos sin contraparte | 11 |
| Párrafos adicionales de convenios incorporados | 0 |
| Párrafos adicionales históricos conservados | 29 |

Una celda fuente puede contener varias ocurrencias de segmentos. En las 64 recuperaciones elegibles, los 17 segmentos residuales se distribuyeron en 15 recursos. Siete segmentos distintos de FN/OS igualaban el código Macro y quedaron representados por el párrafo base. Los otros seis estaban en recursos sin código Macro y carecían de un proyecto institucional al que agregarlos. Los 13 segmentos distintos de FN/OS produjeron **cero párrafos adicionales de convenios**.

Cada valor nuevo de `projectFunding` contiene un párrafo base Macro. Los 29 párrafos adicionales históricos se conservaron por recurso, código Macro, texto y multiplicidad. La reconciliación confirma los conteos aprobados de 55 valores nuevos de `projectFunding`, 208 valores hijos nuevos de `project` y 333 valores hijos nuevos en total.

### Curación posterior a INS-H20

La serie histórica es **1163 → 1350 → 1348 filas**. La primera transición corresponde a la regresión de PER-H16 y PER-H28, con 187 filas añadidas por PER-H16. En la segunda, correspondiente a INS-H20, se conservaron 1335 filas de las 1350 anteriores, se retiraron 15 y se incorporaron 13. Las 28 diferencias se justificaron y afectaron a 12 recursos recuperados.

| Tipo | Retiradas | Incorporadas |
|---|---:|---:|
| `restriction_reason` | 7 | 7 |
| `restricted_until` | 7 | 0 |
| `contractor_association` | 1 | 5 |
| `contract_code` | 0 | 1 |
| **Total** | **15** | **13** |

Al agrupar las diferencias por recurso, `kind` y `field`, se verificaron 8 reformulaciones, 7 resoluciones y 5 observaciones nuevas, para 20 cambios lógicos.

| Categoría | Reformuladas | Resueltas | Nuevas |
|---|---:|---:|---:|
| `restriction_reason` | 7 | 0 | 0 |
| `restricted_until` | 0 | 7 | 0 |
| `contractor_association` | 1 | 0 | 4 |
| `contract_code` | 0 | 0 | 1 |

Una observación resuelta indica que la fila dejó de generarse bajo la regla vigente. La decisión institucional sobre el hallazgo se tramita por separado. Las siete razones propuestas de restricción siguen pendientes de validación institucional.

### Líneas base e integridad de INS-H20

| Referencia local | Archivos registrados | SHA-256 del manifiesto |
|---|---:|---|
| Línea base histórica posterior a PER-H16 y PER-H28 | 1111 | `3870ffbdbed1e20fdb4072c1daa856b10ed543a628f32961121f6bcbc60eb70f` |
| Respaldo previo a INS-H20 | 3494 | `4518db7fb3d83b2c1b97a984c58b97af6c9ef5ecf8a842c39b611182debc18fa` |
| Línea base posterior a INS-H20 | 3502 | `4946659a5b67f19c9eab7dd12baefa2f001d72e2ce641bac52410dd163131a84` |
| **Total** | **8107** | |

La auditoría independiente verificó 8107 hashes y 6996 tamaños. Las primeras dos pasadas observaron 40 y 26 archivos con atributos inestables, respectivamente. La causa quedó indeterminada. La tercera pasada completó la verificación sin inestabilidad.

La línea base posterior contiene 3503 archivos físicos, incluido su manifiesto. La comparación definitiva verificó la conservación semántica de los 1107 JSON entre la línea histórica y el respaldo previo, y reprodujo el diferencial aprobado al comparar cada uno con la línea posterior. Los 3497 archivos fuente respaldados coincidieron en bytes, tamaño y SHA-256 con el estado del proyecto durante esa auditoría. Se satisficieron **17 de 17 criterios de aceptación**. La referencia de código combina el commit de INS-H20, el diff binario de 5494 bytes y la copia de la suite específica. El diff tiene SHA-256 `09277fb78ca2473aa71d5479fbdcfe04a4b5e484366b7aeba57ae5e4018c6879`.

Los respaldos, las líneas base y sus evidencias se conservan localmente y quedan fuera de la publicación en GitHub. La comparación verifica los archivos frente a los manifiestos y las huellas externas disponibles. La integridad desde la creación de un manifiesto requeriría una referencia histórica independiente de ese momento.

Las reevaluaciones posteriores verificaron las huellas de los manifiestos y el subconjunto de archivos necesario para cada contraste. La comprobación integral de 8107 entradas y 6996 tamaños corresponde a la auditoría anterior. En esta edición se cotejaron las huellas de los manifiestos como referencias de integridad.

### Regresión transversal de EXT-H02

El 28 de noviembre de 2026 se cotejaron los **3494 archivos vigentes de datos y reportes** con INS-H20 por ruta relativa, tamaño y SHA-256. La coincidencia completa permitió reutilizar esa línea base como respaldo. Se ejecutó el punto de entrada CEIBA sin `--with-files` y con la ingesta existente.

```bash
.venv/bin/python -B -m src.mapeo.ceiba_metadata_mapping
```

El mapeo duró **6,127 segundos**, salió con código **0**, generó 1107 JSON y registró 27 borradores, 84 recursos omitidos y cero problemas de mapeo. Se preservaron los **2382 archivos de ingesta**, con 1191 `resource_metadata.json` y 1191 `files.json`, sin altas, bajas ni cambios de contenido.

El comparador institucional devolvió estado `complete` con **1107 JSON idénticos, 0 modificados, 0 altas, 0 bajas y 0 sin comparar**. El cotejo independiente confirmó que los 1107 eran idénticos byte a byte y semánticamente. Cada uno de los cinco bloques, `citation`, `geospatial`, `institutional`, `externalReferences` y `biologicalMetadata`, coincidió en presencia, campos, valores, tipos, orden, multiplicidad y estructura. También se conservaron `inventory_data` y las opciones de `datasetVersion`. La igualdad de `biologicalMetadata` corresponde a la regresión diferencial. Su validación funcional sigue pendiente.

| Reporte | Comparación con INS-H20 | Resultado |
|---|---|---|
| `inventory.csv` | Identidad binaria y semántica | 1191 claves únicas |
| `load_plan.csv` | Identidad binaria y semántica | 1107 claves únicas |
| `version_dates.csv` | Identidad binaria y semántica | 1107 claves únicas |
| `mapping_problems.json` | Identidad binaria y semántica | 0 problemas |
| `curation.csv` | Comparación de las cinco columnas por multiconjunto | Solo cuatro adiciones de EXT-H02 |

La bitácora registró cero advertencias, errores y eventos críticos. El proceso emitió dos líneas por `stderr` cuyo texto no se conservó. Una lectura aislada del inventario reprodujo un `UserWarning` de `openpyxl` sobre las definiciones de dependencias del libro. La causa de las dos líneas originales sigue indeterminada. El primer intento del verificador diferencial se detuvo al resolver la ruta temporal de macOS. La verificación posterior fue satisfactoria y el mapeo se ejecutó una sola vez.

### Curación posterior a EXT-H02

El corte de INS-H20 conserva sus **1348 filas**. El corte de EXT-H02 contiene **1352**. Se preservaron las 1348 filas históricas, incluido su orden relativo. Hubo cuatro adiciones, cero eliminaciones y cero modificaciones. Las nuevas filas corresponden exactamente a EXT-H02 en tres recursos. Dos ya tenían curación y uno se incorporó por primera vez.

| Indicador | INS-H20 | EXT-H02 |
|---|---:|---:|
| Filas de curación | 1348 | 1352 |
| Recursos únicos con curación | 912 | 913 |
| Recursos sin curación | 195 | 194 |
| Reparaciones en `reference_url` | 2 | 2 |
| Omisiones en `reference_url` | 1 | 5 |

| Categoría | INS-H20 | EXT-H02 |
|---|---:|---:|
| `author_review` | 8 | 8 |
| `bounding_box` | 37 | 37 |
| `collection_codes` | 154 | 154 |
| `collection_identifier` | 4 | 4 |
| `contact_email` | 31 | 31 |
| `contract_code` | 9 | 9 |
| `contractor_association` | 191 | 191 |
| `date` | 1 | 1 |
| `private_draft` | 27 | 27 |
| `publication_date` | 758 | 758 |
| `reference_url` | 3 | 7 |
| `restricted_until` | 32 | 32 |
| `restriction_reason` | 91 | 91 |
| `terms_of_use` | 2 | 2 |
| **Total** | **1348** | **1352** |

### Línea base posterior a EXT-H02

La línea base vigente es `../linea_base_correccion_ext_h02/`, de acceso local restringido. El SHA-256 de su `manifest.json` es `a5d89a1842596a389f419552080753b8571cf53c7e6de766a9874a363d3f39b3`.

| Componente | Archivos | Bytes |
|---|---:|---:|
| `ingesta/` | 2382 | 45172461 |
| `mapeo/` | 1107 | 56923749 |
| `reportes/` | 5 | 893350 |
| `codigo/` | 3 | 62751 |
| `evidencias/` | 6 | 84160 |
| `README.md` | 1 | 1165 |
| **Total registrado** | **3504** | **103137636** |
| `manifest.json` | 1 | 609910 |
| **Total físico** | **3505** | **103747546** |

La captura de código reúne el archivo de producción, la suite específica y el parche de EXT-H02. Su alcance se limita a esos archivos del repositorio. Se verificaron copias, tamaños, hashes, exhaustividad del manifiesto y ausencia de enlaces simbólicos. Las evidencias incluyen `git_state.json`, `environment.json`, `validation_summary.json`, el resumen y el detalle del comparador, y `verificaciones.txt`. Los datos, las rutas de recursos del manifiesto y las diferencias detalladas permanecen fuera de Git. La edición del PASO 11.7 cotejó las huellas y las evidencias agregadas.

## Pruebas unitarias

### Suite geográfica

La suite ejecutada de forma aislada contiene **11 funciones de prueba y 43 casos**, incluidas las parametrizaciones. Se aprobaron los 43 casos, sin fallos, omisiones ni nuevos `xfail`. [`tests/test_ceiba_geospatial.py`](../tests/test_ceiba_geospatial.py)

- Descripciones simples y múltiples, omisión de valores vacíos, escape HTML y conservación del orden, incluso al rechazar un rectángulo.
- Asignación de los cuatro lados, coordenadas negativas, positivas, mixtas y cero, límites globales y conservación de los valores originales.
- Coordenadas incompletas, no numéricas, fuera de rango, `NaN` e infinitos, inversiones y rectángulos puntuales o lineales.
- Contenido y motivo de las filas de curación, con una fila por rectángulo rechazado con lados informados. Los casos sintéticos de rectángulos completamente vacíos se omiten sin curación.
- Coberturas múltiples con rectángulos válidos e inválidos, ausencia de información geográfica y ausencia de elementos sin fuente.

Los casos sintéticos ejercitan `box_problem()` a través de `map_geospatial()`. La suite verifica la transformación en memoria y las filas de curación. Una carga efectiva en Dataverse queda fuera de su alcance.

### Suite INS-H20

La selección posterior incluye 25 casos de INS-H20. La inspección estática identificó cinco funciones parametrizadas con 21 casos y cuatro funciones con un caso cada una. La suite utiliza datos sintéticos, un libro temporal y dobles de configuración, registro o escritura. Los casos de GeoNetwork y Biocultural comprueban el adjunto compartido por clave exacta. La regresión integral de ambos flujos queda fuera de esa cobertura.

| Función | Casos | Objetivo |
|---|---:|---|
| `test_resolves_only_exact_or_normalized_matches` | 11 | Verificar coincidencias literal y normalizada, ausencias y límites de la normalización. |
| `test_rejects_ambiguous_fallbacks` | 3 | Rechazar ambigüedades en inventario, CEIBA o ambos. |
| `test_preserves_exact_matches_even_when_both_normalized_groups_collide` | 1 | Conservar la prioridad de la coincidencia exacta ante colisiones simultáneas. |
| `test_collects_duplicate_rows_without_changing_existing_workbook_calls` | 1 | Conservar duplicados en la lista, la última fila en el índice literal y el retorno usado por llamadas existentes. |
| `test_attaches_original_row_and_uses_the_existing_macro_and_general_keys` | 2 | Conservar fila, URL e identificador, y verificar las claves de GENERAL y Proyectos Macro. |
| `test_leaves_inventory_empty_when_only_general_has_a_match` | 1 | Mantener el inventario vacío cuando solo hay coincidencia en GENERAL. |
| `test_shared_attachment_still_uses_exact_keys` | 2 | Conservar la búsqueda exacta del adjunto para entradas geográficas y socioculturales. |
| `test_recovery_keeps_access_license_and_publication_rules` | 3 | Conservar las opciones de acceso, licencia y borrador, y verificar la fecha recuperada en el caso restringido. |
| `test_ingest_uses_all_directories_and_logs_only_aggregate_resolution_counts` | 1 | Verificar la integración con todos los directorios, incluidos los nunca publicados, y los conteos agregados. |

### Suite externalReferences

El módulo `tests/test_ceiba_external_references.py` contiene **13 funciones**, con siete parametrizadas que aportan **39 casos** y seis individuales, para **45 casos**. Cubre la referencia de origen, la bibliografía y su multiplicidad, la precedencia de identificadores, la curación de URL, la copia DOI y la reconstrucción del compuesto. [Suite de externalReferences](../tests/test_ceiba_external_references.py)

| Ejecución específica del PASO 11.5 | Casos | Aprobados | Fallidos |
|---|---:|---:|---:|
| Antes de la corrección | 45 | 35 | 10 |
| Después de la corrección | 45 | 45 | 0 |

Los diez fallos iniciales detectaron exclusivamente la falta de curación. Ocho cubrieron variantes HTTP/HTTPS, uno comprobó ocurrencias repetidas y otro ejercitó la integración del compuesto. El contenido de las referencias generadas coincidió en esos casos.

### Regresión acumulada de la selección

| Hito de ejecución | Módulos | Casos | Aprobados | `xfail` estrictos | Fallos inesperados |
|---|---:|---:|---:|---:|---:|
| Validación anterior a la suite geográfica | 12 | 230 | 228 | 2 | 0 |
| Regresión previa a INS-H20 | 13 | 273 | 271 | 2 | 0 |
| Regresión posterior a INS-H20 | 14 | 298 | 296 | 2 | 0 |
| Regresión posterior a EXT-H02 | 15 | 343 | 341 | 2 | 0 |

La selección previa registró **1,31 s** para 273 casos y contiene 131 funciones según la inspección estática. La documentación de esa ejecución registra macOS, Python 3.13.2 y pytest 9.2.0. La captura de entorno de la línea base posterior coincide en esas versiones. La equivalencia completa entre entornos históricos quedó fuera de la verificación.

La siguiente tabla conserva el desglose del corte histórico posterior a INS-H20.

| Módulo bajo `tests/` | Funciones | Casos |
|---|---:|---:|
| `test_citation_title_subject.py` | 7 | 9 |
| `test_citation_nivel1.py` | 4 | 4 |
| `test_citation_language.py` | 7 | 10 |
| `test_citation_other_id.py` | 5 | 15 |
| `test_citation_distribution_date.py` | 17 | 56 |
| `test_palabras_clave_ceiba.py` | 15 | 36 |
| `test_citation_description.py` | 11 | 14 |
| `test_citation_notes.py` | 10 | 12 |
| `test_compare_ceiba_mapping.py` | 9 | 9 |
| `test_ceiba_people.py` | 16 | 25 |
| `test_ceiba_contractors.py` | 16 | 28 |
| `test_ceiba_people_curation.py` | 3 | 12 |
| `test_ceiba_geospatial.py` | 11 | 43 |
| `test_ceiba_inventory_resolution.py` | 9 | 25 |
| **Total** | **140** | **298** |

Los conteos por módulo proceden de la inspección del código mediante AST. Los resultados de ejecución proceden de la documentación histórica y del resumen de validación de la línea base. Los dos `xfail` estrictos preceden a INS-H20. DESC-H01 documenta la pérdida del marcado de énfasis y NOTE-H02 documenta el texto directo de `additionalInfo` sin `para`. Ambos limitan el fallo esperado a `AssertionError`.

Los 25 casos específicos de INS-H20 están incluidos en los 298 de ese corte. El PASO 11.6 conserva esos casos e incorpora los 45 de `externalReferences`. La evidencia de ejecución registra **341 aprobados, 2 `xfail` históricos, 0 fallos inesperados, 0 `xpass` y 0 nuevas exclusiones**. Las pruebas automatizadas, los 17 criterios históricos de aceptación técnica de INS-H20 y los controles de auditoría se contabilizan por separado.

Se excluyeron `tests/test_ceiba_mapping.py` y `tests/test_integracion_ceiba_dataverse.py`, que importan `src.mapeo.ceiba_mapping`, y `tests/test_validar_integracion_ceiba.py`, que importa `src.mapeo.validar_integracion_ceiba`. Esos módulos de producción están ausentes del árbol actual.

`pytest` requiere instalación adicional a las dependencias declaradas del proyecto. Se recomienda ejecutar la selección en un proceso dedicado, dado que las fixtures aíslan dependencias de importación para estas pruebas. El comparador requiere Python 3.10 o posterior. La ejecución informada sólo acredita el entorno macOS indicado.

El comando documentado para la selección previa de 273 casos se ejecuta desde la raíz del repositorio con el entorno virtual preparado.

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
tests/test_ceiba_geospatial.py \
-v --tb=short -p no:cacheprovider
```

El siguiente comando de la regresión de 298 casos procede del registro histórico de la secuencia de trabajo en ChatGPT, incorporado en esta actualización. El repositorio y la evidencia de la línea base sustentan la selección y el resultado, y el registro aporta la invocación exacta.

```bash
.venv/bin/python -B -m pytest tests/ \
  --ignore=tests/test_ceiba_mapping.py \
  --ignore=tests/test_integracion_ceiba_dataverse.py \
  --ignore=tests/test_validar_integracion_ceiba.py \
  -p no:cacheprovider -q --tb=short
```

El comando alternativo enumera los 14 módulos, desactiva la autocarga de plugins y la caché, y evita escribir bytecode. Se documenta para reproducir la selección.

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
tests/test_ceiba_geospatial.py \
tests/test_ceiba_inventory_resolution.py \
-v --tb=short -p no:cacheprovider
```

El comando de la selección vigente corresponde a la ejecución registrada en la evidencia del PASO 11.6.

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest tests/ \
  --ignore=tests/test_ceiba_mapping.py \
  --ignore=tests/test_integracion_ceiba_dataverse.py \
  --ignore=tests/test_validar_integracion_ceiba.py \
  -p no:cacheprovider -q --tb=short -r xX
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

### Comandos históricos de ingesta y mapeo de INS-H20

El registro histórico de la secuencia en ChatGPT aporta estas invocaciones. Los resultados agregados se contrastaron por separado con el resumen de la línea base. Esta actualización fue documental y se realizó sin ejecutar los comandos.

```bash
.venv/bin/python -m src.ingest.ceiba_ingest
python3 -m src.mapeo.ceiba_metadata_mapping
```

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
| PER-H22 | Una organización quedó excluida como contratista. | Persiste una exclusión respaldada por EML. Las apariciones finales de nombre respaldadas por organización fueron 147 → 147, las respaldadas por persona 719 → 719 y las indeterminadas 138 → 140. Las dos altas presentan señales léxicas institucionales y su identidad permanece indeterminada. | Su información contractual puede requerir un tratamiento distinto. | Media | Exclusión confirmada. Admisión de organizaciones y fuente de autoridad pendientes de decisión. | Acordar si se admiten organizaciones como contratistas y qué evidencia acredita su identidad. |
| PER-H24 | La equivalencia de nombres usa subconjuntos de palabras. | Antecedente de 92 coincidencias por subconjuntos y 35 casos múltiples. Medición exclusiva 92 → 96, inclusiva 110 → 115 y múltiple 35 → 38. Los conjuntos pueden superponerse. El criterio histórico exacto no se recuperó. | La coincidencia textual requiere respaldo adicional para acreditar identidad. | Media | Confirmado, revisión semántica pendiente. | Revisar candidatos múltiples y acordar criterios de identidad o curación. |
| PER-H25 | Faltan datos del inventario biológico en recursos publicados. | Antecedente de 80 recursos. En los 1107 elegibles, la reconstrucción independiente obtuvo 80 → 16 ausencias y 64 mitigadas mediante INS-H20. Quedan 38 ausencias totales, 22 en recursos sin JSON final. El predicado histórico exacto no se recuperó. | Limita el enriquecimiento cuya única fuente es ese inventario. | Media | Mitigado técnicamente, abierto. | Determinar cuáles de las 16 ausencias elegibles requieren una fuente adicional o curación. Documentar por separado las 22 sin JSON final. |
| PER-H26 | El reconocimiento de códigos distingue mayúsculas y minúsculas. | Se conservaron tres señales de capitalización en los mismos recursos. Hubo cero señales nuevas, cero pérdidas observadas y cero incorporaciones adicionales al flexibilizar las variantes evaluadas. | Podría excluir variantes de capitalización en otros datos. | Baja | Limitación potencial caracterizada, abierta. | Mantener la regla hasta contar con evidencia de impacto y una decisión. |
| PER-H27 | Hay información residual del inventario sin proyecto Macro asociado. | Antecedente de 265 recursos. La medición independiente de recursos sin código Macro con residuales distintos de FN/OS dio 265 → 271. De los seis casos nuevos, cinco coinciden literalmente con la financiación EML y uno conserva el residual sólo en `inventory_data` dentro del alcance auditado. En el escenario actual, 34 residuales se conservan sólo en ese nivel y nueve tienen coincidencia textual parcial. Véase la [reconciliación de I03](#reconciliación-de-i03-en-projectfunding). | El destino depende de la pertinencia de cada segmento y de su respaldo. Los conteos de recursos, segmentos, valores y párrafos corresponden a unidades distintas. | Media | Confirmado, destino institucional pendiente. | Clasificar los valores y acordar el destino de la información pertinente. |
| PER-H29 | Los nombres de contratistas del inventario contienen separadores. | Antecedente de 27 recursos con criterio no recuperado. Medición ampliada 58 → 61 y filtro de barra vertical 27 → 30. Hay tres casos nuevos. En el escenario actual, nueve casos tienen coincidencias textuales con nombres EML documentados por separado, 49 quedan indeterminados y tres son denominaciones institucionales respaldadas. Hubo cero fragmentaciones nuevas. | La separación podría cambiar el conteo de nombres y el resultado de la asociación con códigos. | Media | Confirmado, regla de separación pendiente. | Conservar la cadena original y acordar la evidencia necesaria para dividir nombres o revisar asociaciones. |
| PER-H36 | Algunas apariciones institucionales se clasificaron internamente como personas. | 3 apariciones en 2 recursos. | Puede requerir revisar el reconocimiento de instituciones. | Media | Confirmado. | Revisar los casos y definir si se necesita una regla particular o una autoridad. |
| PER-H37 | Se generaron afiliaciones redundantes. | 2 afiliaciones en 1 recurso. | Añade información repetida al destino. | Baja | Confirmado. | Revisar el origen de la redundancia antes de modificar la regla. |
| PER-H38 | Hay diferencias de afiliación entre apariciones deduplicadas. | 36 conflictos. | La primera aparición puede conservar una afiliación distinta de otra fuente. | Media | Confirmado, revisión semántica pendiente. | Acordar si se mantiene la precedencia o se envían los conflictos a curación. |
| PER-H39 | Hay diferencias de correo entre apariciones deduplicadas. | 2 conflictos. Uno coincide con un conflicto de afiliación. | Puede prevalecer un correo distinto del que corresponda usar. | Media | Confirmado, revisión semántica pendiente. | Revisar las fuentes y acordar precedencia o curación. |
| INS-H20 | La búsqueda literal impedía asociar filas biológicas con variantes de espacios o capitalización. | 1088 asociaciones originales conservadas, 65 recuperadas, 64 de ellas con JSON final, y 38 ausencias residuales. | Aumenta la cobertura del inventario y cambia los valores derivados que se documentan en la regresión. | Por reevaluar | **Corrección implementada y validación técnica aprobada.** Corte de código registrado en `1c61488`. | Gestionar las ausencias residuales mediante PER-H25. |

El PASO 10.12.2.13.5 reevaluó los seis hallazgos relacionados. PER-H25 conserva el antecedente de 80 recursos publicados sin datos de inventario. La reconstrucción reproduce esa cifra en el universo elegible con el criterio documentado en la matriz. La equivalencia con el procedimiento histórico queda indeterminada. Los seis hallazgos permanecen abiertos para decisión institucional.

### Hallazgos geográficos

Los hallazgos geográficos pueden corresponder al mismo recurso. Sus cantidades no se suman para estimar recursos únicos afectados.

| ID | Descripción | Evidencia | Impacto | Prioridad | Estado | Recomendación |
|---|---|---|---|---|---|---|
| GEO-H01 | Se omiten los rectángulos completamente vacíos sin fila de curación. | Comportamiento confirmado en pruebas sintéticas. 0 casos en los recursos evaluados. | Una cobertura futura sin ningún lado informado quedaría sin fila de curación. | Baja | Confirmado con evidencia sintética, sin impacto observado. | Mantener el comportamiento actual sin modificación inmediata. |
| GEO-H02 | Hay rectángulos aceptados con longitudes positivas. | 20 rectángulos. En 18 casos la longitud oeste es negativa y en 2 ambas longitudes son positivas. | La longitud positiva indica un caso para revisión y por sí sola es compatible con una cobertura legítima. | Media | Indicador diagnóstico, pendiente de revisión individual. | Revisar la coherencia geográfica y concertar indicadores adicionales de curación. |
| GEO-H03 | Las descripciones de varias coberturas se consolidan en párrafos HTML. | Orden y consolidación verificados en pruebas sintéticas. 0 recursos evaluados con varias coberturas. | El comportamiento conserva varias descripciones en un único campo cuando aparecen. | Baja | Confirmado con evidencia sintética. | Mantener la cobertura sintética y revisar el formato junto con GEO-H06. |
| GEO-H04 | Se identificó una inversión real de longitud. | 1 rectángulo con oeste > este, omitido del JSON final y registrado en curación. | El rectángulo rechazado queda disponible para revisión de origen. | Baja | Confirmado, tratamiento vigente verificado. | Mantener la regla de rechazo y curación. |
| GEO-H05 | Hay rectángulos de área cero. | 36 rectángulos, con 26 puntos, 7 de ancho cero y 3 de alto cero. Todos figuran en curación. | El JSON final omite coberturas que pueden representar puntos o líneas legítimos. | Media | Confirmado, tratamiento definitivo pendiente. | Concertar el tratamiento de coberturas puntuales y lineales. |
| GEO-H06 | Las descripciones geográficas se transforman a HTML. | 1107 descripciones transformadas y 305287 caracteres normalizados conservados. | La representación visual depende del formato elegido para el campo. | Media | Conservación textual confirmada, formato pendiente de concertación. | Acordar el formato definitivo de `geographicCoverageDescription`. |
| GEO-H07 | Un rectángulo aceptado es compatible con un posible intercambio de latitud y longitud. | 1 recurso con mención de Colombia y longitudes positivas. La geometría es consistente con la hipótesis de intercambio. | El intercambio, si se confirma, alteraría la ubicación asignada a la cobertura. | Alta | Hipótesis diagnóstica, pendiente de revisión individual. | Revisar la fuente y el alcance del recurso, conservando las coordenadas originales durante la revisión. |
| GEO-H08 | Hay rectángulos aceptados fuera de la referencia aproximada de Colombia. | 4 rectángulos fuera de la referencia. 1 menciona Colombia. | Puede haber una discrepancia entre la cobertura y lo que declara la descripción. | Media | Indicador diagnóstico, pendiente de revisión individual. | Evaluar la coherencia con la cobertura real de los recursos. |
| GEO-H09 | Una cobertura puntual queda fuera de la referencia aproximada de Colombia. | 1 de 26 puntos evaluados. Ya figura en curación por área cero. | La ubicación del punto puede revisarse en la fila existente. | Baja | Indicador diagnóstico sobre un caso ya registrado en curación. | Revisar junto con el tratamiento de coberturas puntuales. |

### Hallazgos de externalReferences

| ID | Descripción | Evidencia | Impacto | Prioridad | Estado | Recomendación |
|---|---|---|---|---|---|---|
| EXT-H01 | Hay repeticiones bibliográficas exactas en el destino. | 28 repeticiones en 20 recursos. De ellas, 25 proceden de la ingesta y tres resultan de la normalización. | Deduplicar podría retirar ocurrencias de origen o combinar identificadores distintos. | Baja | Abierto, pendiente de política institucional. | Conservar multiplicidad y orden hasta acordar los criterios de deduplicación. |
| EXT-H02 | Cuatro identificadores HTTP/HTTPS malformados quedaban sin curación. | Se añadieron cuatro filas en tres recursos. Las 1107 listas finales permanecieron idénticas. | Los identificadores omitidos quedan disponibles para revisión. | Media | **Cerrado técnicamente.** Corrección implementada y regresión aprobada. | Mantener la cobertura de curación y revisar los destinos de forma individual. |
| EXT-H03 | El destino de GBIF dataset key es una opción no decidida. | 682 valores con forma UUID. Coexisten con un DOI reconocido en 681 recursos. | El valor queda en el inventario adjunto. Hace falta una regla para asignarlo al bloque. | Baja | Abierto, pendiente de definición institucional. | Acordar campo, tipo de referencia y criterio de identidad antes de mapear. |
| EXT-H04 | Se evaluó la conservación textual de la bibliografía. | Las 9288 citas conservan el texto disponible en la ingesta. | El cotejo acredita la transformación a HTML desde el JSON intermedio. | Baja | **Cerrado técnicamente para ingesta JSON → destino JSON.** | Acordar si el equipo requiere un cotejo desde XML original, incluido el contenido anidado. |

Las diferencias textuales de versión, el token de inventario con apariencia DOI y los comportamientos sintéticos de texto anidado y codificación se mantienen como observaciones de alcance en [Resultados de externalReferences](#resultados-de-externalreferences).

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

### Observaciones pendientes tras INS-H20

- **Cobertura del inventario.** Quedan 38 recursos sin asociación en el universo completo. Una recuperación no produjo JSON final por ausencia de una raíz EML reconocida.
- **Completitud de los valores recuperados.** Se registraron 12 proyectos sin NOMBRE DIEGO, 11 sin SUSCRITO y 7 DOI no vacíos que la regla vigente no reconoció.
- **Curación.** Quedan 7 razones propuestas de restricción por validar. Se registraron 4 nuevas ambigüedades de asociación contractual, 1 observación contractual reformulada y 1 código de tipo FN adicional en curación.
- **Cobertura de pruebas del proyecto.** DESC-H01 y NOTE-H02 siguen pendientes. Los tres módulos heredados excluidos requieren adaptación. Las comprobaciones de GeoNetwork y Biocultural cubren el adjunto compartido.
- **Controles de auditoría.** La [conciliación del acumulado](#conciliación-del-acumulado-de-controles) conserva los cortes históricos. Se registran por separado un control histórico no evaluable y dos controles informativos no evaluables.

Estas observaciones delimitan la cobertura técnica y las decisiones pendientes. La aprobación institucional definitiva y la carga efectiva en Dataverse quedan fuera de esta entrega.

### Conciliación del acumulado de controles

El corte histórico de **1008 controles obligatorios aprobados** corresponde al PASO 10.12.2.13.3. El registro conciliado de INS-H20 incorpora los aportes posteriores hasta el corte de 1267.

| Paso | Aporte | Acumulado |
|---|---:|---:|
| Subtotal previo a PER-H24, hasta 13.5.2.2 PER-H22 | — | 1098 |
| 13.5.2.3 PER-H24 | 26 | 1124 |
| 13.5.2.4 PER-H26 | 25 | 1149 |
| 13.5.2.5 PER-H27 | 24 | 1173 |
| 13.5.2.5.1 Reconciliación I03 | 24 | 1197 |
| 13.5.2.6 PER-H29 | 23 | 1220 |
| 13.5.2.7 Consolidación | 21 | 1241 |
| 13.5.3.1 Auditoría documental | 14 | 1255 |
| 13.5.3.1.1 Conciliación documental | 12 | 1267 |

El acumulado anteriormente informado de **1240** se rectificó a **1241** para el mismo corte, el PASO 10.12.2.13.5.2.7. PER-H26 preveía 25 controles obligatorios. La primera ejecución aprobó 24 y dejó pendiente L01 por la reutilización de la variable `d`. La ejecución correctiva accedió explícitamente a `scenes["D"]` y aprobó los 25 controles. L01 ya pertenecía al plan original. Se contabilizó únicamente la ejecución definitiva. La procedencia exacta de la transcripción del subtotal anterior no se recuperó.

El I03 de PER-H26 verificó la financiación Macro y la clasificación de tramos en la cohorte elegible. El I03 original de PER-H27, sobre los párrafos adicionales de convenios, y el G01 original de la auditoría documental, sobre el acumulado, conservan sus estados históricos en revisión. Se registran sus respectivas conciliaciones en los pasos 10.12.2.13.5.2.5.1 y 10.12.2.13.5.3.1.1. Cada conciliación contribuye una sola vez. La resolución del control original se documenta sin añadir otra aprobación.

Los **1267 controles obligatorios aprobados** corresponden al corte documental anterior de INS-H20. Las verificaciones periódicas de integridad se contabilizan por paso. Los reintentos dentro de un mismo paso, los controles informativos y los no evaluables se excluyen del acumulado.

El PASO 11.2 partió de un acumulado informado de **1310** controles. Ese subtotal se conserva como referencia de partida sin asignar un desglose a los pasos intermedios. El resumen de validación de la línea base EXT-H02 acredita los 20 controles del PASO 11.6 y el acumulado de **1381**. Los 343 casos de pytest se contabilizan por separado.

| Corte | Controles aprobados en el paso | Acumulado |
|---|---:|---:|
| Antes del PASO 11.2 | — | 1310 |
| PASO 11.2 · Caracterización | 13 | 1323 |
| PASO 11.3 · Validación funcional | 24 | 1347 |
| PASOS 11.4 y 11.5 · Corrección y pruebas | 14 | 1361 |
| PASO 11.6 · Regresión y línea base | 20 | **1381** |

## Preguntas para Marius y el equipo

1. ¿Se mantiene HTML para `dsDescriptionValue` o se adopta texto plano? La evaluación cubrió 1107 descripciones y no detectó pérdida de contenido textual.
2. ¿Debemos conservar las etiquetas de énfasis y enlaces originales del EML? Se perdieron ocho etiquetas de énfasis en cuatro párrafos de tres recursos. No se identificaron casos reales de enlaces en las descripciones evaluadas.
3. ¿Se admite texto directo de `additionalInfo` sin `para`? El comportamiento se reprodujo con una prueba sintética y no se encontraron casos reales en la evaluación.
4. ¿Se contempla incorporar tablas de autoridades de personas y organizaciones? La revisión de fuentes incluyó 11804 apariciones y el flujo evaluado carece de `people.csv` y `organisations.csv`.
5. ¿Debemos actualizar la denominación de la tabla de roles en el crosswalk? La referencia documental usa `contributor_roles.csv` y el código consume `party_roles.csv`.
6. ¿Es correcto extender la reparación del dominio de correo a todas las direcciones institucionales afectadas? Se identificaron 14 contactos finales no correspondientes al correo I2D.
7. ¿Se mantiene la primera aparición cuando existen afiliaciones o correos diferentes para una misma identidad? Se identificaron 36 conflictos de afiliación y dos de correo, con un caso que presenta ambas diferencias.
8. ¿Qué evidencia de identidad se exigirá antes de deduplicar por subconjuntos cuando haya varios candidatos EML? Los casos múltiples pasaron de 35 a 38.
9. ¿Se aprueba `contractor_association` como categoría de curación y se mantiene una fila por recurso con asociación indeterminada? Tras INS-H20 hubo cuatro observaciones nuevas y una reformulada en la cohorte recuperada.
10. ¿Se admitirán organizaciones como contratistas y qué fuente acreditará su identidad? Persiste una exclusión respaldada por EML y las dos altas de nombre permanecen indeterminadas.
11. ¿Qué evidencia permitirá trasladar un residual sin código Macro a financiación o convenio, y cómo se tratarán los valores preservados sólo en `inventory_data` y los de coincidencia parcial?
12. ¿Qué evidencia habilitará la separación de una cadena de `contratista` y qué curación se aplicará si hay códigos asociados o la identidad es indeterminada?
13. ¿Cómo se realizará la conservación externa de las unidades curatoriales? Se identificaron 42 recursos con `jgtiCuratorialUnit` y queda pendiente verificar el tratamiento completo.
14. ¿Se deben fortalecer los controles del comparador antes de utilizarlo como criterio automático de aceptación? La auditoría detectó casos de entradas incompletas y riesgos de exposición de reportes.
15. ¿Conviene declarar dependencias de desarrollo y mejorar el aislamiento de las fixtures? `pytest` requiere instalación adicional y la selección actual se recomienda en un proceso dedicado.
16. ¿Cuál debe ser el tratamiento definitivo de las coberturas puntuales y lineales que generan rectángulos de área cero? ¿Se mantienen exclusivamente en curación o existe una representación alternativa compatible con Dataverse? La evaluación identificó 36 casos ya registrados en curación.
17. ¿Conviene incorporar indicadores de coherencia geográfica para detectar longitudes positivas, posibles intercambios de coordenadas y coberturas incompatibles con su descripción, sin modificar automáticamente los valores originales? Los indicadores identificaron 20 recursos únicos entre longitudes positivas y posible intercambio. También se observaron cuatro rectángulos aceptados fuera de la referencia aproximada.
18. ¿Se mantiene la representación HTML de `geographicCoverageDescription` o se prefiere texto plano, en concordancia con la decisión sobre el formato de `dsDescriptionValue`? Las 1107 descripciones geográficas conservan el contenido textual normalizado en el formato actual.
19. ¿Se deben incorporar al reporte de curación los rectángulos explícitamente presentes en EML pero completamente vacíos, diferenciándolos de las coberturas que no incluyen boundingCoordinates? Este comportamiento se identificó mediante pruebas sintéticas, sin casos observados en los 1107 recursos evaluados (GEO-H01).
20. ¿Se confirma que country, state, city, otherGeographicCoverage, geographicUnit, minimumAltitude, maximumAltitude y wkt deben permanecer sin diligenciar durante la migración inicial, dejando su eventual incorporación para una etapa posterior de curación o enriquecimiento de metadatos?
21. ¿Qué evidencia permitirá resolver cada una de las 16 ausencias de asociación en recursos elegibles y cómo se tratarán las 22 ausencias en recursos sin JSON final?
22. ¿Qué evidencia de impacto justificaría flexibilizar la capitalización de los códigos contractuales?
23. ¿Se acepta el alcance local validado de INS-H20 para preparar su entrega y gestionar las ausencias residuales mediante PER-H25?
24. ¿Puede el equipo acreditar la procedencia y autorización de los ejemplos históricos identificados en DOC-H02, o conviene sustituirlos por ejemplos inequívocamente sintéticos antes de publicar?
25. ¿Se conserva la multiplicidad de las citas bibliográficas o se adopta una política de deduplicación? De las 28 repeticiones adicionales, 25 ya estaban presentes en la ingesta y tres aparecen después de normalizar. Dos grupos tienen identificadores distintos en origen.
26. ¿Qué campo y tipo de referencia, si corresponde, deben recibir GBIF dataset key? Hay 682 valores con forma UUID y 681 coexisten con un DOI reconocido.
27. ¿Qué clases de identificadores bibliográficos adicionales deben migrarse o enviarse a curación? Se observaron 1099 valores de otra clase, entre ellos formas con apariencia de URL o DOI.
28. ¿Qué evidencia del inventario permitiría reconocer un DOI cuyo token tiene la forma esperada pero se presenta en un contexto distinto? Se observó un caso de ese tipo entre los once valores fuera de la lista estricta de marcadores.
29. ¿Se ratifica `inventory.csv` como fuente de la versión en las URL de origen CEIBA? La versión extraída de `@packageId` difirió textualmente en 593 casos y la versión de `inventory.csv` coincidió con el plan de carga en los 1107 recursos.
30. ¿Se requiere verificar las citas de `externalReferences` desde el XML original y qué contenido anidado o marcado debe preservarse? La comprobación actual cubre las 9288 citas desde el JSON de ingesta.

Estas preguntas quedan abiertas para concertación. Las recomendaciones de la matriz orientan la revisión y no constituyen autorizaciones de cambio.

## Próximas actividades

### Actividades realizadas

1. Implementar la corrección de INS-H20.
2. Completar la validación técnica local.
3. Cotejar la regresión transversal de los cinco bloques.
4. Construir y validar la línea base posterior a INS-H20.
5. Reevaluar los seis hallazgos relacionados.
6. Conciliar I03.
7. Conciliar el acumulado de controles.
8. Incorporar localmente los resultados al documento acumulativo.
9. Completar la caracterización y la validación funcional de `externalReferences`.
10. Corregir EXT-H02 y aprobar sus pruebas y la regresión transversal.
11. Consolidar y verificar la línea base posterior a EXT-H02.

### Actividades pendientes

1. Publicar `externalReferences` en el Draft PR #13 después del cierre documental y de la revisión de confidencialidad de los archivos candidatos, incluido el tratamiento de DOC-H02.
2. Caracterizar y validar funcionalmente `biologicalMetadata`.
3. Consolidar la evaluación de los cinco bloques, incluidos los elementos restantes de `institutional`, y ejecutar la regresión integral con los criterios acordados.
4. Consolidar las pruebas y preparar la documentación final del proyecto.
5. Revisar con el equipo las decisiones institucionales pendientes, incluidos los indicadores geográficos, las coberturas puntuales y lineales, el formato de las descripciones y las actividades de integración.
