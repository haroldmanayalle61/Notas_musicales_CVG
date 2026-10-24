import cv2
import numpy as np
import unicodedata

from config import (
    ANCHO, ALTO, NOMBRE_VENTANA,
    FONDO, PANEL, BORDE, BLANCO, GRIS, AZUL,
    TAMANO_TEXTO, TAMANO_TITULO,
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


def crear_pantalla(nota="DO", octava=3, estado="Esperando cámara"):
    """Construye la pantalla inicial con datos de demostración."""

    pantalla = np.full((ALTO, ANCHO, 3), FONDO, dtype=np.uint8)

    # Encabezado
    escribir_texto(pantalla,"PIANO MEDIANTE GESTOS",(40, 65),titulo=True)

    escribir_texto(pantalla,"Reconocimiento de manos y notas musicales",(40, 105),GRIS)

    cv2.line(pantalla, (40, 130), (1060, 130), BORDE, 1)

    # Panel izquierdo: espacio reservado para la cámara
    cv2.rectangle(pantalla, (40, 160), (720, 570), PANEL, -1)

    cv2.rectangle(pantalla, (40, 160), (720, 570), BORDE, 1)

    escribir_texto(pantalla, "CAMARA", (65, 200), AZUL)

    escribir_centrado(pantalla, "La imagen de la camara aparecera aqui", 380, 355)

    escribir_centrado(pantalla, "Pendiente de conectar la deteccion de manos", 380, 395)

    # Panel derecho: información musical
    cv2.rectangle(pantalla, (750, 160), (1060, 570), PANEL, -1)

    cv2.rectangle(pantalla, (750, 160), (1060, 570), BORDE, 1)

    escribir_texto(pantalla, "INFORMACION MUSICAL", (775, 200), AZUL)

    cv2.line(pantalla, (775, 225), (1035, 225), BORDE, 1)

    escribir_texto(pantalla, "Nota seleccionada", (775, 275), GRIS)

    escribir_texto(pantalla, str(nota), (775, 315))

    cv2.line(pantalla, (775, 345), (1035, 345), BORDE, 1)

    escribir_texto(pantalla, "Octava seleccionada", (775, 395), GRIS)

    escribir_texto(pantalla, str(octava), (775, 435))

    escribir_texto(pantalla, "Modo demostracion", (775, 530), AZUL)

    # Estado del programa
    escribir_texto(pantalla, f"Estado: {estado}", (40, 615))

    cv2.line(pantalla, (40, 640), (1060, 640), BORDE, 1)

    # Pie de la ventana
    escribir_texto(pantalla, "ESC: salir", (40, 675), GRIS)

    return pantalla


def mostrar_pantalla(pantalla):
    cv2.imshow(NOMBRE_VENTANA, pantalla)