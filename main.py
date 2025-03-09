import pygame
import random
import asyncio
import sys

# Initialize Pygame
pygame.init()

# Screen size: reasonable default for local testing, overridden by pygbag
if "pygbag" in sys.argv[0]:  # Detect if running in pygbag
    info = pygame.display.Info()
    WIDTH = info.current_w  # Fullscreen for web
    HEIGHT = info.current_h
else:
    WIDTH = 800  # Default for local testing
    HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_CYAN = (0, 255, 255)

# Load images with dynamic scaling
def load_image(filename, scale_to=None, use_alpha=True):
    try:
        img = pygame.image.load(filename)
        if use_alpha:
            img = img.convert_alpha()
        else:
            img = img.convert()
        return pygame.transform.scale(img, scale_to) if scale_to else img
    except pygame.error as e:
        print(f"Error loading {filename}: {e}")
        return pygame.Surface(scale_to or (100, 100), pygame.SRCALPHA if use_alpha else 0)

player_img = load_image("player.png", (WIDTH // 8, HEIGHT // 10), True)
enemy_img = load_image("enemy.png", (WIDTH // 13, HEIGHT // 10), True)
bullet_img = load_image("bullet.png", (WIDTH // 100, HEIGHT // 30), True)
explosion_sheet = load_image("explosion.png", None, True)
background_img = load_image("space_background.jpg", (WIDTH, HEIGHT), False)

# Load sound effect (optional, may not work in pygbag)
try:
    hit_sound = pygame.mixer.Sound("explosion.ogg")
except pygame.error as e:
    print(f"Error loading explosion.ogg: {e}")
    hit_sound = None

# Player class
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = player_img
        self.rect = self.image.get_rect()
        self.rect.centerx = WIDTH // 2
        self.rect.bottom = HEIGHT - HEIGHT // 60
        self.speed = WIDTH // 160

    def update(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] and self.rect.left > 0:
            self.rect.x -= self.speed
        if keys[pygame.K_RIGHT] and self.rect.right < WIDTH:
            self.rect.x += self.speed

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.image = enemy_img
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-200, -80)
        self.speed = random.randrange(1, max(4, HEIGHT // 150))

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-200, -80)
            self.speed = random.randrange(1, max(4, HEIGHT // 150))

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -HEIGHT // 60

    def update(self):
        self.rect.y += self.speed
        if self.rect.bottom < 0:
            self.kill()

# Explosion class
class Explosion(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.frame_width = explosion_sheet.get_width() // 8
        self.frame_height = explosion_sheet.get_height()
        try:
            self.frames = [
                explosion_sheet.subsurface((i * self.frame_width, 0, self.frame_width, self.frame_height))
                for i in range(8)
            ]
            self.frames = [pygame.transform.scale(frame, (WIDTH // 10, WIDTH // 10)) for frame in self.frames]
        except pygame.error as e:
            print(f"Error processing explosion frames: {e}")
            self.frames = [pygame.Surface((WIDTH // 10, WIDTH // 10), pygame.SRCALPHA) for _ in range(8)]
        self.frame = 0
        self.image = self.frames[self.frame]
        self.rect = self.image.get_rect()
        self.rect.center = (x, y)
        self.timer = 0
        self.frame_duration = 5

    def update(self):
        self.timer += 1
        if self.timer >= self.frame_duration:
            self.frame += 1
            self.timer = 0
            if self.frame >= len(self.frames):
                self.kill()
            else:
                self.image = self.frames[self.frame]

# Game states
START = 0
PLAYING = 1
GAME_OVER = 2

# Initialize game variables
def init_game():
    global all_sprites, enemies, bullets, explosions, player, score, game_state
    all_sprites = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    player = Player()
    all_sprites.add(player)
    for i in range(8):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)
    score = 0
    game_state = START

# Initial setup
init_game()
font = pygame.font.Font(None, HEIGHT // 15)
clock = pygame.time.Clock()

# Input handling for keyboard and touch
def handle_input():
    global game_state
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            return False, None, False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                return False, None, False  # Exit with Esc
            if event.key == pygame.K_RETURN:
                if game_state == START:
                    game_state = PLAYING
                elif game_state == GAME_OVER:
                    init_game()
                    game_state = PLAYING
                return True, None, False
            elif event.key == pygame.K_SPACE and game_state == PLAYING:
                return True, None, True
        if event.type == pygame.FINGERDOWN or event.type == pygame.MOUSEBUTTONDOWN:
            pos = event.pos if hasattr(event, 'pos') else (event.x * WIDTH, event.y * HEIGHT)
            if game_state == START:
                game_state = PLAYING
            elif game_state == GAME_OVER:
                init_game()
                game_state = PLAYING
            elif game_state == PLAYING:
                return True, pos[0], True
        if event.type == pygame.FINGERMOTION or event.type == pygame.MOUSEMOTION:
            pos = event.pos if hasattr(event, 'pos') else (event.x * WIDTH, event.y * HEIGHT)
            return True, pos[0], False
    return True, None, False

# Main game loop
async def main():
    global score, game_state
    running = True
    while running:
        running, touch_x, shoot = handle_input()
        if not running:
            break

        # Update player position with touch or keyboard
        if touch_x is not None and game_state == PLAYING:
            player.rect.centerx = touch_x
            player.rect.clamp_ip(screen.get_rect())
        if shoot and game_state == PLAYING:
            player.shoot()

        # State machine
        if game_state == START:
            screen.blit(background_img, (0, 0))
            start_text = font.render("Start Game - Tap or Press Enter", True, NEON_CYAN)
            screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 - start_text.get_height() // 2))

        elif game_state == PLAYING:
            all_sprites.update()
            explosions.update()

            hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
            for hit in hits:
                score += 10
                explosion = Explosion(hit.rect.centerx, hit.rect.centery)
                all_sprites.add(explosion)
                explosions.add(explosion)
                if hit_sound:
                    hit_sound.play()
                enemy = Enemy()
                all_sprites.add(enemy)
                enemies.add(enemy)

            if pygame.sprite.spritecollide(player, enemies, False):
                game_state = GAME_OVER

            screen.blit(background_img, (0, 0))
            all_sprites.draw(screen)
            explosions.draw(screen)
            score_text = font.render(f"Score: {score}", True, WHITE)
            screen.blit(score_text, (WIDTH // 80, HEIGHT // 60))

        elif game_state == GAME_OVER:
            screen.blit(background_img, (0, 0))
            game_over_text = font.render("Game Over", True, NEON_CYAN)
            score_text = font.render(f"Total Score: {score}", True, NEON_CYAN)
            play_again_text = font.render("Play Again - Tap or Press Enter", True, NEON_CYAN)
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - HEIGHT // 10))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
            screen.blit(play_again_text, (WIDTH // 2 - play_again_text.get_width() // 2, HEIGHT // 2 + HEIGHT // 10))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

    pygame.quit()

if __name__ == "__main__":
    asyncio.run(main())
    