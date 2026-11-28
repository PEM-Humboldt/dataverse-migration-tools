# Validación parcial del mapeo CEIBA–Dataverse

Este informe acompaña el Draft Pull Request #13 de `feature/validacion-ceiba-mapping` a `develop`, según la última configuración verificada. Consolida la evaluación funcional de los cinco bloques CEIBA–Dataverse y conserva los cortes históricos de INS-H20 y EXT-H02. La regresión de BIO-H01 preservó los 1107 JSON finales y añadió 13 avisos de curación. El PASO 12.8 completó el cierre técnico local de `biologicalMetadata`, con ocho de ocho actividades ejecutadas y el 100 % del plan técnico del bloque. Los cambios pendientes se publicarán en una sola entrega al finalizar la consolidación general.

## Resumen ejecutivo

La validación técnica de los **cinco bloques** CEIBA–Dataverse está completa para el universo y las reglas evaluadas. De **1191 recursos de ingesta**, **1107** produjeron JSON finales y **84** quedaron fuera por falta de una raíz EML reconocida. Los elegibles incluyen **1080 `PUBLIC`** y **27 `PRIVATE`** previstos como borradores, con **1032 EML 2.1.1** y **75 EML 2.2.0**. El inventario contiene fila biológica para **1153 recursos** del universo total y para **1091 elegibles**.

El escenario BIO-H01 conserva **1365 filas de curación** en **916 recursos elegibles** y **cero problemas de mapeo**. Se acreditaron **siete correcciones propias**. La suite archivada contiene **408 casos**, **406 aprobados** y **dos `xfail` históricos**. Los **57 hallazgos** abarcan condiciones de origen, resultados técnicos, limitaciones y decisiones pendientes. Las 33 preguntas históricas y los pendientes adicionales se organizan en **25 grupos de decisión**.

