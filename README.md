# Piano mediante gestos

Aplicación de visión artificial que permite tocar notas de piano levantando los dedos frente a una webcam. Detecta ambas manos, compara los movimientos con una calibración inicial y reproduce la nota correspondiente. La pantalla muestra la cámara en espejo, los dedos activos en azul, la nota y la octava seleccionadas.

## Instalación y ejecución

Necesitas Windows, **Python 3.13.17**, una webcam y salida de audio. Abre la carpeta del repositorio en Visual Studio Code y ejecuta estos comandos en su terminal PowerShell:

```powershell
py -3.13 -m venv src/.venv
./src/.venv/Scripts/python.exe -m pip install -r requirements.txt
./src/.venv/Scripts/python.exe src/main.py
```

Los dos primeros comandos se realizan solo al preparar el proyecto. Si ya tienes el entorno instalado, ejecuta únicamente el último. No necesitas activar el entorno para usar estos comandos.

## Cómo comenzar

1. Coloca la cámara de forma que se vean **ambas manos completas**, con buena iluminación.
2. Selecciona la ventana del programa y presiona **C** para calibrar.
3. Durante los primeros **5 segundos**, mantén los dedos extendidos en reposo y las palmas quietas.
4. Cuando cambie el mensaje, **levanta todos los dedos** durante otros **5 segundos**, manteniendo las palmas en su posición.
5. Vuelve al reposo. Luego levanta un dedo musical para tocar y bájalo al reposo para soltar la nota.

La calibración aprende la diferencia entre reposo y levantamiento: tener el dedo extendido por sí solo no activa una nota. Si la calibración falla o cambias la posición de la cámara o de las manos, repítela con **C**.

## Notas y octavas

Las manos corresponden a tu izquierda y derecha, aunque la imagen se muestre en espejo.

| Mano | Dedo que levantas | Nota |
| --- | --- | --- |
| Izquierda | Pulgar | DO |
| Izquierda | Índice | RE |
| Izquierda | Medio | MI |
| Izquierda | Anular | FA |
| Izquierda | Meñique | SOL |
| Derecha | Pulgar | LA |
| Derecha | Índice | SI |

Los dedos **medio, anular y meñique de la mano derecha** controlan la octava según cuántos mantengas levantados:

| Dedos de control levantados | Octava |
| --- | --- |
| 0 | 3 |
| 1 | 4 |
| 2 | 5 |
| 3 | 6 |

Cambiar la octava no produce sonido por sí solo. Por ejemplo, levanta el índice izquierdo y un dedo de control derecho para tocar **RE4**.

## Controles y recomendaciones

- **C:** iniciar o repetir la calibración. Durante ella no se reproduce sonido.
- **ESC o botón de cierre de la ventana:** salir del programa.
- Se reproduce **una sola nota a la vez**. Si levantas varios dedos musicales, hay silencio.
- Mantener un dedo levantado no repite la nota. Para repetirla, vuelve al reposo y levántalo otra vez.
- Mantén ambas manos visibles y evita movimientos bruscos. Si se pierde una mano, el sonido se detiene; al recuperarla, vuelve al reposo antes de tocar.
- La detección estima movimientos mediante la cámara; su precisión depende de la iluminación, la posición y la calibración.
