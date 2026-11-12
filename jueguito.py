
import pygame
import math
import random
import struct
import sys

# ==========================================
# JUEGUITO PLATAFORMERO
# Creado con Python + Pygame
# ==========================================

pygame.mixer.pre_init(22050, -16, 1, 512)
pygame.init()

# CONFIGURACION
ANCHO = 900
ALTO = 550
FPS = 60

pantalla = pygame.display.set_mode((ANCHO, ALTO))
pygame.display.set_caption("Jueguito Plataformero")

reloj = pygame.time.Clock()

# COLORES
AZUL = (100, 190, 255)
VERDE = (60, 180, 75)
VERDE_OSCURO = (30, 120, 50)
CAFÉ = (130, 80, 40)
AMARILLO = (255, 220, 30)
BLANCO = (255, 255, 255)
NEGRO = (25, 25, 35)
ROJO = (220, 50, 50)
NARANJA = (255, 140, 30)

fuente = pygame.font.SysFont("Arial", 26, bold=True)
fuente_grande = pygame.font.SysFont("Arial", 55, bold=True)
fuente_pequena = pygame.font.SysFont("Arial", 19)

# ==========================================
# MUSICA Y EFECTOS GENERADOS POR CODIGO
# ==========================================

def crear_sonido(frecuencia, duracion, volumen=0.3):
    """Genera un sonido cuadrado sin archivos externos."""
    if not pygame.mixer.get_init():
        return None

    frecuencia = max(1, frecuencia)
    frecuencia_muestreo = 22050
    muestras = int(frecuencia_muestreo * duracion)
    datos = bytearray()

    for i in range(muestras):
        t = i / frecuencia_muestreo
        onda = 1 if math.sin(2 * math.pi * frecuencia * t) > 0 else -1

        # Desvanecimiento para evitar clics
        envolvente = min(1, i / 150, (muestras - i) / 400)
        valor = int(32767 * volumen * onda * max(0, envolvente))
        datos.extend(struct.pack("<h", valor))

    return pygame.mixer.Sound(buffer=bytes(datos))


def crear_musica():
    """Crea una pequeña melodia retro de videojuego."""
    if not pygame.mixer.get_init():
        return None

    notas = [
        523, 659, 784, 659,
        523, 659, 880, 784,
        659, 784, 988, 784,
        659, 523, 587, 659
    ]

    frecuencia_muestreo = 22050
    duracion_nota = 0.16
    datos = bytearray()

    for nota in notas:
        cantidad = int(frecuencia_muestreo * duracion_nota)

        for i in range(cantidad):
            t = i / frecuencia_muestreo
            onda = 1 if math.sin(2 * math.pi * nota * t) > 0 else -1
            envolvente = max(0, 1 - i / cantidad)
            valor = int(5000 * onda * envolvente)
            datos.extend(struct.pack("<h", valor))

    return pygame.mixer.Sound(buffer=bytes(datos))


try:
    sonido_salto = crear_sonido(550, 0.15, 0.35)
    sonido_moneda = crear_sonido(1000, 0.12, 0.3)
    sonido_muerte = crear_sonido(160, 0.4, 0.35)
    sonido_golpe = crear_sonido(280, 0.12, 0.3)
    musica = crear_musica()

    if musica:
        musica.set_volume(0.18)
        musica.play(-1)

except pygame.error:
    sonido_salto = None
    sonido_moneda = None
    sonido_muerte = None
    sonido_golpe = None
    musica = None


def reproducir(sonido):
    if sonido:
        sonido.play()


# ==========================================
# MUNDO DEL JUEGO
# ==========================================

ANCHO_MUNDO = 2800
GRAVEDAD = 0.7
VELOCIDAD = 5
FUERZA_SALTO = -14

# Plataformas: x, y, ancho, alto
plataformas = [
    pygame.Rect(0, 490, 650, 60),
    pygame.Rect(750, 490, 550, 60),
    pygame.Rect(1400, 490, 550, 60),
    pygame.Rect(2100, 490, 700, 60),

    pygame.Rect(250, 400, 140, 25),
    pygame.Rect(480, 330, 140, 25),
    pygame.Rect(850, 390, 160, 25),
    pygame.Rect(1100, 320, 140, 25),
    pygame.Rect(1500, 390, 150, 25),
    pygame.Rect(1750, 310, 160, 25),
    pygame.Rect(2200, 390, 140, 25),
    pygame.Rect(2450, 320, 150, 25),
]

