"""Crea el ZIP para repartir a los alumnos: solo lo que hace falta para instalar y usar.

    python3 herramientas/empaquetar.py [carpeta de salida] [--2k]

Deja Arboles-<versión>.zip con una carpeta «Arboles» dentro (instalar.py, plug-ins,
scripts, texturas, iconos, README.md y GUIA_ALUMNOS.md). Sin pruebas, herramientas ni cachés.
Por defecto las texturas van solo a 512 y 1K (ZIP ligero para el aula); con --2k
incluye también las de 2K y 4K. Si falta una resolución, el plugin usa la más cercana.
"""

import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUIR = ("instalar.py", "README.md", "GUIA_ALUMNOS.md", "plug-ins", "scripts", "texturas", "iconos")


def version():
    with open(os.path.join(RAIZ, "scripts", "arboles", "__init__.py"), encoding="utf-8") as f:
        return re.search(r'__version__ = "([^"]+)"', f.read()).group(1)


LIGERAS = ("512", "1k")


def _sobra(carpeta, con_2k):
    """True para las carpetas de texturas que no van en el ZIP ligero."""
    partes = os.path.relpath(carpeta, RAIZ).split(os.sep)
    return (not con_2k and len(partes) == 3 and partes[0] == "texturas"
            and partes[2] not in LIGERAS)


def archivos(con_2k=False):
    for nombre in INCLUIR:
        ruta = os.path.join(RAIZ, nombre)
        if os.path.isfile(ruta):
            yield ruta
        for carpeta, subcarpetas, ficheros in os.walk(ruta):
            if _sobra(carpeta, con_2k):
                subcarpetas[:] = []
                continue
            subcarpetas[:] = sorted(d for d in subcarpetas if d != "__pycache__")
            for f in sorted(ficheros):
                if not f.endswith((".pyc", ".DS_Store", ".tx")):
                    yield os.path.join(carpeta, f)


def main(*argumentos):
    con_2k = "--2k" in argumentos
    resto = [a for a in argumentos if a != "--2k"]
    salida = resto[0] if resto else None
    salida = os.path.abspath(salida or os.path.join(RAIZ, "dist"))
    os.makedirs(salida, exist_ok=True)
    destino = os.path.join(salida, "Arboles-{}.zip".format(version()))
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta in archivos(con_2k):
            z.write(ruta, os.path.join("Arboles", os.path.relpath(ruta, RAIZ)))
    print(destino)
    return destino


if __name__ == "__main__":
    main(*sys.argv[1:])
