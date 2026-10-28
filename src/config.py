# Opciones comunes de la aplicación.
# Cambia estos valores para ajustar la presentación y la salida.

# Tamaño del lienzo donde se dibuja la interfaz, en píxeles.
# El diseño actual está preparado para estas dimensiones.
ANCHO = 1100
ALTO = 700
NOMBRE_VENTANA = "Piano mediante gestos"

# Colores en formato BGR: azul, verde y rojo (de 0 a 255).
FONDO = (24, 24, 24)
PANEL = (38, 38, 38)
BORDE = (65, 65, 65)
BLANCO = (240, 240, 240)
GRIS = (185, 185, 185)
AZUL = (235, 175, 85)

# Escala de los textos: el título es más grande.
TAMANO_TEXTO = 0.65
TAMANO_TITULO = 1.1

# Espera entre actualizaciones y código de la tecla ESC.
# La espera no incluye el tiempo que tarde en procesarse cada imagen.
ESPERA_MS = 1
TECLA_SALIR = 27

# Opciones para conectar los módulos.
CAMARA_INDICE = 0
# Reflejar solo la imagen mostrada; el detector recibe el original.
ESPEJO = True
# Un estado debe mantenerse este tiempo para aceptarlo como estable.
VENTANA_ESTABILIDAD_MS = 60
# La imagen se analiza cada ciclo; la estabilidad se controla aparte.
TECLA_CALIBRAR = ord("c")
CALIBRACION_SEGUNDOS = 5
CALIBRACION_MUESTREO_MS = 1000
CALIBRACION_MIN_MUESTRAS = 5
# Fraccion del recorrido aprendido: levantar activa; volver al reposo libera.
GESTO_ACTIVACION = 0.65
GESTO_LIBERACION = 0.35
GESTO_RECORRIDO_MINIMO = 0.08
GESTO_TOLERANCIA_LATERAL = 0.35
PESO_PROFUNDIDAD = 0.5
