"""Árboles de ejemplo realistas, por especie.

Cada especie se describe con su tronco y una receta por nivel de ramas
(principales, secundarias, ramitas). El generador reparte las ramas con
pequeñas variaciones (siempre las mismas: la semilla es fija), así que el
resultado es un árbol normal del editor: todo se puede tocar después.

Lo que da realismo con pocos triángulos:
- tres niveles de ramas, cada uno más corto, fino y caído que el anterior;
- la silueta de la copa sale del largo de las ramas según dónde nacen (perfil);
- las hojas se concentran en las ramitas finales, no en las ramas gruesas;
- nada es perfecto: ángulos, largos, giros y posiciones varían un poco.
"""

import math
import random

from arboles.arbol import Arbol

_DORADO = 137.5


def _perfil(nombre, p):
    """Largo relativo de una rama según dónde nace (p de 0 a 1 en la zona con ramas)."""
    if nombre == "conico":       # abeto: largas abajo, cortas arriba
        return 1.0 - 0.85 * p
    if nombre == "redondo":      # roble, haya: más largas en el centro de la copa
        return 0.55 + 0.45 * math.sin(math.pi * (0.25 + 0.75 * p))
    if nombre == "parasol":      # pino piñonero: todo arriba y abierto
        return 0.75 + 0.25 * p
    if nombre == "ovalado":      # abedul, sauce
        return 0.6 + 0.4 * math.sin(math.pi * (0.1 + 0.8 * p))
    if nombre == "columna":      # ciprés
        return 1.0 - 0.6 * p * p
    return 1.0