# Monedas
monedas = []

for x, y in [
    (280, 355), (330, 355), (520, 285),
    (580, 285), (900, 345), (960, 345),
    (1150, 275), (1200, 275), (1550, 345),
    (1800, 265), (1850, 265), (2250, 345),
    (2500, 275), (2550, 275), (2670, 440)
]:
    monedas.append(pygame.Rect(x, y, 20, 20))

# Enemigos
enemigos = [
    {"rect": pygame.Rect(400, 455, 35, 35), "vel": 2,
     "min": 350, "max": 620},
    {"rect": pygame.Rect(1000, 455, 35, 35), "vel": 2,
     "min": 800, "max": 1250},
    {"rect": pygame.Rect(1650, 455, 35, 35), "vel": 2,
     "min": 1450, "max": 1900},
    {"rect": pygame.Rect(2300, 455, 35, 35), "vel": 2,
     "min": 2150, "max": 2700},
]


# ==========================================
# PERSONAJE
# ==========================================

class Jugador:
    def __init__(self):
        self.rect = pygame.Rect(80, 420, 35, 55)
        self.vel_y = 0
        self.suelo = False
        self.vidas = 3
        self.puntos = 0
        self.invulnerable = 0
        self.direccion = 1

    def actualizar(self, teclas):
        # Movimiento horizontal
        dx = 0

        if teclas[pygame.K_LEFT] or teclas[pygame.K_a]:
            dx = -VELOCIDAD
            self.direccion = -1

        if teclas[pygame.K_RIGHT] or teclas[pygame.K_d]:
            dx = VELOCIDAD
            self.direccion = 1

        # Saltar
        if (teclas[pygame.K_SPACE] or teclas[pygame.K_UP]
                or teclas[pygame.K_w]) and self.suelo:
            self.vel_y = FUERZA_SALTO
            self.suelo = False
            reproducir(sonido_salto)

        # Movimiento horizontal y colisiones
        self.rect.x += dx

        for plataforma in plataformas:
            if self.rect.colliderect(plataforma):
                if dx > 0:
                    self.rect.right = plataforma.left
                elif dx < 0:
                    self.rect.left = plataforma.right

        self.rect.left = max(0, self.rect.left)
        self.rect.right = min(ANCHO_MUNDO, self.rect.right)

        # Gravedad
        self.vel_y += GRAVEDAD
        self.vel_y = min(self.vel_y, 14)

        self.rect.y += int(self.vel_y)
        self.suelo = False

        # Colisiones verticales
        for plataforma in plataformas:
            if self.rect.colliderect(plataforma):
                if self.vel_y > 0:
                    self.rect.bottom = plataforma.top
                    self.vel_y = 0
                    self.suelo = True

                elif self.vel_y < 0:
                    self.rect.top = plataforma.bottom
                    self.vel_y = 0

        # Caer fuera del mapa
        if self.rect.top > ALTO + 100:
            perder_vida()

        # Tiempo de invulnerabilidad
        if self.invulnerable > 0:
            self.invulnerable -= 1

    def dibujar(self, superficie, camara):
        x = self.rect.x - camara
        y = self.rect.y

        # Parpadeo después de recibir daño
        if self.invulnerable > 0 and self.invulnerable // 6 % 2:
            return

        # Cuerpo
        pygame.draw.rect(superficie, ROJO, (x, y + 18, 35, 37))

        # Cabeza
        pygame.draw.rect(superficie, (255, 190, 130),
                         (x + 3, y, 29, 25))

        # Gorra
        pygame.draw.rect(superficie, ROJO, (x, y, 35, 9))
        pygame.draw.rect(superficie, ROJO, (x - 3, y + 7, 38, 6))

        # Ojos
        pygame.draw.rect(superficie, NEGRO, (x + 22, y + 10, 4, 5))

        # Piernas
        pygame.draw.rect(superficie, (50, 50, 150),
                         (x + 3, y + 42, 12, 13))
        pygame.draw.rect(superficie, (50, 50, 150),
                         (x + 20, y + 42, 12, 13))


jugador = Jugador()

# ==========================================
# ESTADOS DEL JUEGO
# ==========================================

ESTADO_INICIO = 0
ESTADO_JUGANDO = 1
ESTADO_GAME_OVER = 2
ESTADO_VICTORIA = 3

estado = ESTADO_INICIO

camara = 0
particulas = []


