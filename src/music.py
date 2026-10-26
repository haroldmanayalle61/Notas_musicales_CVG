# Parte de Hirano
# Convierte el estado de los dedos en una nota musical y una octava.


# SECCIÓN 1: Importar los formatos compartidos

from contracts import FingerState, MusicState


# SECCIÓN 2: Definir las notas y octavas disponibles

NOTAS = ("DO", "RE", "MI", "FA", "SOL", "LA", "SI")
OCTAVAS = (3, 4, 5, 6)


# SECCIÓN 3: Relacionar las notas con las letras de los audios

SIMBOLOS = dict(zip(
    NOTAS,
    ("C", "D", "E", "F", "G", "A", "B")
))


# SECCIÓN 4: Asignar una nota a cada dedo musical
# Cada fila contiene: mano, posición del dedo y nota.

DEDOS_NOTAS = (
    ("left", 0, "DO"),
    ("left", 1, "RE"),
    ("left", 2, "MI"),
    ("left", 3, "FA"),
    ("left", 4, "SOL"),
    ("right", 0, "LA"),
    ("right", 1, "SI"),
)


# SECCIÓN 5: Definir los dedos que seleccionan la octava

DEDOS_OCTAVA = (2, 3, 4)


# SECCIÓN 6: Obtener el nombre del archivo de una nota

def nombre_archivo(nota: str, octava: int) -> str:
    if not isinstance(nota, str) or nota not in SIMBOLOS:
        raise ValueError(f"Nota no admitida: {nota!r}.")

    if type(octava) is not int or octava not in OCTAVAS:
        raise ValueError(f"Octava no admitida: {octava!r}; usa {OCTAVAS}.")

    return f"{SIMBOLOS[nota]}{octava}.wav"


# SECCIÓN 7: Enumerar las 28 combinaciones musicales

def combinaciones_musicales() -> tuple[tuple[str, int], ...]:
    return tuple(
        (nota, octava)
        for octava in OCTAVAS
        for nota in NOTAS
    )


# SECCIÓN 8: Interpretar los dedos y elegir la nota

class MusicEngine:
    def resolve(self, estado: FingerState) -> MusicState:

        # Comprobar que recibimos un estado válido.
        if not isinstance(estado, FingerState) or estado.valid is not True:
            return MusicState(reason="Estado de manos no valido")

        # Cada mano debe contener cinco valores booleanos.
        for mano in (estado.left, estado.right):
            if not isinstance(mano, (list, tuple)) or len(mano) != 5:
                return MusicState(
                    reason="Se necesitan cinco estados por mano"
                )

            if not all(type(dedo) is bool for dedo in mano):
                return MusicState(
                    reason="Los estados deben ser True o False"
                )

        # Contar los dedos derechos que controlan la octava.
        cantidad_control = sum(
            estado.right[indice]
            for indice in DEDOS_OCTAVA
        )

        octava = OCTAVAS[cantidad_control]

        # Buscar los dedos musicales que están activos.
        notas_activas = []

        for mano, indice, nota in DEDOS_NOTAS:
            dedos = estado.left if mano == "left" else estado.right

            if dedos[indice]:
                notas_activas.append(nota)

        # Sin dedos musicales activos, producir silencio.
        if not notas_activas:
            return MusicState(True, None, octava, "Silencio")

        # La primera versión permite una sola nota simultánea.
        if len(notas_activas) > 1:
            return MusicState(
                True,
                None,
                octava,
                "Varias notas: baja un solo dedo"
            )

        nota = notas_activas[0]

        return MusicState(True, nota, octava, f"{nota}{octava}")