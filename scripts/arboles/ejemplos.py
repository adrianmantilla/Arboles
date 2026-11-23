"""Plantillas de inicio del editor: árboles ya montados para no empezar de cero.

Todo lo que crean se puede editar después. «vacio» es solo un tronco.
"""

from arboles.arbol import Arbol

_DORADO = 137.5


def vacio():
    arbol = Arbol("arbol_nuevo")
    arbol.anadir_tronco(altura=400, grosor=18, curvatura=0.1)
    return arbol


def copa_redonda():
    arbol = Arbol("copa_redonda")
    tronco = arbol.anadir_tronco(altura=520, grosor=22, estrechamiento=0.3, inclinacion=4,
                                 curvatura=0.12, raices=0.45, irregularidad=0.3, nudos=3)
    principales = 7
    for i in range(principales):
        f = i / float(principales - 1)
        rama = arbol.anadir_rama(tronco, posicion=0.42 + 0.5 * f, giro=(i * _DORADO) % 360,
                                 angulo=68 - 28 * f, longitud=330 - 170 * f, caida=0.25,
                                 curvatura=0.25, grosor=0.55 - 0.15 * f, nudos=1,
                                 follaje="hoja_ancha", densidad=0.35, zona=0.35)
        for j in range(2):
            arbol.anadir_rama(rama, posicion=0.45 + 0.3 * j, giro=90 + 180 * j + 25 * i,
                              angulo=45, longitud=(150 - 60 * f) * (1.0 - 0.25 * j), caida=0.25,
                              curvatura=0.15, grosor=0.65, nudos=0, irregularidad=0.1,
                              follaje="hoja_ancha", densidad=0.7, zona=0.8)
    return arbol


def columnar():
    arbol = Arbol("columnar")
    tronco = arbol.anadir_tronco(altura=750, grosor=20, estrechamiento=0.2, curvatura=0.05,
                                 raices=0.3, irregularidad=0.2, nudos=2)
    ramas = 12
    for i in range(ramas):
        f = i / float(ramas - 1)
        arbol.anadir_rama(tronco, posicion=0.18 + 0.78 * f, giro=(i * _DORADO) % 360,
                          angulo=22 + 8 * (1 - f), longitud=230 - 130 * f, caida=0.05,
                          curvatura=0.35, grosor=0.35, follaje="hoja_fina", densidad=0.8,
                          zona=0.85, hacia_arriba=0.7)
    return arbol


def lloron():
    arbol = Arbol("lloron")
    tronco = arbol.anadir_tronco(altura=450, grosor=26, estrechamiento=0.4, inclinacion=6,
                                 curvatura=0.2, raices=0.6, irregularidad=0.4, nudos=4)
    principales = 6
    for i in range(principales):
        f = i / float(principales - 1)
        rama = arbol.anadir_rama(tronco, posicion=0.6 + 0.35 * f, giro=(i * _DORADO) % 360,
                                 angulo=55 - 15 * f, longitud=300 - 80 * f, caida=0.3,
                                 curvatura=0.45, grosor=0.5, follaje="ninguno")
        for j in range(2):
            arbol.anadir_rama(rama, posicion=0.4 + 0.35 * j, giro=(j * _DORADO + 40 * i) % 360,
                              angulo=40, longitud=340 - 60 * j, caida=1.0, curvatura=0.0,
                              grosor=0.5, estrechamiento=0.15, follaje="hoja_fina",
                              densidad=0.8, zona=0.85, hacia_arriba=0.0)
    return arbol


def arbusto():
    arbol = Arbol("arbusto")
    tronco = arbol.anadir_tronco(altura=60, grosor=9, estrechamiento=0.6, curvatura=0.0,
                                 raices=0.2, irregularidad=0.3, nudos=0)
    tallos = 9
    for i in range(tallos):
        arbol.anadir_rama(tronco, posicion=0.5 + 0.5 * (i % 3) / 2.0, giro=(i * _DORADO) % 360,
                          angulo=25 + 30 * ((i * 7) % 3) / 2.0, longitud=110 + 25 * ((i * 5) % 4),
                          caida=0.2, curvatura=0.3, grosor=0.55, follaje="hoja_ancha",
                          densidad=0.9, zona=0.8, tamano_hoja=0.8, hacia_arriba=0.5)
    return arbol


PLANTILLAS = {
    "vacio": vacio,
    "copa_redonda": copa_redonda,
    "columnar": columnar,
    "lloron": lloron,
    "arbusto": arbusto,
}
EJEMPLOS = PLANTILLAS
