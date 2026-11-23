"""Árbol de ejemplo para probar los módulos (fase 1).

En la fase 2 estos ejemplos se convertirán en las plantillas de inicio del
editor (copa redonda, columnar, llorón, arbusto).
"""

from arboles.arbol import Arbol

_ANGULO_DORADO = 137.5


def copa_redonda():
    arbol = Arbol("copa_redonda")
    tronco = arbol.anadir_tronco(altura=520, grosor=22, estrechamiento=0.3, inclinacion=4,
                                 curvatura=0.12, raices=0.45, irregularidad=0.3, nudos=3)
    principales = 7
    for i in range(principales):
        f = i / float(principales - 1)
        rama = arbol.anadir_rama(tronco, posicion=0.42 + 0.5 * f, giro=(i * _ANGULO_DORADO) % 360,
                                 angulo=68 - 28 * f, longitud=330 - 170 * f, caida=0.25,
                                 curvatura=0.25, grosor=0.55 - 0.15 * f, nudos=1)
        for j in range(2):
            arbol.anadir_rama(rama, posicion=0.45 + 0.3 * j, giro=90 + 180 * j + 25 * i,
                              angulo=45, longitud=(150 - 60 * f) * (1.0 - 0.25 * j), caida=0.25,
                              curvatura=0.15, grosor=0.65, nudos=0, irregularidad=0.1)
    return arbol


EJEMPLOS = {"copa_redonda": copa_redonda}
