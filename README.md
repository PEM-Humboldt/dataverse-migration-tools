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