El cierre local de BIO-H01 y los demás cierres técnicos conservan sus alcances. La resolución de pendientes, la aprobación institucional y la migración efectiva son etapas separadas. La publicación del trabajo se realizará en una sola entrega general. Véanse las [condiciones de despliegue](#condiciones-para-la-migración-efectiva).

## Índice

1. [Resumen ejecutivo](#resumen-ejecutivo)
2. [Contexto y alcance](#contexto-y-alcance)
3. [Arquitectura evaluada](#arquitectura-evaluada)
4. [Metodología](#metodología)
5. [Caracterización de los datos](#caracterización-de-los-datos)
6. [Cobertura consolidada de los cinco bloques](#cobertura-consolidada-de-los-cinco-bloques)
7. [Resultados de citation](#resultados-de-citation)
8. [Resultados de geospatial](#resultados-de-geospatial)
9. [Personas e instituciones](#personas-e-instituciones)
10. [Resultados de externalReferences](#resultados-de-externalreferences)
11. [Resultados de biologicalMetadata](#resultados-de-biologicalmetadata)
12. [Correcciones implementadas](#correcciones-implementadas)
13. [Regresión y reporte de curación](#regresión-y-reporte-de-curación)
14. [Pruebas unitarias](#pruebas-unitarias)
15. [Reproducibilidad y herramienta de comparación](#reproducibilidad-y-herramienta-de-comparación)
16. [Inventario de líneas base y evidencias](#inventario-de-líneas-base-y-evidencias)
17. [Matriz consolidada de hallazgos](#matriz-consolidada-de-hallazgos)
18. [Resolución de la auditoría documental](#resolución-de-la-auditoría-documental)
19. [Decisiones institucionales y preguntas históricas](#decisiones-institucionales-y-preguntas-históricas)
20. [Condiciones para la migración efectiva](#condiciones-para-la-migración-efectiva)
21. [Estructura definitiva propuesta para el documento Word](#estructura-definitiva-propuesta-para-el-documento-word)
22. [Próximas actividades](#próximas-actividades)

## Contexto y alcance

| Referencia | Valor |
|---|---|
| Repositorio | `PEM-Humboldt/dataverse-migration-tools` |
| Rama de trabajo | `feature/validacion-ceiba-mapping` |
| Rama de partida del desarrollo | `marbotte/ceiba-mapping-example` |
| Base del Draft PR según la última verificación | `develop` |
| Draft Pull Request | [#13](https://github.com/PEM-Humboldt/dataverse-migration-tools/pull/13) |
| Commit histórico de partida | `449385271f8efd92894ba70785e95c2bead70ecd` |
| Commit de referencia de INS-H20 | `7d1e26204688569b88c0fab5b8627e752807deef` |
| HEAD de referencia para la validación de `externalReferences` | `1c6148804f10ded29c99d751320baf530cf44150` |
| HEAD de referencia para `biologicalMetadata` y su regresión | `31e624bd31892a549d46148e2a41058d024c5e46` |
| Commit de los esquemas Dataverse | `ab2841405a24f149ff7fdb6264f179ede27c6e7c` |
| Crosswalk de referencia | `MigracionCeiba_20261125.xlsx` |
| Fecha de corte de la evaluación inicial | 26 de noviembre de 2026 |
| Actualización de la documentación geográfica | 27 de noviembre de 2026 |
| Corte documental anterior a `externalReferences` | 27 de noviembre de 2026 |
| Fecha de corte de esta actualización | 28 de noviembre de 2026 |

La evaluación fortalece la implementación desarrollada por Marius y conserva su arquitectura. Al PASO 12.8, los cinco bloques están validados técnicamente dentro del universo y de las reglas evaluadas. La aprobación institucional, la integración del PR y la carga efectiva en Dataverse quedan pendientes.

| Bloque | Estado técnico al PASO 12.8 | Alcance documentado |
|---|---|---|
| `citation` | Validación técnica completada | Identidad, descripción, notas, palabras clave y los elementos de personas e instituciones auditados. |
| `geospatial` | Validación técnica completada | Descripciones, coordenadas y curación. Los indicadores de coherencia geográfica requieren revisión individual. |
| `institutional` | Validación técnica completada para el alcance auditado | Inventario, proyectos, contratistas, acceso y curaciones asociadas. Las excepciones documentadas siguen abiertas para concertación. |
| `externalReferences` | Validación técnica y regresión completadas | Referencia de origen, bibliografía, copia DOI y curación de URL. EXT-H02 consta en el `HEAD` local de referencia y su seguimiento local. |
| `biologicalMetadata` | Cierre técnico local completado. | Campos independientes, taxonomía, tiempo, métodos y colecciones. BIO-H01 está cerrado técnicamente. |

INS-H20 se validó en el árbol de trabajo local sobre su commit de referencia. En ese corte, dos archivos de producción estaban modificados y la suite específica aún no estaba rastreada. Los cuatro archivos no rastreados ajenos al trabajo quedaron fuera de la entrega. La regresión diferencial abarcó los cinco bloques y el PASO 10.12.2.13.5.2.7 consolidó los resultados técnicos. Los cambios de INS-H20 quedaron registrados en el commit `1c6148804f10ded29c99d751320baf530cf44150`, que sirve como referencia para EXT-H02.

En el corte del PASO 11.6, `externalReferences` contaba con validación funcional completa, EXT-H02 corregido, regresión transversal aprobada y línea base consolidada. Ese corte registró **1381 controles obligatorios acumulados** y **343 casos** de pytest, con **341 aprobados y 2 `xfail` históricos**. La publicación conjunta del bloque estaba pendiente en el corte documental del PASO 11.7. El corte acreditado del PASO 11.8 figura en la [conciliación del acumulado](#conciliación-del-acumulado-de-controles).

Los resultados cuantitativos proceden de las evaluaciones informadas. La FASE 11 consistió en una auditoría estática de solo lectura. Las cifras de pytest corresponden a las ejecuciones de pruebas sintéticas descritas en la sección de pruebas unitarias.

### Historial de Git y candidatos a publicación

El trabajo partió de `origin/marbotte/ceiba-mapping-example`, según la referencia local. La base del Draft PR #13 es `develop` según la última verificación documentada. Ambos valores describen comparaciones distintas. El inventario de 13.1–13.4 se obtuvo sin consultas remotas.

| Base de comparación | Alcance local del diferencial |
|---|---|
| Rama de origen de Marius en `449385271f8efd92894ba70785e95c2bead70ecd` | 8 commits y 21 archivos comprometidos. 18 añadidos y 3 modificados. |
| `origin/develop...HEAD` con referencia local `050a6b5` | 38 archivos en el diferencial de tres puntos. Divergencia local de 3 commits del lado de develop y 25 del lado de trabajo. |

El diferencial frente a `origin/develop` incluye ascendencia distinta. El inventario de commits de este trabajo se atribuye frente a la rama de origen.

| Commit | Aporte registrado localmente |
|---|---|
| `a547075` | fix: improve CEIBA date, keyword and contractor mapping |
| `d3f20c5` | feat: add CEIBA mapping regression comparison tool |
| `ea471af` | test: add and adapt CEIBA metadata mapping tests |
| `ff0f517` | docs: document CEIBA mapping validation and open questions |
| `7cff389` | test: add CEIBA geospatial mapping tests |
| `7d1e262` | docs: document CEIBA geospatial mapping validation |
| `1c61488` | fix(ceiba): recover normalized inventory associations and document INS-H20 validation |
| `31e624b` | fix(ceiba): complete external references validation and URL curation |

Candidatos pendientes de la entrega única. `src/mapeo/ceiba/ceiba_fields.py` conserva el diff local de BIO-H01. `tests/test_ceiba_biological_metadata.py` es un módulo nuevo sin rastrear. `docs/validacion_ceiba_mapping.md` conserva la consolidación documental. Las líneas base, el entorno virtual, las configuraciones con secretos, los cuatro históricos no rastreados y las evidencias detalladas permanecen fuera de la entrega.

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

Para `biologicalMetadata`, el PASO 12.2 caracterizó fuentes, esquema y salidas. El PASO 12.3 reconstruyó de forma independiente los 1107 bloques y las curaciones históricas desde la ingesta. Los PASOS 12.4 y 12.5 caracterizaron los límites de la implementación, aplicaron BIO-H01 y lo verificaron con pruebas sintéticas y un cotejo en memoria. El PASO 12.6 regeneró las salidas, comparó los cinco bloques y archivó el código, los reportes y las evidencias de la regresión. El PASO 12.7 integra esos resultados mediante lectura de evidencias, inspección estática y comprobación de huellas.

Las reevaluaciones conservan los antecedentes históricos y explicitan el universo, el criterio y la unidad de las mediciones posteriores. La [reconciliación de I03](#reconciliación-de-i03-en-projectfunding) distingue celdas fuente, ocurrencias de segmentos, recursos, valores Dataverse y párrafos HTML. Las cifras de esta actualización proceden de las ejecuciones y conciliaciones acreditadas. La edición fue documental.

## Caracterización de los datos

| Indicador | Ingesta total | Elegibles | Omitidos |
|---|---|---|---|
| Recursos | 1191 | 1107 | 84 |
| IPT `PUBLIC` | 1080 | 1080 | 0 |
| IPT `PRIVATE` | 111 | 27 | 84 |
| EML 2.1.1 | 1032 | 1032 | 0 |
| EML 2.2.0 | 75 | 75 | 0 |
| Sin raíz EML reconocida | 84 | 0 | 84 |
| Con fila biológica en el inventario | 1153 | 1091 | 62 |
| Sin fila biológica | 38 | 16 | 22 |
| Con curación | 916 | 916 | 0 |
| Sin curación | 275 | 191 | 84 |

Los 1107 elegibles produjeron JSON finales. El plan prevé liberar 1080 recursos y mantener 27 como borradores. Los 84 omitidos carecían de raíz EML reconocida y el reporte vigente registra cero problemas de mapeo. El indicador `published` identifica la disponibilidad de un EML publicado en la ingesta. El estado `PUBLIC` o `PRIVATE` corresponde al IPT. La publicación efectiva en Dataverse pertenece a la etapa de despliegue.

El denominador de curación operativa es **1107 elegibles**. Se registraron **916 con curación** y **191 sin curación**. En el universo de ingesta, los 275 sin curación incluyen los 84 omitidos. La auditoría cotejó 1191 JSON de ingesta, 1107 JSON finales y cinco reportes contra BIO-H01. La comprobación binaria de los 1191 `files.json` corresponde a la regresión de 12.6, con indexación por ruta durante 13.1–13.4.

### Cobertura del inventario biológico antes y después de INS-H20

| Universo | Total | Asociados antes | Asociados después | Ausencias antes | Ausencias después | Recuperaciones |
|---|---:|---:|---:|---:|---:|---:|
| Ingesta completa | 1191 | 1088 | 1153 | 103 | 38 | 65 |
| Con JSON final | 1107 | 1027 | 1091 | 80 | 16 | 64 |
| Sin JSON final | 84 | 61 | 62 | 23 | 22 | 1 |

La cobertura global pasó de **91,35 % a 96,81 %**, un incremento de **5,46 puntos porcentuales**. Las ausencias disminuyeron **63,11 %** respecto a las 103 de partida. Se conservaron las 1088 asociaciones originales, sin ambigüedades detectadas en la ejecución real. Se verificaron 1114 valores terminales del inventario recuperado y los 1191 archivos `files.json` se conservaron byte a byte.

De las 65 recuperaciones, 64 fueron elegibles para el mapeo. La restante carecía de una raíz EML reconocida. Los 1043 JSON finales fuera de la cohorte recuperada se conservaron. Los dos escenarios produjeron 1107 JSON finales y registraron cero problemas de mapeo. El balance de curación y los cambios por bloque se detallan en la [regresión transversal de INS-H20](#regresión-transversal-de-ins-h20). PER-H25 distingue las 16 ausencias elegibles de las 22 correspondientes a recursos sin JSON final.

## Cobertura consolidada de los cinco bloques

Los cinco bloques están presentes en los 1107 JSON elegibles. Las cantidades de esta sección proceden de la lectura de las salidas vigentes en 13.1–13.4. «Valores» cuenta ítems de contenido no vacíos y conserva multiplicidades. «Filas compuestas» cuenta ocurrencias del padre, incluso si el compuesto admite una sola fila.

| Bloque | Campos emitidos | Campos definidos | Padres emitidos | Padres definidos | Valores | Filas compuestas |
|---|---|---|---|---|---|---|
| `citation` | 29 | 65 | 8 | 15 | 50076 | 25936 |
| `geospatial` | 5 | 13 | 1 | 3 | 5387 | 1070 |
| `institutional` | 13 | 15 | 3 | 3 | 8725 | 3913 |
| `externalReferences` | 6 | 9 | 1 | 1 | 26346 | 11077 |
| `biologicalMetadata` | 25 | 27 | 5 | 5 | 78181 | 33188 |
| **Total** | **78** | **129** | **18** | **27** | **168715** | **75184** |

El TSV y el crosswalk conciliaron nominalmente **129 campos de contenido**. Se observaron **78 campos emitidos de 129 definidos** y **78 de 78 campos con regla propuesta** emitidos al menos en un recurso. Los **51 campos sin fuente** permanecieron ausentes. Se emitieron **18 de 27 padres**. Estas son medidas de cobertura del esquema y de emisión observada. La completitud por recurso depende de la fuente y la cardinalidad de cada campo.

Las matrices consignan recursos únicos por campo o padre y el total de valores o filas. La cardinalidad de un hijo aplica dentro de una fila del padre. «Fuente explícita» indica que el crosswalk registra una fuente en su fila. Las propuestas que derivan un valor del recurso o de otra regla pueden carecer de fuente directa. La trazabilidad identifica escrituras literales cuando se observaron y recurre al JSON final para emisiones de claves dinámicas.

### Campos de citation

| Campo del TSV | Padre | Tipo y cardinalidad TSV | Crosswalk | Emisión observada | Recursos | Valores o filas | Trazabilidad de implementación |
|---|---|---|---|---|---|---|---|
| `title` | — | `text` · `1` | 2 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_citation()` |
| `subtitle` | — | `text` · `0..1` | 3 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `alternativeTitle` | — | `text` · `0..n` | 4 · propuesta · fuente explícita | Sí | 6 | 6 valores | `map_citation()` |
| `alternativeURL` | — | `url` · `0..1` | 5 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `otherIdAgency` | `otherId` | `text` · `0..1` | 6 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_citation()` |
| `otherIdValue` | `otherId` | `text` · `0..1` | 7 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_citation()` |
| `authorName` | `author` | `text` · `1` | 8 · propuesta · fuente explícita | Sí | 1107 | 2045 valores | `map_authors()` |
| `authorAffiliation` | `author` | `text` · `0..1` | 9 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `authorIdentifierScheme` | `author` | `text controlado` · `0..1` | 10 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `authorIdentifier` | `author` | `text` · `0..1` | 11 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `datasetContactName` | `datasetContact` | `text` · `0..1` | 12 · propuesta · fuente explícita | Sí | 1107 | 1426 valores | `map_parties()` |
| `datasetContactAffiliation` | `datasetContact` | `text` · `0..1` | 13 · propuesta · fuente explícita | Sí | 1106 | 1422 valores | `map_parties()` |
| `datasetContactEmail` | `datasetContact` | `email` · `1` | 14 · propuesta · fuente explícita | Sí | 1107 | 1426 valores | `map_parties()` |
| `dsDescriptionValue` | `dsDescription` | `textbox` · `1` | 15 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_description()` |
| `dsDescriptionDate` | `dsDescription` | `date` · `0..1` | 16 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_description()` |
| `subject` | — | `text controlado` · `1..n` | 17 · propuesta | Sí | 1107 | 1107 valores | `map_citation()` |
| `keywordValue` | `keyword` | `text` · `0..1` | 18 · propuesta · fuente explícita | Sí | 1107 | 9860 valores | `map_keywords()` |
| `keywordTermURI` | `keyword` | `url` · `0..1` | 19 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `keywordVocabulary` | `keyword` | `text` · `0..1` | 20 · propuesta · fuente explícita | Sí | 1099 | 2061 valores | `map_keywords()` |
| `keywordVocabularyURI` | `keyword` | `url` · `0..1` | 21 · propuesta · fuente explícita | Sí | 1099 | 2056 valores | `map_keywords()` |
| `topicClassValue` | `topicClassification` | `text` · `0..1` | 22 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `topicClassVocab` | `topicClassification` | `text` · `0..1` | 23 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `topicClassVocabURI` | `topicClassification` | `url` · `0..1` | 24 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `publicationRelationType` | `publication` | `text controlado` · `0..1` | 25 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `publicationCitation` | `publication` | `textbox` · `0..1` | 26 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `publicationIDType` | `publication` | `text controlado` · `0..1` | 27 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `publicationIDNumber` | `publication` | `text` · `0..1` | 28 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `publicationURL` | `publication` | `url` · `0..1` | 29 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `notesText` | — | `textbox` · `0..1` | 30 · propuesta · fuente explícita | Sí | 462 | 462 valores | `map_citation()` |
| `language` | — | `text controlado` · `0..n` | 31 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_citation()` |
| `producerName` | `producer` | `text` · `1` | 32 · propuesta · fuente explícita | Sí | 1107 | 3660 valores | `map_parties()` |
| `producerAffiliation` | `producer` | `text` · `0..1` | 33 · propuesta · fuente explícita | Sí | 1099 | 3208 valores | `map_parties()` |
| `producerAbbreviation` | `producer` | `text` · `0..1` | 34 · propuesta | Sí | 45 | 45 valores | Presencia en el JSON final |
| `producerURL` | `producer` | `url` · `0..1` | 35 · propuesta | Sí | 45 | 45 valores | Presencia en el JSON final |
| `producerLogoURL` | `producer` | `url` · `0..1` | 36 · propuesta | Sí | 45 | 45 valores | Presencia en el JSON final |
| `productionDate` | — | `date` · `0..1` | 37 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `productionPlace` | — | `text` · `0..n` | 38 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `contributorType` | `contributor` | `text controlado` · `0..1` | 39 · propuesta · fuente explícita | Sí | 1107 | 5515 valores | `map_parties()` |
| `contributorName` | `contributor` | `text` · `0..1` | 40 · propuesta · fuente explícita | Sí | 1107 | 5515 valores | `map_parties()` |
| `grantNumberAgency` | `grantNumber` | `text` · `0..1` | 41 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `grantNumberValue` | `grantNumber` | `text` · `0..1` | 42 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `distributorName` | `distributor` | `text` · `0..1` | 43 · propuesta · fuente explícita | Sí | 1106 | 1216 valores | `map_parties()` |
| `distributorAffiliation` | `distributor` | `text` · `0..1` | 44 · propuesta · fuente explícita | Sí | 1094 | 1192 valores | `map_parties()` |
| `distributorAbbreviation` | `distributor` | `text` · `0..1` | 45 · propuesta | Sí | 5 | 5 valores | Presencia en el JSON final |
| `distributorURL` | `distributor` | `url` · `0..1` | 46 · propuesta | Sí | 5 | 5 valores | Presencia en el JSON final |
| `distributorLogoURL` | `distributor` | `url` · `0..1` | 47 · propuesta | Sí | 5 | 5 valores | Presencia en el JSON final |
| `distributionDate` | — | `date` · `0..1` | 48 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_citation()` |
| `depositor` | — | `text` · `0..1` | 49 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `dateOfDeposit` | — | `date` · `0..1` | 50 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `timePeriodCoveredStart` | `timePeriodCovered` | `date` · `0..1` | 51 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `timePeriodCoveredEnd` | `timePeriodCovered` | `date` · `0..1` | 52 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `dateOfCollectionStart` | `dateOfCollection` | `date` · `0..1` | 53 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `dateOfCollectionEnd` | `dateOfCollection` | `date` · `0..1` | 54 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `kindOfData` | — | `text` · `0..n` | 55 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `seriesName` | `series` | `text` · `0..1` | 56 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `seriesInformation` | `series` | `textbox` · `0..1` | 57 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `softwareName` | `software` | `text` · `0..1` | 58 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `softwareVersion` | `software` | `text` · `0..1` | 59 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `relatedMaterial` | — | `textbox` · `0..n` | 60 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `relatedDatasets` | — | `textbox` · `0..n` | 61 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `otherReferences` | — | `text` · `0..n` | 62 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `dataSources` | — | `textbox` · `0..n` | 63 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `originOfSources` | — | `textbox` · `0..1` | 64 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `characteristicOfSources` | — | `textbox` · `0..1` | 65 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `accessToSources` | — | `textbox` · `0..1` | 66 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `author` | — | `compound` · `1..n` | Padre TSV | Sí | 1107 | 2045 filas | `dataverse_fields()` |
| `contributor` | — | `compound` · `0..n` | Padre TSV | Sí | 1107 | 5515 filas | `map_parties()` |
| `datasetContact` | — | `compound` · `1..n` | Padre TSV | Sí | 1107 | 1426 filas | `map_parties()` |
| `dateOfCollection` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `distributor` | — | `compound` · `0..n` | Padre TSV | Sí | 1106 | 1216 filas | `map_parties()` |
| `dsDescription` | — | `compound` · `1..n` | Padre TSV | Sí | 1107 | 1107 filas | `map_citation()` |
| `grantNumber` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `keyword` | — | `compound` · `0..n` | Padre TSV | Sí | 1107 | 9860 filas | `map_citation()` |
| `otherId` | — | `compound` · `0..n` | Padre TSV | Sí | 1107 | 1107 filas | `map_citation()` |
| `producer` | — | `compound` · `0..n` | Padre TSV | Sí | 1107 | 3660 filas | `map_parties()` |
| `publication` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `series` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `software` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `timePeriodCovered` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `topicClassification` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |

### Campos de geospatial

| Campo del TSV | Padre | Tipo y cardinalidad TSV | Crosswalk | Emisión observada | Recursos | Valores o filas | Trazabilidad de implementación |
|---|---|---|---|---|---|---|---|
| `country` | `geographicCoverage` | `text controlado` · `0..1` | 67 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `state` | `geographicCoverage` | `text controlado` · `0..1` | 68 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `city` | `geographicCoverage` | `text` · `0..1` | 69 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `otherGeographicCoverage` | `geographicCoverage` | `text` · `0..1` | 70 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `geographicCoverageDescription` | — | `textbox` · `0..1` | 71 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_geospatial()` |
| `geographicUnit` | — | `text` · `0..1` | 72 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `westLongitude` | `geographicBoundingBox` | `text` · `0..1` | 73 · propuesta · fuente explícita | Sí | 1070 | 1070 valores | Presencia en el JSON final |
| `eastLongitude` | `geographicBoundingBox` | `text` · `0..1` | 74 · propuesta · fuente explícita | Sí | 1070 | 1070 valores | Presencia en el JSON final |
| `northLatitude` | `geographicBoundingBox` | `text` · `0..1` | 75 · propuesta · fuente explícita | Sí | 1070 | 1070 valores | Presencia en el JSON final |
| `southLatitude` | `geographicBoundingBox` | `text` · `0..1` | 76 · propuesta · fuente explícita | Sí | 1070 | 1070 valores | Presencia en el JSON final |
| `minimumAltitude` | `altitudeRange` | `int` · `0..1` | 77 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `maximumAltitude` | `altitudeRange` | `int` · `0..1` | 78 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `wkt` | — | `textbox` · `0..1` | 79 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `altitudeRange` | — | `compound` · `0..1` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |
| `geographicBoundingBox` | — | `compound` · `0..n` | Padre TSV | Sí | 1070 | 1070 filas | `map_geospatial()` |
| `geographicCoverage` | — | `compound` · `0..n` | Padre TSV | No | 0 | 0 filas | Sin hijos emitidos |

### Campos de institutional

| Campo del TSV | Padre | Tipo y cardinalidad TSV | Crosswalk | Emisión observada | Recursos | Valores o filas | Trazabilidad de implementación |
|---|---|---|---|---|---|---|---|
| `projectName` | `project` | `text` · `0..1` | 80 · propuesta · fuente explícita | Sí | 1045 | 1321 valores | `map_projects()` |
| `projectShortName` | `project` | `text` · `0..1` | 81 · propuesta · fuente explícita | Sí | 404 | 407 valores | `map_projects()` |
| `projectID` | `project` | `text` · `0..1` | 82 · propuesta · fuente explícita | Sí | 435 | 632 valores | `map_projects()` |
| `projectDescription` | `project` | `textbox` · `0..1` | 83 · propuesta · fuente explícita | Sí | 194 | 194 valores | `map_projects()` |
| `projectDesignDescription` | `project` | `textbox` · `0..1` | 84 · propuesta · fuente explícita | Sí | 834 | 834 valores | `map_projects()` |
| `projectStudyArea` | `project` | `textbox` · `0..1` | 85 · propuesta · fuente explícita | Sí | 1030 | 1030 valores | `map_projects()` |
| `projectFunding` | `project` | `textbox` · `0..1` | 86 · propuesta · fuente explícita | Sí | 1055 | 1458 valores | `map_projects()` |
| `contractCode` | `contractor` | `text` · `0..1` | 87 · propuesta · fuente explícita | Sí | 464 | 599 valores | `map_contractors()` |
| `contractorName` | `contractor` | `text` · `0..1` | 88 · propuesta · fuente explícita | Sí | 676 | 1006 valores | `map_contractors()` |
| `accessType` | `access` | `text controlado` · `0..1` | 89 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `load_options()`, `map_access()` |
| `restrictionJustification` | `access` | `text controlado` · `0..1` | 90 · propuesta · fuente explícita | Sí | 73 | 73 valores | `map_access()` |
| `localCommunityParticipation` | `access` | `text controlado` · `0..1` | 91 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `altered` | `access` | `text controlado` · `0..1` | 92 · sin fuente | No | 0 | 0 valores | Sin fuente definida |
| `restrictedUntil` | `access` | `date` · `0..1` | 93 · propuesta · fuente explícita | Sí | 50 | 50 valores | `map_access()` |
| `acknowledgement` | — | `textbox` · `0..1` | 94 · propuesta · fuente explícita | Sí | 14 | 14 valores | `map_institutional()` |
| `access` | — | `compound` · `0..1` | Padre TSV | Sí | 1107 | 1107 filas | `map_institutional()` |
| `contractor` | — | `compound` · `0..n` | Padre TSV | Sí | 681 | 1337 filas | `map_institutional()` |
| `project` | — | `compound` · `0..n` | Padre TSV | Sí | 1062 | 1469 filas | `map_institutional()` |

Las matrices de [externalReferences](#campos-de-externalreferences) y [biologicalMetadata](#matriz-de-campos-biológicos) están en sus secciones de resultados e incluyen las reglas de transformación documentadas.

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
- **LANG-H01.** `map_language()` omite códigos de idioma ausentes o sin equivalencia. La prueba caracteriza la omisión vigente y la frecuencia real no fue medida. [Prueba de códigos sin equivalencia](../tests/test_citation_language.py#L73)
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

El efecto posterior de INS-H20 se documenta en la [regresión transversal](#regresión-transversal-de-ins-h20) y en la [matriz de hallazgos](#matriz-consolidada-de-hallazgos).

### Conteos vigentes de institutional

La lectura de los JSON de BIO-H01 produjo los siguientes recuentos descriptivos. El corte histórico de **1327 filas de contratistas**, anterior a INS-H20, se conserva en la sección anterior. Los recuentos vigentes abarcan los mismos destinos y no amplían la revisión semántica histórica.

| Destino | Recursos | Cantidad | Unidad |
|---|---|---|---|
| `contractor` | 681 | 1337 | Filas compuestas |
| `project` | 1062 | 1469 | Filas compuestas |
| `access` | 1107 | 1107 | Filas compuestas |
| `acknowledgement` | 14 | 14 | Valores independientes |

`altered` y `localCommunityParticipation` están definidos en el TSV y marcados sin fuente en el crosswalk. Permanecen ausentes en el corte vigente. [Cobertura de institutional](#campos-de-institutional)

## Resultados de externalReferences

### Alcance, fuentes y esquema del bloque 4

Se evaluaron los 1191 recursos de ingesta, de los cuales 1107 eran elegibles y 84 carecían de JSON final. El alcance comprende las filas 95 a 103 del crosswalk `MigracionCeiba_20261125.xlsx` y el esquema `externalReferences.tsv` del commit indicado en el contexto. La huella SHA-256 del TSV es `22019abe2e490d7d24cf8fe7956bf99bc0f20c996cb25125f6571ac5a9f4666a`.

El padre `externalReference` es compuesto, opcional y repetible (`0..n`). Cada fila tiene nueve hijos posibles, opcionales y de cardinalidad `0..1`. En la tabla, «bibliografía» designa `additionalMetadata/metadata/gbif/bibliography/citation`. Sus identificadores proceden de `@identifier`.

#### Campos de externalReferences

| Campo del TSV | Padre | Tipo y cardinalidad TSV | Crosswalk | Emisión observada | Recursos | Valores o filas | Trazabilidad de implementación | Fuente y tratamiento |
|---|---|---|---|---|---|---|---|---|
| `externalReferenceType` | `externalReference` | `text controlado` · `0..1` | 95 · propuesta · fuente explícita | Sí | 1107 | 11077 valores | `map_external_references()`, `source_reference()` | Procedencia de la fila. La referencia de origen y la copia DOI usan `External Copy of the dataset`. Las citas usan `This dataset references`. Único hijo con vocabulario controlado. |
| `citationText` | `externalReference` | `textbox` · `0..1` | 96 · propuesta · fuente explícita | Sí | 1107 | 10395 valores | `map_external_references()`, `source_reference()` | Etiqueta fija de origen o texto de la bibliografía. Conserva la etiqueta de origen. Para citas, normaliza espacios, escapa el texto y lo envuelve en un párrafo HTML. La copia DOI del inventario carece de texto de cita. |
| `externalReferenceURL` | `externalReference` | `url` · `0..1` | 97 · propuesta · fuente explícita | Sí | 1107 | 1559 valores | `map_external_references()`, `source_reference()` | Clave CEIBA y versión de origen, o identificador bibliográfico. Genera la URL de origen. Conserva las URL bibliográficas admitidas y añade `https://` a las formas `www.` reconstruibles. Aplica la codificación porcentual vigente. Las URL malformadas del alcance quedan en curación. |
| `externalReferenceDOI` | `externalReference` | `text` · `0..1` | 98 · propuesta · fuente explícita | Sí | 732 | 1032 valores | `map_external_references()` | Identificador bibliográfico o `inventory.biologico.doi`. Reconoce el patrón DOI y retira el prefijo del resolutor o de la etiqueta, y los puntos finales. 350 DOI bibliográficos y 682 de copia. |
| `externalReferenceOtherId` | `externalReference` | `text` · `0..1` | 99 · propuesta · fuente explícita | Sí | 1107 | 1176 valores | `map_external_references()`, `source_reference()` | Clave del directorio CEIBA o identificador bibliográfico ISBN/ISSN. Conserva la clave de origen y los ISBN/ISSN con espacios normalizados. 1107 claves de origen y 69 ISBN/ISSN. |
| `externalReferenceNote` | `externalReference` | `textbox` · `0..1` | 100 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `source_reference()` | Texto fijo de origen. Indica que el recurso se migró desde el IPT CEIBA. La curación de URL se registra en el reporte separado. |
| `externalEncoding` | `externalReference` | `text` · `0..1` | 101 · sin fuente | No | 0 | 0 valores | Sin fuente definida | Sin fuente aprobada. Se omite. Información de archivos internos fuera de este campo. |
| `externalFileFormat` | `externalReference` | `text` · `0..1` | 102 · sin fuente | No | 0 | 0 valores | Sin fuente definida | Sin fuente aprobada. Se omite. El formato de archivo necesita corresponder a la referencia externa concreta. |
| `externalFileFormatVersion` | `externalReference` | `text` · `0..1` | 103 · sin fuente | No | 0 | 0 valores | Sin fuente definida | Sin fuente aprobada. Se omite. La versión del formato requiere la misma correspondencia. |
| `externalReference` | — | `compound` · `0..n` | Padre TSV | Sí | 1107 | 11077 filas | `dataverse_fields()` | — |

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

## Resultados de biologicalMetadata

### Alcance, fuentes y esquema del bloque 5

El bloque usa `biologicalMetadata.tsv` del commit `ab2841405a24f149ff7fdb6264f179ede27c6e7c`, con SHA-256 `1ea1e0cc00eb6cf3ecd14a4a018536407789efa463b47046bd946c92243290fb`. Se cotejaron las filas 105 a 131 de `MigracionCeiba_20261125.xlsx` y las equivalencias de `src/mapeo/ceiba/tablas/vocabularies.csv`. El esquema contiene **32 elementos**, distribuidos en **27 campos de contenido** y **cinco padres compuestos**. El crosswalk registra **25 reglas propuestas** y dos campos sin fuente definida, `taxonId` y `biologicalBiases`.

`read_record()` recupera la clave del directorio, los datos de `resource.xml`, `dataset` y la extensión GBIF. `map_biological()` compone el bloque mediante `map_taxonomic()`, `map_temporal()`, `map_methods()` y `map_collections()`. Usa `vocabulary()` para tipo, subtipo, rango y método de preservación. `unflatten_dataset()` reconstruye el bloque con los tipos y cardinalidades del TSV. [Fuentes CEIBA](../src/mapeo/ceiba/ceiba_source.py) · [Transformación](../src/mapeo/ceiba/ceiba_fields.py) · [Reconstrucción](../src/mapeo/reconstruct_mapping.py)

### Matriz de campos biológicos

Los PASOS 12.2 y 12.3 caracterizaron y compararon los valores. Los PASOS 12.6 y 13.1–13.4 confirmaron los recuentos. Las rutas GBIF son relativas a `additionalMetadata/metadata/gbif`.

| Campo del TSV | Padre | Tipo y cardinalidad TSV | Crosswalk | Emisión observada | Recursos | Valores o filas | Trazabilidad de implementación | Fuente y tratamiento |
|---|---|---|---|---|---|---|---|---|
| `emlShortName` | — | `text` · `0..1` | 105 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | `map_biological()` | Nombre del directorio CEIBA. Conserva la clave de origen. |
| `coreType` | — | `text controlado` · `0..1` | 106 · propuesta · fuente explícita | Sí | 1107 | 1107 valores | Presencia en el JSON final | `resource.xml/coreType`. Equivalencia controlada. Precedencia exclusiva de `resource.xml`. |
| `subtype` | — | `text controlado` · `0..1` | 107 · propuesta · fuente explícita | Sí | 950 | 950 valores | Presencia en el JSON final | `resource.xml/subtype`. Equivalencia controlada. Se omite cuando falta el valor. |
| `purpose` | — | `textbox` · `0..1` | 108 · propuesta · fuente explícita | Sí | 990 | 990 valores | Presencia en el JSON final | `dataset/purpose/para` o texto directo. Normaliza espacios y genera párrafos HTML con escape. |
| `introduction` | — | `textbox` · `0..1` | 109 · propuesta · fuente explícita | Sí | 8 | 8 valores | Presencia en el JSON final | `dataset/introduction/para`. Conserva los párrafos utilizables en HTML y su orden. |
| `gettingStarted` | — | `textbox` · `0..1` | 110 · propuesta · fuente explícita | Sí | 6 | 6 valores | Presencia en el JSON final | `dataset/gettingStarted/para` o texto directo. Convierte el texto utilizable en párrafos HTML. |
| `taxonomicCoverageDescription` | — | `textbox` · `0..n` | 111 · propuesta · fuente explícita | Sí | 1068 | 1363 valores | `map_taxonomic()` | `dataset/coverage/taxonomicCoverage/generalTaxonomicCoverage`. Una descripción HTML por cobertura con texto utilizable. |
| `taxonRankName` | `taxonomicClassification` | `text controlado` · `0..1` | 112 · propuesta · fuente explícita | Sí | 1058 | 25354 valores | `map_taxonomic()` | `taxonomicClassification/taxonRankName` en la cobertura. Rango controlado por equivalencia. Los desconocidos pasan a curación. |
| `taxonRankValue` | `taxonomicClassification` | `text` · `0..1` | 113 · propuesta · fuente explícita | Sí | 1068 | 26421 valores | `map_taxonomic()` | `taxonomicClassification/taxonRankValue` en la cobertura. Conserva el nombre científico con espacios normalizados. |
| `commonName` | `taxonomicClassification` | `text` · `0..1` | 114 · propuesta · fuente explícita | Sí | 341 | 5451 valores | `map_taxonomic()` | `taxonomicClassification/commonName` en la cobertura. Conserva los nombres utilizables y los une si hay varios en el nodo. |
| `taxonId` | `taxonomicClassification` | `text` · `0..1` | 115 · sin fuente | No | 0 | 0 valores | Sin fuente definida | Sin fuente definida. Se omite. |
| `temporalCoverageType` | `temporalCoverage` | `text controlado` · `0..1` | 116 · propuesta | Sí | 1090 | 1273 valores | `map_temporal()` | Forma de la cobertura temporal. Vocabulario controlado `Date`, `Date Range` o `Formation period`. |
| `simpleCalendarDate` | `temporalCoverage` | `date` · `0..1` | 117 · propuesta · fuente explícita | Sí | 1 | 1 valores | `map_temporal()` | `singleDateTime/calendarDate` en la cobertura temporal. Valida la fecha y conserva su precisión. |
| `initialCalendarDate` | `temporalCoverage` | `date` · `0..1` | 118 · propuesta · fuente explícita | Sí | 1088 | 1270 valores | `map_temporal()` | `rangeOfDates/beginDate/calendarDate` en la cobertura temporal. Conserva el extremo válido. El extremo inválido informado genera curación `date`. |
| `finalCalendarDate` | `temporalCoverage` | `date` · `0..1` | 119 · propuesta · fuente explícita | Sí | 1089 | 1271 valores | `map_temporal()` | `rangeOfDates/endDate/calendarDate` en la cobertura temporal. Conserva el extremo válido con el mismo criterio que el inicial. |
| `formationPeriod` | `temporalCoverage` | `textbox` · `0..1` | 120 · propuesta · fuente explícita | Sí | 1 | 1 valores | `map_temporal()` | GBIF `formationPeriod`. Conserva el texto normalizado en un párrafo HTML. |
| `emlMethodStudyArea` | `emlMethod` | `textbox` · `0..1` | 121 · propuesta · fuente explícita | Sí | 1104 | 1104 valores | `map_methods()` | `dataset/methods/sampling/studyExtent/description/para`. Convierte los párrafos o el texto utilizable a HTML. |
| `emlMethodSampling` | `emlMethod` | `textbox` · `0..1` | 122 · propuesta · fuente explícita | Sí | 1106 | 1106 valores | `map_methods()` | `dataset/methods/sampling/samplingDescription/para`. Convierte la descripción de muestreo a HTML. |
| `emlMethodQualityControl` | `emlMethod` | `textbox` · `0..1` | 123 · propuesta · fuente explícita | Sí | 669 | 669 valores | `map_methods()` | `dataset/methods/qualityControl/description/para`. Convierte el texto utilizable de control de calidad a HTML. |
| `emlMethodStepNumber` | `emlMethodStep` | `int` · `0..1` | 124 · propuesta | Sí | 1105 | 2503 valores | `map_methods()` | Posición de cada paso emitido. Numera desde 1 y representa el valor como cadena. |
| `emlMethodStepDescription` | `emlMethodStep` | `textbox` · `0..1` | 125 · propuesta · fuente explícita | Sí | 1105 | 2503 valores | `map_methods()` | `dataset/methods/methodStep/description/para`. Conserva un paso por descripción utilizable, en orden y con párrafos HTML. |
| `collectionName` | `collectionData` | `text` · `0..1` | 126 · propuesta · fuente explícita | Sí | 713 | 910 valores | `map_collections()` | GBIF `collection/collectionName`. Conserva el nombre. En listas expandidas, queda en la primera fila. |
| `parentCollectionIdentifier` | `collectionData` | `text` · `0..1` | 127 · propuesta · fuente explícita | Sí | 254 | 316 valores | `map_collections()` | GBIF `collection/parentCollectionIdentifier`. Omite marcadores. En listas expandidas, la madre queda en la primera fila. |
| `collectionIdentifier` | `collectionData` | `text` · `0..n` | 128 · propuesta · fuente explícita | Sí | 78 | 131 valores | `map_collections()` | GBIF `collection/collectionIdentifier`. Conserva un URI o texto RNC como un elemento de lista por fila emitida. |
| `collectionCode` | `collectionData` | `text` · `0..1` | 129 · propuesta · fuente explícita | Sí | 604 | 1713 valores | `map_collections()` | GBIF `collection/collectionIdentifier`. Conserva códigos y expande listas. El texto libre queda como código con curación. |
| `specimenPreservationMethod` | — | `textbox controlado` · `0..n` | 130 · propuesta · fuente explícita | Sí | 628 | 653 valores | `map_biological()` | GBIF `specimenPreservationMethod`. Traduce al vocabulario controlado y deduplica equivalencias por primera aparición. |
| `biologicalBiases` | — | `textbox` · `0..1` | 131 · sin fuente | No | 0 | 0 valores | Sin fuente definida | Sin fuente definida. Se omite. |
| `collectionData` | — | `compound` · `0..n` | Padre TSV | Sí | 713 | 1885 filas | `map_biological()` | — |
| `emlMethod` | — | `compound` · `0..n` | Padre TSV | Sí | 1106 | 1106 filas | `map_methods()` | — |
| `emlMethodStep` | — | `compound` · `0..n` | Padre TSV | Sí | 1105 | 2503 filas | `map_methods()` | — |
| `taxonomicClassification` | — | `compound` · `0..n` | Padre TSV | Sí | 1068 | 26421 filas | `map_taxonomic()` | — |
| `temporalCoverage` | — | `compound` · `0..n` | Padre TSV | Sí | 1090 | 1273 filas | `map_biological()` | — |

En los **1107 bloques** se verificaron **5864 ocurrencias de campos independientes**, **6184 valores independientes** y **71997 valores hijos**, para **78181 valores**. Las **243 filas compuestas repetidas adicionales** conservaron su multiplicidad. El verificador obtuvo cero anomalías estructurales y cero discrepancias inexplicadas de valor, orden o multiplicidad. Los conteos se reprodujeron en el PASO 12.6.

### Campos independientes

La clave del directorio coincide con los 1107 valores de `emlShortName` y con la clave extraída de `packageId`. Los seis `dataset.shortName` presentes son diferentes de esa clave. La versión del recurso se conserva por separado. El cotejo obtuvo 514 coincidencias literales de versión de `packageId` con el inventario y 593 equivalencias numéricas de grafía distinta.

`coreType` y `subtype` usan la representación ingerida de `resource.xml`, según las filas 106 y 107. El cotejo diagnóstico de los términos GBIF interpretables encontró **153 recursos con algún tipo distinto** y **61 recursos con algún subtipo distinto**. Dos recursos tenían subtipo interpretable únicamente en palabras clave. Se mantuvo la precedencia vigente y las 157 ausencias de subtipo. Las diferencias orientan la revisión de fuentes y quedan fuera de los defectos de mapeo confirmados. Las equivalencias usadas de tipo, subtipo, rango y preservación carecían de conflictos y de destinos fuera del TSV.

`purpose`, `introduction` y `gettingStarted` conservan el texto disponible en las formas auditadas. El crosswalk contempla texto directo para `purpose` y `gettingStarted` y sitúa `introduction` y `gettingStarted` en EML 2.2.0. El mapeador actúa sobre la presencia de contenido. La preservación de énfasis y enlaces propuesta en el crosswalk requiere un cotejo desde XML. `specimenPreservationMethod` conserva 653 valores y su orden. `biologicalBiases` queda ausente por falta de fuente definida.

### Cobertura taxonómica

Se reconstruyeron **1364 coberturas** en **1069 recursos**. Los **26422 nodos de origen** produjeron **26421 filas**. El nodo omitido carecía de rango, nombre científico, nombre común y otro texto utilizable. En la población auditada no hubo nodos anidados. Los sintéticos documentan el procesamiento del primer nivel y la omisión de hijos utilizables cuando el padre está vacío.

Las **225 filas repetidas adicionales** corresponden a **222 repeticiones exactas heredadas** y **tres equivalencias por limpieza de espacios**, cada una en un grupo distinto. Se preservaron todas las ocurrencias. La política de deduplicación y el tratamiento de jerarquías se mantienen abiertos. Véase [BIO-H02](#hallazgos-de-biologicalmetadata). `taxonId` queda ausente por falta de fuente definida.

### Cobertura temporal

Las 1272 coberturas de origen aportaron 1271 intervalos y una fecha simple. El período de formación aportó la fila restante. Las 1273 filas finales preservaron los extremos válidos, incluidos **94 con precisión anual**. El único intervalo unilateral conservó su extremo final. El extremo inicial inválido quedó en la curación histórica `date`.

| Clasificación independiente | Intervalos | Avisos nuevos en BIO-H01 |
|---|---:|---:|
| Cronológicamente válidos | 1230 | 0 |
| Inequívocamente invertidos | 13 | 13 |
| Extremos parciales con períodos superpuestos | 27 | 0 |
| Unilaterales | 1 | 0 |
| **Total** | **1271** | **13** |

El verificador calculó los límites calendáricos de cada extremo desde el JSON de ingesta y comparó el mínimo posible del inicio con el máximo posible del fin. Los 13 intervalos invertidos estaban en 13 recursos. Se conservaron extremos y orden de filas, con cero fechas modificadas y cero falsos positivos observados. La [corrección BIO-H01](#bio-h01) añade el aviso. La aceptación de fechas parciales en una carga real queda fuera del cotejo.

### Métodos y pasos metodológicos

Los 1106 objetos de métodos produjeron 1106 filas `emlMethod`. Se omitieron dos descripciones de área y dos de control de calidad con objetos `para` sin texto utilizable. Los **2503 pasos** conservaron orden, contenido y numeración consecutiva como cadenas. La numeración corresponde a los pasos emitidos.

Para métodos y las demás rutas narrativas del bloque se verificaron **7750 valores HTML**, **7762 párrafos** y **338 ocurrencias** con caracteres que requerían escape. Un analizador HTML confirmó el texto normalizado y el orden, con cero discrepancias. Los sintéticos muestran que el contenido disponible solo en nodos estructurados puede perderse y que un enlace puede quedar como texto con URL. El cierre de BIO-H03 cubre **JSON de ingesta → JSON final** para los datos auditados. Marcado, contenido mixto y fidelidad desde XML siguen pendientes, al igual que DESC-H01 y DESC-H02. NOTE-H02 corresponde por separado al texto directo de notas.

### Colecciones biológicas

Los **910 objetos** en **713 recursos** produjeron **1885 filas**. Los 899 identificadores de origen con contenido se clasificaron en 88 URI, 43 textos RNC, 579 códigos simples, 155 listas, cuatro textos libres y 30 marcadores de ausencia. Los otros 11 objetos tenían identificador ausente o vacío. La clasificación de URI y RNC fue sintáctica. Se conservaron las grafías disponibles de nombre y madre con la limpieza vigente y se omitieron los marcadores de ausencia de la madre.

La expansión separa por **coma, punto y coma y barra vertical** (`|`). La **barra inclinada** (`/`) se conserva dentro del código. El nombre y la colección madre quedan en la primera fila. Las filas siguientes preservan los códigos en orden. Las 155 listas produjeron 1130 segmentos, incluidos seis repetidos en tres recursos. Una lista tuvo un solo segmento utilizable y quedó fuera de las **154 curaciones `collection_codes`**. Los cuatro textos libres se conservaron como códigos con curación `collection_identifier`. La identidad de las colecciones y las asociaciones de nombres, madres, identificadores y códigos adicionales quedan pendientes de definición institucional.

## Correcciones implementadas

El inventario distingue las siete correcciones acreditadas de las reglas heredadas. `map_geospatial()` conserva el AST de `4493852` y la regla de rectángulos usa `box_problem()`. La suite y la documentación de geografía se añadieron durante este trabajo. BIO-H01 conserva un parche de trabajo local sin commit.

| Corrección | Archivo | Función | Antes | Después | Justificación | Pruebas | Regresión | Efecto en datos | Commit y estado local |
|---|---|---|---|---|---|---|---|---|---|
| [DATE-01](#date-01) | src/mapeo/ceiba/ceiba_fields.py | iso_date() | Aceptaba fechas imposibles. | Valida calendario y conserva precisión y día de origen. | Fechas imposibles en pruebas sintéticas. | test_citation_distribution_date.py | 1107 JSON y 4 reportes idénticos. | Sin cambio de contenido real en ese corte. | `a547075` · registrado en HEAD y seguimiento local |
| [KW-001](#kw-001) | src/mapeo/ceiba/ceiba_fields.py | GBIF_SUBTYPE_VALUES, usado por map_keywords() | Dos equivalencias de subtipo sin reconocimiento. | Ambos términos reconocidos con vocabulario y URI. | Dos casos reales comprobados. | test_palabras_clave_ceiba.py | 1105 JSON idénticos y 2 modificados · reportes iguales. | 2 valores de vocabulario y 2 URI incorporados. | `a547075` · registrado en HEAD y seguimiento local |
| [PER-H16](#per-h16) | src/mapeo/ceiba/ceiba_fields.py | map_contractors(), map_institutional() | No se generaba aviso para asociaciones indeterminadas. | Una curación por recurso ambiguo y se conserva la separación de entradas. | Revisión de atribución contractual sin combinar valores. | test_ceiba_contractors.py · test_ceiba_people_curation.py | 187 avisos en el corte inicial. Curación vigente 191 tras INS-H20. | El aviso añade trazabilidad · los cambios de metadatos se atribuyen al diferencial de PER-H28 en el corte conjunto. | `a547075` · registrado en HEAD y seguimiento local |
| [PER-H28](#per-h28) | src/mapeo/ceiba/ceiba_fields.py | _split_inventory_contracts(), map_projects(), map_contractors() | Parte de los códigos quedaba fuera o como convenio. | Reconoce listas y prefijo PS redundante donde el tramo se puede clasificar completo. | Omisión contractual real y desclasificación de convenios. | test_ceiba_contractors.py · test_ceiba_people_curation.py | Corte conjunto con 1104 JSON iguales y 3 modificados. | 10 códigos incorporados y 3 valores projectFunding ajustados. | `a547075` · registrado en HEAD y seguimiento local |
| [INS-H20](#ins-h20) | src/formato/ceiba_format.py · src/ingest/ceiba_ingest.py | map_biologico_inventory(), normalize_ceiba_identifier(), resolve_ceiba_inventory(), main() | Coincidencia literal y pérdida de correspondencias por espacios o mayúsculas. | Mantiene literales y recupera correspondencias inequívocas en inventario biológico. | 65 ausencias recuperables en ingesta sin alterar identificadores originales. | test_ceiba_inventory_resolution.py · comparador | 64 JSON elegibles modificados, 28 diferencias de filas justificadas y 333 valores hijos nuevos. | 65 asociaciones incluyendo 1 omitida. Efecto en institutional, externalReferences e inventory_data. | `1c61488` · registrado en HEAD y seguimiento local |
| [EXT-H02](#ext-h02) | src/mapeo/ceiba/ceiba_fields.py | map_external_references() | HTTP/HTTPS malformadas se omitían sin curación en la rama afectada. | Añade curación manteniendo la prioridad de identificadores y la omisión del campo URL. | 4 ocurrencias en 3 recursos. | test_ceiba_external_references.py | 1107 JSON idénticos y 4 filas añadidas. | 1348 a 1352 filas de curación, con 7 reference_url tras la corrección. | `31e624b` · registrado en HEAD y seguimiento local |
| [BIO-H01](#bio-h01) | src/mapeo/ceiba/ceiba_fields.py | _temporal_limit(), map_temporal() | Validación individual sin aviso de inversión. | Compara límites válidos y agrega un aviso por ocurrencia, preservando los extremos. | 13 inversiones inequívocas. | test_ceiba_biological_metadata.py | 1107 JSON idénticos, cinco bloques estables y 13 avisos exactos. | 1352 a 1365 filas. Sin modificación de fechas o de los demás reportes. | Sin commit · diff local de 22 inserciones · entrega general pendiente |

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

### BIO-H01

El cambio se concentra en `src/mapeo/ceiba/ceiba_fields.py`, con **22 inserciones y cero eliminaciones**. Incorpora `json` y `calendar.monthrange` de la biblioteca estándar, añade la función privada `_temporal_limit()` y modifica `map_temporal()`. `iso_date()` conserva su validación individual y su retorno a la precisión original. El resto del mapeador y los demás mapeadores se conservaron. [Implementación de BIO-H01](../src/mapeo/ceiba/ceiba_fields.py#L292)

`_temporal_limit()` interpreta fechas ya validadas. Una fecha completa tiene el mismo límite inferior y superior. Para un año, los límites corresponden al primer y último día del año. Para un mes, van del primer día al último día calendárico, incluidos los febreros bisiestos. `map_temporal()` registra la inversión si ambos extremos son utilizables y el inicio mínimo posible supera el fin máximo posible. La igualdad, los solapamientos parciales y los extremos ausentes o inválidos quedan fuera de ese aviso. El tratamiento histórico `date` de una fecha inválida se conserva.

Cada ocurrencia invertida genera una fila `temporal_range_order` en el campo `temporalCoverage`. La fila identifica el recurso y guarda en `value` una lista JSON con los extremos validados, en su orden y precisión originales. Los límites de comparación son diagnósticos. El destino mantiene sus extremos, orden y multiplicidad, incluidas inversiones repetidas. Ejemplo con un recurso y fechas sintéticos.

```json
{
  "resource": "recurso-sintetico",
  "kind": "temporal_range_order",
  "field": "temporalCoverage",
  "value": "[\"2096-03-01\", \"2096-02\"]",
  "note": "Fecha inicial posterior a la fecha final para la precisión registrada. Revisar el intervalo de origen."
}
```

La comprobación en memoria de los PASOS 12.4 y 12.5 preservó los 1107 bloques y las 159 curaciones biológicas históricas. Reconstruyó exactamente los 13 avisos nuevos. La [regresión del PASO 12.6](#regresión-transversal-de-bio-h01) comprobó ese resultado en los archivos regenerados y cerró BIO-H01 técnicamente.

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

La serie histórica hasta INS-H20 es **1163 → 1350 → 1348 filas**. La primera transición corresponde a la regresión de PER-H16 y PER-H28, con 187 filas añadidas por PER-H16. En la segunda, correspondiente a INS-H20, se conservaron 1335 filas de las 1350 anteriores, se retiraron 15 y se incorporaron 13. Las 28 diferencias se justificaron y afectaron a 12 recursos recuperados.

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

El comparador institucional devolvió estado `complete` con **1107 JSON idénticos, 0 modificados, 0 altas, 0 bajas y 0 sin comparar**. El cotejo independiente confirmó que los 1107 eran idénticos byte a byte y semánticamente. Cada uno de los cinco bloques, `citation`, `geospatial`, `institutional`, `externalReferences` y `biologicalMetadata`, coincidió en presencia, campos, valores, tipos, orden, multiplicidad y estructura. También se conservaron `inventory_data` y las opciones de `datasetVersion`. En este corte, la evidencia de `biologicalMetadata` se limitaba a la regresión diferencial. Su validación funcional se documenta en los [resultados del bloque](#resultados-de-biologicalmetadata).

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

La línea base de ese corte es `../linea_base_correccion_ext_h02/`, de acceso local restringido. El SHA-256 de su `manifest.json` es `a5d89a1842596a389f419552080753b8571cf53c7e6de766a9874a363d3f39b3`.

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

### Regresión transversal de BIO-H01

El PASO 12.6 se ejecutó el **28 de noviembre de 2026**. Inició a las **11:14:09.852** y terminó a las **11:14:15.786**, en `America/Bogota` (UTC−05:00). Duró **5,934 segundos** y finalizó con código **0**. Se ejecutó una sola vez, sin adjuntos y con la ingesta existente.

```bash
.venv/bin/python -B -m src.mapeo.ceiba_metadata_mapping
```

El mapeador procesó una ingesta de 1191 recursos. Generó 1107 JSON finales, con 84 recursos omitidos, 27 borradores, cero problemas de mapeo y 1365 filas de curación. Los **2382 archivos de ingesta** y los **1107 JSON finales** conservaron ruta, tamaño, SHA-256 y bytes. No hubo altas ni bajas.

El comparador institucional devolvió `complete`, con **1107 JSON idénticos, 0 modificados, 0 sin comparar, 0 altas y 0 bajas**. La lectura independiente confirmó la igualdad semántica, incluido el orden de las listas y su multiplicidad. Se cotejaron **5535 pares recurso–bloque**, con cero diferencias en `citation`, `geospatial`, `institutional`, `externalReferences` y `biologicalMetadata`. También se conservaron `metadataLanguage`, `inventory_data`, las demás opciones de `datasetVersion` y los valores externos a `metadataBlocks`.

La regresión reprodujo los recuentos de [referencias externas](#validación-funcional-y-referencia-de-origen) y de [metadatos biológicos](#matriz-de-campos-biológicos). Se preservaron las 1273 filas temporales. El nuevo aviso se comprobó por ocurrencia, con la clasificación independiente documentada en [Cobertura temporal](#cobertura-temporal). La regresión acredita la estabilidad de la transformación en el universo auditado. Las decisiones institucionales y la carga efectiva se gestionan por separado.

| Reporte | Resultado respecto a EXT-H02 |
|---|---|
| `inventory.csv` | Igualdad binaria y semántica. 1191 claves únicas. |
| `load_plan.csv` | Igualdad binaria y semántica. 1107 claves únicas. |
| `version_dates.csv` | Igualdad binaria y semántica. 1107 claves únicas. |
| `mapping_problems.json` | Igualdad binaria y semántica. Cero problemas. |
| `curation.csv` | Único cambio de contenido. Trece adiciones exactas de BIO-H01. |

#### Incidencias de ejecución y verificación

- `stdout` quedó vacío y la bitácora registró dos mensajes `INFO`, con cero errores y eventos críticos. `stderr` conservó el `UserWarning` de `openpyxl` sobre una dependencia interna del libro. El texto de la advertencia fue `xl/pivotCache/_rels/pivotCacheDefinition1.xml.rels contains invalid dependency definitions`. Se anonimizó la ruta de instalación. El reporte de problemas de mapeo permaneció vacío.
- El filtro inicial de confidencialidad detectó su propio patrón de búsqueda en el código histórico. Se ajustó el filtro para identificar rutas reales y se repitió la verificación de lectura.
- El primer verificador posterior se detuvo al sumar un `Counter` y un diccionario. Se corrigió el tipo en el verificador y se repitió el cotejo. Se conservaron los primeros intentos como evidencia. Ambos ajustes se limitaron a los verificadores y la ejecución del mapeador siguió siendo única.

### Curación posterior a BIO-H01

La serie de filas de curación por corte es **1163 → 1350 → 1348 → 1352 → 1365**, desde KW-001, PER-H16/PER-H28 e INS-H20 hasta EXT-H02 y BIO-H01. En el último corte se conservaron las 1352 filas históricas y su orden relativo. Las cinco columnas de las **13 adiciones** coincidieron con la reconstrucción independiente en contenido y multiplicidad. Se obtuvieron cero eliminaciones, cero modificaciones y cero adiciones inesperadas. Diez de los 13 recursos afectados ya tenían curación y tres se incorporaron por primera vez.

| Indicador | EXT-H02 | BIO-H01 |
|---|---:|---:|
| Curaciones globales | 1352 | 1365 |
| Recursos con curación | 913 | 916 |
| Recursos sin curación | 194 | 191 |
| Curaciones biológicas | 159 | 172 |
| Recursos con curaciones biológicas | 159 | 170 |
| `temporal_range_order` | 0 | 13 |

| Categoría | EXT-H02 · filas | BIO-H01 · filas | BIO-H01 · recursos únicos | Origen | Tipo | Finalidad |
|---|---|---|---|---|---|---|
| `author_review` | 8 | 8 | 8 | citation · map_authors() | Revisión institucional | Solicitar revisión de la atribución o de la tabla de autores. |
| `bounding_box` | 37 | 37 | 37 | geospatial · map_geospatial() | Inconsistencia o condición de origen | Revisar rectángulos rechazados por orden, límites o área cero conforme a la regla vigente. |
| `collection_codes` | 154 | 154 | 154 | biologicalMetadata · map_collections() | Transformación documentada | Asignar nombre y colección madre a códigos adicionales tras dividir una lista. |
| `collection_identifier` | 4 | 4 | 4 | biologicalMetadata · map_collections() | Revisión institucional | Verificar identificadores que se conservaron como código ante texto libre. |
| `contact_email` | 31 | 31 | 27 | citation · map_parties() | Transformación documentada | Dejar traza de correos suplidos desde el EML o el respaldo institucional. |
| `contract_code` | 9 | 9 | 9 | institutional · map_projects() | Omisión justificada | Revisar FN/OS sin campo propio y ausentes de la financiación EML. |
| `contractor_association` | 191 | 191 | 191 | institutional · map_contractors() | Advertencia | Revisar correspondencias no inequívocas entre nombres y códigos. |
| `date` | 1 | 1 | 1 | biologicalMetadata · map_temporal() | Inconsistencia de origen | Revisar el extremo inicial que no pasó la validación calendárica. |
| `private_draft` | 27 | 27 | 27 | Configuración de carga · map_records() | Transformación documentada | Registrar que se mantendrá como borrador un recurso privado elegible. |
| `publication_date` | 758 | 758 | 758 | Fechas de versión · version_dates_row()/map_records() | Advertencia | Revisar un historial IPT incompleto y la fecha inicial sugerida. |
| `reference_url` | 7 | 7 | 4 | externalReferences · map_external_references() | Transformación u omisión justificada | Revisar 2 reparaciones y 5 identificadores omitidos por sintaxis. |
| `restricted_until` | 32 | 32 | 32 | institutional · map_access() | Omisión justificada | Revisar fecha de liberación ausente, inválida o sin precisión de día. |
| `restriction_reason` | 91 | 91 | 91 | institutional · map_access() | Revisión institucional | Completar o validar razones de restricción del inventario. |
| `temporal_range_order` | 0 | 13 | 13 | biologicalMetadata · map_temporal() | Inconsistencia de origen | Revisar extremos invertidos conservados en la salida. |
| `terms_of_use` | 2 | 2 | 2 | Configuración de carga · load_options()/map_records() | Impedimento potencial de carga | Completar condiciones o licencia donde ambas faltan. |
| **Total** | **1352** | **1365** | **916** | — | — | Unión de recursos, con superposiciones entre categorías. |

El total de recursos únicos se calcula sobre **1107 elegibles** y los conteos por categoría se superponen. Las 1365 filas incluyen avisos, transformaciones, omisiones justificadas y revisiones institucionales. El conteo de problemas de mapeo procede de `mapping_problems.json` y permanece en cero. La comparación vigente también verificó cero filas de curación duplicadas en sus cinco columnas.

Las siete curaciones `reference_url` de EXT-H02 se preservaron, incluidas dos reparaciones y cinco omisiones. Las 172 filas biológicas corresponden a 154 `collection_codes`, cuatro `collection_identifier`, una `date` y 13 `temporal_range_order`.

### Línea base posterior a BIO-H01

La línea base vigente es `../linea_base_correccion_bio_h01/`. Su `manifest.json` tiene SHA-256 `875ace69c48f89e2b090f16ef5abc3cddb39ad2a7695b7cd589325c500cae4b1`. EXT-H02 se reutilizó como respaldo previo después de verificar sus **3504 archivos registrados** y comprobar la igualdad inicial por ruta, tamaño y SHA-256 de los **3494 archivos vigentes** con sus copias.

| Componente | Archivos registrados |
|---|---:|
| `ingesta/` | 2382 |
| `mapeo/` | 1107 |
| `reportes/` | 5 |
| `codigo/` | 3 |
| `evidencias/` | 24 |
| `README.md` | 1 |
| **Total registrado** | **3522** |
| `manifest.json` | 1 |
| **Total físico** | **3523** |

El manifiesto registra **103473613 bytes**. La auditoría del PASO 12.6 comparó las copias con sus fuentes y verificó huellas, tamaños e inventario completo. Hubo cero faltantes, extras, rutas duplicadas, enlaces simbólicos y diferencias de tamaño o hash. El directorio tiene modo `0700` y los archivos modo `0600`.

`codigo/` conserva el mapeador, la suite biológica y el parche binario de BIO-H01. `evidencias/` conserva el estado Git, el entorno, el resumen de validación, las capturas del mapeador y de pytest, el resumen y el detalle restringido del comparador, la conciliación de curaciones y los verificadores del paso. Se recuperaron y verificaron por SHA-256 las evidencias de 12.3 y 12.4–12.5. El paquete identifica las versiones y huellas necesarias para la reproducción local con los insumos externos correspondientes.

Las líneas base están fuera del repositorio. Los datos, las rutas de recursos del manifiesto y el detalle de las diferencias quedan bajo acceso restringido y fuera de la publicación. La evidencia de integridad acredita la correspondencia con los manifiestos verificados y las huellas de referencia disponibles.

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

### Suite biologicalMetadata

`tests/test_ceiba_biological_metadata.py` contiene **24 funciones**, nueve de ellas parametrizadas, para un total de **65 casos**. Las parametrizaciones aportan 50 casos y las otras funciones aportan 15. Se verificaron tipos, cardinalidades, vocabularios, ausencias, orden, multiplicidad y curaciones con fixtures sintéticas. [Suite de biologicalMetadata](../tests/test_ceiba_biological_metadata.py)

| Grupo | Funciones | Casos |
|---|---:|---:|
| Campos independientes | 5 | 6 |
| Taxonomía | 4 | 6 |
| Cobertura temporal | 4 | 26 |
| Métodos y pasos | 5 | 9 |
| Colecciones | 5 | 17 |
| Integración del bloque | 1 | 1 |
| **Total** | **24** | **65** |

Hay **57 casos de conformidad** y **ocho de caracterización**. Los ocho caracterizan los límites vigentes de jerarquías taxonómicas y contenido estructurado, incluidos énfasis, listas, enlaces y texto mixto. Siete casos de conformidad integraron la selección específica de BIO-H01. En el ciclo red–green, los siete fallaron antes de la corrección por ausencia de los avisos, con las filas temporales esperadas ya correctas. Los siete pasaron tras la corrección con las mismas expectativas. Los 65 casos aprobaron la ejecución específica de 12.5 y la acumulada de 12.6.

Los 36 casos sintéticos en memoria del PASO 12.3 se registran como caracterización independiente y quedan fuera del balance de pytest.

### Regresión acumulada de la selección

| Hito de ejecución | Módulos | Casos | Aprobados | `xfail` estrictos | Fallos inesperados |
|---|---:|---:|---:|---:|---:|
| Validación anterior a la suite geográfica | 12 | 230 | 228 | 2 | 0 |
| Regresión previa a INS-H20 | 13 | 273 | 271 | 2 | 0 |
| Regresión posterior a INS-H20 | 14 | 298 | 296 | 2 | 0 |
| Regresión posterior a EXT-H02 | 15 | 343 | 341 | 2 | 0 |
| Regresión posterior a BIO-H01 | 16 | 408 | 406 | 2 | 0 |

La selección previa registró **1,31 s** para 273 casos y contiene 131 funciones según la inspección estática. La documentación de esa ejecución registra macOS, Python 3.13.2 y pytest 9.2.0. La captura de entorno de la línea base posterior coincide en esas versiones. La equivalencia completa entre entornos históricos quedó fuera de la verificación.

La siguiente tabla conserva el desglose de INS-H20 e incorpora los dos módulos agregados en los cortes posteriores.

| Módulo bajo `tests/` | Funciones | Casos | Parametrización | Objetivo y cobertura | Resultado archivado conciliado | Limitación |
|---|---|---|---|---|---|---|
| `test_citation_title_subject.py` | 7 | 9 | 1 función · 3 casos | Título, nombre alternativo, normalización y vocabulario de asunto. ALT-H01 · comportamiento de campos simples. | 9 aprobados | No fija una nueva regla de versión EML. |
| `test_citation_nivel1.py` | 4 | 4 | 0 funciones · 0 casos | Integración de los elementos simples de citation en el mapeo. Reglas de título, idioma, notas y fecha. | 4 aprobados | Esquema y registros sintéticos. |
| `test_citation_language.py` | 7 | 10 | 2 funciones · 5 casos | Identificadores ISO, equivalencias, orden, repetición y lectura sintética del TSV. LANG-H01, LANG-H02, LANG-H03. | 10 aprobados | No cuantifica códigos originales desconocidos en el universo real. |
| `test_citation_other_id.py` | 5 | 15 | 2 funciones · 12 casos | Identificadores de origen, versión y reconstrucción compuesta. Identidad CEIBA · vínculo con fuente de versión. | 15 aprobados | No comprueba identidad del recurso en servicios externos. |
| `test_citation_distribution_date.py` | 17 | 56 | 10 funciones · 49 casos | Fechas calendáricas, precisión parcial, distribución, fechas de descripción, cobertura y restricción. DATE-01, DATE-H01, BIO-H01 como cobertura histórica de extremos, sin su aviso. | 56 aprobados | No comprueba aceptación del formato por Dataverse. |
| `test_palabras_clave_ceiba.py` | 15 | 36 | 9 funciones · 30 casos | Clasificación de conjuntos, normalización, tesauros y reconstrucción. KW-001 y reglas de palabras clave. | 36 aprobados | Sin comprobar registros de vocabulario externos en tiempo real. |
| `test_citation_description.py` | 11 | 14 | 2 funciones · 5 casos | Texto, HTML, orden y pérdida de énfasis. DESC-H01, DESC-H02, DESC-H03, DESC-H04. | 13 aprobados y 1 `xfail` estricto | Un xfail estricto de énfasis. Los sintéticos no garantizan todo XML. |
| `test_citation_notes.py` | 10 | 12 | 1 función · 3 casos | Texto adicional, párrafos, escape y omisión. NOTE-H01, NOTE-H02. | 11 aprobados y 1 `xfail` estricto | Un xfail estricto para texto directo sin para. |
| `test_compare_ceiba_mapping.py` | 9 | 9 | 0 funciones · 0 casos | Diferencias de JSON/CSV, duplicados, ruta segura, incompletitud y reporte privado. REG-H01 a REG-H04. | 9 aprobados | Los tests prueban mecanismos concretos · siguen abiertos los límites de aceptación y POSIX. |
| `test_ceiba_people.py` | 16 | 25 | 3 funciones · 12 casos | Nombres, entidades, correos, roles y precedencias para personas. PER-H01, PER-H11, PER-H22, PER-H38, PER-H39. | 25 aprobados | Caracterización sintética · autoridad e identidad semánticas pendientes. |
| `test_ceiba_contractors.py` | 16 | 28 | 6 funciones · 18 casos | Extracción, clasificación y separación de identidades y códigos. PER-H16, PER-H28 · comportamiento contractual. | 28 aprobados | Sin verificación de identidad de personas o contratos reales. |
| `test_ceiba_people_curation.py` | 3 | 12 | 2 funciones · 11 casos | Curación de autores, contactos, roles y asociaciones contractuales. PER-H16 y curación de personas. | 12 aprobados | Las notas y los registros se prueban sin decidir identidad institucional. |
| `test_ceiba_geospatial.py` | 11 | 43 | 6 funciones · 38 casos | Descripción, asignación, orden y casos extremos de rectángulos. GEO-H01, GEO-H03, GEO-H04, GEO-H05, GEO-H06. | 43 aprobados | Los indicadores de coherencia real requieren triage independiente. |
| `test_ceiba_inventory_resolution.py` | 9 | 25 | 5 funciones · 21 casos | Prioridad literal, normalización, ambigüedad y adjunto, incluido flujo de ingesta sintético. INS-H20, PER-H25. | 25 aprobados | GeoNetwork y Biocultural solo en el adjunto compartido. |
| **Subtotal posterior a INS-H20** | **140** | **298** | — | — | — | — |
| `test_ceiba_external_references.py` | 13 | 45 | 7 funciones · 39 casos | Referencia inicial, bibliografía, DOI, orden, URL malformada y curación. EXT-H01, EXT-H02, EXT-H03, EXT-H04. | 45 aprobados | Sin resolución externa ni cotejo desde XML original. |
| **Subtotal posterior a EXT-H02** | **153** | **343** | — | — | — | — |
| `test_ceiba_biological_metadata.py` | 24 | 65 | 9 funciones · 50 casos | Transformación biológica e integración sintética con TSV, orden y curación. BIO-H01 a BIO-H04, DATE-01. | 65 aprobados | Jerarquías y texto mixto se caracterizan con sintéticos · no prueban carga. |
| **Total posterior a BIO-H01** | **177** | **408** | — | — | — | — |

Los conteos por módulo proceden de la inspección del código mediante AST. Los resultados de ejecución proceden de la documentación histórica y del resumen de validación de la línea base. Los dos `xfail` estrictos preceden a INS-H20. DESC-H01 documenta la pérdida del marcado de énfasis y NOTE-H02 documenta el texto directo de `additionalInfo` sin `para`. Ambos limitan el fallo esperado a `AssertionError`.

Los 25 casos específicos de INS-H20 están incluidos en los 298 de ese corte. El PASO 11.6 conserva esos casos e incorpora los 45 de `externalReferences`. La evidencia de ejecución registra **341 aprobados, 2 `xfail` históricos, 0 fallos inesperados, 0 `xpass` y 0 nuevas exclusiones**. Las pruebas automatizadas, los 17 criterios históricos de aceptación técnica de INS-H20 y los controles de auditoría se contabilizan por separado.

El PASO 12.6 registró **406 aprobados, 2 `xfail` históricos, 0 `failed`, 0 `xpassed` y 0 `skipped`** en la selección acumulada. Los motivos de DESC-H01 y NOTE-H02 se mantuvieron y el PASO 12.7 cotejó el inventario mediante AST y la evidencia conservada.

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

El comando de la selección vigente corresponde a la invocación registrada en los PASOS 11.6 y 12.6. El universo de módulos corresponde a cada corte.

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest tests/ \
  --ignore=tests/test_ceiba_mapping.py \
  --ignore=tests/test_integracion_ceiba_dataverse.py \
  --ignore=tests/test_validar_integracion_ceiba.py \
  -p no:cacheprovider -q --tb=short -r xX
```

## Reproducibilidad y herramienta de comparación

### Entorno e insumos

| Componente | Archivado en 12.6 | Consulta local en 13.1–13.4 |
|---|---|---|
| Python | 3.13.2 | 3.13.2 |
| Sistema y arquitectura | Darwin 26.7.3 arm64 | Darwin 26.7.3 arm64 |
| Git | git version 2.50.1 (Apple Git-155) | git version 2.50.1 (Apple Git-155) |
| openpyxl | 3.1.5 | 3.1.5 |
| pyDataverse | 0.3.5 | 0.3.5 |
| pytest | 9.2.0 | 9.2.0 |
| python-dotenv | 1.2.4 | 1.2.4 |
| requests | Sin versión independiente registrada para ese corte | 2.34.2 |
| xmltodict | Sin versión independiente registrada para ese corte | 1.0.4 |

Las versiones presentes en ambas capturas concilian. `requirements.txt` declara las dependencias del proyecto y la selección de pruebas requiere pytest como dependencia adicional. La reproducibilidad fuera del entorno documentado queda pendiente de validación. [Dependencias del proyecto](../requirements.txt)

La configuración nominal usa `CEIBA_ORIGIN_PATH` para los directorios CEIBA con `resource.xml` y las versiones EML, `CEIBA_DATA_DIR` y `METADATA_DIR` para salidas intermedias y finales, `INVENTORY_PATH` para el libro de inventario y `TSV_FILES_PATH` para los esquemas efectivos. `FILES_DIR` se usa al preparar adjuntos. Las rutas privadas y los valores de configuración se gestionan fuera de la documentación.

La ingesta escribe `resource_metadata.json` y `files.json` por recurso y genera `inventory.csv`. El mapeo consume esas salidas, el inventario autorizado, la versión EML inicial cuando corresponde y las cuatro tablas CEIBA `citation_authors.csv`, `party_roles.csv`, `restriction_reasons.csv` y `vocabularies.csv`. El entorno auditado tenía ocho TSV, incluidos los cinco del alcance. El crosswalk sirve de referencia técnica. El mapeo genera los JSON finales y `load_plan.csv`, `version_dates.csv`, `curation.csv` y `mapping_problems.json`.

El mapeador escribe `curation.csv` en la raíz de `CEIBA_DATA_DIR`. Cada fila registra un caso de omisión, transformación, advertencia o revisión y conserva `resource`, `kind`, `field`, `value` y `note`. El reporte local sirve como insumo para preparar tablas de correcciones. El equipo debe acordar qué filas exportar, cómo tratarlas y qué acceso conceder. Las exportaciones que dependen de datos cargados en Dataverse requieren coordinar la instancia de destino y la carga autorizada. [Generación del reporte local](../src/mapeo/ceiba_metadata_mapping.py#L198)

La [receta de ingesta y mapeo de INS-H20](#comandos-históricos-de-ingesta-y-mapeo-de-ins-h20), el [mapeo sin adjuntos de BIO-H01](#regresión-transversal-de-bio-h01) y la [selección de pytest](#regresión-acumulada-de-la-selección) corresponden a los cortes indicados. La inspección AST en 13.1–13.4 cotejó la selección archivada. Esta consolidación no reejecutó procesos.

### Comparador institucional

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

## Inventario de líneas base y evidencias

| Directorio local | Finalidad | Corte | Commit de referencia | Archivos registrados | Bytes sin manifiesto | SHA-256 de manifest.json | Evidencia y alcance |
|---|---|---|---|---|---|---|---|
| `linea_base_correccion_per_h16_h28` | Línea base histórica posterior a PER-H16/PER-H28 | 2026-11-26T16:34:08.569766-05:00 | `449385271f8efd92894ba70785e95c2bead70ecd` | 1111 | 57627627 | `3870ffbdbed1e20fdb4072c1daa856b10ed543a628f32961121f6bcbc60eb70f` | 1111 hashes registrados en el manifiesto original. Tamaño físico de las rutas registradas medido por metadato. Alcance de JSON y reportes históricos, con código de referencia y SHA-256 del archivo modificado. |
| `respaldo_pre_regresion_ins_h20` | Respaldo anterior a INS-H20 | 2026-11-27T22:57:23.612841+00:00 | Sin commit declarado | 3494 | 102771671 | `4518db7fb3d83b2c1b97a984c58b97af6c9ef5ecf8a842c39b611182debc18fa` | 3494 pares de huella y tamaño, con auditoría histórica de integridad. Respaldo de los datos antes de la regeneración. El manifiesto no declara commit de producción. |
| `linea_base_correccion_ins_h20` | Línea base posterior a INS-H20 | 2026-11-27T20:58:12-05:00 | `7d1e26204688569b88c0fab5b8627e752807deef` | 3502 | 103034767 | `4946659a5b67f19c9eab7dd12baefa2f001d72e2ce641bac52410dd163131a84` | Registro de entorno, Git, validación e inventario de entradas. 17 criterios cumplidos y diferencial conservado. Commit de partida y parche, con archivos seleccionados de datos, código y evidencias. |
| `linea_base_correccion_ext_h02` | Línea base posterior a EXT-H02 | 2026-11-28T09:46:41-05:00 | `1c6148804f10ded29c99d751320baf530cf44150` | 3504 | 103137636 | `a5d89a1842596a389f419552080753b8571cf53c7e6de766a9874a363d3f39b3` | Resumen de 20 controles, 343 casos y comparación agregada. Detalle restringido fuera de Git. Parte de la reconstrucción de trazabilidad empieza en 1361. |
| `linea_base_correccion_bio_h01` | Línea base posterior a BIO-H01 | 2026-11-28T11:20:36.032-05:00 | `31e624bd31892a549d46148e2a41058d024c5e46` | 3522 | 103473613 | `875ace69c48f89e2b090f16ef5abc3cddb39ad2a7695b7cd589325c500cae4b1` | Capturas verificadas, entorno, Git, resultados de pytest, conciliación, comparador y verificadores. 24 controles de 12.6. Los datos y las diferencias detalladas se conservan con los permisos documentados. La auditoría actual releyó únicamente evidencias y datos necesarios. |

Los tamaños excluyen los manifiestos. El tamaño histórico de PER-H16/PER-H28 se obtuvo por metadato del sistema de archivos porque el manifiesto registra huellas sin tamaños por entrada. Para los otros cuatro cortes se sumaron los tamaños declarados. El inventario físico completo de las bases corresponde a sus auditorías acreditadas. Los recuentos y las huellas identifican los cortes. Los respaldos contienen los archivos declarados y requieren el repositorio, las fuentes auxiliares y el entorno correspondiente para reproducción.

Las líneas base y los detalles de comparación permanecen fuera del repositorio y bajo acceso restringido. BIO-H01 contiene 3523 archivos físicos, incluido el manifiesto, y la evidencia registra modo `0700` para el directorio y `0600` para sus archivos.

La auditoría general se conserva como informe agregado y paquete de verificadores, fuera del repositorio.

| Insumo de 13.1–13.4 | SHA-256 verificado |
|---|---|
| `Informe_consolidado_13_1_a_13_4.txt` | `e30790291d1689c2bf20d04910974a7e6d6bcabc9440aa5fdf546e75bdf1d07e` |
| `Evidencias_13_1_a_13_4.zip` | `0f4a2d987caf0098c9c3934b383d1d9616cdab45a2bf68cfe8eb18d72c2042bd` |

## Matriz consolidada de hallazgos

Los **57 identificadores** incluyen hallazgos confirmados, caracterizaciones de comportamiento, limitaciones y decisiones de origen. La clasificación principal del corte 13.1–13.4 es mutuamente excluyente. El estado histórico se conserva junto con el último estado documentado. La prioridad orienta la revisión y queda separada de los acuerdos institucionales.

| Estado principal del corte 13.1–13.4 | Cantidad |
|---|---|
| Cerrado técnicamente | 8 |
| Cerrado para el universo evaluado | 4 |
| Mitigado con limitaciones | 1 |
| Pendiente de decisión institucional | 28 |
| Pendiente técnico | 12 |
| No evaluable con la evidencia disponible | 4 |
| **Total** | **57** |

La prioridad es una propuesta para organizar la revisión. **Alta** identifica decisiones que condicionan una operación, la aceptación de una regresión o la protección de información. **Media** identifica posibles efectos en la calidad o la trazabilidad. **Baja** identifica límites documentales o casos sin afectación observada. Los estados distinguen evidencia confirmada, limitaciones potenciales y decisiones institucionales abiertas.

| ID | Componente | Descripción e impacto | Evidencia inicial y posterior | Intervención | Estado histórico y antecedente documental | Estado principal 13.1–13.4 | Limitaciones | Prioridad registrada y acción pendiente |
|---|---|---|---|---|---|---|---|---|
| ALT-H01 | citation / ingesta de origen | Falta una comprobación explícita de versión EML para `shortName`. **Impacto.** Una entrada fuera de la versión prevista podría generar `alternativeTitle`. | No se encontraron casos reales fuera de EML 2.2.0. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado por inspección, sin impacto observado. | Pendiente de decisión institucional | Confirmado por inspección, sin impacto observado. | Baja. Acordar si la versión debe exigirse en el mapeo o en la validación de origen. |
| LANG-H01 | citation | Se omiten códigos de idioma ausentes o sin equivalencia. **Impacto.** Un código futuro sin equivalencia quedaría fuera del destino. | `map_language()` y `test_omits_missing_or_unknown_language_from_dataverse()` en `tests/test_citation_language.py:73`. Resultado documentado. Omisión caracterizada por inspección y prueba archivada. Frecuencia real no medida. | Se conserva la omisión vigente · se señala como omisión documental. | Comportamiento vigente caracterizado en prueba. | Pendiente de decisión institucional | Impacto real sin cuantificar. La prueba caracteriza la omisión vigente. | Acordar el registro o la curación de códigos de idioma desconocidos. |
| LANG-H02 | citation / ingesta de origen | Un recurso documenta `oci` y se conserva `Occitan`. **Impacto.** Puede requerir confirmar el idioma declarado en la fuente. | 1 recurso con ese código. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, pendiente de curación. | Pendiente de decisión institucional | Confirmado, pendiente de curación. | Media. Revisar la fuente y conservar la equivalencia mientras se verifica. |
| LANG-H03 | citation / ingesta de origen | Hay una fila del vocabulario sin identificador. **Impacto.** La fila carece de una clave para la búsqueda por identificador. | 1 fila, sin impacto observado. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado. | Pendiente técnico | Confirmado. | Baja. Revisar la fila con el responsable del vocabulario. |
| DESC-H01 | citation / ingesta de origen | Se pierde el marcado de énfasis. **Impacto.** Pérdida de formato en las descripciones afectadas. | 3 recursos, 4 párrafos y 8 etiquetas. El texto se conserva y el caso sintético tiene `xfail` estricto. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, pendiente de decisión. | Pendiente de decisión institucional | Confirmado, pendiente de decisión. | Media. Acordar qué marcado debe preservarse y revisar su paso por la ingesta. |
| DESC-H02 | citation / ingesta de origen | Posible pérdida o transformación incompleta de enlaces. **Impacto.** Podría cambiar la representación de los enlaces de futuros recursos. | Sin casos reales en las descripciones evaluadas. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Limitación potencial. | Pendiente de decisión institucional | Limitación potencial. | Baja. Definir la regla y cubrirla con casos sintéticos si se aprueba. |
| DESC-H03 | citation / ingesta de origen | El XML mixto puede requerir tratamiento adicional. **Impacto.** Podría afectar el orden o el marcado en otras formas de XML. | Sin casos reales en las descripciones evaluadas. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Limitación potencial. | Pendiente de decisión institucional | Limitación potencial. | Baja. Caracterizar las formas necesarias antes de ampliar la transformación. |
| DESC-H04 | citation / ingesta de origen | Formato de `dsDescriptionValue` pendiente de acuerdo. **Impacto.** Afecta presentación y conservación del marcado. | La ruta evaluada usa HTML. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Decisión institucional pendiente. | Pendiente de decisión institucional | Decisión institucional pendiente. | Media. Resolver si se conserva HTML o se usa texto plano. |
| NOTE-H01 | citation / ingesta de origen | La regla de HTML para `notesText` carece de explicitación en el crosswalk. **Impacto.** La expectativa documental puede diferir de la salida. | La implementación usa HTML. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, pendiente de decisión. | Pendiente de decisión institucional | Confirmado, pendiente de decisión. | Media. Acordar y documentar el formato en la fila correspondiente. |
| NOTE-H02 | citation / ingesta de origen | Se admite texto directo en `additionalInfo` sin `para`. **Impacto.** Una entrada de esa forma podría generar `notesText`. | Sin casos reales identificados. Se conserva un caso sintético con `xfail` estricto. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado con evidencia sintética, pendiente de decisión. | Pendiente de decisión institucional | Confirmado con evidencia sintética, pendiente de decisión. | Baja. Acordar si se admite el texto directo. |
| CUR-H01 | citation / ingesta de origen | Tratamiento externo de `jgtiCuratorialUnit` pendiente. **Impacto.** Se requiere una vía para conservar la información y verificar su exclusión del mapeo. | 42 recursos identificados. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Presencia confirmada, verificación integral pendiente. | Pendiente de decisión institucional | Presencia confirmada, verificación integral pendiente. | Alta. Definir el archivo externo y comprobar su cobertura. |
| PER-H01 | citation / personas y organizaciones | El crosswalk y el código nombran de forma distinta la tabla de roles. **Impacto.** Dificulta identificar la tabla que gobierna el mapeo. | contributor_roles.csv frente a party_roles.csv. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Diferencia documental confirmada. | Pendiente de decisión institucional | Diferencia documental confirmada. | Baja. Concertar la denominación y alinear la documentación. |
| PER-H02 | citation / personas y organizaciones | El flujo evaluado carece de una autoridad de personas. **Impacto.** La identificación depende de las fuentes disponibles y sus reglas de comparación. | Fila histórica PER-H02/H03. Falta people.csv en el flujo. Resultado documentado. Ausencia observada de `people.csv` y `organisations.csv` en el flujo evaluado. | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado para el flujo evaluado. En el antecedente documental figura la fila agrupada PER-H02/H03. | Pendiente de decisión institucional | Confirmado para el flujo evaluado. | Media. Definir si se incorporan autoridades y quién las mantiene. |
| PER-H03 | citation / personas y organizaciones | El flujo evaluado carece de una autoridad de organizaciones. **Impacto.** La identificación depende de las fuentes disponibles y sus reglas de comparación. | Fila histórica PER-H02/H03. Falta organisations.csv en el flujo. Resultado documentado. Ausencia observada de `people.csv` y `organisations.csv` en el flujo evaluado. | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado para el flujo evaluado. En el antecedente documental figura la fila agrupada PER-H02/H03. | Pendiente de decisión institucional | Confirmado para el flujo evaluado. | Media. Definir si se incorporan autoridades y quién las mantiene. |
| PER-H11 | citation / personas y organizaciones | La reparación de `@humboldt.org` se extiende a otros correos institucionales. **Impacto.** Puede cambiar direcciones distintas del contacto institucional de respaldo. | 14 contactos finales no correspondientes al correo I2D. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, política pendiente. | Pendiente de decisión institucional | Confirmado, política pendiente. | Media. Validar el alcance de la reparación con el equipo. |
| PER-H22 | institutional / contratos | Una organización quedó excluida como contratista. **Impacto.** Su información contractual puede requerir un tratamiento distinto. | 1 organización. (ff0f517). Resultado documentado. Persiste una exclusión respaldada por EML. Las apariciones finales de nombre respaldadas por organización fueron 147 → 147, las respaldadas por persona 719 → 719 y las indeterminadas 138 → 140. Las dos altas presentan señales léxicas institucionales y su identidad permanece indeterminada. | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, admisión pendiente de decisión. Estado en el Markdown anterior. Exclusión confirmada. Admisión de organizaciones y fuente de autoridad pendientes de decisión. | Pendiente de decisión institucional | Exclusión confirmada. Admisión de organizaciones y fuente de autoridad pendientes de decisión. | Media. Acordar si se admiten organizaciones como contratistas y qué evidencia acredita su identidad. |
| PER-H24 | institutional / contratos | La equivalencia de nombres usa subconjuntos de palabras. **Impacto.** La coincidencia textual requiere respaldo adicional para acreditar identidad. | 92 coincidencias por subconjuntos y 35 casos con múltiples coincidencias posibles. (ff0f517). Resultado documentado. Antecedente de 92 coincidencias por subconjuntos y 35 casos múltiples. Medición exclusiva 92 → 96, inclusiva 110 → 115 y múltiple 35 → 38. Los conjuntos pueden superponerse. El criterio histórico exacto no se recuperó. | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, revisión semántica pendiente. | Pendiente de decisión institucional | Confirmado, revisión semántica pendiente. | Media. Revisar candidatos múltiples y acordar criterios de identidad o curación. |
| PER-H25 | Ingesta / inventario | Faltan datos del inventario biológico en recursos publicados. **Impacto.** Limita el enriquecimiento cuya única fuente es ese inventario. | 80 recursos. (ff0f517). Resultado documentado. 80 a 16 ausencias elegibles · 38 en el total, incluidas 22 omitidas. Antecedente de 80 recursos. En los 1107 elegibles, la reconstrucción independiente obtuvo 80 → 16 ausencias y 64 mitigadas mediante INS-H20. Quedan 38 ausencias totales, 22 en recursos sin JSON final. El predicado histórico exacto no se recuperó. | Mitigar ausencias mediante INS-H20. | Confirmado. Estado en el Markdown anterior. Mitigado técnicamente, abierto. | Mitigado con limitaciones | El predicado histórico exacto quedó sin recuperar. | Media. Determinar cuáles de las 16 ausencias elegibles requieren una fuente adicional o curación. Documentar por separado las 22 sin JSON final. |
| PER-H26 | institutional / contratos | El reconocimiento de códigos distingue mayúsculas y minúsculas. **Impacto.** Podría excluir variantes de capitalización en otros datos. | Comportamiento caracterizado, sin pérdida real identificada. (ff0f517). Resultado documentado. Se conservaron tres señales de capitalización en los mismos recursos. Hubo cero señales nuevas, cero pérdidas observadas y cero incorporaciones adicionales al flexibilizar las variantes evaluadas. | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Limitación potencial, sin pérdida observada. Estado en el Markdown anterior. Limitación potencial caracterizada, abierta. | Pendiente de decisión institucional | Limitación potencial caracterizada, abierta. | Baja. Mantener la regla hasta contar con evidencia de impacto y una decisión. |
| PER-H27 | institutional / contratos | Hay información residual del inventario sin proyecto Macro asociado. **Impacto.** El destino depende de la pertinencia de cada segmento y de su respaldo. Los conteos de recursos, segmentos, valores y párrafos corresponden a unidades distintas. | 265 recursos. (ff0f517). Resultado documentado. Antecedente de 265 recursos. La medición independiente de recursos sin código Macro con residuales distintos de FN/OS dio 265 → 271. De los seis casos nuevos, cinco coinciden literalmente con la financiación EML y uno conserva el residual sólo en `inventory_data` dentro del alcance auditado. En el escenario actual, 34 residuales se conservan sólo en ese nivel y nueve tienen coincidencia textual parcial. Véase la [reconciliación de I03](#reconciliación-de-i03-en-projectfunding). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, destino pendiente de decisión. Estado en el Markdown anterior. Confirmado, destino institucional pendiente. | Pendiente de decisión institucional | Confirmado, destino institucional pendiente. | Media. Clasificar los valores y acordar el destino de la información pertinente. |
| PER-H29 | institutional / contratos | Los nombres de contratistas del inventario contienen separadores. **Impacto.** La separación podría cambiar el conteo de nombres y el resultado de la asociación con códigos. | 27 recursos. (ff0f517). Resultado documentado. Antecedente de 27 recursos con criterio no recuperado. Medición ampliada 58 → 61 y filtro de barra vertical 27 → 30. Hay tres casos nuevos. En el escenario actual, nueve casos tienen coincidencias textuales con nombres EML documentados por separado, 49 quedan indeterminados y tres son denominaciones institucionales respaldadas. Hubo cero fragmentaciones nuevas. | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, regla pendiente de decisión. Estado en el Markdown anterior. Confirmado, regla de separación pendiente. | Pendiente de decisión institucional | Confirmado, regla de separación pendiente. | Media. Conservar la cadena original y acordar la evidencia necesaria para dividir nombres o revisar asociaciones. |
| PER-H36 | citation / personas y organizaciones | Algunas apariciones institucionales se clasificaron internamente como personas. **Impacto.** Puede requerir revisar el reconocimiento de instituciones. | 3 apariciones en 2 recursos. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado. | Pendiente técnico | Confirmado. | Media. Revisar los casos y definir si se necesita una regla particular o una autoridad. |
| PER-H37 | citation / personas y organizaciones | Se generaron afiliaciones redundantes. **Impacto.** Añade información repetida al destino. | 2 afiliaciones en 1 recurso. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado. | Pendiente técnico | Confirmado. | Baja. Revisar el origen de la redundancia antes de modificar la regla. |
| PER-H38 | citation / personas y organizaciones | Hay diferencias de afiliación entre apariciones deduplicadas. **Impacto.** La primera aparición puede conservar una afiliación distinta de otra fuente. | 36 conflictos. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, revisión semántica pendiente. | Pendiente de decisión institucional | Confirmado, revisión semántica pendiente. | Media. Acordar si se mantiene la precedencia o se envían los conflictos a curación. |
| PER-H39 | citation / personas y organizaciones | Hay diferencias de correo entre apariciones deduplicadas. **Impacto.** Puede prevalecer un correo distinto del que corresponda usar. | 2 conflictos. Uno coincide con un conflicto de afiliación. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, revisión semántica pendiente. | Pendiente de decisión institucional | Confirmado, revisión semántica pendiente. | Media. Revisar las fuentes y acordar precedencia o curación. |
| INS-H20 | Ingesta CEIBA / inventario | La búsqueda literal impedía asociar filas biológicas con variantes de espacios o capitalización. **Impacto.** Aumenta la cobertura del inventario y cambia los valores derivados que se documentan en la regresión. | 1088 asociaciones originales conservadas, 65 recuperadas, 64 de ellas con JSON final, y 38 ausencias residuales. (1c61488). Resultado documentado. 1088 asociaciones conservadas, 65 recuperadas, 64 con JSON final y 38 ausencias residuales. | Resolución exacta prioritaria y respaldo normalizado inequívoco antes del adjunto. | Ausencias por coincidencia literal, diagnosticadas antes de la corrección. Estado en el Markdown anterior. **Corrección implementada y validación técnica aprobada.** Corte de código registrado en `1c61488`. | Cerrado técnicamente | La resolución de las 38 ausencias se gestiona mediante PER-H25. | Por reevaluar. Gestionar las ausencias residuales mediante PER-H25. |
| DATE-01 | Fechas compartidas | La función admitía fechas calendáricamente imposibles. **Impacto.** Podía conservar un valor imposible o afectar validación posterior. | Auditoría sintética de `iso_date()` y diff `a547075`. Resultado documentado. 1107 JSON y cuatro reportes idénticos en la regresión documentada. | Validar calendario y retener precisión original. | Defecto funcional detectado. | Cerrado técnicamente | Validación de calendario, con sufijos ISO completos y aceptación del destino fuera de alcance. | Cerrar la validación calendárica · precisión y zona quedan bajo DATE-H01. |
| KW-001 | citation | Dos términos oficiales de subtipo GBIF carecían de reconocimiento. **Impacto.** Omisión de dos asignaciones de vocabulario y de sus URI. | Validación de palabras clave y diff `a547075`. Resultado documentado. Dos recursos ajustados, 1105 JSON idénticos, dos valores de vocabulario y dos URI añadidos. | Añadir dos términos a `GBIF_SUBTYPE_VALUES`. | Equivalencias faltantes confirmadas. | Cerrado técnicamente | Abarca las dos equivalencias confirmadas. | Conservar ambos términos y cobertura sintética. |
| PER-H16 | institutional | Una asociación ambigua conservaba nombres y códigos separados sin aviso específico. **Impacto.** Asociaciones indeterminadas requieren revisión. | Regresión contractual y diff `a547075`. Resultado documentado. 187 filas en el primer corte. Después de INS-H20, 191 filas vigentes. | Añadir curación `contractor_association` sin combinar nombres y códigos arbitrariamente. | Brecha de curación identificada. | Cerrado técnicamente | La validez institucional de la categoría y de cada asociación sigue abierta. | Validar la categoría y el tratamiento de casos ambiguos con el equipo. |
| PER-H28 | institutional | Códigos contractuales en listas o con prefijo redundante quedaban sin extraer. **Impacto.** Faltaban códigos y parte aparecía como financiación. | Regresión contractual y diff `a547075`. Resultado documentado. Recuperación de 10 códigos en 3 recursos y ajuste de 3 valores `projectFunding` en el corte original. | Separar códigos válidos con coma y prefijo PS redundante en `_split_inventory_contracts()`. | Pérdida real confirmada antes de la corrección. | Cerrado técnicamente | Tramos mixtos mantienen la regla previa. PER-H26 sigue abierto. | Conservar la clasificación compartida y revisar variantes solo con nueva evidencia. |

El PASO 10.12.2.13.5 reevaluó los seis hallazgos relacionados. PER-H25 conserva el antecedente de 80 recursos publicados sin datos de inventario. La reconstrucción reproduce esa cifra en el universo elegible con el criterio documentado en la matriz. La equivalencia con el procedimiento histórico queda indeterminada. Los seis hallazgos permanecen abiertos para decisión institucional.

### Hallazgos geográficos

Los hallazgos geográficos pueden corresponder al mismo recurso. Sus cantidades no se suman para estimar recursos únicos afectados.

| ID | Componente | Descripción e impacto | Evidencia inicial y posterior | Intervención | Estado histórico y antecedente documental | Estado principal 13.1–13.4 | Limitaciones | Prioridad registrada y acción pendiente |
|---|---|---|---|---|---|---|---|---|
| GEO-H01 | geospatial | Se omiten los rectángulos completamente vacíos sin fila de curación. **Impacto.** Una cobertura futura sin ningún lado informado quedaría sin fila de curación. | Comportamiento confirmado en pruebas sintéticas. 0 casos en los recursos evaluados. (7d1e262). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado con evidencia sintética, sin impacto observado. | Pendiente de decisión institucional | Confirmado con evidencia sintética, sin impacto observado. | Baja. Mantener el comportamiento actual sin modificación inmediata. |
| GEO-H02 | geospatial | Hay rectángulos aceptados con longitudes positivas. **Impacto.** La longitud positiva indica un caso para revisión y por sí sola es compatible con una cobertura legítima. | 20 rectángulos. En 18 casos la longitud oeste es negativa y en 2 ambas longitudes son positivas. (7d1e262). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Indicador diagnóstico, pendiente de revisión individual. | Pendiente técnico | Indicador diagnóstico, pendiente de revisión individual. | Media. Revisar la coherencia geográfica y concertar indicadores adicionales de curación. |
| GEO-H03 | geospatial | Las descripciones de varias coberturas se consolidan en párrafos HTML. **Impacto.** El comportamiento conserva varias descripciones en un único campo cuando aparecen. | Orden y consolidación verificados en pruebas sintéticas. 0 recursos evaluados con varias coberturas. (7d1e262). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado con evidencia sintética. | Pendiente de decisión institucional | Confirmado con evidencia sintética. | Baja. Mantener la cobertura sintética y revisar el formato junto con GEO-H06. |
| GEO-H04 | geospatial | Se identificó una inversión real de longitud. **Impacto.** El rectángulo rechazado queda disponible para revisión de origen. | 1 rectángulo con oeste > este, omitido del JSON final y registrado en curación. (7d1e262). Resultado documentado. 1 inversión real omitida del destino y registrada correctamente. | Verificar la regla heredada de exclusión y curación. | Confirmado, tratamiento vigente verificado. | Cerrado para el universo evaluado | Cierre para el rectángulo observado. | Baja. Mantener la regla de rechazo y curación. |
| GEO-H05 | geospatial | Hay rectángulos de área cero. **Impacto.** El JSON final omite coberturas que pueden representar puntos o líneas legítimos. | 36 rectángulos, con 26 puntos, 7 de ancho cero y 3 de alto cero. Todos figuran en curación. (7d1e262). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado, tratamiento definitivo pendiente. | Pendiente de decisión institucional | Confirmado, tratamiento definitivo pendiente. | Media. Concertar el tratamiento de coberturas puntuales y lineales. |
| GEO-H06 | geospatial | Las descripciones geográficas se transforman a HTML. **Impacto.** La representación visual depende del formato elegido para el campo. | 1107 descripciones transformadas y 305287 caracteres normalizados conservados. (7d1e262). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Conservación textual confirmada, formato pendiente de concertación. | Pendiente de decisión institucional | Conservación textual confirmada, formato pendiente de concertación. | Media. Acordar el formato definitivo de `geographicCoverageDescription`. |
| GEO-H07 | geospatial | Un rectángulo aceptado es compatible con un posible intercambio de latitud y longitud. **Impacto.** El intercambio, si se confirma, alteraría la ubicación asignada a la cobertura. | 1 recurso con mención de Colombia y longitudes positivas. La geometría es consistente con la hipótesis de intercambio. (7d1e262). Resultado documentado. El posible intercambio solo cuenta con un indicador. | Conservar el valor y señalar revisión individual. | Hipótesis diagnóstica, pendiente de revisión individual. | No evaluable con la evidencia disponible | La coherencia real exige comprobar la fuente individual. | Alta. Revisar la fuente y el alcance del recurso, conservando las coordenadas originales durante la revisión. |
| GEO-H08 | geospatial | Hay rectángulos aceptados fuera de la referencia aproximada de Colombia. **Impacto.** Puede haber una discrepancia entre la cobertura y lo que declara la descripción. | 4 rectángulos fuera de la referencia. 1 menciona Colombia. (7d1e262). Resultado documentado. 4 indicadores fuera de la referencia aproximada, con una descripción que menciona Colombia. | Conservar valores admitidos y señalar revisión individual. | Indicador diagnóstico, pendiente de revisión individual. | No evaluable con la evidencia disponible | La referencia rectangular carece de valor como frontera oficial. | Media. Evaluar la coherencia con la cobertura real de los recursos. |
| GEO-H09 | geospatial | Una cobertura puntual queda fuera de la referencia aproximada de Colombia. **Impacto.** La ubicación del punto puede revisarse en la fila existente. | 1 de 26 puntos evaluados. Ya figura en curación por área cero. (7d1e262). Resultado documentado. 1 punto fuera de la referencia diagnóstica entre 26 puntos. | Conservar el caso en curación por área cero. | Indicador diagnóstico sobre un caso ya registrado en curación. | No evaluable con la evidencia disponible | La incoherencia geográfica requiere contraste individual. | Baja. Revisar junto con el tratamiento de coberturas puntuales. |

### Hallazgos de externalReferences

| ID | Componente | Descripción e impacto | Evidencia inicial y posterior | Intervención | Estado histórico y antecedente documental | Estado principal 13.1–13.4 | Limitaciones | Prioridad registrada y acción pendiente |
|---|---|---|---|---|---|---|---|---|
| EXT-H01 | externalReferences | Hay repeticiones bibliográficas exactas en el destino. **Impacto.** Deduplicar podría retirar ocurrencias de origen o combinar identificadores distintos. | 28 repeticiones en 20 recursos. De ellas, 25 proceden de la ingesta y tres resultan de la normalización. (31e624b). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Abierto, pendiente de política institucional. | Pendiente de decisión institucional | Abierto, pendiente de política institucional. | Baja. Conservar multiplicidad y orden hasta acordar los criterios de deduplicación. |
| EXT-H02 | externalReferences | Cuatro identificadores HTTP/HTTPS malformados quedaban sin curación. **Impacto.** Los identificadores omitidos quedan disponibles para revisión. | Se añadieron cuatro filas en tres recursos. Las 1107 listas finales permanecieron idénticas. (31e624b). Resultado documentado. Cuatro adiciones en tres recursos, con dos reparaciones y cinco omisiones acumuladas. 1107 JSON idénticos. | Añadir aviso por URL HTTP/HTTPS no admisible, preservando salida y precedencia. | Cuatro ocurrencias malformadas carecían de curación antes de EXT-H02. Estado en el Markdown anterior. **Cerrado técnicamente.** Corrección implementada y regresión aprobada. | Cerrado técnicamente | No acredita resolución externa de URL o DOI. | Media. Mantener la cobertura de curación y revisar los destinos de forma individual. |
| EXT-H03 | externalReferences | El destino de GBIF dataset key es una opción no decidida. **Impacto.** El valor queda en el inventario adjunto. Hace falta una regla para asignarlo al bloque. | 682 valores con forma UUID. Coexisten con un DOI reconocido en 681 recursos. (31e624b). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Abierto, pendiente de definición institucional. | Pendiente de decisión institucional | Abierto, pendiente de definición institucional. | Baja. Acordar campo, tipo de referencia y criterio de identidad antes de mapear. |
| EXT-H04 | externalReferences | Se evaluó la conservación textual de la bibliografía. **Impacto.** El cotejo acredita la transformación a HTML desde el JSON intermedio. | Las 9288 citas conservan el texto disponible en la ingesta. (31e624b). Resultado documentado. 9288 citas preservaron texto normalizado desde la ingesta. | Cotejar HTML y extracción del texto en las dos representaciones. | Cerrado técnicamente para ingesta JSON → destino JSON. | Cerrado para el universo evaluado | Alcance JSON de ingesta a JSON final. | Baja. Acordar si el equipo requiere un cotejo desde XML original, incluido el contenido anidado. |

Las diferencias textuales de versión, el token de inventario con apariencia DOI y los comportamientos sintéticos de texto anidado y codificación se mantienen como observaciones de alcance en [Resultados de externalReferences](#resultados-de-externalreferences).

### Hallazgos de biologicalMetadata

| ID | Componente | Descripción e impacto | Evidencia inicial y posterior | Intervención | Estado histórico y antecedente documental | Estado principal 13.1–13.4 | Limitaciones | Prioridad registrada y acción pendiente |
|---|---|---|---|---|---|---|---|---|
| BIO-H01 | biologicalMetadata | Los extremos válidos se evaluaban individualmente y las inversiones carecían de aviso. **Impacto.** La curación identifica los intervalos para revisión y el destino conserva las fechas. | 1271 intervalos, con 1230 cronológicos, 13 invertidos, 27 parciales superpuestos y uno unilateral. Se conservaron 94 extremos anuales y todas las filas. Los 13 avisos coinciden en 13 recursos, sin falsos positivos observados. (Markdown vigente). Resultado documentado. 13 avisos en 13 recursos, sin cambios en 1107 JSON y sin falsos positivos observados. 1271 intervalos, con 1230 cronológicos, 13 invertidos, 27 parciales superpuestos y uno unilateral. Se conservaron 94 extremos anuales y todas las filas. Los 13 avisos coinciden en 13 recursos, sin falsos positivos observados. | Comparar extremos de intervalos parciales o completos y añadir aviso por ocurrencia. | Brecha en PASO 12.3 · D03 en REVISAR. Estado en el Markdown anterior. **Cerrado técnicamente.** Regresión del PASO 12.6 aprobada. | Cerrado técnicamente | Aceptación de fechas o carga en Dataverse fuera de alcance. | Media. Revisar los casos de origen mediante la nueva categoría. |
| BIO-H02 | biologicalMetadata | La taxonomía conserva repeticiones y procesa el primer nivel. **Impacto.** La deduplicación o el tratamiento de jerarquías podría cambiar la representación de origen. | 26422 nodos y 26421 filas. Se omitió un nodo sin datos utilizables. De 225 repeticiones finales, 222 se heredaron y tres resultan de limpiar espacios. Los sintéticos muestran omisión de hijos. (Markdown vigente). Resultado documentado. 26422 nodos a 26421 filas. 222 repeticiones heredadas y 3 por espacios. 26422 nodos y 26421 filas. Se omitió un nodo sin datos utilizables. De 225 repeticiones finales, 222 se heredaron y tres resultan de limpiar espacios. Los sintéticos muestran omisión de hijos. | Conservar orden y multiplicidad. Caracterizar jerarquías sintéticamente. | Cerrado técnicamente para el universo auditado.** Política de deduplicación y jerarquías pendientes. | Cerrado para el universo evaluado | Primer nivel en la población y tratamiento de hijos pendiente. | Baja. Conservar multiplicidad y acordar cómo representar hijos y variantes. |
| BIO-H03 | biologicalMetadata | Se evaluó la conservación textual de las rutas narrativas. **Impacto.** La evidencia acredita el texto disponible entre los dos JSON. | 7750 valores HTML, 7762 párrafos y 338 ocurrencias con escape, sin diferencias textuales. Los sintéticos muestran límites de marcado y texto mixto. (Markdown vigente). Resultado documentado. 7750 valores HTML, 7762 párrafos y 338 ocurrencias con caracteres que requieren escape, sin discrepancias. 7750 valores HTML, 7762 párrafos y 338 ocurrencias con escape, sin diferencias textuales. Los sintéticos muestran límites de marcado y texto mixto. | Cotejar texto normalizado y HTML desde la ingesta. | Cerrado para la conservación textual de JSON de ingesta → JSON final.** Marcado, contenido mixto y XML original pendientes. DESC-H01 y DESC-H02 siguen abiertos. | Cerrado para el universo evaluado | JSON de ingesta a JSON final. XML, marcado y contenido mixto pendientes. | Baja. Definir el contenido que debe preservarse y cotejar contra XML cuando corresponda. |
| BIO-H04 | biologicalMetadata | Las listas de códigos de colección se expanden y la asociación se registra para curación. **Impacto.** Nombre y madre quedan en la primera fila. Los códigos adicionales conservan orden y requieren revisar su asociación. | 910 objetos, 1885 filas, 154 curaciones `collection_codes` y cuatro `collection_identifier`. Se separa por coma, punto y coma y barra vertical. La barra inclinada se conserva. (Markdown vigente). Resultado documentado. 910 objetos, 1885 filas, 154 curaciones de códigos y 4 de identificadores. 910 objetos, 1885 filas, 154 curaciones `collection_codes` y cuatro `collection_identifier`. Se separa por coma, punto y coma y barra vertical. La barra inclinada se conserva. | Caracterizar la clasificación y conservar la expansión vigente. | Cerrado técnicamente para la implementación vigente.** Identidad y asociación institucional pendientes. | Cerrado técnicamente | Asociación e identidad de colecciones pendientes. | Baja. Definir cómo acreditar nombres, madres, identificadores y códigos adicionales. |

### Hallazgos de auditoría previa a publicación

| ID | Componente | Descripción e impacto | Evidencia inicial y posterior | Intervención | Estado histórico y antecedente documental | Estado principal 13.1–13.4 | Limitaciones | Prioridad registrada y acción pendiente |
|---|---|---|---|---|---|---|---|---|
| REG-H01 | Comparador y regresión | El comparador admite entradas idénticas o vacías y no exige todas las columnas de curación. **Impacto.** Una ejecución completa puede dar falsa confianza sobre el universo o las columnas comparadas. | La revisión estática identificó que puede aceptar la misma carpeta en ambos lados y que `value` y `note` no son obligatorios al leer `curation.csv`. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado por inspección. | Pendiente técnico | Confirmado por inspección. | Alta. Validar entradas distintas, universo esperado y las cinco columnas de curación antes de automatizar la aceptación. |
| REG-H02 | Comparador y regresión | El reporte detallado puede contener información sensible y quedar dentro del repositorio. **Impacto.** Riesgo de incorporación accidental a la publicación. | --detailed conserva valores y filas individuales. El destino se comprueba respecto a las entradas y puede quedar dentro del árbol de Git. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Riesgo confirmado por inspección. | Pendiente técnico | Riesgo confirmado por inspección. | Alta. Escribir los reportes fuera del repositorio y mantener acceso restringido a los detalles. |
| REG-H03 | Comparador y regresión | Las etiquetas del resumen pueden proceder de valores de entrada. **Impacto.** Una etiqueta libre o mal formada puede exponer contenido sensible en un agregado. | Los nombres de campos y valores de `kind` y `field` se usan como claves de agrupación. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Riesgo potencial identificado por inspección. | Pendiente técnico | Riesgo potencial identificado por inspección. | Media. Revisar el resumen antes de compartirlo y evaluar la validación o anonimización de etiquetas. |
| REG-H04 | Comparador y regresión | La escritura de los reportes puede completarse sólo en parte. **Impacto.** Puede quedar una salida parcial que bloquee un reintento en el mismo destino. | El resumen y el detalle se escriben en secuencia. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Limitación potencial identificada por inspección. | Pendiente técnico | Limitación potencial identificada por inspección. | Baja. Usar otro directorio al reintentar y evaluar la publicación conjunta de las salidas. |
| TEST-H01 | Pruebas | `pytest` no está declarado como dependencia. **Impacto.** Un entorno nuevo requiere preparación adicional. | Las pruebas lo importan y las dependencias del proyecto no lo incluyen. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado por inspección. | Pendiente técnico | Confirmado por inspección. | Media. Considerar una dependencia de desarrollo y documentar su instalación. |
| TEST-H02 | Pruebas | Las fixtures pueden dejar módulos importados en el mismo proceso. **Impacto.** Una suite futura que use configuración real podría recibir referencias sintéticas. | Se sustituyen dependencias temporalmente y los módulos importados pueden quedar en caché. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Limitación potencial identificada por inspección. | Pendiente técnico | Limitación potencial identificada por inspección. | Media. Ejecutar la selección en un proceso dedicado y revisar el aislamiento al ampliar la suite. |
| TEST-H03 | Pruebas | Una prueba de permisos depende de POSIX. **Impacto.** La portabilidad de esa prueba queda por verificar en otros sistemas. | La aserción comprueba bits de permisos del archivo detallado. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Supuesto confirmado por inspección. | Pendiente técnico | Supuesto confirmado por inspección. | Media. Documentar el entorno verificado y revisar la aserción antes de ampliar plataformas. |
| DATE-H01 | Fechas compartidas | La validación de fechas tiene alcance calendárico. **Impacto.** El resultado válido no certifica una fecha y hora ISO 8601 completa. | datetime.date comprueba el calendario y la expresión heredada admite determinados sufijos libres. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Alcance confirmado por inspección. | Pendiente de decisión institucional | Alcance confirmado por inspección. | Baja. Describir el alcance y acordar por separado cualquier validación adicional de hora o zona. |
| DOC-H01 | Documentación/publicación | DATE-01 redujo parte de la explicación heredada sobre fechas parciales. **Impacto.** Puede perderse el contexto de la decisión de conservar precisión parcial. | Observación del diff de `iso_date()`. (ff0f517). | Caracterización registrada en el corte documentado · sin corrección adicional acreditada. | Confirmado por inspección. | Pendiente técnico | Confirmado por inspección. | Baja. Conservar esa justificación en la documentación técnica acordada. |
| DOC-H02 | Documentación/publicación | Hay ejemplos heredados de procedencia no verificada. **Impacto.** Su publicación requiere confirmar que sean adecuados como ejemplos. | La auditoría localizó ejemplos nominales y contractuales presentes en el commit base. (ff0f517). Resultado documentado. AST y docstring iguales al origen en `src/mapeo/ceiba/ceiba_fields.py:684`. Se omiten los ejemplos del informe. | Mantener el hallazgo abierto. Comprobar que al menos el ejemplo nominal en `same_name()` procede del commit de origen. | Procedencia pendiente de verificar. | No evaluable con la evidencia disponible | La herencia del texto acredita ubicación y antigüedad, con autorización y procedencia personal pendientes. | Baja. Mitigado en los archivos vigentes mediante ejemplos sintéticos en 13.7 y 13.7.1. Su procedencia y autorización originales siguen sin acreditarse. Véase [revisión de DOC-H02](#revisión-previa-de-doc-h02). |

### Observaciones pendientes tras INS-H20

- **Cobertura del inventario.** Quedan 38 recursos sin asociación en el universo completo. Una recuperación no produjo JSON final por ausencia de una raíz EML reconocida.
- **Completitud de los valores recuperados.** Se registraron 12 proyectos sin NOMBRE DIEGO, 11 sin SUSCRITO y 7 DOI no vacíos que la regla vigente no reconoció.
- **Curación.** Quedan 7 razones propuestas de restricción por validar. Se registraron 4 nuevas ambigüedades de asociación contractual, 1 observación contractual reformulada y 1 código de tipo FN adicional en curación.
- **Cobertura de pruebas del proyecto.** DESC-H01 y NOTE-H02 siguen pendientes. Los tres módulos heredados excluidos requieren adaptación. Las comprobaciones de GeoNetwork y Biocultural cubren el adjunto compartido.
- **Controles de auditoría.** La [conciliación del acumulado](#conciliación-del-acumulado-de-controles) conserva los cortes históricos. Se registran por separado un control histórico no evaluable y dos controles informativos no evaluables.

Estas observaciones delimitan la cobertura técnica y las decisiones pendientes. La aprobación institucional definitiva y la carga efectiva en Dataverse quedan fuera de esta entrega.

### Revisión previa de DOC-H02

**Estado vigente al PASO 13.7.1 · mitigado en los archivos preparados para la entrega.** En el PASO 13.7 se sustituyó el ejemplo nominal heredado del docstring de `same_name()` por dos nombres ficticios que ilustran la misma comparación por subconjuntos de palabras. El AST coincidió al excluir exclusivamente ese docstring. [Ejemplo nominal sintético](../src/mapeo/ceiba/ceiba_fields.py#L684)

En el PASO 13.7.1 se sustituyeron los cinco ejemplos contractuales heredados por identificadores sintéticos. Los comentarios los identifican como sintéticos y conservan los prefijos relevantes, separadores, formatos y significado técnico. El AST completo coincidió antes y después de esta sustitución. El cotejo de tokens confirmó cambios únicamente en esos tres comentarios. La comparación con la versión aprobada antes de DOC-H02 atribuyó las diferencias adicionales al docstring y a los cinco ejemplos. Las reglas de procesamiento permanecen iguales y BIO-H01 es el único cambio funcional de esta entrega. [Comentarios con ejemplos sintéticos](../src/mapeo/ceiba/ceiba_fields.py#L581)

La autorización de los ejemplos contractuales y la habilitación del commit y el push quedaron en **REVISAR** en el PASO 13.7. La sustitución autorizada y la nueva revisión de confidencialidad se documentan en el PASO 13.7.1. J03 de 13.4 conserva el estado histórico **NO EVALUABLE**. La presencia de los ejemplos originales en el ancestro `4493852` está acreditada. Su procedencia y autorización siguen sin acreditarse y el historial de Git conserva esas versiones.

### Pendientes consolidados por alcance

| Tipo | Pendientes al PASO 12.7 |
|---|---|
| Técnico | Caracterizar jerarquías taxonómicas anidadas y formas narrativas no cubiertas por el universo real. Mantener abiertos DOC-H02, DESC-H01, NOTE-H02 y los demás hallazgos de la matriz según su evidencia. |
| Institucional | Concertar deduplicación bibliográfica y taxonómica, identidad y asociaciones de colecciones, precedencia de tipo y subtipo, GBIF dataset key, DOI ambiguo y fuente autorizada de la versión CEIBA. |
| De alcance | Definir la comprobación desde XML original del marcado y el contenido mixto, incluidos los antecedentes DESC-H01 y DESC-H02. Conservar la distinción con NOTE-H02. |
| De despliegue | Incorporar `biologicalMetadata` a la publicación única del cierre general del proyecto. La aprobación institucional, integración y carga efectiva quedan fuera de lo acreditado. |

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

El registro continúa desde el corte acreditado del PASO 11.8. Se conservan por separado las cifras de pruebas y las verificaciones informativas.

| Paso | Controles aprobados en el paso | Acumulado |
|---|---:|---:|
| PASO 11.8 | 13 | 1406 |
| PASO 12.2 | 15 | 1421 |
| PASO 12.3 | 20 | 1441 |
| PASOS 12.4 y 12.5 | 16 | 1457 |
| PASO 12.6 | 24 | 1481 |
| PASO 12.7 | 18 | **1499** |
| PASO 12.8 | 12 | **1511** |
| PASOS 13.1–13.4 | 22 | **1533** |
| PASO 13.5 | 24 | **1557** |

D03 del PASO 12.3 conserva el estado histórico `REVISAR` por los intervalos sin aviso. Los controles F01, F02 y G02 del PASO 12.6 acreditan su resolución técnica, con los extremos y las curaciones históricas conservados. El acumulado incluye los controles nuevos y mantiene D03 histórico fuera de las aprobaciones. Los 408 casos de pytest y los 36 casos sintéticos independientes se contabilizan por separado.

El acumulado **1533** es el corte histórico registrado al finalizar 13.4, con 22 de 25 controles nuevos aprobados. Las cifras documentadas se conservan junto con su grado de reconstrucción. Se acreditaron 612 aprobados antes del manifiesto INS-H20 y constan los subtotales de 1008 y 1098 en los cortes correspondientes. El control **I02 de 13.4 sigue NO EVALUABLE** porque falta desglose independiente de los tramos 612→1008, 1008→1098 y 1267→1310. Entre el corte 11.6 de 1381 y el corte 11.8 de 1406, el aporte de 11.8 acredita 13 controles. La **diferencia de 12** queda sin atribuir a un paso sin evidencia específica.

I03 de PER-H27, G01 del acumulado documental y D03 de 12.3 conservan su registro histórico y su resolución posterior por separado. El control L01 de PER-H26 se cuenta una sola vez en su plan original. El acumulado excluye el control histórico no evaluable, las dos verificaciones informativas no evaluables, los 17 criterios de aceptación INS-H20, los casos de pytest y las 36 caracterizaciones sintéticas de 12.3.

**J02 de 13.4 conserva su estado histórico REVISAR**. Los ajustes documentales se resuelven después en el PASO 13.5 y quedan acreditados por sus controles nuevos. **J03 de 13.4 sigue NO EVALUABLE** y **DOC-H02 sigue abierto**. Véase [la revisión de procedencia](#revisión-previa-de-doc-h02).

### Controles del PASO 12.7

| Control | Criterio de aceptación | Estado |
|---|---|---|
| A01 | Git inicial coincide en rama, HEAD y seguimiento local. Staging vacío. Las únicas diferencias iniciales son las autorizadas y los cuatro históricos no rastreados. | Aprobado |
| A02 | Huellas iniciales de código, parche, cinco manifiestos, crosswalk, TSV y tablas auxiliares concilian con las evidencias. | Aprobado |
| A03 | Markdown inicial registrado y leído íntegro. Evidencias de 12.2–12.6 suficientes para documentar cifras sin volver a ejecutar procesos. | Aprobado |
| B01 | Las 32 filas de matriz corresponden a 27 campos y cinco padres del TSV y a las filas 105–131 del crosswalk. | Aprobado |
| B02 | Conteos por campo, cardinalidades, padres y totales concilian con los pasos 12.2, 12.3 y 12.6. | Aprobado |
| B03 | Los cinco grupos documentan fuentes, transformaciones, ausencias y límites. La divergencia de palabras clave queda como diagnóstico. | Aprobado |
| C01 | Los cuatro estados BIO y pendientes se corresponden con las evidencias. Los estados de DESC-H01, DESC-H02 y NOTE-H02 permanecen diferenciados. | Aprobado |
| C02 | La explicación y el ejemplo sintético concilian con la corrección de 22 inserciones, números de intervalos y nuevo aviso. | Aprobado |
| D01 | El inventario de módulos, funciones y casos concilia con AST y la evidencia de pytest, sin reejecutarlo. | Aprobado |
| D02 | Se conservan cortes históricos, red–green, exclusiones y xfail, y se excluyen del balance los casos sintéticos en memoria. | Aprobado |
| E01 | Fecha, comando, universo, integridad de los cinco bloques e incidencias de la regresión corresponden a las evidencias. | Aprobado |
| E02 | Reportes y multiconjunto de curaciones concilian, incluidos 15 categorías, suma 1365 y recursos biológicos únicos. | Aprobado |
| F01 | La composición, tamaño y huella de BIO-H01 coinciden con el manifiesto verificado. | Aprobado |
| F02 | Se documentan EXT-H02, copia restringida y evidencia preservada, con rutas relativas y alcance reproducible. | Aprobado |
| G01 | Resumen y cierre distinguen el avance de los cinco bloques, la base histórica y la última configuración verificada del Draft PR, y el PASO 12.8 pendiente. | Aprobado |
| G02 | Matriz y preguntas preservan los estados históricos e incorporan pendientes sin duplicaciones. Acumulado suma solo los controles nuevos y D03 histórico sigue en revisión. | Aprobado |
| H01 | Solo el Markdown difiere durante esta intervención. Huellas protegidas, Git y espacios en blanco pasan. | Aprobado |
| H02 | Las nuevas líneas pasan revisión de confidencialidad y sus referencias internas resuelven. | Aprobado |

## Resolución de la auditoría documental

### Matriz de resolución de los 11 ajustes

Los identificadores conservan el orden de los 11 ajustes del informe 13.1–13.4. La verificación de 13.5 resuelve J02 en el plano documental. Los controles no evaluables y los hallazgos técnicos o institucionales mantienen su estado.

| Ajuste | Sección afectada | Inconsistencia u omisión | Evidencia | Modificación realizada | Resultado de verificación |
|---|---|---|---|---|---|
| 1 | Contexto y alcance / Índice | El cierre 12.8 está documentado, pero falta el balance consolidado 13.1–13.4 con denominadores y condiciones de despliegue. | 1.191 ingesta, 1.107 elegibles, 84 omitidos, 27 borradores · 916/191 sobre elegibles. | Se incorporó el resumen y se separaron los hitos de despliegue. [Resumen ejecutivo](#resumen-ejecutivo) · [Condiciones para la migración efectiva](#condiciones-para-la-migración-efectiva) | Verificado. Universo, estados de despliegue y navegación cotejados · B01, E02 y J01. |
| 2 | Caracterización de los datos / Regresión y reporte de curación | Los cortes y denominadores están dispersos y faltan recursos únicos por categoría. | 1.365 filas, 15 categorías, 916 recursos · `contact_email` 31/27, `reference_url` 7/4 · 84 omitidos fuera del denominador 916/191. | Se añadió el cuadro del universo y se amplió el corte BIO-H01 con recursos únicos y tipo de curación. [Curación posterior a BIO-H01](#curación-posterior-a-bio-h01) | Verificado. Quince categorías, denominadores y cortes históricos conciliados · C01–C02. |
| 3 | Resultados de citation / Matriz de hallazgos | LANG-H01 no aparece en la matriz documental. | `tests/test_citation_language.py:73` y `map_language()` omiten códigos ausentes o desconocidos. | Se añadió LANG-H01 a citation y a la matriz. Se mantuvieron LANG-H02 y LANG-H03. [Elementos simples](#elementos-simples) | Verificado. Omisión vigente y frecuencia real sin cuantificar · D01–D02. |
| 4 | Resultados de los cinco bloques | Falta una matriz homogénea que separe campos, padres, valores y filas. Los indicios positivos de población no acreditan una fuente para los campos ausentes. | 129 filas de contenido del crosswalk: 78 propuestas emitidas y 51 sin fuente, con 27 padres del TSV y 18 emitidos. | Se incorporaron la matriz general y el detalle por campo y padre. [Cobertura consolidada de los cinco bloques](#cobertura-consolidada-de-los-cinco-bloques) | Verificado. 129 campos, 27 padres, 78 emisiones y 51 ausencias cotejados · B02–B03. |
| 5 | Personas e instituciones · Contratistas | La tabla de 1327 filas pertenece al corte previo a INS-H20. Falta un recuento vigente con unidad idéntica. | JSON vigentes: 1337 filas `contractor` en 681 recursos. `project`: 1469 filas en 1062 recursos. `acknowledgement`: 14 valores. | Se añadió el recuento actual de project, contractor, access y acknowledgement sin sustituir el anterior. [Conteos vigentes de institutional](#conteos-vigentes-de-institutional) | Verificado. 1337 y 681, 1469 y 1062 y 14 cotejados por unidad · B03. |
| 6 | Conciliación del acumulado de controles | El detalle acreditado tiene intervalos sin desglose. La separación entre avances y controles reabiertos debe mantenerse. | 612 archivados antes del manifiesto INS-H20 · 1008 y 1098 como cortes documentados · 1267→1310 y 1381→1393 sin desglose independiente. | Se actualizaron los cortes y se explicitaron los tramos sin desglose y los estados históricos. [Conciliación del acumulado](#conciliación-del-acumulado-de-controles) | Verificado. Aportes de 22 y del PASO 13.5 separados. Diferencia de 12 sin atribuir · I01. |
| 7 | Matriz de hallazgos pendientes / Preguntas | El título agrupa estados abiertos y cerrados. PER-H02/H03 comparte una fila. Decisiones semánticas e hipótesis aparecen juntas. | 57 identificadores individuales, incluido LANG-H01 de la suite. 33 preguntas históricas. | Se actualizó el título de la matriz, se separaron PER-H02/PER-H03 y se agruparon las decisiones con su numeración original. [Matriz consolidada de hallazgos](#matriz-consolidada-de-hallazgos) · [Grupos de decisión](#grupos-de-decisión) | Verificado. 57 identificadores y 33 preguntas conciliados · D01–D02 y E01. |
| 8 | DOC-H02 / Preparación de la entrega | La procedencia y autorización de ejemplos heredados siguen abiertas. | Docstring de `same_name()` coincide con el ancestro · comparar candidatos por huella y revisar fragmentos sin publicar valores. | Se registró la presencia de los ejemplos en el ancestro y se acotó la propuesta de revisión de confidencialidad. [Revisión previa de DOC-H02](#revisión-previa-de-doc-h02) | Verificado. DOC-H02 abierto, J03 no evaluable, huellas intactas y ausencia de nuevos ejemplos · I02 y K01. |
| 9 | Herramienta de comparación / Pruebas y reproducibilidad | La receta de ejecución está dispersa y la evidencia de entorno no certifica reproducibilidad fuera de macOS. | Python 3.13.2, arm64, macOS 26.7.3 y 408 casos archivados · ocho TSV efectivos, cuatro tablas internas de trabajo, inventario externo y crosswalk con huellas. | Se reunió la receta por corte y el entorno, las dependencias, los insumos y la comparación con trazabilidad. [Reproducibilidad](#reproducibilidad-y-herramienta-de-comparación) | Verificado. Comandos, configuración nominal y dos capturas de entorno cotejados · F02–F03. |
| 10 | Contexto y alcance · Git y publicación | La referencia local de `develop` y la rama de partida aportan diferenciales distintos. | 8 commits / 21 archivos comprometidos frente a la rama de Marius · 25 commits del lado de trabajo y 38 archivos del diff de tres puntos frente a `origin/develop` local. | Se separaron hechos locales, rama de origen, referencia de develop y base documentada del PR. [Historial de Git](#historial-de-git-y-candidatos-a-publicación) | Verificado. 8 commits y 21 archivos frente al origen. 38 archivos en el diferencial local de tres puntos · F01. |
| 11 | Líneas base y reproducibilidad | El inventario de respaldos está repartido entre cortes y no distingue todos los métodos de cálculo de tamaño. | Cinco huellas de manifiesto verificadas · el histórico PER-H16/PER-H28 solo aporta hashes por entrada y su tamaño se midió por stat. | Se incorporaron el inventario único de respaldos, métodos de tamaño, huellas y condiciones de acceso. [Inventario de líneas base](#inventario-de-líneas-base-y-evidencias) | Verificado. Cinco registros, tamaños sin manifiesto y huellas cotejados · G01. |

### Controles nuevos del PASO 13.5

| Control | Criterio | Resultado |
|---|---|---|
| A01 | Rama, HEAD, seguimiento local, staging, conjunto de cambios y huellas iniciales de candidatos y parche concilian. | APROBADO |
| A02 | Están disponibles ambos insumos 13.1–13.4. Sus huellas, copias y contenido concilian, al igual que los cinco manifiestos y los insumos auxiliares. | APROBADO |
| B01 | El resumen y universo separan ingesta, JSON elegibles, omitidos, IPT, EML, inventario, curación y estados de despliegue. | APROBADO |
| B02 | La matriz general concilia valores, filas, campos y padres por bloque y en sus totales. | APROBADO |
| B03 | La matriz detallada conserva el recuento por campo y padre, distingue fuente y emisión, y cubre los 129 campos y 27 padres con trazabilidad. | APROBADO |
| C01 | El corte vigente concilia las 15 categorías, filas y recursos únicos por categoría, y los denominadores global y biológico. | APROBADO |
| C02 | Se preservan los cortes históricos y se separa curación de problemas de mapeo y de omisiones. | APROBADO |
| D01 | Los 57 identificadores, LANG-H01 y PER-H02/PER-H03 separados coinciden con la auditoría. | APROBADO |
| D02 | Estados, evidencias, intervenciones, límites y acciones permanecen trazables, con distribución exacta y hallazgos históricos abiertos. | APROBADO |
| D03 | Se acreditan siete correcciones, pruebas, regresiones y referencia de versiones, con geospatial heredado. | APROBADO |
| E01 | Los 25 grupos preservan comportamiento, evidencia, riesgo, alternativas, recomendación, prioridad y dependencias y cubren las 33 preguntas. | APROBADO |
| E02 | Las siete etapas de migración distinguen lo completado y lo pendiente, sin inferir acuerdos institucionales. | APROBADO |
| F01 | Se distinguen origen, base documentada del PR, dos diferenciales locales, ocho commits y tres candidatos pendientes. | APROBADO |
| F02 | Inventario y cortes de pruebas concilian con las evidencias sin nueva ejecución · se conservan exclusiones y dos xfail estrictos. | APROBADO |
| F03 | Reproducibilidad reúne comandos, entorno actual e histórico, configuración nominal e insumos y protege resultados detallados. | APROBADO |
| G01 | Inventario de cinco líneas base concilia tamaños, huellas, cortes, evidencias y su alcance fuera del repositorio. | APROBADO |
| H01 | Los 11 ajustes se aplican en sus secciones con evidencia y verificación individual, sin completar faltantes con supuestos. | APROBADO |
| H02 | El estado histórico de J02 queda en REVISAR y su resolución documental posterior se enlaza a controles nuevos aprobados. | APROBADO |
| I01 | I02 conserva NO EVALUABLE, tramos sin desglose y diferencia de 12. 1533 consta como acumulado histórico registrado. | APROBADO |
| I02 | J03 conserva NO EVALUABLE y DOC-H02 sigue abierto con recomendación de autorización específica, sin divulgar ejemplos. | APROBADO |
| J01 | Índice, enlaces internos, navegación histórica y redacción de cortes e indicadores concilian. | APROBADO |
| J02 | Se conserva el título acotado y se incluye una estructura definitiva de Word, sin generar el documento. | APROBADO |
| K01 | El estado final y huellas de código, pruebas, parche, cinco manifiestos, insumos y cuatro históricos coinciden con el inicio. | APROBADO |
| K02 | El Markdown es el único cambio del paso, su diff está limpio, y las copias de entrega y huellas concilian. | APROBADO |

Se aprobaron **24 controles nuevos**. El acumulado registrado pasa de **1533 a 1557**. Los 25 controles de 13.1–13.4 y los resultados de pruebas mantienen su registro previo.

## Decisiones institucionales y preguntas históricas

Las 33 preguntas se organizan en **25 grupos**. El número remite a la pregunta original y «—» indica un pendiente adicional sustentado. Las prioridades y recomendaciones corresponden a la auditoría. La decisión indicada requiere concertación y su inclusión no equivale a aprobación institucional.

### Grupos de decisión

| Tema | Preguntas históricas | ID o alcance | Decisión requerida | Comportamiento vigente | Evidencia | Riesgo | Alternativas | Recomendación técnica | Prioridad y razón | Dependencias |
|---|---|---|---|---|---|---|---|---|---|---|
| Identidad y roles | 4, 5 | PER-H01, PER-H02, PER-H03 | Qué tablas aprueba el equipo y quién las mantiene. | Roles desde tabla y normalización de nombre · el flujo carece de autoridades. | 11804 apariciones comparadas · denominación de tabla distinta en el crosswalk. | Emparejamiento de entidades y trazabilidad de roles inconsistentes. | Conservar regla actual con revisión · añadir autoridades controladas y alinear tabla. | Alinear el nombre de la tabla y definir responsables de una eventual autoridad. | Media · afecta interpretación y trazabilidad de múltiples campos. | Responsables de metadatos y tablas auxiliares. |
| Contactos y afiliaciones | 6, 7 | PER-H11, PER-H38, PER-H39 | Alcance de reparación y criterio de fuente o curación. | Corrección de dominio y selección por primera aparición en cada destino. | 14 contactos con aplicación extendida · 36 conflictos de afiliación y 2 de correo, con una superposición. | Conservar correo o afiliación distintos del dato autorizado. | Revisar por caso · priorizar fuente · enviar conflicto a curación. | Revisar los conflictos antes de cambiar precedencia en bloque. | Alta · el contacto puede quedar asociado a la identidad equivocada. | Fuentes de autoridad y privacidad de contactos. |
| Identidad contractual | 8, 10 | PER-H22, PER-H24, PER-H29 | Requisitos para admitir organizaciones e identificar equivalencias. | Comparación por subconjuntos · el flujo de personas omite una organización identificada. | 38 coincidencias múltiples en la medición posterior y una exclusión institucional respaldada. | Combinar identidades o perder contratistas colectivos. | Exigir autoridad · gestionar coincidencias múltiples manualmente · aceptar organizaciones bajo evidencia definida. | Suspender decisiones automáticas en coincidencias múltiples hasta acordar evidencia. | Alta · atribución contractual. | Autoridad, EML y propietario del inventario. |
| Asociaciones y separación | 9, 12 | PER-H16, PER-H29 | Categoría de curación aprobada y criterios de separación y asociación. | Se conservan nombres y códigos separados si son ambiguos · una curación por recurso. El nombre de inventario se conserva como cadena. | 191 avisos vigentes · 61 candidatos con separadores según la medición ampliada. | La fragmentación sin respaldo alteraría identidad y asociación. | Retener cadena y curar · separar con segmentos respaldados y asociación explícita. | Mantener las asociaciones conservadoras hasta contar con evidencia por segmento. | Alta · asociación potencialmente incorrecta. | Gobernanza de contratos e inventario. |
| Reconocimiento de códigos | 22 | PER-H26, PER-H28 | Evidencia mínima para admitir variantes. | Reglas de código acotadas · las variantes de capitalización pueden quedar fuera. | Tres señales de capitalización y cero pérdidas o incorporaciones adicionales en la evaluación. | Nuevas variantes podrían quedar sin reconocer. | Mantener reglas · flexibilizar después de reproducir un caso perdido. | Conservar regla hasta que una muestra justifique revisión. | Baja · sin impacto verificado en la cohorte. | Muestras verificadas y regresión contractual. |
| Inventario institucional | 21, 23 | INS-H20, PER-H25 | Aceptación del alcance, fuente complementaria y plan de revisión. | Coincidencia literal prioritaria y recuperación normalizada inequívoca. | 65 recuperaciones · 16 ausencias elegibles y 22 omitidas. | Faltan valores derivados en los recursos elegibles sin correspondencia. | Recuperar desde otra fuente autorizada · mantener ausencias justificadas · curar por recurso. | Tratar por separado las 16 ausencias elegibles y los 22 omitidos. | Media · completitud de la cohorte. | Equipo de inventario y validación de origen. |
| Proyectos y financiación | 11 | PER-H27, I03 | Qué residuales son financiación y dónde conservarlos. | El proyecto Macro y el del EML son entradas distintas · cada nuevo valor Macro tiene un párrafo base. | 17 segmentos residuales, 13 distintos de FN/OS y cero párrafos adicionales en la reconciliación. | Asignar convenios a un proyecto incorrecto o perder contexto semántico. | Mantener `inventory_data` · curar · trasladar solo con enlace documental. | Exigir un vínculo comprobable entre residual, proyecto y fuente. | Media · contexto de la financiación. | Códigos Macro, financiación EML y criterio de curación. |
| Versiones y fechas de referencia | 29 | DATE-01, DATE-H01, versión CEIBA | Fuente autorizada de versión y precisión admitida en la operación de carga. | `inventory.csv` aporta la versión de la URL. `iso_date()` conserva precisión calendárica. | 593 diferencias de grafía frente a `packageId` · 1107 coincidencias del inventario con el plan. | Usar una versión textual distinta o interpretar una fecha parcial como completa. | Ratificar `inventory.csv` · reconciliar discrepancias · validar fecha parcial en el destino. | Conservar versión y precisión de origen mientras se acuerda la validación del destino. | Media · identidad de versión y fechas. | Equipo de metadatos y esquema efectivo del destino. |
| Temporalidad biológica | — | BIO-H01, DATE-H01 | Política de revisión de fechas invertidas y parciales antes de cargar. | Extremos anuales y mensuales se comparan por límites, con curación de inversiones. | 13 inversiones en 13 recursos y 94 extremos anuales conservados. | Fechas parciales o invertidas podrían requerir revisión operativa en destino. | Conservar y curar · acordar validación específica en piloto. | Validar aceptación real manteniendo la precisión sin completar fechas. | Media · afecta interpretación y requisitos del destino. | Piloto y versiones efectivas de Dataverse. |
| GBIF dataset key | 26 | EXT-H03 | Campo, tipo de referencia y validez de identidad. | UUID disponible en `inventory_data`, con destino sin decidir. | 682 UUID · 681 coexisten con un DOI reconocido. | Vincular dos identificadores como equivalentes sin evidencia de identidad. | Mantener en inventario · mapear a un campo aprobado tras cotejo de identidad. | Mantener el valor disponible en el inventario hasta ratificar significado y destino. | Media · relaciona recursos que pueden ser distintos. | Crosswalk y fuente de identificación. |
| Identificadores externos | 27, 28 | EXT-H02, DOI ambiguo | Clases admitidas y evidencia para validar un DOI ambiguo. | El flujo reconoce DOI, URL e ISBN/ISSN por reglas acotadas · el texto ambiguo queda aparte. | 1099 identificadores en otra clase y un caso de token DOI en un contexto distinto. | Aceptar un enlace o DOI incorrecto u omitir uno válido. | Mantener clasificación · curar nuevos patrones · ampliar con casos verificados. | Revisar el contexto del token antes de ampliar reconocimiento. | Media · calidad de referencias. | Inventario, bibliografía y revisión de fuente. |
| Jerarquía taxonómica | 31 | BIO-H02 | Qué hacer con hijos, padres vacíos y orden por niveles. | El flujo procesa el primer nivel de cada clasificación. | Cero jerarquías anidadas en el universo auditado. Hijos utilizables omitidos en sintéticos. | Pérdida de niveles taxonómicos en futuras representaciones. | Conservar DOM jerárquico fuera del destino · documentar una regla recursiva y sus límites. | Acordar primero la semántica de representación jerárquica y evaluar casos fuera del universo. | Alta · potencial pérdida de información. | Crosswalk y modelo objetivo de taxonomía. |
| Identidad de colecciones | 32 | BIO-H04 | Fuente oficial y criterios de asignación de nombre, madre e identificadores. | Una lista se expande. Nombre y madre quedan en la primera fila. | 154 expansiones curadas y cuatro identificadores en texto libre enviados a revisión. | Atribuir identificadores o códigos adicionales a la colección equivocada. | Mantener revisión · introducir una autoridad y asignar cada código bajo evidencia. | Mantener orden y asociación conservadora hasta contar con autoridad. | Alta · asociación de entidades. | Responsables de colecciones y fuentes de autoridad. |
| Precedencia de vocabularios | 33 | coreType, subtype | Qué fuente es autorizada y cuándo admitir otra. | `resource.xml` como fuente exclusiva · palabras clave sirven de contraste. | 153 diferencias diagnósticas de tipo, 61 de subtipo y dos subtipos disponibles solo en palabras clave. | Fusionar fuentes que describen conceptos distintos. | Mantener precedencia · usar palabras clave para curación · definir alternativa con precedencia. | Conservar la regla vigente y revisar primero los casos diagnósticos. | Media · semántica del campo controlado. | Crosswalk, vocabulario GBIF y propietario de `resource.xml`. |
| Formatos narrativos | 1, 18 | DESC-H04, GEO-H06, NOTE-H01 | Formato y representación esperada de cada destino. | HTML en descripción, notas y descripción geográfica. | 1107 descripciones geográficas conservadas y 1107 descripciones de citation evaluadas. | Una conversión distinta cambia presentación o estructura disponible. | Conservar HTML · texto plano documentado · regla por campo. | Elegir formato por campo y mantener pruebas de escape y orden. | Media · presentación y preservación textual. | Aprobación de crosswalk y esquema destino. |
| Marcado, XML y texto mixto | 2, 30 | DESC-H01, DESC-H02, DESC-H03, EXT-H04, BIO-H03 | Qué elementos y contenido mixto se conservan por bloque. | El cotejo de textos biológicos y citas externas cubre JSON a JSON. La ingesta pierde énfasis en el caso documentado. | 8 etiquetas en 3 recursos de citation · 9288 citas y 7750 valores biológicos conciliados en su alcance. | Pérdida de marcado o contenido exclusivamente estructurado. | Conservar representación original · reconstruir marcado selectivo · validar alcance XML. | Definir primero el marcado necesario y cotejarlo desde XML. | Alta · pérdida observada o potencial. | Archivos originales autorizados y fixtures para XML mixto. |
| Notas con texto directo | 3 | NOTE-H02 | Admisión de texto sin `para`. | Se admite texto directo en `additionalInfo` sin `para`. | Caso sintético reproducido · sin ocurrencias reales en la evaluación. | Comportamiento distinto de una lectura estricta de la fuente propuesta. | Aceptar la forma directa · restringirla · enviar a curación si aparece. | Conservar evidencia sintética hasta que se decida su tratamiento. | Baja · alcance sintético sin efecto observado. | Crosswalk y prueba estricta histórica. |
| Deduplicación de ocurrencias | 25 | EXT-H01, BIO-H02 | Si se deduplica, claves y evidencia exigida en cada bloque. | Las listas preservan orden y multiplicidad. | 28 repeticiones bibliográficas y 225 taxonómicas, con orígenes diferenciados. | Deduplicar por texto puede perder identificadores o nodos de origen. | Preservar multiplicidad · deduplicar bajo identidad comprobada con traza. | Mantener ocurrencias mientras se definen criterios separados por bloque. | Media · cambia cardinalidad y trazabilidad. | Identidad, precisión de los comparadores y crosswalk. |
| Confidencialidad y procedencia | 24 | DOC-H02, REG-H02, REG-H03 | Autorización de ejemplos y revisión de los tres candidatos. | Persisten ejemplos heredados y los detalles locales del comparador contienen valores individuales. | Procedencia del contenido de ejemplos sin verificar. Su presencia en el ancestro se pudo comprobar. | Exposición de datos personales o contractuales durante la publicación. | Obtener validación institucional · sustituir ejemplos por sintéticos tras autorización · limitar artefactos. | Revisar y autorizar ejemplos antes de publicar. Mantener datos y diferencias detalladas fuera de Git. | Alta · posibilidad de exposición sensible. | Responsable de datos, auditoría de diff y reglas de exclusión. |
| Validación efectiva en Dataverse | — | Despliegue, terms_of_use, GEO-H05, DATE-H01 | Instancia, esquema, credenciales autorizadas, piloto y criterios de aceptación. | La evidencia técnica acredita generación local y plan de carga. | 1107 JSON, 27 borradores, 2 revisiones de términos y 0 problemas estructurales del mapeador. | Un esquema distinto, términos faltantes o reglas de destino pueden impedir la carga. | Validación en destino · piloto autorizado · carga escalonada y verificación posterior. | Usar una muestra que incluya casos límite, mantener un plan de reversión y aprobarlo antes de carga. | Alta · posible impedimento de carga y publicación. | Decisiones institucionales, protección de datos y permisos de destino. |
| Coherencia geográfica | 16, 17, 19, 20 | GEO-H01 a GEO-H09 | Política de geometrías degeneradas, vacíos, atributos sin fuente e indicadores de coherencia. | Se curan rectángulos inválidos y se preservan los aceptados. Los compuestos sin fuente se omiten. | 37 rechazos y 20 recursos con indicadores positivos o de intercambio · 0 vacíos observados. | Interpretar hipótesis como errores confirmados o dejar puntos, líneas y campos necesarios fuera del destino. | Mantener reglas · revisión individual · aprobar tratamiento de casos geométricos y vacíos. | Revisar indicios sin corregir automáticamente valores originales. | Media · calidad y alcance en un conjunto delimitado. | Fuente geográfica, crosswalk y piloto Dataverse. |
| Unidades curatoriales | 13 | CUR-H01 | Qué conservar, en qué formato y quién mantiene la salida. | Se identificó contenido de origen que requiere un archivo externo de curación. | 42 recursos identificados y verificación integral de exclusión pendiente. | Omitir material que necesita trazabilidad fuera de los metadatos. | Preparar salida separada con cobertura auditada · concertar destino autorizado. | Definir el soporte y verificar cobertura antes de configurar la carga. | Alta · conservación de información de origen. | Equipo de curación y revisión de acceso a datos. |
| Automatización de aceptación | 14, 15 | REG-H01 a REG-H04, TEST-H01 a TEST-H03 | Qué comprobaciones pasan a ser requisitos de desarrollo o entrega. | El comparador devuelve completitud y la suite usa preparación adicional y fixtures específicas. | 408 casos archivados · revisiones estáticas de completitud, aislamiento y portabilidad. | Aprobar insumos incompletos o interpretar mal un resultado de ejecución. | Mantener proceso dedicado con verificaciones explícitas · robustecer contrato y pruebas tras aprobación. | Conservar controles de universo, cinco columnas y confidencialidad antes de automatizar. | Media · confiabilidad y repetibilidad. | Política de CI y plataformas aprobadas. |
| Motivos de restricción | — | restriction_reason, restricted_until | Autorización de razones, plazos y sustitutos permitidos. | Se registra una curación ante ausencia o validación pendiente de la fuente. | 91 razones de restricción y 32 fechas de liberación en curación · siete razones propuestas en la cohorte INS-H20 siguen abiertas. | Aplicar políticas de acceso con datos incompletos o ambiguos. | Revisar inventario y tablas · aprobar excepción explícita · mantener borrador cuando corresponda. | Resolver los casos cuyo acceso dependa de un dato en revisión antes del piloto. | Alta · puede afectar permisos o carga. | Responsable de acceso y condiciones de uso. |
| Idioma y versión EML | — | LANG-H01, LANG-H02, LANG-H03, ALT-H01 | Reglas institucionales de idioma y versión esperada para nombres cortos. | Equivalencias de idioma por TSV y `shortName` sin condición explícita de versión. | Un `oci`, una fila de vocabulario sin identificador y cero casos de `shortName` fuera de EML 2.2.0 · omisión de códigos desconocidos caracterizada. | Omisión de códigos nuevos o empleo de un campo fuera de la versión esperada. | Conservar regla · registrar desconocidos · exigir la versión cuando se acuerde. | Comprobar `oci` y el vocabulario antes de cambiar código. | Baja · sin pérdida confirmada por códigos desconocidos en este paso. | Responsable de vocabulario y validación EML. |

### Preguntas históricas numeradas

1. ¿Se mantiene HTML para `dsDescriptionValue` o se adopta texto plano? La evaluación cubrió 1107 descripciones y no detectó pérdida de contenido textual.
2. ¿Debemos conservar las etiquetas de énfasis y enlaces originales del EML? Se perdieron ocho etiquetas de énfasis en cuatro párrafos de tres recursos. No se identificaron casos reales de enlaces en las descripciones evaluadas. Para las rutas narrativas de `biologicalMetadata` queda por definir, además, el tratamiento del contenido mixto y su verificación desde XML.
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
25. ¿Se conserva la multiplicidad de las citas bibliográficas o se adopta una política de deduplicación? De las 28 repeticiones adicionales, 25 ya estaban presentes en la ingesta y tres aparecen después de normalizar. Dos grupos tienen identificadores distintos en origen. Para taxonomía, ¿qué evidencia permitiría deduplicar las repeticiones originales o las coincidencias por limpieza de espacios? Se conservaron las 225 ocurrencias adicionales.
26. ¿Qué campo y tipo de referencia, si corresponde, deben recibir GBIF dataset key? Hay 682 valores con forma UUID y 681 coexisten con un DOI reconocido.
27. ¿Qué clases de identificadores bibliográficos adicionales deben migrarse o enviarse a curación? Se observaron 1099 valores de otra clase, entre ellos formas con apariencia de URL o DOI.
28. ¿Qué evidencia del inventario permitiría reconocer un DOI cuyo token tiene la forma esperada pero se presenta en un contexto distinto? Se observó un caso de ese tipo entre los once valores fuera de la lista estricta de marcadores.
29. ¿Se ratifica `inventory.csv` como fuente de la versión en las URL de origen CEIBA? La versión extraída de `@packageId` difirió textualmente en 593 casos y la versión de `inventory.csv` coincidió con el plan de carga en los 1107 recursos.
30. ¿Se requiere verificar las citas de `externalReferences` desde el XML original y qué contenido anidado o marcado debe preservarse? La comprobación actual cubre las 9288 citas desde el JSON de ingesta.
31. ¿Cómo debe representarse una jerarquía taxonómica anidada cuando el padre carece de datos utilizables y sus hijos contienen taxones válidos? La situación se reprodujo con datos sintéticos.
32. ¿Qué evidencia permitirá identificar una colección y asignar nombre y colección madre a los identificadores o códigos adicionales de una lista expandida? Las 154 listas con más de un segmento utilizable quedaron registradas para curación.
33. ¿Se ratifica `resource.xml` como fuente exclusiva de tipo y subtipo? Los términos GBIF interpretables señalaron diferencias diagnósticas en 153 recursos para tipo y 61 para subtipo.

Estas preguntas quedan abiertas para concertación. Las recomendaciones de la matriz orientan la revisión y no constituyen autorizaciones de cambio.

## Condiciones para la migración efectiva

| Etapa | Estado | Evidencia o condición |
|---|---|---|
| Validación técnica del mapeador | Completada dentro del alcance | Esquema y crosswalk, JSON, curaciones, pruebas y regresiones archivadas. |
| Resolución de pendientes relevantes | Pendiente | Resolver o aceptar explícitamente excepciones y riesgos de acceso, identidad y conservación. |
| Aprobación institucional | Pendiente | Aprobar reglas, excepciones, responsabilidad y alcance de confidencialidad. |
| Validación contra el Dataverse de destino | Pendiente | Confirmar versión, esquemas, vocabularios, condiciones de acceso y límites de fechas y geometrías. |
| Carga piloto | Pendiente | Acordar muestra, permisos, aceptación y reversión. Probar borradores y casos límite. |
| Migración efectiva | Pendiente | Autorizar y medir el plan de lotes y el tratamiento de fallos. |
| Verificación posterior a la carga | Pendiente | Conciliar conteos, metadatos, identificadores, permisos y estados en el destino. |

Las evidencias de este documento acreditan la validación técnica local y los cierres indicados. La publicación del código y el informe se programa como una sola entrega general. La aprobación institucional, la integración y la carga en Dataverse conservan su propio proceso.

## Estructura definitiva propuesta para el documento Word

1. Portada institucional, ficha de versión, alcance del corte, fuentes y responsables.
2. Resumen ejecutivo con universo, estado de cinco bloques y límites de despliegue.
3. Arquitectura, configuración nominal y metodología de comparación.
4. Resultados por bloque con matriz de cobertura y denominadores.
5. Código y correcciones, con commits y fragmentos sintéticos autorizados.
6. Regresiones y evolución de curaciones, con criterios de aprobación.
7. Pruebas automatizadas e historial de ejecución.
8. Matriz de hallazgos, limitaciones y decisiones institucionales con responsables.
9. Reproducibilidad, líneas base y condiciones de piloto, migración y verificación.
10. Anexos de huellas y controles con trazabilidad agregada y referencias al repositorio.

Los anexos de distribución general usarán resultados agregados, referencias a código y datos sintéticos autorizados. Las evidencias privadas permanecen en su repositorio de custodia. El documento Word se elaboró por separado y permanece fuera de los candidatos a publicación.

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
12. Registrar el corte de EXT-H02 en la referencia local `31e624b`.
13. Completar la caracterización y la validación funcional de `biologicalMetadata`.
14. Corregir BIO-H01 y aprobar la suite biológica y la regresión transversal de los cinco bloques.
15. Consolidar y verificar la línea base BIO-H01 e integrar el corte en este documento mediante el PASO 12.7.
16. Completar el cierre técnico local de `biologicalMetadata` mediante la auditoría documental y de integridad del PASO 12.8.
17. Consolidar la auditoría general, las decisiones pendientes y los insumos de la entrega mediante los PASOS 13.1–13.4.
18. Integrar la consolidación definitiva del Markdown y resolver los 11 ajustes de J02 en el PASO 13.5.

### Actividades pendientes

1. Mantener las evidencias de procedencia y autorización de los ejemplos heredados de DOC-H02 bajo revisión restringida.
2. Completar la entrega general de `biologicalMetadata` y la documentación en el Draft PR #13 tras verificar los controles de publicación.
3. Concertar los pendientes técnicos e institucionales de la matriz, incluidos indicadores geográficos, coberturas puntuales o lineales, formatos narrativos y decisiones aún abiertas del alcance auditado de `institutional`.
4. Adaptar los módulos históricos excluidos y planificar la regresión de cualquier cambio posterior aprobado.
5. Acordar con el equipo la aceptación institucional y las actividades de integración y carga efectiva.
