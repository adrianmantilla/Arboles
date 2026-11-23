"""Genera las texturas de corteza de cada especie con Substance Designer (sbsrender).

Se ejecuta con mayapy (trae numpy y PySide6), en un ordenador con Substance 3D
Designer instalado. No abre ninguna aplicación de Substance::

    mayapy herramientas/texturas_corteza.py <carpeta de salida> [--4k] [especie ...]

Parte de ``wood_bark.sbsar`` (de los materiales de serie de Substance 3D
Painter) con unos ajustes por especie, y deja en la salida::

    <especie>/<512|1k|2k|4k>/corteza_color.jpg, corteza_normal.jpg, corteza_rugosidad.jpg

La normal se deja al estilo OpenGL (verde hacia arriba), que es lo que espera
Maya: si Substance la da al estilo DirectX, se le da la vuelta al verde.
"""

import glob
import os
import shutil
import subprocess
import sys
import tempfile

SBSRENDER = (
    "/Applications/Adobe Substance 3D Designer/Adobe Substance 3D Designer.app/Contents/MacOS/sbsrender",
    r"C:\Program Files\Adobe\Adobe Substance 3D Designer\sbsrender.exe",
)
SBSAR = (
    "/Applications/Adobe Substance 3D Painter/Adobe Substance 3D Painter.app/Contents/Resources/"
    "starter_assets/materials/Wood/wood_bark.sbsar",
    r"C:\Program Files\Adobe\Adobe Substance 3D Painter\resources\starter_assets\materials\Wood\wood_bark.sbsar",
)

# especie: (preset o None, semilla, color, rugosidad de la corteza, densidad, partes que faltan)
CORTEZAS = {
    "roble": ("Long Wood Bark", 7, (0.26, 0.22, 0.18), 0.9, 0.8, 0.3),
    "haya": ("Small Wood Bark", 3, (0.56, 0.56, 0.53), 0.1, 0.15, 0.0),
    "pino_pinonero": (None, 11, (0.46, 0.29, 0.19), 0.6, 0.5, 0.2),
    "abeto": ("Small Wood Bark", 5, (0.37, 0.33, 0.29), 0.4, 0.4, 0.1),
    "abedul": ("Small Wood Bark", 9, (0.86, 0.84, 0.79), 0.2, 0.25, 0.15),
    "sauce_lloron": ("Long Wood Bark", 13, (0.36, 0.32, 0.27), 0.8, 0.7, 0.2),
    "cipres": ("Long Wood Bark", 17, (0.43, 0.31, 0.23), 0.6, 0.6, 0.1),
    "olivo": ("Long Wood Bark", 19, (0.41, 0.39, 0.35), 0.85, 0.75, 0.4),
    "arbusto": ("Small Wood Bark", 23, (0.34, 0.29, 0.24), 0.4, 0.4, 0.1),
}
# Salidas del .sbsar → canal del plugin
SALIDAS = {"basecolor": "color", "normal": "normal", "roughness": "rugosidad", "height": "altura"}
TAMANOS = {"512": 512, "1k": 1024, "2k": 2048, "4k": 4096}


def _primero(rutas):
    for r in rutas:
        if os.path.exists(r):
            return r
    raise SystemExit("No encuentro: " + rutas[0])


def renderizar(especie, carpeta, tamano_log2=11):
    preset, semilla, color, rugosidad, densidad, faltan = CORTEZAS[especie]
    orden = [_primero(SBSRENDER), "render", _primero(SBSAR),
             "--output-path", carpeta, "--output-name", "{outputNodeName}", "--output-format", "png",
             "--set-value", "$outputsize@{0},{0}".format(tamano_log2),
             "--set-value", "$randomseed@{}".format(semilla),
             "--set-value", "bark_color@{:.3f},{:.3f},{:.3f}".format(*color),
             "--set-value", "bark_roughness@{}".format(rugosidad),
             "--set-value", "bark_density@{}".format(densidad),
             "--set-value", "missing_part_density@{}".format(faltan)]
    for salida in SALIDAS:
        orden += ["--input-graph-output", salida]
    if preset:
        orden += ["--use-preset", preset]
    subprocess.check_call(orden)
    return {SALIDAS[k]: os.path.join(carpeta, k + ".png") for k in SALIDAS}


