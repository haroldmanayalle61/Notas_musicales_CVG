import cv2
from ui import crear_pantalla, mostrar_pantalla
from config import ESPERA_MS, TECLA_SALIR

def main():
    try:
        while True:
            pantalla = crear_pantalla()
            mostrar_pantalla(pantalla)

            # Espera brevemente y comprueba si presionaste ESC.
            if cv2.waitKey(ESPERA_MS) & 0xFF == TECLA_SALIR:
                break
    finally:
        # Cierra las ventanas, incluso si ocurre un error.
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()