def reiniciar():
    global jugador, enemigos, monedas, camara, particulas

    jugador = Jugador()
    camara = 0
    particulas = []

    monedas = [
        pygame.Rect(x, y, 20, 20)
        for x, y in [
            (280, 355), (330, 355), (520, 285),
            (580, 285), (900, 345), (960, 345),
            (1150, 275), (1200, 275), (1550, 345),
            (1800, 265), (1850, 265), (2250, 345),
            (2500, 275), (2550, 275), (2670, 440)
        ]
    ]

    enemigos = [
        {"rect": pygame.Rect(400, 455, 35, 35), "vel": 2,
         "min": 350, "max": 620},
        {"rect": pygame.Rect(1000, 455, 35, 35), "vel": 2,
         "min": 800, "max": 1250},
        {"rect": pygame.Rect(1650, 455, 35, 35), "vel": 2,
         "min": 1450, "max": 1900},
        {"rect": pygame.Rect(2300, 455, 35, 35), "vel": 2,
         "min": 2150, "max": 2700},
    ]


def perder_vida():
    global estado

    if jugador.invulnerable > 0:
        return

    jugador.vidas -= 1
    jugador.invulnerable = 100
    reproducir(sonido_muerte)

    if jugador.vidas <= 0:
        estado = ESTADO_GAME_OVER
    else:
        jugador.rect.x = max(80, jugador.rect.x - 100)
        jugador.rect.y = 350
        jugador.vel_y = 0


# ==========================================
# DIBUJAR EL ESCENARIO
# ==========================================

def dibujar_fondo():
    pantalla.fill(AZUL)

    # Sol
    pygame.draw.circle(pantalla, AMARILLO, (760, 90), 45)

    # Nubes
    for x, y in [(100, 90), (350, 140), (600, 65), (820, 180)]:
        pygame.draw.circle(pantalla, BLANCO, (x, y), 22)
        pygame.draw.circle(pantalla, BLANCO, (x + 25, y), 28)
        pygame.draw.circle(pantalla, BLANCO, (x + 50, y), 20)

    # Montañas decorativas
    for x in range(-100, ANCHO + 150, 220):
        pygame.draw.circle(pantalla, (90, 200, 110),
                           (x - int(camara * 0.25), 500), 130)


def dibujar_mundo():
    # Plataformas
    for p in plataformas:
        x = p.x - camara

        if x < -200 or x > ANCHO + 200:
            continue

        pygame.draw.rect(pantalla, CAFÉ,
                         (x, p.y, p.width, p.height))
        pygame.draw.rect(pantalla, VERDE,
                         (x, p.y, p.width, 9))

    # Monedas
    for moneda in monedas:
        x = moneda.x - camara
        pygame.draw.circle(pantalla, AMARILLO,
                           (x + 10, moneda.y + 10), 10)
        pygame.draw.circle(pantalla, NARANJA,
                           (x + 10, moneda.y + 10), 5)

    # Enemigos
    for enemigo in enemigos:
        r = enemigo["rect"]
        x = r.x - camara

        pygame.draw.ellipse(pantalla, (150, 70, 40),
                            (x, r.y + 5, r.width, r.height - 5))
        pygame.draw.circle(pantalla, BLANCO, (x + 11, r.y + 14), 5)
        pygame.draw.circle(pantalla, BLANCO, (x + 25, r.y + 14), 5)
        pygame.draw.circle(pantalla, NEGRO, (x + 11, r.y + 14), 2)
        pygame.draw.circle(pantalla, NEGRO, (x + 25, r.y + 14), 2)

    # Meta
    meta_x = 2700 - camara
    pygame.draw.rect(pantalla, BLANCO, (meta_x, 370, 8, 120))
    pygame.draw.polygon(
        pantalla, ROJO,
        [(meta_x + 8, 370), (meta_x + 65, 390),
         (meta_x + 8, 410)]
    )


# ==========================================
# INTERFAZ
# ==========================================

def dibujar_interfaz():
    pygame.draw.rect(pantalla, NEGRO, (10, 10, 260, 85),
                     border_radius=12)

    pantalla.blit(
        fuente.render(f"Monedas: {jugador.puntos}", True, AMARILLO),
        (25, 18)
    )

    pantalla.blit(
        fuente.render(f"Vidas: {jugador.vidas}", True, BLANCO),
        (25, 52)
    )

    texto = fuente_pequena.render(
        "ESC: Salir  |  M: Musica ON/OFF", True, BLANCO
    )
    pantalla.blit(texto, (ANCHO - 300, 15))