def _ramificar(arbol, madre, largo_madre, niveles, azar, profundidad=0, desfase=0.0):
    if profundidad >= len(niveles):
        return
    r = niveles[profundidad]
    n = r["n"]
    if isinstance(n, tuple):
        n = azar.randint(*n)
    a, b = r["pos"]
    for i in range(n):
        f = (i + 0.5) / n if n > 1 else 0.5
        posicion = min(0.98, max(0.02, a + (b - a) * f + azar.uniform(-0.5, 0.5) * (b - a) / max(n, 1)))
        if r.get("giro") == "opuesto":
            giro = (desfase + 180.0 * i + 90.0 * (i // 2) + azar.uniform(-25, 25)) % 360
        elif r.get("giro") == "verticilo":
            por_piso = r.get("por_piso", 4)
            giro = (desfase + (i % por_piso) * 360.0 / por_piso + (i // por_piso) * 37.0 + azar.uniform(-15, 15)) % 360
            posicion = min(0.98, a + (b - a) * (i // por_piso) / max(1, (n - 1) // por_piso))
        else:
            giro = (desfase + i * _DORADO + azar.uniform(-20, 20)) % 360
        p = (posicion - a) / max(b - a, 1e-6)
        largo = largo_madre * r["largo"] * _perfil(r.get("perfil"), p) * azar.uniform(0.8, 1.15)
        valores = dict(
            posicion=posicion, giro=giro,
            angulo=r["angulo"] + r.get("angulo_punta", 0.0) * p + azar.uniform(-1, 1) * r.get("var_angulo", 8.0),
            longitud=max(12.0, largo),
            caida=min(1.0, max(0.0, r["caida"] + azar.uniform(-0.08, 0.08))),
            curvatura=r.get("curvatura", 0.0) + azar.uniform(-0.1, 0.1),
            grosor=r.get("grosor", 0.5), estrechamiento=r.get("estrechamiento", 0.25),
            irregularidad=r.get("irregularidad", 0.15), nudos=r.get("nudos", 0),
            torsion=azar.uniform(-1, 1) * r.get("torsion", 0.0),
            follaje=r.get("follaje", "ninguno"),
        )
        if valores["follaje"] != "ninguno":
            valores.update(densidad=r["densidad"], zona=r["zona"], tamano_hoja=r.get("tamano", 1.0),
                           hacia_arriba=r.get("hacia_arriba", 0.4))
        rama = arbol.anadir_rama(madre, **valores)
        tortuoso = r.get("tortuoso", 0.0)
        if tortuoso:  # ramas que cambian de rumbo, no arcos perfectos
            for indice, peso in ((0, 1.0), (1, 0.8), (2, 0.4)):
                d = [azar.uniform(-1, 1) for _ in range(3)]
                d[1] *= 0.6
                rama.fijar_control(indice, tuple(c * tortuoso * valores["longitud"] * peso for c in d))
        _ramificar(arbol, rama, valores["longitud"], niveles, azar, profundidad + 1, azar.uniform(0, 360))


def _especie(nombre, tronco, niveles, semilla):
    arbol = Arbol(nombre, material=nombre)  # texturas de su especie si están instaladas
    t = arbol.anadir_tronco(**tronco)
    _ramificar(arbol, t, tronco["altura"], niveles, random.Random(semilla))
    return arbol


def roble():
    """Tronco corto y grueso, ramas principales tortuosas y una copa ancha y redonda."""
    return _especie("roble", dict(altura=430, grosor=36, estrechamiento=0.35, inclinacion=5, curvatura=0.15,
                                  raices=0.7, irregularidad=0.55, nudos=5, torsion=25), [
        dict(n=6, pos=(0.4, 0.95), angulo=60, angulo_punta=-25, largo=1.0, perfil="redondo", caida=0.15,
             curvatura=0.15, grosor=0.62, irregularidad=0.45, nudos=2, torsion=40, var_angulo=12, tortuoso=0.12),
        dict(n=(3, 4), pos=(0.3, 0.92), angulo=50, largo=0.5, caida=0.3, curvatura=0.15, grosor=0.6,
             irregularidad=0.25, nudos=1, tortuoso=0.1, follaje="hoja_ancha", densidad=0.9, zona=0.5, tamano=2.0),
        dict(n=(2, 3), pos=(0.4, 0.95), angulo=42, largo=0.5, caida=0.35, grosor=0.6, estrechamiento=0.3,
             follaje="hoja_ancha", densidad=1.4, zona=0.95, tamano=2.0, hacia_arriba=0.45),
    ], 11)


def haya():
    """Tronco recto, liso y gris; copa alta y ovalada de ramas que suben y luego se abren."""
    return _especie("haya", dict(altura=720, grosor=27, estrechamiento=0.25, curvatura=0.05,
                                 raices=0.55, irregularidad=0.08, nudos=1), [
        dict(n=7, pos=(0.3, 0.95), angulo=38, angulo_punta=-15, largo=0.58, perfil="ovalado", caida=0.25,
             curvatura=0.2, grosor=0.5, irregularidad=0.08, tortuoso=0.08),
        dict(n=(3, 4), pos=(0.3, 0.95), angulo=50, largo=0.55, caida=0.45, curvatura=0.05, grosor=0.6,
             tortuoso=0.06, follaje="hoja_ancha", densidad=0.9, zona=0.5, tamano=1.8),
        dict(n=2, pos=(0.5, 0.95), angulo=45, largo=0.45, caida=0.5, grosor=0.6,
             follaje="hoja_ancha", densidad=1.3, zona=0.95, tamano=1.8, hacia_arriba=0.5),
    ], 23)


def pino_pinonero():
    """Tronco alto que se abre en brazos en forma de copa de vino, con una sombrilla plana y densa arriba."""
    return _especie("pino_pinonero", dict(altura=650, grosor=26, estrechamiento=0.45, inclinacion=6,
                                          curvatura=0.12, raices=0.4, irregularidad=0.35, nudos=2), [
        dict(n=5, pos=(0.82, 1.0), angulo=42, largo=0.6, caida=0.0, curvatura=-0.35, grosor=0.7,
             estrechamiento=0.4, irregularidad=0.3, nudos=1, var_angulo=6, tortuoso=0.08),
        dict(n=(4, 5), pos=(0.45, 1.0), angulo=75, largo=0.65, caida=0.0, curvatura=-0.1, grosor=0.6,
             tortuoso=0.06, follaje="aguja", densidad=0.6, zona=0.4, tamano=3.0, hacia_arriba=0.95),
        dict(n=(2, 3), pos=(0.3, 1.0), angulo=55, largo=0.55, caida=0.05, curvatura=0.2, grosor=0.6,
             follaje="aguja", densidad=1.1, zona=0.95, tamano=3.0, hacia_arriba=0.95),
    ], 37)


def abeto():
    """Pisos de ramas que bajan un poco y suben en la punta, cubiertas de agujas: un cono denso."""
    return _especie("abeto", dict(altura=900, grosor=22, estrechamiento=0.08, curvatura=0.02,
                                  raices=0.35, irregularidad=0.2), [
        dict(n=30, pos=(0.08, 0.97), giro="verticilo", por_piso=5, angulo=95, angulo_punta=-35, largo=0.36,
             perfil="conico", caida=0.35, curvatura=0.3, grosor=0.3, estrechamiento=0.1, var_angulo=5,
             follaje="aguja", densidad=0.8, zona=0.95, tamano=3.0, hacia_arriba=0.2),
        dict(n=2, pos=(0.35, 0.85), giro="opuesto", angulo=60, largo=0.4, caida=0.25, grosor=0.5,
             follaje="aguja", densidad=0.55, zona=0.95, tamano=2.6, hacia_arriba=0.15),
    ], 41)


def abedul():
    """Tronco fino y claro, ramas que suben y ramitas largas y colgantes."""
    return _especie("abedul", dict(altura=680, grosor=15, estrechamiento=0.22, inclinacion=4,
                                   curvatura=0.15, raices=0.2, irregularidad=0.15, nudos=5), [
        dict(n=9, pos=(0.3, 0.95), angulo=35, angulo_punta=-10, largo=0.4, perfil="ovalado", caida=0.15,
             curvatura=0.35, grosor=0.45, irregularidad=0.1, nudos=1, tortuoso=0.08),
        dict(n=(4, 5), pos=(0.25, 0.95), angulo=50, largo=0.7, caida=0.75, grosor=0.55, estrechamiento=0.2,
             follaje="hoja_redonda", densidad=1.1, zona=0.85, tamano=1.4, hacia_arriba=0.2),
    ], 53)


def sauce_lloron():
    """Tronco corto que se abre en brazos curvos; de ellos cuelgan cortinas de ramitas hasta casi el suelo."""
    return _especie("sauce_lloron", dict(altura=330, grosor=32, estrechamiento=0.45, inclinacion=7,
                                         curvatura=0.2, raices=0.6, irregularidad=0.5, nudos=4), [
        dict(n=6, pos=(0.5, 1.0), angulo=50, angulo_punta=-15, largo=1.0, perfil="ovalado", caida=0.25,
             curvatura=0.25, grosor=0.55, irregularidad=0.35, nudos=1, tortuoso=0.12, var_angulo=12),
        dict(n=(5, 6), pos=(0.3, 1.0), angulo=70, largo=1.2, caida=1.0, curvatura=-0.2, grosor=0.4,
             estrechamiento=0.12, follaje="hoja_fina", densidad=0.85, zona=0.9, tamano=1.0, hacia_arriba=0.0),
    ], 61)


def cipres():
    """Columna estrecha y densa: muchas ramas cortas que suben pegadas al tronco."""
    return _especie("cipres", dict(altura=950, grosor=18, estrechamiento=0.1, curvatura=0.03,
                                   raices=0.3, irregularidad=0.2), [
        dict(n=40, pos=(0.04, 0.98), angulo=26, largo=0.22, perfil="columna", caida=0.0, curvatura=0.45,
             grosor=0.35, estrechamiento=0.15, var_angulo=5, follaje="escama", densidad=1.2, zona=0.95,
             tamano=2.2, hacia_arriba=0.9),
    ], 71)


def olivo():
    """Tronco corto, retorcido y abierto en varios brazos; copa baja y redondeada de hoja fina."""
    return _especie("olivo", dict(altura=210, grosor=28, estrechamiento=0.6, inclinacion=12,
                                  curvatura=0.3, raices=0.8, irregularidad=0.8, nudos=6, torsion=90), [
        dict(n=4, pos=(0.75, 1.0), angulo=40, largo=1.4, perfil="redondo", caida=0.1, curvatura=0.3,
             grosor=0.7, estrechamiento=0.4, irregularidad=0.6, nudos=3, torsion=60, var_angulo=12, tortuoso=0.14),
        dict(n=(3, 4), pos=(0.35, 1.0), angulo=48, largo=0.55, caida=0.35, curvatura=0.1, grosor=0.55,
             irregularidad=0.3, tortuoso=0.1, follaje="hoja_fina", densidad=0.8, zona=0.5, tamano=1.1,
             hacia_arriba=0.55),
        dict(n=(2, 3), pos=(0.45, 1.0), angulo=40, largo=0.5, caida=0.45, grosor=0.6,
             follaje="hoja_fina", densidad=1.3, zona=0.95, tamano=1.1, hacia_arriba=0.55),
    ], 83)


def arbusto():
    """Muchos tallos que salen del suelo y se abren hacia fuera, cada uno ramificado, con hoja pequeña."""
    return _especie("arbusto", dict(altura=12, grosor=7, estrechamiento=0.7, raices=0.3,
                                    irregularidad=0.3), [
        dict(n=11, pos=(0.1, 1.0), angulo=30, angulo_punta=0, largo=11.0, caida=0.3, curvatura=-0.15,
             grosor=0.45, irregularidad=0.2, var_angulo=14, tortuoso=0.1),
        dict(n=(3, 4), pos=(0.25, 1.0), angulo=45, largo=0.45, caida=0.3, grosor=0.6,
             follaje="hoja_redonda", densidad=1.2, zona=0.95, tamano=0.9, hacia_arriba=0.5),
    ], 97)


ESPECIES = {
    "roble": roble,
    "haya": haya,
    "pino_pinonero": pino_pinonero,
    "abeto": abeto,
    "abedul": abedul,
    "sauce_lloron": sauce_lloron,
    "cipres": cipres,
    "olivo": olivo,
    "arbusto": arbusto,
}
