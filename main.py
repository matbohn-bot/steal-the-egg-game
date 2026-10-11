import math
import pygame
import sys

# -----------------------------
# CONSTANTES
# -----------------------------
WIDTH, HEIGHT = 960, 640
FPS = 60

# Couleurs
BG = (18, 24, 36)
WALL = (60, 78, 94)
PLAYER = (105, 200, 255)
GUARD = (235, 90, 90)
EGG = (255, 220, 110)
EXIT = (120, 220, 120)
TEXT = (245, 245, 245)
DARK = (25, 30, 35)

# -----------------------------
# CLASSES
# -----------------------------
class Player:
    def __init__(self, x, y):
        self.rect = pygame.Rect(x, y, 28, 28)
        self.speed = 190
        self.has_egg = False

    def move(self, dx, dy, walls):
        # Mouvement horizontal
        self.rect.x += dx
        for wall in walls:
            if self.rect.colliderect(wall):
                if dx > 0:
                    self.rect.right = wall.left
                elif dx < 0:
                    self.rect.left = wall.right

        # Mouvement vertical
        self.rect.y += dy
        for wall in walls:
            if self.rect.colliderect(wall):
                if dy > 0:
                    self.rect.bottom = wall.top
                elif dy < 0:
                    self.rect.top = wall.bottom

    def update(self, keys, walls):
        dx = 0
        dy = 0

        if keys[pygame.K_z] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
            dy += 1
        if keys[pygame.K_q] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1

        if dx != 0 and dy != 0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length

        self.move(dx * self.speed / FPS, dy * self.speed / FPS, walls)


class Guard:
    def __init__(self, x, y, w, h, patrol_a, patrol_b, speed=90):
        self.rect = pygame.Rect(x, y, w, h)
        self.patrol_a = patrol_a
        self.patrol_b = patrol_b
        self.speed = speed
        self.axis = "x" if abs(patrol_b[0] - patrol_a[0]) > abs(patrol_b[1] - patrol_a[1]) else "y"
        self.direction = 1
        self.chasing = False
        self.detect_radius = 170
        self.patrol_pos = 0

    def patrol_update(self, walls):
        if self.axis == "x":
            self.rect.x += self.direction * self.speed / FPS
            if self.rect.x <= min(self.patrol_a[0], self.patrol_b[0]):
                self.rect.x = min(self.patrol_a[0], self.patrol_b[0])
                self.direction = 1
            if self.rect.x >= max(self.patrol_a[0], self.patrol_b[0]):
                self.rect.x = max(self.patrol_a[0], self.patrol_b[0])
                self.direction = -1
        else:
            self.rect.y += self.direction * self.speed / FPS
            if self.rect.y <= min(self.patrol_a[1], self.patrol_b[1]):
                self.rect.y = min(self.patrol_a[1], self.patrol_b[1])
                self.direction = 1
            if self.rect.y >= max(self.patrol_a[1], self.patrol_b[1]):
                self.rect.y = max(self.patrol_a[1], self.patrol_b[1])
                self.direction = -1

    def update(self, player, walls, dt):
        dx = player.rect.centerx - self.rect.centerx
        dy = player.rect.centery - self.rect.centery
        distance = math.hypot(dx, dy)

        if distance < self.detect_radius:
            self.chasing = True
        else:
            self.chasing = False

        if self.chasing:
            move_x = dx / (distance if distance else 1)
            move_y = dy / (distance if distance else 1)
            self.rect.x += move_x * self.speed * dt
            self.rect.y += move_y * self.speed * dt

            for wall in walls:
                if self.rect.colliderect(wall):
                    self.rect.x -= move_x * self.speed * dt
                    self.rect.y -= move_y * self.speed * dt
        else:
            self.patrol_update(walls)


