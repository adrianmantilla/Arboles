# Árboles

Editor de árboles para Autodesk Maya 2026 y 2027 (Windows y macOS), pensado para estudiantes.
Montas el árbol a mano con módulos (tronco, ramas y follaje), lo guardas en tu biblioteca y lo
plantas en la escena como instancias ligadas al original.

> **Versión 0.9.** Editor, follaje, biblioteca, jardín con copias ligadas, 19 especies de serie
> con texturas de corteza y hoja, y guía para alumnos en [GUIA_ALUMNOS.md](GUIA_ALUMNOS.md).

No necesita instalar nada más: funciona con el Python que trae Maya.

## Instalar

1. Descarga o clona esta carpeta donde quieras dejarla, por ejemplo `Documentos/Plugins/Arboles`.
   No la muevas después de instalar (si la mueves, repite el paso 2).
2. Abre Maya y **arrastra el archivo `instalar.py` hasta el visor**.
3. Elige la carpeta de tu biblioteca. Por defecto, `Documentos/Arboles`.

Aparece el menú **Árboles** en la barra de Maya y se cargará solo cada vez que abras Maya.
Si algo falla, usa **Árboles > Comprobar instalación**.

## Desinstalar

Borra el archivo `arboles.mod` de la carpeta `modules` de tus preferencias de Maya
(la ruta exacta se escribe en el Script Editor al instalar) y desactiva `arboles_plugin`
en el Plug-in Manager.

## Menú Árboles

| Opción | Qué hace |
| --- | --- |
| Editor de árboles... | Monta, edita y guarda árboles |
| Plantar desde la biblioteca... | Panel con miniaturas para plantar con un clic, Desligar, Editar maestro y Ejemplos |
| Herramientas rápidas | Árbol de ejemplo, generar versión ligera, cuadros en la corteza |
| Carpeta de la biblioteca... | Cambia dónde se guardan tus árboles |
| Resolución de texturas | 512 (aula), 1K (recomendada), 2K o 4K (render final); cambia también las texturas ya puestas en la escena |
| Estilo de texturas | Realista, Cartoon (colores planos) o Estilizado (pintado); cambia también los árboles de la escena |
| Crear materiales clay | Crea `arboles_clay_corteza` y `arboles_clay_hoja` (standardSurface, se ven en el visor y en Arnold) |
| Comprobar instalación | Versión de Maya, Arnold y carpeta de la biblioteca |

## Texturas

Cada especie de serie trae su corteza (color, relieve y rugosidad, repetible) y su hoja
(color, relieve, rugosidad y trasluz) en `texturas/<especie>/<resolución>/`. Un árbol usa
las de su «Material» (combo del editor); «Clay» es gris neutro para modelar. En el visor se
ven con el modo texturizado (tecla 6). Los árboles guardados con versiones anteriores a la 0.5
no tienen material: toman el de la especie que indique su nombre, o el clay si no coincide. Las cortezas
se generan con `herramientas/texturas_corteza.py` (Substance 3D Designer, `sbsrender`) y
las hojas con `herramientas/texturas_hojas.py` (numpy y Pillow). Ver `texturas/LEEME.md`.
Los estilos cartoon y estilizado están en `texturas/<especie>/<estilo>/1k/` y salen del
realista con `herramientas/texturas_estilos.py` (numpy y Pillow); si un estilo no trae un
canal, se usa el realista. Las cortezas parten de materiales de serie de Adobe Substance: úsalas en clase y revisa
la licencia antes de publicarlas fuera del curso.

## Idiomas

Los textos están en `scripts/arboles/i18n/es.json`. Para traducir, copia ese archivo como
`en.json` (u otro código), traduce los valores y define la variable de entorno
`ARBOLES_IDIOMA=en` antes de abrir Maya.

## Para el profesor

- `python3 herramientas/empaquetar.py` crea `dist/Arboles-<versión>.zip` para repartir
  (sin pruebas ni herramientas), con texturas a 512 y 1K (unos 40 MB). Con `--2k` incluye
  también las de 2K (unos 130 MB) para render final. Si falta una resolución, se usa la más
  cercana. GitHub Actions genera el ZIP ligero en cada push, en «Artifacts».
- `python3 herramientas/miniaturas_ayuda.py` rehace las miniaturas de la ayuda de los
  deslizadores (`iconos/ayuda/`): el mismo árbol con un valor bajo y uno alto.
- `python3 herramientas/vista_previa.py` dibuja cada especie sin Maya (frente, 3/4 y planta)
  con su número de triángulos, para ajustar siluetas rápido.
- Pruebas sin Maya: `python3 -m unittest discover -s tests` (se ejecutan en Windows, macOS y Linux).
- Prueba completa en Maya: `mayapy herramientas/prueba_maya.py`.
- Render de comprobación en Arnold: `mayapy herramientas/render_jardin.py <carpeta>`.

## Estructura

```
instalar.py              arrastrar al visor para instalar
GUIA_ALUMNOS.md          guía rápida para alumnos
plug-ins/arboles_plugin.py  plugin de Maya (menú y comando de deshacer)
scripts/arboles/
  modulos.py, arbol.py   tronco y ramas: parámetros y geometría (sin Maya)
  follaje.py             grupos de hojas y dónde se cuelgan
  ejemplos.py            plantillas y frondosidad
  biblioteca.py          árboles guardados, miniaturas y ramas favoritas
  construir_maya.py      crea las mallas en Maya
  editor.py, editor_ui.py   editor en tiempo real
  plantar.py, plantar_ui.py jardín: maestros, copias ligadas y panel
  ajustes.py, materiales.py, interfaz_maya.py, i18n/
herramientas/            pruebas en Maya, capturas, renders y empaquetado
tests/                   pruebas sin Maya
```
