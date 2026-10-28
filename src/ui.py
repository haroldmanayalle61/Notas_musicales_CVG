import cv2
import numpy as np
import unicodedata

from config import (
    ANCHO, ALTO, NOMBRE_VENTANA,
    FONDO, PANEL, BORDE, BLANCO, GRIS, AZUL,
    TAMANO_TEXTO, TAMANO_TITULO, ESPEJO,
)

FUENTE = cv2.FONT_HERSHEY_SIMPLEX


def escribir_texto(imagen, texto, posicion, color=BLANCO, titulo=False):
    """Dibuja texto con un tamaño común, excepto para el título."""

    # La fuente de OpenCV no representa bien las tildes.
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = texto.encode("ascii", "ignore").decode("ascii")

    tamano = TAMANO_TITULO if titulo else TAMANO_TEXTO
    grosor = 2 if titulo else 1
    cv2.putText(imagen,texto,posicion,FUENTE,tamano,color,grosor,cv2.LINE_AA)


def escribir_centrado(imagen, texto, centro_x, posicion_y, color=GRIS):
    """Centra horizontalmente un texto."""

    (ancho_texto, _), _ = cv2.getTextSize(texto, FUENTE, TAMANO_TEXTO, 1)
    posicion_x = int(centro_x - ancho_texto / 2)
    escribir_texto(imagen, texto, (posicion_x, posicion_y), color)


def _dibujar_camara(pantalla, frame, hands, fingers=None):
    """Muestra una copia de la cámara y refleja también los puntos al dibujar."""
    alto, ancho = frame.shape[:2]
    escala = min(640 / ancho, 330 / alto)
    ancho_visible = max(1, min(640, round(ancho * escala)))
    alto_visible = max(1, min(330, round(alto * escala)))
    imagen = cv2.resize(frame, (ancho_visible, alto_visible), interpolation=cv2.INTER_AREA)
    if ESPEJO:
        imagen = cv2.flip(imagen, 1)

    conexiones = (
        (0, 1), (1, 2), (2, 3), (3, 4),
        (0, 5), (5, 6), (6, 7), (7, 8),
        (5, 9), (9, 10), (10, 11), (11, 12),
        (9, 13), (13, 14), (14, 15), (15, 16),
        (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),
    )
    for hand in hands:
        if len(hand.points) != 21:
            continue
        puntos = []
        for x, y, _ in hand.points:
            # Reflejar la posición visual conserva Left/Right del detector.
            x = 1.0 - x if ESPEJO else x
            puntos.append((
                int(np.clip(x, 0, 1) * (ancho_visible - 1)),
                int(np.clip(y, 0, 1) * (alto_visible - 1)),
            ))
        for inicio, fin in conexiones:
            cv2.line(imagen, puntos[inicio], puntos[fin], GRIS, 1, cv2.LINE_AA)
        for punto in puntos:
            cv2.circle(imagen, punto, 3, BLANCO, -1, cv2.LINE_AA)

        estados = None
        if fingers is not None and fingers.valid:
            estados = fingers.left if hand.side == "Left" else fingers.right
        if estados is not None:
            for index, tip in enumerate((4, 8, 12, 16, 20)):
                if estados[index]:
                    cv2.circle(imagen, puntos[tip], 7, AZUL, -1, cv2.LINE_AA)

        # Las etiquetas se dibujan después del espejo para que sean legibles.
        etiqueta = "Izquierda" if hand.side == "Left" else "Derecha"
        (ancho_texto, _), _ = cv2.getTextSize(etiqueta, FUENTE, TAMANO_TEXTO, 1)
        x_texto = max(0, min(min(x for x, _ in puntos), ancho_visible - ancho_texto))
        y_texto = max(24, min(min(y for _, y in puntos) - 10, alto_visible - 6))
        escribir_texto(imagen, etiqueta, (x_texto, y_texto), AZUL)

    x_panel = 60 + (640 - ancho_visible) // 2
    y_panel = 220 + (330 - alto_visible) // 2
    pantalla[y_panel:y_panel + alto_visible, x_panel:x_panel + ancho_visible] = imagen


def crear_pantalla(
    nota=None, octava=None, estado="Esperando cámara", *, frame=None, hands=None,
    fingers=None, calibrado=False, contador=None,
):
    """Construye la pantalla con la cámara y los resultados reales."""

    pantalla = np.full((ALTO, ANCHO, 3), FONDO, dtype=np.uint8)

    # Encabezado
    escribir_texto(pantalla,"PIANO MEDIANTE GESTOS",(40, 65),titulo=True)

    escribir_texto(pantalla,"Reconocimiento de manos y notas musicales",(40, 105),GRIS)

    cv2.line(pantalla, (40, 130), (1060, 130), BORDE, 1)

    # Panel izquierdo: cámara con puntos y etiquetas de las manos
    cv2.rectangle(pantalla, (40, 160), (720, 570), PANEL, -1)

    cv2.rectangle(pantalla, (40, 160), (720, 570), BORDE, 1)

    escribir_texto(pantalla, "CAMARA", (65, 200), AZUL)

    if frame is not None:
        _dibujar_camara(pantalla, frame, hands or [], fingers)
    else:
        escribir_centrado(pantalla, "Esperando imagen de la camara", 380, 355)

    # Panel derecho: información musical
    cv2.rectangle(pantalla, (750, 160), (1060, 570), PANEL, -1)

    cv2.rectangle(pantalla, (750, 160), (1060, 570), BORDE, 1)

    escribir_texto(pantalla, "INFORMACION MUSICAL", (775, 200), AZUL)

    cv2.line(pantalla, (775, 225), (1035, 225), BORDE, 1)

    escribir_texto(pantalla, "Nota seleccionada", (775, 275), GRIS)

    escribir_texto(pantalla, nota if nota is not None else "--", (775, 315))

    cv2.line(pantalla, (775, 345), (1035, 345), BORDE, 1)

    escribir_texto(pantalla, "Octava seleccionada", (775, 395), GRIS)

    escribir_texto(pantalla, str(octava) if octava is not None else "--", (775, 435))

    escribir_texto(
        pantalla, (f"Calibrando: {contador} s" if contador is not None else
         "Gestos preparados" if calibrado else "Pendiente: pulsa C"),
        (775, 530), AZUL,
    )

    # Estado del programa
    escribir_texto(pantalla, f"Estado: {estado}", (40, 615))

    cv2.line(pantalla, (40, 640), (1060, 640), BORDE, 1)

    # Pie de la ventana
    escribir_texto(pantalla, "C: calibrar (5 s reposo + 5 s levantados) | ESC/X: salir", (40, 675), GRIS)

    return pantalla


def mostrar_pantalla(pantalla):
    cv2.imshow(NOMBRE_VENTANA, pantalla)