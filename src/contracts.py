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
    True = dedo abajo (activo); False = dedo arriba (en reposo).
    IMPORTANTE: este acuerdo sustituye al anterior de extendido/doblado.
    Un dedo puede bajar sin flexionarse mucho. Piero compara su posición
    con una referencia de reposo, no solo el ángulo de sus articulaciones.
    Abajo no significa necesariamente una coordenada y mayor en la imagen:
    depende de la cámara. Se necesita una referencia inicial y distinguir
    el movimiento del dedo del movimiento de toda la mano.
    La referencia y los umbrales se implementan en gestures.py; mientras
    no exista una referencia utilizable, se entrega valid=False.
    No se afirma que haya contacto físico con la mesa.

    Siete dedos se asignan a DO, RE, MI, FA, SOL, LA y SI:
    - Arriba: no activan su nota.
    - Al bajar: activan su nota; al subir, la sueltan.
    - Mantener el dedo abajo no genera pulsaciones repetidas por imagen.
    - Para repetir la misma nota, hay que subir el dedo y volver a bajarlo.
    Sin dedos musicales abajo hay silencio. Si hay más de uno, por ahora
    también hay silencio: la primera versión toca una sola nota a la vez.

    Los otros tres dedos seleccionan la octava por cantidad de dedos abajo:
    0 = primera disponible, 1 = segunda, 2 = tercera, 3 = cuarta.
    La octava se mantiene mientras se conserve esa combinación; al cambiar
    la cantidad, cambia la selección. Seleccionar octava no dispara sonido
    por sí solo. El reparto de dedos y las cuatro octavas musicales
    concretas se acuerdan en equipo y se definen en music.py/config.py.
    No confundir primera octava disponible con la octava musical número 1.

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
