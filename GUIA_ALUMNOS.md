# Árboles · Guía rápida

Con Árboles montas un árbol a mano en Maya, lo guardas en tu biblioteca y lo plantas en la
escena tantas veces como quieras. Las copias plantadas siguen ligadas a su original: si
cambias el original, cambian todas.

## 1. Instalar (una vez)

1. Descomprime el ZIP en una carpeta que no vayas a mover, por ejemplo `Documentos/Plugins/Arboles`.
2. Abre Maya 2026 o 2027 y arrastra el archivo `instalar.py` hasta el visor.
3. Si Maya pregunta por un plug-in no confiable («Untrusted Plugin Loading»), pulsa **Allow**.
4. Elige dónde guardar tu biblioteca. Por defecto, `Documentos/Arboles`.

Aparece el menú **Árboles** en la barra de Maya. Se cargará solo cada vez que abras Maya.

## 2. Tu primer árbol en cinco minutos

1. Abre **Árboles › Editor de árboles…**
2. En **Empezar desde** elige una plantilla y su **frondosidad** (clara, normal o frondosa), y pulsa **Empezar**.
3. Haz clic en una rama de la lista o en el visor y mueve los deslizadores. Todo cambia al momento.
4. Ponle un nombre y pulsa **Guardar**. Se guarda con una miniatura.

Plantillas: roble, haya, pino piñonero, abeto, abedul, sauce llorón, ciprés, olivo y arbusto.
«Solo tronco» es para empezar de cero.

## 3. Editar

| Quiero… | Cómo |
| --- | --- |
| Añadir una rama donde yo diga | **Rama con un clic** y haz clic en el tronco o en una rama. Esc para terminar. |
| Cambiar varias ramas a la vez | Selecciónalas todas y mueve el deslizador: cada una cambia desde su valor. |
| Repartir ramas alrededor del tronco | Selecciona una y pulsa **Repetir alrededor**. |
| Doblar una rama a mano | Activa **Tiradores de la curva** y mueve los puntos amarillos. **Enderezar** lo deshace. |
| Copiar el aspecto de una rama a otras | **Copiar ajustes** en una, selecciona las otras y **Pegar ajustes**. |
| Reutilizar una rama en otro árbol | **Ramas favoritas**. |
| Ver la escala | **Figura humana (1,75 m)**. |
| Deshacer | Ctrl+Z (Cmd+Z en Mac), en todo. |

El deslizador estrella es **Peso**: dobla la rama hacia abajo por su peso. Con él pasas de
un roble a un sauce.

### Hojas

En cada rama eliges el tipo de **Hojas**, su **Densidad**, su **Tamaño**, la **Zona con hojas**
(solo la punta o toda la rama) y cuánto miran **Hacia el cielo**.

| Tipo | Se parece a |
| --- | --- |
| Hoja ancha | roble, haya |
| Hoja fina | sauce, olivo |
| Hoja redonda | abedul, álamo |
| Hoja grande | castaño, plátano de sombra |
| Plumosa | acacia, fresno, mimosa |
| Escamas | ciprés, tuya |
| Agujas | pino, abeto |

### El semáforo

Abajo, en el editor, hay un contador de triángulos con un color. **Verde**: cabe sin problema en un
jardín de 50 árboles. **Amarillo**: pesado; planta menos o usa calidad baja. **Rojo**: quita
ramas u hojas.

## 4. Plantar un jardín

1. Abre **Árboles › Plantar desde la biblioteca…** (o el botón **Plantar…** del editor).
2. ¿Biblioteca vacía? Pulsa **Ejemplos** y tendrás los árboles de serie.
3. Elige un árbol, la **calidad** (baja, media o alta) y pulsa **Plantar con clic**.
4. Cada clic en el visor planta un árbol sobre el suelo, con un giro al azar. Esc para terminar.

Debajo verás cuántos árboles y triángulos tiene tu jardín, con el mismo semáforo.

### Cambiar todas las copias a la vez

1. Selecciona una copia y pulsa **Editar maestro**.
2. Cambia lo que quieras en el editor y pulsa **Guardar**.
3. Acepta **actualizar las copias**: cambian todas a la vez.

¿Quieres que una copia sea distinta? Selecciónala y pulsa **Desligar**: pasa a ser un árbol
independiente que ya no cambia con el maestro.

## 5. Render

Cada especie de ejemplo trae sus texturas de corteza y de hoja. En el editor, el desplegable
**Material** elige cuáles usa tu árbol: la de una especie, o **Clay** (gris neutro, cómodo
para modelar). Las texturas se ven en el visor y en Arnold.

En **Árboles › Resolución de texturas** eliges la calidad: 512 o 1K mientras trabajas en
clase, 2K o 4K para el render final. Cambiarla actualiza los árboles que ya tienes en la escena.

También puedes asignar tus propios materiales. Las UVs de la corteza son limpias: cualquier
textura repetible encaja.

## Si algo falla

- **Árboles › Comprobar instalación** dice la versión de Maya, si está Arnold y dónde está tu biblioteca.
- Si moviste la carpeta del plugin, vuelve a arrastrar `instalar.py` al visor.
- Las hojas se ven negras en el visor: activa la iluminación por las dos caras
  (en el visor, **Lighting › Two Sided Lighting**). El editor la activa solo.