def texto_centrado(texto, y, tipografia, color=BLANCO):
    imagen = tipografia.render(texto, True, color)
    pantalla.blit(imagen, imagen.get_rect(center=(ANCHO // 2, y)))


def dibujar_inicio():
    dibujar_fondo()

    pygame.draw.rect(pantalla, NEGRO, (120, 110, 660, 340),
                     border_radius=25)

    texto_centrado("JUEGUITO PLATAFORMERO", 175,
                   fuente_grande, AMARILLO)

    texto_centrado("¡Una aventura pixelada!", 240, fuente)

    texto_centrado("Flechas o A/D = Moverse", 310, fuente)
    texto_centrado("ESPACIO / W / ARRIBA = Saltar", 350, fuente)

    texto_centrado("Presiona ENTER para comenzar", 415,
                   fuente, VERDE)


def dibujar_final(titulo, subtitulo, color):
    dibujar_fondo()

    pygame.draw.rect(pantalla, NEGRO, (120, 130, 660, 290),
                     border_radius=25)

    texto_centrado(titulo, 205, fuente_grande, color)
    texto_centrado(subtitulo, 280, fuente)
    texto_centrado(
        f"Monedas conseguidas: {jugador.puntos}",
        330, fuente
    )
    texto_centrado("ENTER para volver a jugar", 380,
                   fuente, AMARILLO)


# ==========================================
# BUCLE PRINCIPAL
# ==========================================

ejecutando = True

while ejecutando:

    reloj.tick(FPS)

    # EVENTOS
    for evento in pygame.event.get():

        if evento.type == pygame.QUIT:
            ejecutando = False

        if evento.type == pygame.KEYDOWN:

            if evento.key == pygame.K_ESCAPE:
                ejecutando = False

            if evento.key == pygame.K_m:
                if musica:
                    if pygame.mixer.Channel(0).get_busy():
                        musica.stop()
                    else:
                        musica.play(-1)

            if evento.key == pygame.K_RETURN:

                if estado in (ESTADO_INICIO,
                              ESTADO_GAME_OVER,
                              ESTADO_VICTORIA):

                    reiniciar()
                    estado = ESTADO_JUGANDO

    teclas = pygame.key.get_pressed()

    # --------------------------------------
    # PANTALLA DE INICIO
    # --------------------------------------

    if estado == ESTADO_INICIO:
        dibujar_inicio()

    # --------------------------------------
    # PARTIDA
    # --------------------------------------

    elif estado == ESTADO_JUGANDO:

        jugador.actualizar(teclas)

        # Cámara
        camara = jugador.rect.centerx - ANCHO // 2
        camara = max(0, min(camara, ANCHO_MUNDO - ANCHO))

        # Enemigos
        for enemigo in enemigos[:]:
            r = enemigo["rect"]
            r.x += enemigo["vel"]

            if r.x < enemigo["min"] or r.x > enemigo["max"]:
                enemigo["vel"] *= -1

            if jugador.rect.colliderect(r):

                # Saltar encima del enemigo
                if jugador.vel_y > 0 and jugador.rect.bottom - r.top < 22:
                    jugador.rect.bottom = r.top
                    jugador.vel_y = -9
                    enemigos.remove(enemigo)
                    jugador.puntos += 100
                    reproducir(sonido_golpe)

                else:
                    perder_vida()

        # Recoger monedas
        for moneda in monedas[:]:
            if jugador.rect.colliderect(moneda):
                monedas.remove(moneda)
                jugador.puntos += 50
                reproducir(sonido_moneda)

        # Llegar a la meta
        if jugador.rect.colliderect(
            pygame.Rect(2700, 370, 80, 120)
        ):
            estado = ESTADO_VICTORIA

        # Dibujar todo
        dibujar_fondo()
        dibujar_mundo()
        jugador.dibujar(pantalla, camara)
        dibujar_interfaz()

    # --------------------------------------
    # GAME OVER
    # --------------------------------------

    elif estado == ESTADO_GAME_OVER:
        dibujar_final(
            "GAME OVER",
            "¡No te rindas, vuelve a intentarlo!",
            ROJO
        )

    # --------------------------------------
    # VICTORIA
    # --------------------------------------

    elif estado == ESTADO_VICTORIA:
        dibujar_final(
            "¡GANASTE!",
            "¡Has llegado a la meta!",
            AMARILLO
        )

    pygame.display.flip()


# ==========================================
# CERRAR JUEGO
# ==========================================

pygame.quit()
sys.exit()
