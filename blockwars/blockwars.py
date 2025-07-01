#!/usr/bin/python3
# Description: blockwars - A simple game written in Python. 
# Usage: python3 blockwars.py
# Author: Justin Oros
# Source: https://github.com/JustinOros

import pygame
import random
import time
import os

# Initialize pygame
pygame.init()

# Set up full-screen mode
SCREEN_WIDTH = pygame.display.Info().current_w
SCREEN_HEIGHT = pygame.display.Info().current_h
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Block Wars")

# Define colors
WHITE = (255, 255, 255)
BLUE = (0, 0, 255)
RED = (255, 0, 0)
DARK_GRAY = (50, 50, 50)

# Function to load sound safely
def load_sound(filename):
    if os.path.exists(filename):
        return pygame.mixer.Sound(filename)
    else:
        print(f"Warning: {filename} not found. Sound will be disabled.")
        return None

# Load sounds
GO_SOUND = load_sound("go_sound.wav")
FIRE_SOUND = load_sound("player_fire_sound.wav")
DIE_SOUND = load_sound("player_death_sound.wav")
LEVEL_UP_SOUND = load_sound("level_up_sound.wav")
ENEMY_DEATH_SOUND = load_sound("enemy_death_sound.wav")
EXPLOSION_SOUND = load_sound("explosion_sound.wav")  # Explosion sound

# Set font for score
font = pygame.font.SysFont(None, 30)

# Initialize the joystick (controller)
pygame.joystick.init()
controller = None
if pygame.joystick.get_count() > 0:
    controller = pygame.joystick.Joystick(0)
    controller.init()

# Player class
class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.size = 20
        self.color = BLUE
        self.speed = 5
        self.direction = None  # Will store direction of last movement for firing

    def move(self, keys, joystick_axes):
        # Handle movement via keyboard or controller
        if joystick_axes[1] < -0.5:  # Up (left thumbstick)
            self.y -= self.speed
            self.direction = 'up'
        elif joystick_axes[1] > 0.5:  # Down (left thumbstick)
            self.y += self.speed
            self.direction = 'down'
        if joystick_axes[0] < -0.5:  # Left (left thumbstick)
            self.x -= self.speed
            self.direction = 'left'
        elif joystick_axes[0] > 0.5:  # Right (left thumbstick)
            self.x += self.speed
            self.direction = 'right'

        # Keyboard controls
        if keys[pygame.K_w]:  # Move up
            self.y -= self.speed
            self.direction = 'up'
        if keys[pygame.K_s]:  # Move down
            self.y += self.speed
            self.direction = 'down'
        if keys[pygame.K_a]:  # Move left
            self.x -= self.speed
            self.direction = 'left'
        if keys[pygame.K_d]:  # Move right
            self.x += self.speed
            self.direction = 'right'

        # Wrap the player around the screen edges
        if self.x < 0:
            self.x = SCREEN_WIDTH - self.size
        elif self.x > SCREEN_WIDTH - self.size:
            self.x = 0
        if self.y < 0:
            self.y = SCREEN_HEIGHT - self.size
        elif self.y > SCREEN_HEIGHT - self.size:
            self.y = 0

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))


# Projectile class
class Projectile:
    def __init__(self, x, y, direction):
        self.x = x
        self.y = y
        self.size = 5
        self.color = WHITE
        self.speed = 15  # Bullet speed
        self.direction = direction

    def move(self):
        if self.direction == 'up':
            self.y -= self.speed
        elif self.direction == 'down':
            self.y += self.speed
        elif self.direction == 'left':
            self.x -= self.speed
        elif self.direction == 'right':
            self.x += self.speed

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))


# Explosion class
class Explosion:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.size = 50
        self.lifetime = 10  # How long the explosion lasts in frames

    def draw(self):
        pygame.draw.circle(screen, (255, 165, 0), (self.x, self.y), self.size)
        self.lifetime -= 1

    def is_alive(self):
        return self.lifetime > 0


# Enemy class
class Enemy:
    def __init__(self, speed):
        # Spawn enemies at random positions along the outskirts of the screen
        edge = random.choice(["top", "bottom", "left", "right"])
        if edge == "top":
            self.x = random.randint(0, SCREEN_WIDTH - 20)
            self.y = 0
        elif edge == "bottom":
            self.x = random.randint(0, SCREEN_WIDTH - 20)
            self.y = SCREEN_HEIGHT - 20
        elif edge == "left":
            self.x = 0
            self.y = random.randint(0, SCREEN_HEIGHT - 20)
        else:  # "right"
            self.x = SCREEN_WIDTH - 20
            self.y = random.randint(0, SCREEN_HEIGHT - 20)

        self.size = 20
        self.color = RED
        self.speed = speed

    def move(self, player_x, player_y):
        # Move towards the player
        if self.x < player_x:
            self.x += self.speed
        elif self.x > player_x:
            self.x -= self.speed
        if self.y < player_y:
            self.y += self.speed
        elif self.y > player_y:
            self.y -= self.speed

    def draw(self):
        pygame.draw.rect(screen, self.color, (self.x, self.y, self.size, self.size))


