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
#        redondez del contorno (más bajo = más redonda), disposición, forma)
# disposición «espiral»: hojas alrededor del tallito; «plano»: a los dos lados, como una pluma.
# forma: «ovalada», «lanceolada» (estrecha y en punta), «triangular» (ancha abajo y en punta),
#        «lobulada» (tres lóbulos por lado, como el roble), «palmeada» (ancha, con lóbulos en punta,
#        como el arce) o «aguja» (tira fina y plana: pocas caras).
TIPOS = {
    "hoja_ancha": (12, 15.0, 9.5, 42.0, 60.0, 0.35, 0.7, "espiral", "ovalada"),      # haya
    "hoja_roble": (11, 17.0, 10.5, 42.0, 60.0, 0.3, 0.6, "espiral", "lobulada"),     # roble
    "hoja_fina": (14, 17.0, 3.2, 44.0, 45.0, 0.5, 0.7, "espiral", "lanceolada"),     # sauce, olivo
    "hoja_redonda": (16, 8.5, 8.0, 40.0, 65.0, 0.25, 0.4, "espiral", "triangular"),  # abedul, álamo
    "hoja_grande": (6, 30.0, 17.0, 30.0, 55.0, 0.4, 0.6, "espiral", "ovalada"),      # magnolio, catalpa
    "hoja_palmeada": (7, 20.0, 19.0, 34.0, 58.0, 0.3, 0.5, "espiral", "palmeada"),   # arce, plátano de sombra
    "hoja_castano": (7, 26.0, 8.0, 34.0, 55.0, 0.35, 0.7, "espiral", "lanceolada"),  # castaño
    "hoja_pequena": (18, 6.5, 3.8, 34.0, 62.0, 0.15, 0.6, "espiral", "ovalada"),     # encina, boj
    "plumosa": (18, 13.0, 3.5, 48.0, 75.0, 0.2, 0.8, "plano", "lanceolada"),         # acacia, fresno
    "escama": (40, 8.0, 2.6, 46.0, 34.0, 0.05, 0.9, "plano", "aguja"),               # ciprés, tuya
    "aguja": (36, 12.0, 1.4, 20.0, 70.0, 0.1, 0.7, "espiral", "aguja"),              # pinos en general
    "pinocha": (34, 15.0, 1.6, 9.0, 82.0, 0.18, 0.7, "espiral", "aguja"),            # pino piñonero: borla
    "aguja_corta": (44, 8.0, 1.5, 44.0, 62.0, 0.12, 0.8, "espiral", "aguja"),        # abeto: escobilla
}
# calidad: filas a lo largo de cada hoja (las agujas usan la mitad)
CALIDADES = {"alta": 6, "baja": 2}
_DORADO = math.radians(137.5)


def calidad_de_nivel(nivel):
    return "alta" if nivel in ("denso", "alto") else "baja"


def contorno(forma, t, redondez=0.7, filas=6):
    """Medio ancho relativo (0-1) de la hoja a la altura t (0 en el tallo, 1 en la punta)."""
    base = math.sin(math.pi * min(0.98, 0.08 + t * 0.92)) ** redondez
    if forma == "lanceolada":
        return base * (1.0 - 0.35 * t)
    if forma == "triangular":  # ancha cerca de la base y terminada en punta
        return math.sin(math.pi * min(0.97, 0.05 + 0.95 * t ** 0.75))
    if forma == "palmeada":  # ancha hacia la base, con lóbulos en punta y entrantes hondos
        ancho = math.sin(math.pi * min(0.97, 0.05 + 0.95 * t ** 0.6))
        k = int(round(t * filas))
        if filas >= 4 and 0 < k < filas:
            ancho *= 1.0 if k % 2 else 0.45
        return ancho
    if forma == "lobulada" and filas >= 4:
        # Filas impares: lóbulo; pares: entrante. Tres lóbulos por lado con 6 filas.
        k = int(round(t * filas))
        return base * (1.0 if k % 2 else 0.55) if 0 < k < filas else base
    return base


def _hoja(m, origen, eje, lado, largo, ancho, curva, filas, redondez=0.7, cuadro=0, forma="ovalada"):
    """Añade a ``m`` una hoja doblada por el nervio, de ``origen`` hacia ``eje``.

    La textura de hoja lleva cuatro variantes de color en 2x2; ``cuadro`` (0-3) dice cuál usa.
    Las agujas son una tira plana (una cara por fila) y con la mitad de filas.
    """
    cu, cv = (cuadro % 2) * 0.5, (cuadro // 2) * 0.5
    columnas = (-1.0, 1.0) if forma == "aguja" else (-1.0, 0.0, 1.0)
    if forma == "aguja":
        filas = max(1, filas // 2)
    n = len(columnas)
    normal = v.unitario(v.cruz(eje, lado)) or v.perpendicular(eje)
    base = len(m.vertices)
    base_uv = len(m.us)
    for k in range(filas + 1):
        t = k / float(filas)
        perfil = contorno(forma, t, redondez, filas)
        if forma == "aguja":
            perfil = 1.0 - 0.6 * t * t  # casi del mismo ancho hasta la punta
        centro = v.suma(origen, v.suma(v.escala(eje, largo * t), v.escala(normal, -curva * largo * t * t)))
        for x in columnas:
            pliegue = 0.12 * ancho * (1.0 - abs(x)) * perfil  # el nervio un poco levantado
            p = v.suma(centro, v.suma(v.escala(lado, x * ancho * 0.5 * perfil), v.escala(normal, pliegue)))
            m.vertices.append(p)
            m.us.append(cu + (x + 1.0) * 0.25)
            m.vs.append(cv + t * 0.5)
    for k in range(filas):
        for j in range(n - 1):
            a = base + k * n + j
            m.conteos.append(4)
            m.conexiones += [a, a + 1, a + 1 + n, a + n]
            u = base_uv + k * n + j
            m.uv_ids += [u, u + 1, u + 1 + n, u + n]


def prototipo(tipo, calidad="alta"):
    """Malla del grupo de hojas ``tipo`` en espacio local."""
    hojas, largo, ancho, tallo, apertura, curva, redondez, disposicion, forma = TIPOS[tipo]
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
        _hoja(m, (0.0, tallo * t, 0.0), eje, lado, largo * escala, ancho * escala, curva, filas, redondez,
              azar.randrange(4), forma)
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
    cantidad = max(0, int(round(guia.largo * val["zona"] / separacion)))  # 0: solo el de la punta
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
        if TIPOS[tipo][7] == "plano":
            # Ramilletes planos tumbados de cara al cielo, como crecen para coger luz.
            x = v.unitario(v.cruz(eje, v.ARRIBA)) or x
            x = v.rotar(x, eje, azar.uniform(-0.45, 0.45))
        else:
            x = v.rotar(x, eje, azar.uniform(0.0, 2.0 * math.pi))
        z = v.cruz(x, eje)
        e = tamano * azar.uniform(0.8, 1.2)
        matrices.append((
            x[0] * e, x[1] * e, x[2] * e, 0.0,
            eje[0] * e, eje[1] * e, eje[2] * e, 0.0,
            z[0] * e, z[1] * e, z[2] * e, 0.0,
            sitio[0], sitio[1], sitio[2], 1.0))
    return matrices
