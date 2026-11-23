# Árboles

Editor de árboles para Autodesk Maya 2026 y 2027 (Windows y macOS), pensado para estudiantes.
Montas el árbol a mano con módulos (tronco, ramas y follaje), lo guardas en tu biblioteca y lo
plantas en la escena como instancias ligadas al original.

> **Estado: fase 0.** Instalación, menú, idioma, carpeta de la biblioteca y materiales clay.
> El editor y la biblioteca llegan en las fases siguientes.

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
| Editor de árboles... | Fase 2 |
| Biblioteca... | Fase 3 |
| Carpeta de la biblioteca... | Cambia dónde se guardan tus árboles |
| Crear materiales clay | Crea `arboles_clay_corteza` y `arboles_clay_hoja` (standardSurface, se ven en el visor y en Arnold) |
| Comprobar instalación | Versión de Maya, Arnold y carpeta de la biblioteca |

## Idiomas

Los textos están en `scripts/arboles/i18n/es.json`. Para traducir, copia ese archivo como
`en.json` (u otro código), traduce los valores y define la variable de entorno
`ARBOLES_IDIOMA=en` antes de abrir Maya.

## Estructura

```
instalar.py              arrastrar al visor para instalar
plug-ins/arboles_plugin.py  plugin de Maya (crea el menú al cargarse)
scripts/arboles/
  ajustes.py             carpeta de la biblioteca y preferencias (no depende de Maya)
  materiales.py          materiales clay
  interfaz_maya.py       menú, bienvenida y comprobación
  i18n/                  textos por idioma
herramientas/
  prueba_maya.py         prueba dentro de Maya con mayapy
tests/                   pruebas sin Maya: python3 -m unittest discover tests
```
