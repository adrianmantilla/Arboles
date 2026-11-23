"""Follaje: grupos de hojas prefabricados y dónde se cuelgan de cada rama.

Los grupos de hojas son piezas fijas que trae el plugin, modeladas aquí en
código para no depender de archivos externos. En Maya las hojas de cada rama
son una sola malla (todas sus copias del grupo juntas): así se borran y
rehacen sin problemas al editar, y plantar el árbol entero como instancia
(fase 3) es lo que ahorra memoria en el jardín.
El eje Y del grupo apunta hacia fuera de la rama; el origen es donde se
engancha. Tamaño de referencia: unos 55 cm.
"""

import math
import random

from arboles import vectores as v
from arboles.modulos import Malla

# tipo: (hojas, largo de hoja, ancho, largo del tallito, apertura en grados, curvatura de la hoja,
#        redondez del contorno (más bajo = más redonda), disposición)
# «espiral»: hojas alrededor del tallito; «plano»: a los dos lados, como una pluma o una ramita de ciprés.
TIPOS = {
    "hoja_ancha": (12, 15.0, 9.5, 42.0, 60.0, 0.35, 0.7, "espiral"),     # roble, haya
    "hoja_fina": (14, 17.0, 3.2, 44.0, 45.0, 0.5, 0.7, "espiral"),       # sauce, olivo
    "hoja_redonda": (16, 8.5, 8.0, 40.0, 65.0, 0.25, 0.4, "espiral"),    # abedul, álamo
    "hoja_grande": (6, 30.0, 17.0, 30.0, 55.0, 0.4, 0.6, "espiral"),     # castaño, plátano de sombra
    "plumosa": (18, 13.0, 3.5, 48.0, 75.0, 0.2, 0.8, "plano"),           # acacia, fresno, mimosa
    "escama": (24, 9.0, 2.4, 46.0, 38.0, 0.05, 0.9, "plano"),            # ciprés, tuya
    "aguja": (30, 11.0, 0.7, 20.0, 70.0, 0.1, 0.7, "espiral"),           # pino, abeto
}
# calidad: filas a lo largo de cada hoja
CALIDADES = {"alta": 4, "baja": 2}
_DORADO = math.radians(137.5)


def calidad_de_nivel(nivel):
    return "alta" if nivel in ("denso", "alto") else "baja"


def _hoja(m, origen, eje, lado, largo, ancho, curva, filas, redondez=0.7):
    """Añade a ``m`` una hoja doblada por el nervio, de ``origen`` hacia ``eje``."""
    normal = v.unitario(v.cruz(eje, lado)) or v.perpendicular(eje)
    base = len(m.vertices)
    base_uv = len(m.us)
    for k in range(filas + 1):
        t = k / float(filas)
        perfil = math.sin(math.pi * min(0.98, 0.08 + t * 0.92)) ** redondez
        centro = v.suma(origen, v.suma(v.escala(eje, largo * t), v.escala(normal, -curva * largo * t * t)))
        for j, x in enumerate((-1.0, 0.0, 1.0)):
            pliegue = 0.12 * ancho * (1.0 - abs(x)) * perfil  # el nervio un poco levantado
            p = v.suma(centro, v.suma(v.escala(lado, x * ancho * 0.5 * perfil), v.escala(normal, pliegue)))
            m.vertices.append(p)
            m.us.append((x + 1.0) * 0.5)
            m.vs.append(t)
    for k in range(filas):
        for j in range(2):
            a = base + k * 3 + j
            m.conteos.append(4)
            m.conexiones += [a, a + 1, a + 4, a + 3]
            u = base_uv + k * 3 + j
            m.uv_ids += [u, u + 1, u + 4, u + 3]


