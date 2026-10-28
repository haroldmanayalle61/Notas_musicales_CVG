"""Formatos de información compartidos por el equipo.
Andrea entrega HandObservation; Piero entrega FingerState;
Hirano entrega MusicState; Harold recibe estos datos para mostrarlos.
Este archivo no detecta manos, interpreta gestos ni reproduce sonidos.
Los tipos indican qué datos esperamos; no los validan automáticamente.
"""

from dataclasses import dataclass, field
from typing import Literal


@dataclass
class HandObservation:
    """Una mano detectada por Andrea.

    side: "Left" para izquierda o "Right" para derecha de la persona.
    Andrea debe mantener esta identificación al usar imagen en espejo.
    points: 21 puntos en el orden de MediaPipe, cada uno como (x, y, z).
    Se conservan las coordenadas normalizadas de MediaPipe, no píxeles:
    x e y se expresan respecto al tamaño de imagen; z indica profundidad
    relativa y no representa una distancia en metros.
    Si no hay manos, vision.py devuelve una lista vacía [], no una mano
    inventada con puntos en cero. La lista tendrá como máximo dos manos.
    """

    side: Literal["Left", "Right"]
    points: list[tuple[float, float, float]]


@dataclass
class FingerState:
    """Estado de los dedos calculado por Piero.

    left y right contienen cinco valores, en este orden:
    [pulgar, índice, medio, anular, meñique].
    True = dedo levantado (activo); False = extendido en reposo.
    Levantado indica desplazamiento respecto a la postura de reposo, no
    simplemente tener el dedo recto. Se guardan dos poses con C: primero
    cinco segundos en reposo y luego cinco segundos con los dedos levantados,
    manteniendo las palmas quietas. gestures.py aprende el recorrido de cada
    punta relativo a la palma. La camara no mide contacto con una mesa.
    Antes de calibrar ambas poses, se entrega valid=False.

    Siete dedos producen DO, RE, MI, FA, SOL, LA y SI al levantarlos;
    al volver al reposo se suelta la nota. Mantener el gesto no repite el
    sonido; para repetir hay que volver al reposo y levantar otra vez.
    Sin dedos musicales activos hay silencio. Con varios tambien: esta
    version permite una sola nota a la vez.

    Los tres dedos restantes de la derecha eligen octava por cantidad
    de dedos levantados: 0, 1, 2 o 3 seleccionan las octavas 3, 4, 5 o 6.
    Cambiar octava no produce sonido por si solo. music.py define el reparto.

    valid solo será True si ambas manos están disponibles y el estado
    se puede interpretar. False significa dato no válido, no una octava
    ni una combinación de dedos. Al perder una mano se entrega valid=False
    para que el programa guarde silencio. El estabilizador conserva
    este mismo formato.
    """

    valid: bool = False
    left: list[bool] = field(default_factory=lambda: [False] * 5)
    right: list[bool] = field(default_factory=lambda: [False] * 5)


@dataclass
class MusicState:
    """Resultado musical elegido por Hirano.

    valid indica si la entrada se pudo interpretar correctamente.
    note: DO, RE, MI, FA, SOL, LA o SI; None indica silencio.
    octave: número de octava musical seleccionado, según el acuerdo del
    equipo. Se puede conservar aunque no esté sonando ninguna nota para
    mostrarlo en pantalla. None indica que no hay una selección válida.
    reason: mensaje breve que Harold puede mostrar en pantalla.

    Silencio normal: valid=True, note=None y octave seleccionada.
    Entrada no válida: valid=False, note=None y octave=None.
    Si valid=False o note=None, audio.py debe detener el sonido.
    La selección de notas y octavas se implementa en music.py.
    """

    valid: bool = False
    note: Literal["DO", "RE", "MI", "FA", "SOL", "LA", "SI"] | None = None
    octave: int | None = None
    reason: str = "Esperando manos"
