import pygame
import random
import asyncio
import sys

# Initialize Pygame
pygame.init()

# Set up the display
WIDTH = 800
HEIGHT = 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Space Invaders")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
NEON_CYAN = (0, 255, 255)  # Added neon color for start and game over text

# Load images
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

player_img = load_image("player.png", (100, 60), True)
enemy_img = load_image("enemy.png", (60, 60), True)
bullet_img = load_image("bullet.png", (8, 20), True)
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
        self.rect.bottom = HEIGHT - 10
        self.speed = 5

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
        self.speed = random.randrange(1, 4)

    def update(self):
        self.rect.y += self.speed
        if self.rect.top > HEIGHT:
            self.rect.x = random.randrange(WIDTH - self.rect.width)
            self.rect.y = random.randrange(-200, -80)
            self.speed = random.randrange(1, 4)

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = bullet_img
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speed = -10

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
            self.frames = [pygame.transform.scale(frame, (80, 80)) for frame in self.frames]
        except pygame.error as e:
            print(f"Error processing explosion frames: {e}")
            self.frames = [pygame.Surface((80, 80), pygame.SRCALPHA) for _ in range(8)]
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
font = pygame.font.Font(None, 48)
clock = pygame.time.Clock()

# Main game loop
async def main():
    global score, game_state
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:  # Enter key
                    if game_state == START:
                        game_state = PLAYING
                    elif game_state == GAME_OVER:
                        init_game()  # Reset game
                        game_state = PLAYING
                elif event.key == pygame.K_SPACE and game_state == PLAYING:
                    player.shoot()

        # State machine
        if game_state == START:
            screen.blit(background_img, (0, 0))
            start_text = font.render("Start Game - Press Enter", True, NEON_CYAN)  # Changed to Neon Cyan
            screen.blit(start_text, (WIDTH // 2 - start_text.get_width() // 2, HEIGHT // 2 - start_text.get_height() // 2))

        elif game_state == PLAYING:
            # Update
            all_sprites.update()
            explosions.update()

            # Check for collisions
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

            # Check if player hit
            if pygame.sprite.spritecollide(player, enemies, False):
                game_state = GAME_OVER

            # Draw
            screen.blit(background_img, (0, 0))
            all_sprites.draw(screen)
            explosions.draw(screen)
            score_text = font.render(f"Score: {score}", True, WHITE)  # Kept white
            screen.blit(score_text, (10, 10))

        elif game_state == GAME_OVER:
            screen.blit(background_img, (0, 0))
            game_over_text = font.render("Game Over", True, NEON_CYAN)  # Changed to Neon Cyan
            score_text = font.render(f"Total Score: {score}", True, NEON_CYAN)  # Changed to Neon Cyan
            play_again_text = font.render("Play Again - Press Enter", True, NEON_CYAN)  # Changed to Neon Cyan
            screen.blit(game_over_text, (WIDTH // 2 - game_over_text.get_width() // 2, HEIGHT // 2 - 100))
            screen.blit(score_text, (WIDTH // 2 - score_text.get_width() // 2, HEIGHT // 2))
            screen.blit(play_again_text, (WIDTH // 2 - play_again_text.get_width() // 2, HEIGHT // 2 + 100))

        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)  # Yield to browser event loop

    pygame.quit()

# Entry point for pygbag
if __name__ == "__main__":
    asyncio.run(main())