def prototipo(tipo, calidad="alta"):
    """Malla del grupo de hojas ``tipo`` en espacio local."""
    hojas, largo, ancho, tallo, apertura, curva, redondez, disposicion = TIPOS[tipo]
    filas = CALIDADES[calidad]
    m = Malla("{}_{}".format(tipo, calidad))
    azar = random.Random(len(tipo) * 7919)
    apertura = math.radians(apertura)
    for i in range(hojas):
        t = 0.25 + 0.75 * i / max(1, hojas - 1)
        if i == hojas - 1:
            t, inclinacion = 1.0, 0.15
        else:
            inclinacion = apertura * (1.0 - 0.3 * t)
        if disposicion == "plano":
            radial = (1.0 if i % 2 else -1.0, 0.0, azar.uniform(-0.12, 0.12))
            radial = v.unitario(radial)
            escala = 1.0 - 0.45 * t * t + azar.uniform(-0.05, 0.05)  # más cortas hacia la punta
        else:
            azimut = i * _DORADO
            radial = (math.cos(azimut), 0.0, math.sin(azimut))
            escala = 0.75 + 0.25 * t + azar.uniform(-0.08, 0.08)
        eje = v.unitario(v.suma(v.escala(v.ARRIBA, math.cos(inclinacion)), v.escala(radial, math.sin(inclinacion))))
        lado = v.unitario(v.cruz(v.ARRIBA, radial)) or (1.0, 0.0, 0.0)
        if disposicion == "plano":
            lado = v.unitario(v.cruz((0.0, 0.0, 1.0), eje)) or lado  # la hoja tumbada en el plano
        _hoja(m, (0.0, tallo * t, 0.0), eje, lado, largo * escala, ancho * escala, curva, filas, redondez)
    return m


_CACHE = {}


def prototipo_cache(tipo, calidad):
    clave = (tipo, calidad)
    if clave not in _CACHE:
        _CACHE[clave] = prototipo(tipo, calidad)
    return _CACHE[clave]


def combinar(tipo, nivel, matrices, nombre="hojas"):
    """Una malla con una copia del grupo ``tipo`` por cada matriz (filas, como Maya)."""
    base = prototipo_cache(tipo, calidad_de_nivel(nivel))
    m = Malla(nombre)
    nv, nuv = len(base.vertices), len(base.us)
    for k, a in enumerate(matrices):
        for x, y, z in base.vertices:
            m.vertices.append((x * a[0] + y * a[4] + z * a[8] + a[12],
                               x * a[1] + y * a[5] + z * a[9] + a[13],
                               x * a[2] + y * a[6] + z * a[10] + a[14]))
        m.us += base.us
        m.vs += base.vs
        m.conteos += base.conteos
        m.conexiones += [i + k * nv for i in base.conexiones]
        m.uv_ids += [i + k * nuv for i in base.uv_ids]
    return m


def triangulos_prototipo(tipo, nivel):
    return prototipo_cache(tipo, calidad_de_nivel(nivel)).triangulos


def colocar(modulo):
    """Matrices 4x4 (filas, como las de Maya) de los grupos de hojas de una rama.

    Necesita la guía calculada. Devuelve una lista vacía si la rama no lleva follaje.
    """
    val = modulo.valores
    tipo = val.get("follaje", "ninguno")
    guia = modulo.guia
    if tipo == "ninguno" or guia is None or val["densidad"] <= 0:
        return []
    azar = random.Random(modulo.semilla)
    tamano = val["tamano_hoja"]
    inicio = 1.0 - val["zona"]
    separacion = 30.0 * tamano / max(val["densidad"], 0.05)
    cantidad = max(1, int(round(guia.largo * val["zona"] / separacion)))
    matrices = []
    for i in range(cantidad + 1):
        punta = i == cantidad
        s = 1.0 if punta else min(1.0, inicio + (i + azar.random() * 0.8) / cantidad * val["zona"])
        t, n, b = guia.marco(s)
        if punta:
            eje = t
            sitio = guia.punto(1.0)
        else:
            angulo = i * _DORADO + azar.uniform(-0.4, 0.4)
            radial = v.suma(v.escala(n, math.cos(angulo)), v.escala(b, math.sin(angulo)))
            sitio = v.suma(guia.punto(s), v.escala(radial, guia.radio(s, angulo) * 0.7))
            eje = v.unitario(v.suma(v.escala(radial, 0.8), v.escala(t, 0.6)))
        eje = v.unitario(v.suma(v.escala(eje, 1.0 - val["hacia_arriba"]),
                                v.escala(v.ARRIBA, val["hacia_arriba"]))) or eje
        x = v.unitario(v.cruz(eje, v.perpendicular(eje)))
        x = v.rotar(x, eje, azar.uniform(0.0, 2.0 * math.pi))
        z = v.cruz(x, eje)
        e = tamano * azar.uniform(0.8, 1.2)
        matrices.append((
            x[0] * e, x[1] * e, x[2] * e, 0.0,
            eje[0] * e, eje[1] * e, eje[2] * e, 0.0,
            z[0] * e, z[1] * e, z[2] * e, 0.0,
            sitio[0], sitio[1], sitio[2], 1.0))
    return matrices