class Egg:
    def __init__(self, x, y, radius=12):
        self.x = x
        self.y = y
        self.radius = radius
        self.picked = False

    def draw(self, screen):
        if not self.picked:
            pygame.draw.circle(screen, EGG, (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(screen, (255, 255, 220), (int(self.x), int(self.y)), self.radius - 3)

    def check_pickup(self, player):
        if not self.picked:
            dist = math.hypot(player.rect.centerx - self.x, player.rect.centery - self.y)
            if dist < 30:
                self.picked = True
                player.has_egg = True


class Exit:
    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)

    def draw(self, screen):
        pygame.draw.rect(screen, EXIT, self.rect)
        pygame.draw.rect(screen, (80, 180, 80), self.rect, 3)

    def check_win(self, player):
        if player.has_egg and self.rect.colliderect(player.rect):
            return True
        return False


# -----------------------------
# FONCTIONS
# -----------------------------
def create_walls():
    return [
        pygame.Rect(0, 0, WIDTH, 20),
        pygame.Rect(0, HEIGHT - 20, WIDTH, 20),
        pygame.Rect(0, 0, 20, HEIGHT),
        pygame.Rect(WIDTH - 20, 0, 20, HEIGHT),

        pygame.Rect(110, 90, 200, 20),
        pygame.Rect(110, 90, 20, 160),
        pygame.Rect(110, 250, 220, 20),

        pygame.Rect(360, 90, 20, 160),
        pygame.Rect(360, 230, 230, 20),
        pygame.Rect(550, 90, 20, 240),

        pygame.Rect(650, 350, 200, 20),
        pygame.Rect(650, 350, 20, 200),
        pygame.Rect(760, 350, 20, 200),

        pygame.Rect(260, 360, 200, 20),
        pygame.Rect(260, 360, 20, 180),
        pygame.Rect(430, 520, 200, 20),

        pygame.Rect(560, 430, 20, 140),
    ]


def draw_text(screen, text, x, y, size=28, color=TEXT):
    font = pygame.font.SysFont("arial", size, bold=True)
    surface = font.render(text, True, color)
    screen.blit(surface, (x, y))


# -----------------------------
# JEU
# -----------------------------
def game_loop():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Steal the Egg")
    clock = pygame.time.Clock()

    walls = create_walls()
    player = Player(60, 520)
    egg = Egg(470, 180)
    exit_zone = Exit(820, 50, 70, 60)

    guards = [
        Guard(250, 160, 18, 18, (250, 160), (300, 160), 80),
        Guard(680, 170, 18, 18, (680, 170), (680, 260), 80),
        Guard(760, 520, 18, 18, (760, 520), (760, 560), 75),
    ]

    timer = 45.0
    game_over = False
    win = False

    while True:
        dt = clock.tick(FPS) / 1000.0

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        if not game_over:
            keys = pygame.key.get_pressed()
            player.update(keys, walls)

            egg.check_pickup(player)

            if exit_zone.check_win(player):
                win = True
                game_over = True

            for guard in guards:
                guard.update(player, walls, dt)

            for guard in guards:
                if player.rect.colliderect(guard.rect):
                    game_over = True
                    win = False

            timer -= dt
            if timer <= 0:
                game_over = True
                win = False

        if game_over:
            if pygame.key.get_pressed()[pygame.K_r]:
                return

        screen.fill(BG)

        for wall in walls:
            pygame.draw.rect(screen, WALL, wall)

        exit_zone.draw(screen)
        egg.draw(screen)
        pygame.draw.rect(screen, PLAYER, player.rect)

        for guard in guards:
            pygame.draw.rect(screen, GUARD, guard.rect)

        draw_text(screen, "Steal the Egg", 20, 18, 28)
        draw_text(screen, f"Temps: {max(0, timer):.1f}s", 760, 18, 24)

        if not player.has_egg and not egg.picked:
            draw_text(screen, "Récupère l'oeuf !", 330, 18, 24)
        elif player.has_egg:
            draw_text(screen, "Retourne à la sortie !", 290, 18, 24)

        if game_over:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            screen.blit(overlay, (0, 0))

            if win:
                draw_text(screen, "GAGNE !", 390, 260, 42)
                draw_text(screen, "Appuie sur R pour rejouer", 290, 320, 22)
            else:
                draw_text(screen, "PERDU !", 390, 260, 42)
                draw_text(screen, "Appuie sur R pour rejouer", 290, 320, 22)

        pygame.display.flip()


def main():
    while True:
        game_loop()


if __name__ == "__main__":
    main()
