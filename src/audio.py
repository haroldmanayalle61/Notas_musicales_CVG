# Parte de Hirano
# Carga los audios y reproduce cada activación musical una sola vez.


# SECCIÓN 1: Importar las herramientas y el estado musical

import math
from pathlib import Path

from contracts import MusicState
from music import combinaciones_musicales, nombre_archivo


# SECCIÓN 2: Localizar la carpeta de los audios

RUTA_NOTAS = Path(__file__).resolve().parent / "assets" / "notes"


class AudioPlayer:

    # SECCIÓN 3: Preparar el reproductor y cargar los sonidos

    def __init__(
        self,
        notes_dir: str | Path | None = None,
        volume: float = 0.5
    ):
        # Comprobar el volumen.
        if (
            isinstance(volume, bool)
            or not isinstance(volume, (int, float))
            or not math.isfinite(volume)
            or not 0 <= volume <= 1
        ):
            raise ValueError("El volumen debe estar entre 0 y 1.")

        carpeta = RUTA_NOTAS if notes_dir is None else Path(notes_dir)

        rutas = {
            combinacion: carpeta / nombre_archivo(*combinacion)
            for combinacion in combinaciones_musicales()
        }

        # Comprobar que estén los 28 archivos.
        faltantes = [
            ruta.name
            for ruta in rutas.values()
            if not ruta.is_file()
        ]

        if faltantes:
            raise FileNotFoundError(
                f"Faltan audios en {carpeta}: {', '.join(faltantes)}. "
                "Coloca los archivos WAV descargados en src/assets/notes/."
            )

        try:
            import pygame
        except ImportError as error:
            raise RuntimeError(
                "Instala pygame con el requirements.txt del equipo."
            ) from error

        self._mixer = pygame.mixer
        self._canal = None
        self._sonidos = {}
        self._seleccion = None
        self._cerrado = False
        self._iniciado_aqui = self._mixer.get_init() is None

        try:
            # Iniciar el audio una sola vez.
            if self._iniciado_aqui:
                try:
                    self._mixer.init(
                        frequency=44100,
                        size=-16,
                        channels=2,
                        buffer=512
                    )
                except pygame.error as error:
                    raise RuntimeError(
                        "No se pudo iniciar el dispositivo de audio."
                    ) from error

            self._canal = self._mixer.find_channel()

            if self._canal is None:
                raise RuntimeError("No hay un canal de audio libre.")

            # Cargar los sonidos una sola vez.
            for combinacion, ruta in rutas.items():
                try:
                    sonido = self._mixer.Sound(file=str(ruta))
                except pygame.error as error:
                    raise RuntimeError(
                        f"No se pudo cargar el audio {ruta.name}."
                    ) from error

                sonido.set_volume(volume)
                self._sonidos[combinacion] = sonido

        except Exception:
            self.close()
            raise

    # SECCIÓN 4: Reproducir los cambios de nota y octava

    def update(self, estado: MusicState) -> None:
        if self._cerrado:
            raise RuntimeError("El reproductor de audio esta cerrado.")

        if not isinstance(estado, MusicState):
            self._silenciar()
            raise TypeError(
                "AudioPlayer.update necesita un MusicState."
            )

        # Detener cuando la entrada sea inválida o indique silencio.
        if estado.valid is not True or estado.note is None:
            self._silenciar()
            return

        try:
            nombre_archivo(estado.note, estado.octave)
        except ValueError:
            self._silenciar()
            raise

        seleccion = (estado.note, estado.octave)

        # Mantener el mismo gesto no reinicia el sonido.
        if seleccion == self._seleccion:
            return

        self._silenciar()

        self._canal.play(
            self._sonidos[seleccion],
            loops=0
        )

        self._seleccion = seleccion

    # SECCIÓN 5: Detener la nota actual

    def _silenciar(self) -> None:
        if self._seleccion is not None and self._canal is not None:
            self._canal.stop()

        self._seleccion = None

    # SECCIÓN 6: Cerrar el reproductor

    def close(self) -> None:
        if self._cerrado:
            return

        self._cerrado = True

        try:
            if self._canal is not None:
                self._canal.stop()
        finally:
            self._seleccion = None
            self._sonidos.clear()

            if self._iniciado_aqui and self._mixer.get_init() is not None:
                self._mixer.quit()


# SECCIÓN 7: Probar los audios al ejecutar este archivo directamente

if __name__ == "__main__":
    reproductor = AudioPlayer()

    try:
        print("Escribe DO3, RE4, MI5, SI6, SILENCIO o SALIR.")

        while True:
            entrada = input("Nota: ").strip().upper()

            if entrada == "SALIR":
                break

            if entrada in ("", "SILENCIO"):
                reproductor.update(MusicState(valid=True))
                continue

            try:
                nota = entrada[:-1]
                octava = int(entrada[-1])

                reproductor.update(
                    MusicState(True, nota, octava)
                )

            except ValueError:
                reproductor.update(MusicState(valid=True))
                print(
                    "Usa una nota de DO a SI y una octava de 3 a 6."
                )

    except (KeyboardInterrupt, EOFError):
        pass

    finally:
        reproductor.close()