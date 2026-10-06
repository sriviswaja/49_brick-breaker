import pygame
import math
import array
from .paddle import Paddle
from .ball import Ball
from .brick import Brick

# Game Engine

WHITE = (255, 255, 255)
BG = (15, 15, 25)
BRICK_COLORS = [
    (200, 60, 60),
    (200, 140, 60),
    (200, 200, 60),
    (80, 180, 80),
    (80, 140, 200),
]

class GameEngine:
    def __init__(self, width, height, difficulty="medium"):
        self.width = width
        self.height = height
        self.difficulty = difficulty
        self.selected_difficulty = None

        self.game_over = False
        self.result = None
        self.exit_requested = False
        self.selected_difficulty = None

        self.sound_enabled = pygame.mixer.get_init() is not None

        if self.sound_enabled:
            self.brick_sound = self._create_sound(700, 0.08, 0.25)
            self.paddle_sound = self._create_sound(400, 0.08, 0.25)
            self.wall_sound = self._create_sound(250, 0.05, 0.20)
            self.game_over_sound = self._create_sound(150, 0.40, 0.30)
        else:
            self.brick_sound = None
            self.paddle_sound = None
            self.wall_sound = None
            self.game_over_sound = None


        if difficulty == "easy":
            self.ball_speed = 3
            paddle_width = 120
        elif difficulty == "hard":
            self.ball_speed = 6
            paddle_width = 80
        else:
            self.ball_speed = 4
            paddle_width = 100

        self.paddle = Paddle(
            width // 2 - paddle_width // 2,
            height - 30,
            paddle_width,
            14
        )

        self.ball = Ball(width // 2, height - 50, radius=8)
        self.ball.vx = self.ball_speed
        self.ball.vy = -self.ball_speed

        self.rows, self.cols = 5, 8
        self.bricks = self._build_bricks(self.rows, self.cols)

        self.lives = 3
        self.score = 0
        self.font = pygame.font.SysFont("Arial", 28)
        self.game_over = False
        self.result = None
        self.exit_requested = False  # "win" or "lose"

    def _create_sound(self, frequency, duration, volume=0.3):
        sample_rate = 44100
        sample_count = int(sample_rate * duration)

        samples = array.array("h")

        for i in range(sample_count):
            time = i / sample_rate
            value = int(
                32767
                * volume
                * math.sin(2 * math.pi * frequency * time)
            )
            samples.append(value)

        return pygame.mixer.Sound(buffer=samples)    

    def _build_bricks(self, rows, cols):
        bricks = []
        margin, gap, top = 30, 6, 60
        brick_w = (self.width - margin * 2 - gap * (cols - 1)) // cols
        brick_h = 22
        for r in range(rows):
            for c in range(cols):
                x = margin + c * (brick_w + gap)
                y = top + r * (brick_h + gap)
                bricks.append(Brick(x, y, brick_w, brick_h))
        return bricks

    def handle_event(self, event):
        if not self.game_over:
            return

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                self.selected_difficulty = "easy"
                self.exit_requested = True

            elif event.key == pygame.K_2:
                self.selected_difficulty = "medium"
                self.exit_requested = True

            elif event.key == pygame.K_3:
                self.selected_difficulty = "hard"
                self.exit_requested = True

            elif event.key == pygame.K_4:
                self.selected_difficulty = None
                self.exit_requested = True

    def handle_input(self):
        if self.game_over:
            return
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            self.paddle.move(-self.paddle.speed, self.width)
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            self.paddle.move(self.paddle.speed, self.width)

    def update(self):
        if self.game_over:
            return

        # Store the ball's position before moving
        previous_rect = self.ball.rect()

        self.ball.move()

        if self.ball.x - self.ball.radius <= 0 or self.ball.x + self.ball.radius >= self.width:
            self.ball.vx *= -1
            self.play_sound(self.wall_sound)

        if self.ball.y - self.ball.radius <= 0:
            self.ball.vy *= -1
            self.play_sound(self.wall_sound)

        # Paddle collision
        if self.ball.rect().colliderect(self.paddle.rect()):
            current_rect = self.ball.rect()
            paddle_rect = self.paddle.rect()
            

            # Determine whether the ball hit the horizontal or vertical side
            if previous_rect.right <= paddle_rect.left or previous_rect.left >= paddle_rect.right:
                self.ball.vx *= -1
            else:
                self.ball.vy *= -1
            self.play_sound(self.paddle_sound)

        # Brick collisions
        for brick in self.bricks:
            if brick.alive and self.ball.rect().colliderect(brick.rect()):
                brick.alive = False
                self.score += 1
                self.play_sound(self.brick_sound)

                current_rect = self.ball.rect()
                brick_rect = brick.rect()

                # Determine which side of the brick was hit
                if previous_rect.right <= brick_rect.left or previous_rect.left >= brick_rect.right:
                    self.ball.vx *= -1
                else:
                    self.ball.vy *= -1

                break

        if self.ball.y - self.ball.radius > self.height:
            self.lives -= 1
            if self.lives <= 0:
                self.game_over = True
                self.result = "lose"
                self.play_sound(self.game_over_sound)
            else:
                self._reset_ball()

        if all(not b.alive for b in self.bricks):
            self.game_over = True
            self.result = "win"
            self.play_sound(self.game_over_sound)

    def _reset_ball(self):
        self.ball.x, self.ball.y = self.width // 2, self.height - 50
        self.ball.vx = self.ball_speed
        self.ball.vy = -self.ball_speed
    def render(self, screen):
        screen.fill(BG)

        pygame.draw.rect(screen, WHITE, self.paddle.rect())
        pygame.draw.circle(screen, WHITE, (int(self.ball.x), int(self.ball.y)), self.ball.radius)

        for i, brick in enumerate(self.bricks):
            if brick.alive:
                row = i // self.cols
                color = BRICK_COLORS[row % len(BRICK_COLORS)]
                pygame.draw.rect(screen, color, brick.rect())

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        lives_text = self.font.render(f"Lives: {self.lives}", True, WHITE)
        screen.blit(lives_text, (self.width - 130, 10))

        if self.game_over:
            # Dark overlay
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(180)
            overlay.fill((0, 0, 0))
            screen.blit(overlay, (0, 0))

            # Win or lose message
            if self.result == "win":
                result_text = self.font.render("YOU WIN!", True, WHITE)
            else:
                result_text = self.font.render("GAME OVER", True, WHITE)

            score_text = self.font.render(
                f"Final Score: {self.score}",
                True,
                WHITE
            )

            instruction_text = self.font.render(
                "1: Easy   2: Medium   3: Hard   4: Exit",
                True,
                WHITE
            )
            

            screen.blit(
                result_text,
                result_text.get_rect(
                    center=(self.width // 2, self.height // 2 - 60)
                )
            )

            screen.blit(
                score_text,
                score_text.get_rect(
                    center=(self.width // 2, self.height // 2)
                )
            )

            screen.blit(
                instruction_text,
                instruction_text.get_rect(
                    center=(self.width // 2, self.height // 2 + 60)
                )
            )

    def play_sound(self, sound):
        if self.sound_enabled and sound is not None:
            sound.play()        