# Main game loop
def game():
    clock = pygame.time.Clock()
    player = Player()
    projectiles = []
    explosions = []  # List to hold active explosions
    level = 1
    score = 0
    enemies = [Enemy(2)]  # Enemies spawn a bit away from the player
    running = True
    player_dead = False  # Flag to ensure death sound is played once

    # Play "GO!" sound to start the game immediately
    if GO_SOUND:
        GO_SOUND.play()

    while running:
        screen.fill(DARK_GRAY)

        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                if event.key == pygame.K_SPACE:  # Fire with spacebar
                    if player.direction:
                        projectiles.append(Projectile(player.x + player.size // 2, player.y + player.size // 2, player.direction))
                        if FIRE_SOUND:
                            FIRE_SOUND.play()  # Play fire sound
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0:  # A button on controller
                    if player.direction:
                        projectiles.append(Projectile(player.x + player.size // 2, player.y + player.size // 2, player.direction))
                        if FIRE_SOUND:
                            FIRE_SOUND.play()  # Play fire sound
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left mouse button click
                    if player.direction:
                        projectiles.append(Projectile(player.x + player.size // 2, player.y + player.size // 2, player.direction))
                        if FIRE_SOUND:
                            FIRE_SOUND.play()  # Play fire sound

        keys = pygame.key.get_pressed()

        # Get joystick axis for movement
        joystick_axes = [controller.get_axis(0), controller.get_axis(1)] if controller else [0, 0]

        player.move(keys, joystick_axes)

        # Move and draw projectiles
        for projectile in projectiles[:]:
            projectile.move()
            projectile.draw()
            if projectile.x < 0 or projectile.x > SCREEN_WIDTH or projectile.y < 0 or projectile.y > SCREEN_HEIGHT:
                projectiles.remove(projectile)

        # Move and draw enemies
        for enemy in enemies:
            enemy.move(player.x, player.y)
            enemy.draw()

            # Check if enemy touches player
            if pygame.Rect(player.x, player.y, player.size, player.size).colliderect(pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)):
                if not player_dead:  # Check if death sound has already played
                    if DIE_SOUND:
                        DIE_SOUND.play()  # Play die sound
                    player_dead = True  # Set flag to prevent double death sound
                show_final_score(score)
                running = False  # Player dies

            # Check if enemy is hit by projectile
            for projectile in projectiles[:]:
                if pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size).colliderect(pygame.Rect(projectile.x, projectile.y, projectile.size, projectile.size)):
                    # Create explosion
                    explosions.append(Explosion(enemy.x + enemy.size // 2, enemy.y + enemy.size // 2))
                    if ENEMY_DEATH_SOUND:
                        ENEMY_DEATH_SOUND.play()  # Play enemy death sound
                    enemies.remove(enemy)
                    projectiles.remove(projectile)
                    score += 100
                    break

        # Handle explosions
        for explosion in explosions[:]:
            explosion.draw()
            if not explosion.is_alive():
                explosions.remove(explosion)

        # Level up
        if not enemies:
            level += 1
            if LEVEL_UP_SOUND:
                LEVEL_UP_SOUND.play()  # Play level-up sound
            # Increase speed of enemies with each level, but slower speed increase
            enemy_speed = 2 + (level // 3)  # Slow the speed increase
            enemies = [Enemy(enemy_speed) for _ in range(level)]  # Increase number of enemies per level

        # Draw the player
        player.draw()

        # Draw score at the top-left corner
        score_text = font.render(f"Score: {score}", True, (255, 255, 255))
        screen.blit(score_text, (10, 10))

        # Draw level at the top-right corner
        level_text = font.render(f"Level: {level}", True, (255, 255, 255))
        screen.blit(level_text, (SCREEN_WIDTH - level_text.get_width() - 10, 10))

        pygame.display.flip()
        clock.tick(60)  # Frame rate (60 FPS)


# Function to display the final score on death
def show_final_score(score):
    font_large = pygame.font.SysFont(None, 80)
    final_score_text = font_large.render(f"Final Score: {score}", True, (255, 255, 255))
    screen.fill(DARK_GRAY)  # Fill the screen with dark gray before showing the score
    screen.blit(final_score_text, (SCREEN_WIDTH // 2 - final_score_text.get_width() // 2, SCREEN_HEIGHT // 2 - final_score_text.get_height() // 2))
    pygame.display.flip()
    time.sleep(3)  # Display final score for 3 seconds


# Run the game
if __name__ == "__main__":
    game()

pygame.quit()
