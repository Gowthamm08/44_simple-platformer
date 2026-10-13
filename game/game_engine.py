
import math
from array import array

import pygame

from .player import Player
from .platform import Platform
from .hazard import Hazard


WHITE = (255, 255, 255)
BLACK = (15, 20, 35)
BROWN = (150, 100, 60)
RED = (220, 60, 60)
GREEN = (0, 200, 0)
YELLOW = (255, 220, 80)
SKY = (100, 160, 220)
DARK_BLUE = (35, 55, 100)


class GameEngine:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.start_x = 40
        self.start_y = height - 120

        self.font = pygame.font.SysFont("Arial", 28)
        self.small_font = pygame.font.SysFont("Arial", 20)
        self.title_font = pygame.font.SysFont("Arial", 44, bold=True)

        # Try to initialize audio. The game still works without audio.
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=22050,
                    size=-16,
                    channels=1
                )
            self.jump_sound = self.make_sound(660, 0.10)
            self.goal_sound = self.make_sound(880, 0.18)
            self.death_sound = self.make_sound(180, 0.25)
        except pygame.error:
            self.jump_sound = None
            self.goal_sound = None
            self.death_sound = None

        self.difficulties = {
            "Easy": {"gravity": 0.45, "jump": -10.5},
            "Medium": {"gravity": 0.60, "jump": -12.0},
            "Hard": {"gravity": 0.85, "jump": -14.0},
        }

        self.difficulty = "Medium"
        self.gravity = 0.60
        self.game_over = False
        self.final_score = 0
        self.score = 0

        self.reset_level()

    def make_sound(self, frequency, duration):
        """Create a short sound effect without external audio files."""
        sample_rate = 22050
        samples = array("h")
        total_samples = int(sample_rate * duration)

        for i in range(total_samples):
            fade = 1.0 - (i / total_samples)
            value = int(
                10000
                * fade
                * math.sin(2 * math.pi * frequency * i / sample_rate)
            )
            samples.append(value)

        # pygame expects native signed 16-bit sample data.
        if samples.itemsize != 2:
            return None

        return pygame.mixer.Sound(buffer=samples.tobytes())

    def play_sound(self, sound):
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def reset_level(self):
        """Create a fresh player and level while keeping the score."""
        self.player = Player(self.start_x, self.start_y)
        self.player.jump_strength = self.difficulties[
            self.difficulty
        ]["jump"]

        ground_y = self.height - 40

        self.platforms = [
            Platform(0, ground_y, 160),
            Platform(220, ground_y, 140),
            Platform(420, ground_y - 60, 120),
            Platform(600, ground_y, 180),
        ]

        self.hazards = [
            Hazard(240, ground_y - 14, 100)
        ]

        self.goal_x = 740

    def restart(self, difficulty):
        """Start a new game at the chosen difficulty."""
        self.difficulty = difficulty
        self.gravity = self.difficulties[difficulty]["gravity"]
        self.score = 0
        self.final_score = 0
        self.game_over = False
        self.reset_level()

    def handle_event(self, event):
        if event.type != pygame.KEYDOWN:
            return

        if self.game_over:
            # Select a difficulty to replay.
            if event.key == pygame.K_1:
                self.restart("Easy")
            elif event.key == pygame.K_2:
                self.restart("Medium")
            elif event.key == pygame.K_3:
                self.restart("Hard")

            # Exit the application.
            elif event.key in (pygame.K_ESCAPE, pygame.K_q):
                pygame.event.post(
                    pygame.event.Event(pygame.QUIT)
                )
            return

        if event.key in (
            pygame.K_SPACE,
            pygame.K_UP,
            pygame.K_w
        ):
            was_on_ground = self.player.on_ground
            self.player.jump()

            if was_on_ground and not self.player.on_ground:
                self.play_sound(self.jump_sound)

    def handle_input(self):
        if self.game_over:
            return

        keys = pygame.key.get_pressed()
        self.player.vx = 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.player.vx = -self.player.speed

        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.player.vx = self.player.speed

    def end_game(self):
        if not self.game_over:
            self.game_over = True
            self.final_score = self.score
            self.play_sound(self.death_sound)

    def update(self):
        if self.game_over:
            return

        # Horizontal movement.
        self.player.x += self.player.vx
        self.player.x = max(
            0,
            min(self.player.x, self.width - self.player.width)
        )

        # Save the previous position before vertical movement.
        previous_rect = self.player.rect().copy()
        previous_bottom = previous_rect.bottom

        self.player.vy += self.gravity

        # Prevent excessively large frame-to-frame falls.
        self.player.vy = min(self.player.vy, 18)

        self.player.y += self.player.vy
        current_rect = self.player.rect()

        self.player.on_ground = False

        # Swept landing detection: detect crossing a platform top,
        # even when the player moves past it in one frame.
        if self.player.vy >= 0:
            for platform in self.platforms:
                platform_rect = platform.rect()

                horizontal_overlap = (
                    current_rect.right > platform_rect.left
                    and current_rect.left < platform_rect.right
                )

                crossed_platform_top = (
                    previous_bottom <= platform_rect.top
                    and current_rect.bottom >= platform_rect.top
                )

                if horizontal_overlap and crossed_platform_top:
                    self.player.y = (
                        platform_rect.top - self.player.height
                    )
                    self.player.vy = 0
                    self.player.on_ground = True
                    current_rect = self.player.rect()
                    break

        # Hazard collision.
        for hazard in self.hazards:
            if self.player.rect().colliderect(hazard.rect()):
                self.end_game()
                return

        # Falling off the screen.
        if self.player.y > self.height:
            self.end_game()
            return

        # Reaching the goal earns a point and resets the player.
        if self.player.x + self.player.width >= self.goal_x:
            self.score += 1
            self.play_sound(self.goal_sound)

            self.player.x = self.start_x
            self.player.y = self.start_y
            self.player.vx = 0
            self.player.vy = 0
            self.player.on_ground = False

    def draw_text_centered(
        self, screen, text, font, color, y
    ):
        surface = font.render(text, True, color)
        screen.blit(
            surface,
            (
                (self.width - surface.get_width()) // 2,
                y
            )
        )

    def render(self, screen):
        screen.fill(SKY)

        # Platforms.
        for platform in self.platforms:
            pygame.draw.rect(
                screen, BROWN, platform.rect(), border_radius=3
            )

        # Hazards.
        for hazard in self.hazards:
            pygame.draw.rect(
                screen, RED, hazard.rect(), border_radius=3
            )

        # Goal.
        goal_rect = pygame.Rect(
            self.goal_x, 0, 6, self.height
        )
        pygame.draw.rect(screen, GREEN, goal_rect)

        # Player.
        pygame.draw.rect(
            screen, WHITE, self.player.rect(), border_radius=5
        )

        # Score and difficulty.
        score_surface = self.font.render(
            f"Score: {self.score}", True, WHITE
        )
        screen.blit(score_surface, (10, 10))

        difficulty_surface = self.small_font.render(
            f"Difficulty: {self.difficulty}",
            True,
            WHITE
        )
        screen.blit(difficulty_surface, (10, 45))

        if self.game_over:
            self.render_game_over(screen)

    def render_game_over(self, screen):
        # Dark translucent overlay.
        overlay = pygame.Surface(
            (self.width, self.height), pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        self.draw_text_centered(
            screen,
            "GAME OVER",
            self.title_font,
            RED,
            105
        )

        self.draw_text_centered(
            screen,
            f"Final Score: {self.final_score}",
            self.font,
            WHITE,
            175
        )

        self.draw_text_centered(
            screen,
            "Choose difficulty to play again",
            self.small_font,
            YELLOW,
            235
        )

        self.draw_text_centered(
            screen,
            "1 - Easy",
            self.font,
            WHITE,
            275
        )

        self.draw_text_centered(
            screen,
            "2 - Medium",
            self.font,
            WHITE,
            315
        )

        self.draw_text_centered(
            screen,
            "3 - Hard",
            self.font,
            WHITE,
            355
        )

        self.draw_text_centered(
            screen,
            "Q or ESC - Exit",
            self.small_font,
            WHITE,
            410
        )