def _qt():
    from PySide6 import QtGui
    if QtGui.QGuiApplication.instance() is None:
        QtGui.QGuiApplication(["texturas", "-platform", "offscreen"])
    return QtGui


def _a_numpy(imagen):
    import numpy as np
    QtGui = _qt()
    imagen = imagen.convertToFormat(QtGui.QImage.Format_RGB888)
    ancho, alto = imagen.width(), imagen.height()
    datos = np.frombuffer(imagen.constBits(), np.uint8, imagen.bytesPerLine() * alto)
    return datos.reshape(alto, imagen.bytesPerLine())[:, :ancho * 3].reshape(alto, ancho, 3).copy()


def _de_numpy(matriz):
    QtGui = _qt()
    alto, ancho = matriz.shape[:2]
    matriz = matriz.astype("uint8").copy(order="C")
    return QtGui.QImage(matriz.data, ancho, alto, ancho * 3, QtGui.QImage.Format_RGB888).copy()


def normal_es_directx(normal, altura):
    """True si la normal está al estilo DirectX (verde hacia abajo).

    Normal = (-dh/dx, -dh/dy, 1): en OpenGL, donde la superficie sube hacia
    arriba de la imagen el verde baja de 0,5; en DirectX, sube.
    """
    import numpy as np
    n = _a_numpy(normal)[:, :, 1].astype(float) - 127.5
    h = _a_numpy(altura)[:, :, 0].astype(float)
    pendiente = np.roll(h, 1, axis=0) - np.roll(h, -1, axis=0)  # sube hacia la fila de arriba
    return float((n * pendiente).sum()) > 0


def guardar(imagenes, destino, resoluciones):
    QtGui = _qt()
    from PySide6 import QtCore
    voltear = normal_es_directx(QtGui.QImage(imagenes["normal"]), QtGui.QImage(imagenes["altura"]))
    for canal in ("color", "normal", "rugosidad"):
        imagen = QtGui.QImage(imagenes[canal])
        if canal == "normal" and voltear:
            m = _a_numpy(imagen)
            m[:, :, 1] = 255 - m[:, :, 1]
            imagen = _de_numpy(m)
        if canal == "rugosidad":
            imagen = imagen.convertToFormat(QtGui.QImage.Format_Grayscale8)
        for res in resoluciones:
            lado = TAMANOS[res]
            copia = imagen if imagen.width() == lado else imagen.scaled(
                lado, lado, QtCore.Qt.IgnoreAspectRatio, QtCore.Qt.SmoothTransformation)
            carpeta = os.path.join(destino, res)
            os.makedirs(carpeta, exist_ok=True)
            copia.save(os.path.join(carpeta, "corteza_{}.jpg".format(canal)), "JPG", 92)
    return voltear


def main(argumentos):
    con_4k = "--4k" in argumentos
    argumentos = [a for a in argumentos if a != "--4k"]
    if not argumentos:
        raise SystemExit(__doc__)
    salida = os.path.abspath(argumentos[0])
    especies = argumentos[1:] or list(CORTEZAS)
    resoluciones = ["512", "1k", "2k"] + (["4k"] if con_4k else [])
    for especie in especies:
        temporal = tempfile.mkdtemp(prefix="arboles_corteza_")
        try:
            imagenes = renderizar(especie, temporal, 12 if con_4k else 11)
            voltear = guardar(imagenes, os.path.join(salida, especie), resoluciones)
            print("{}: {}{}".format(especie, ", ".join(resoluciones), " (verde de la normal volteado)" if voltear else ""))
        finally:
            shutil.rmtree(temporal, ignore_errors=True)
    print("Listo: " + salida)
    print("\n".join(sorted(glob.glob(os.path.join(salida, "*", "1k", "*.jpg")))))


if __name__ == "__main__":
    main(sys.argv[1:])
