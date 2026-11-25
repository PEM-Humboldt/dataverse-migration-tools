import re

def normalize_string(texto):
    # Unifica saltos de línea (\r\n, \r, \n) a \n
    texto = re.sub(r"\r\n?|\n", "\n", texto)
    # Colapsa múltiples saltos de línea en uno solo
    texto = re.sub(r"\n+", "\n", texto)
    # Quita espacios/tabs alrededor de cada salto de línea
    texto = re.sub(r"[ \t]*\n[ \t]*", "\n", texto)
    # Colapsa múltiples espacios o tabs horizontales en un espacio
    texto = re.sub(r"[ \t]+", " ", texto)
    return texto.strip()