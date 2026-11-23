# Texturas de Árboles

Una carpeta por juego de texturas (normalmente, una por especie: `roble`, `haya`…),
con una subcarpeta por resolución y una imagen por canal:

```
texturas/
  roble/
    512/  1k/  2k/  4k/
      corteza_color.png   corteza_normal.png   corteza_rugosidad.png
      hoja_color.png      hoja_normal.png      hoja_rugosidad.png   hoja_translucidez.png
```

- Formatos: .png, .jpg, .tif o .exr. Puede faltar algún canal o alguna resolución:
  se usa la más cercana que haya.
- La corteza debe ser **repetible** (sin costuras en horizontal ni en vertical):
  el plugin da vueltas enteras de textura alrededor de cada rama.
- La hoja ocupa toda la imagen: a lo ancho de la hoja (el nervio en el centro)
  y a lo largo, del tallo (abajo) a la punta (arriba).
- Normales en espacio tangente, estilo OpenGL (verde hacia arriba).
- Color y translucidez en sRGB; normal y rugosidad sin gestión de color.

Un árbol usa el juego que dice su «Material» en el editor. Si el juego no
está instalado, el árbol se ve en clay. La resolución se elige en el menú
Árboles > Resolución de texturas.
