"""Crea el ZIP para repartir a los alumnos: solo lo que hace falta para instalar y usar.

    python3 herramientas/empaquetar.py [carpeta de salida]

Deja Arboles-<versión>.zip con una carpeta «Arboles» dentro (instalar.py, plug-ins,
scripts, texturas, README.md y GUIA_ALUMNOS.md). Sin pruebas, herramientas ni cachés.
"""

import os
import re
import sys
import zipfile

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INCLUIR = ("instalar.py", "README.md", "GUIA_ALUMNOS.md", "plug-ins", "scripts", "texturas")


def version():
    with open(os.path.join(RAIZ, "scripts", "arboles", "__init__.py"), encoding="utf-8") as f:
        return re.search(r'__version__ = "([^"]+)"', f.read()).group(1)


def archivos():
    for nombre in INCLUIR:
        ruta = os.path.join(RAIZ, nombre)
        if os.path.isfile(ruta):
            yield ruta
        for carpeta, subcarpetas, ficheros in os.walk(ruta):
            subcarpetas[:] = sorted(d for d in subcarpetas if d != "__pycache__")
            for f in sorted(ficheros):
                if not f.endswith((".pyc", ".DS_Store")):
                    yield os.path.join(carpeta, f)


def main(salida=None):
    salida = os.path.abspath(salida or os.path.join(RAIZ, "dist"))
    os.makedirs(salida, exist_ok=True)
    destino = os.path.join(salida, "Arboles-{}.zip".format(version()))
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as z:
        for ruta in archivos():
            z.write(ruta, os.path.join("Arboles", os.path.relpath(ruta, RAIZ)))
    print(destino)
    return destino


if __name__ == "__main__":
    main(*sys.argv[1:])
