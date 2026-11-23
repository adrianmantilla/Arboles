# Árboles

Editor de árboles para Autodesk Maya 2026 y 2027 (Windows y macOS), pensado para estudiantes.
Montas el árbol a mano con módulos (tronco, ramas y follaje), lo guardas en tu biblioteca y lo
plantas en la escena como instancias ligadas al original.

> **Estado: fase 4 (aula).** Editor, follaje, biblioteca, jardín con copias ligadas y guía para
> alumnos en [GUIA_ALUMNOS.md](GUIA_ALUMNOS.md).

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
| Crear materiales clay | Crea `arboles_clay_corteza` y `arboles_clay_hoja` (standardSurface, se ven en el visor y en Arnold) |
| Comprobar instalación | Versión de Maya, Arnold y carpeta de la biblioteca |

## Idiomas

Los textos están en `scripts/arboles/i18n/es.json`. Para traducir, copia ese archivo como
`en.json` (u otro código), traduce los valores y define la variable de entorno
`ARBOLES_IDIOMA=en` antes de abrir Maya.

## Para el profesor

- `python3 herramientas/empaquetar.py` crea `dist/Arboles-<versión>.zip` para repartir
  (sin pruebas ni herramientas). GitHub Actions lo genera también en cada push, en «Artifacts».
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
