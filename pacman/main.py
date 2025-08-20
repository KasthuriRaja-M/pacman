import pygame
import math
import random
import os
from typing import List, Tuple, Optional

# Initialize Pygame
pygame.init()
pygame.mixer.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
TILE_SIZE = 20
GRID_WIDTH = 28
GRID_HEIGHT = 31
PACMAN_SPEED = 120
GHOST_SPEED = 100
FRIGHTENED_SPEED = 80

# Colors
BLACK = (0, 0, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
WHITE = (255, 255, 255)
RED = (255, 0, 0)
PINK = (255, 182, 255)
CYAN = (0, 255, 255)
ORANGE = (255, 182, 85)
DARK_BLUE = (0, 0, 139)
PELLET_COLOR = (255, 255, 224)
POWER_COLOR = (255, 255, 0)

# Maze layout (simplified)
MAZE = [
    "############################",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o####.#####.##.#####.####o#",
    "#.####.#####.##.#####.####.#",
    "#..........................#",
    "#.####.##.########.##.####.#",
    "#.####.##.########.##.####.#",
    "#......##....##....##......#",
    "######.##### ## #####.######",
    "     #.##### ## #####.#     ",
    "     #.##          ##.#     ",
    "     #.## ###HH### ##.#     ",
    "######.## #B G  I# ##.######",
    "      .   #  P   #   .      ",
    "######.## #C    P# ##.######",
    "     #.## ######## ##.#     ",
    "     #.##          ##.#     ",
    "     #.## ######## ##.#     ",
    "######.## ######## ##.######",
    "#............##............#",
    "#.####.#####.##.#####.####.#",
    "#o..##................##..o#",
    "###.##.##.########.##.##.###",
    "#......##....##....##......#",
    "#.##########.##.##########.#",
    "#..........................#",
    "############################"
]

class Pacman:
    def __init__(self, x: int, y: int):
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.direction = [1, 0]
        self.next_direction = [1, 0]
        self.speed = PACMAN_SPEED
        self.mouth_angle = 0
        self.lives = 3
        self.score = 0
        
    def update(self, dt: float, maze: List[str]):
        # Handle input
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.next_direction = [-1, 0]
        elif keys[pygame.K_RIGHT]:
            self.next_direction = [1, 0]
        elif keys[pygame.K_UP]:
            self.next_direction = [0, -1]
        elif keys[pygame.K_DOWN]:
            self.next_direction = [0, 1]
            
        # Try to change direction at tile center
        grid_x = self.x // TILE_SIZE
        grid_y = self.y // TILE_SIZE
        center_x = grid_x * TILE_SIZE + TILE_SIZE // 2
        center_y = grid_y * TILE_SIZE + TILE_SIZE // 2
        
        if abs(self.x - center_x) < 2 and abs(self.y - center_y) < 2:
            next_x = grid_x + self.next_direction[0]
            next_y = grid_y + self.next_direction[1]
            if (0 <= next_x < GRID_WIDTH and 0 <= next_y < GRID_HEIGHT and 
                maze[next_y][next_x] != '#'):
                self.direction = self.next_direction.copy()
        
        # Move
        new_x = self.x + self.direction[0] * self.speed * dt
        new_y = self.y + self.direction[1] * self.speed * dt
        
        # Check collision
        new_grid_x = int(new_x // TILE_SIZE)
        new_grid_y = int(new_y // TILE_SIZE)
        
        if (0 <= new_grid_x < GRID_WIDTH and 0 <= new_grid_y < GRID_HEIGHT and 
            maze[new_grid_y][new_grid_x] != '#'):
            self.x = new_x
            self.y = new_y
            
        # Wrap around tunnel
        if self.y // TILE_SIZE == 9:
            if self.x < 0:
                self.x = SCREEN_WIDTH
            elif self.x > SCREEN_WIDTH:
                self.x = 0
                
        # Animate mouth
        self.mouth_angle += 8 * dt
        
    def draw(self, screen: pygame.Surface):
        # Draw Pacman with animated mouth
        mouth_open = abs(math.sin(self.mouth_angle)) * 0.3
        start_angle = mouth_open
        end_angle = 2 * math.pi - mouth_open
        
        # Rotate based on direction
        if self.direction == [1, 0]:  # Right
            rotation = 0
        elif self.direction == [-1, 0]:  # Left
            rotation = math.pi
        elif self.direction == [0, -1]:  # Up
            rotation = -math.pi / 2
        else:  # Down
            rotation = math.pi / 2
            
        start_angle += rotation
        end_angle += rotation
        
        # Draw Pacman
        points = [(self.x, self.y)]
        for i in range(20):
            angle = start_angle + (end_angle - start_angle) * (i / 19)
            x = self.x + 8 * math.cos(angle)
            y = self.y + 8 * math.sin(angle)
            points.append((x, y))
            
        if len(points) > 2:
            pygame.draw.polygon(screen, YELLOW, points)

class Ghost:
    def __init__(self, x: int, y: int, color: Tuple[int, int, int], name: str):
        self.x = x * TILE_SIZE + TILE_SIZE // 2
        self.y = y * TILE_SIZE + TILE_SIZE // 2
        self.color = color
        self.name = name
        self.direction = [-1, 0]
        self.speed = GHOST_SPEED
        self.state = "CHASE"  # CHASE, SCATTER, FRIGHTENED, EATEN
        self.frightened_timer = 0
        self.target_corner = self._get_corner()
        
    def _get_corner(self) -> Tuple[int, int]:
        if self.name == "Blinky":
            return (GRID_WIDTH - 2, 1)
        elif self.name == "Pinky":
            return (1, 1)
        elif self.name == "Inky":
            return (GRID_WIDTH - 2, GRID_HEIGHT - 2)
        else:  # Clyde
            return (1, GRID_HEIGHT - 2)
            
    def update(self, dt: float, maze: List[str], pacman: Pacman, mode: str):
        if self.state == "FRIGHTENED":
            self.frightened_timer -= dt
            if self.frightened_timer <= 0:
                self.state = mode
                self.speed = GHOST_SPEED
                
        # Simple AI: move towards target
        if self.state == "FRIGHTENED":
            target_x = pacman.x
            target_y = pacman.y
            self.speed = FRIGHTENED_SPEED
        elif mode == "SCATTER":
            target_x = self.target_corner[0] * TILE_SIZE + TILE_SIZE // 2
            target_y = self.target_corner[1] * TILE_SIZE + TILE_SIZE // 2
        else:  # CHASE
            target_x = pacman.x
            target_y = pacman.y
            
        # Simple pathfinding: try to move towards target
        grid_x = int(self.x // TILE_SIZE)
        grid_y = int(self.y // TILE_SIZE)
        
        # Try different directions
        directions = [(1, 0), (-1, 0), (0, 1), (0, -1)]
        best_direction = self.direction
        
        for dx, dy in directions:
            if [dx, dy] != [-self.direction[0], -self.direction[1]]:  # Don't reverse
                new_x = grid_x + dx
                new_y = grid_y + dy
                if (0 <= new_x < GRID_WIDTH and 0 <= new_y < GRID_HEIGHT and 
                    maze[new_y][new_x] != '#'):
                    # Calculate distance to target
                    dist = abs(new_x - target_x // TILE_SIZE) + abs(new_y - target_y // TILE_SIZE)
                    if dist < abs(grid_x - target_x // TILE_SIZE) + abs(grid_y - target_y // TILE_SIZE):
                        best_direction = [dx, dy]
                        break
                        
        self.direction = best_direction
        
        # Move
        new_x = self.x + self.direction[0] * self.speed * dt
        new_y = self.y + self.direction[1] * self.speed * dt
        
        new_grid_x = int(new_x // TILE_SIZE)
        new_grid_y = int(new_y // TILE_SIZE)
        
        if (0 <= new_grid_x < GRID_WIDTH and 0 <= new_grid_y < GRID_HEIGHT and 
            maze[new_grid_y][new_grid_x] != '#'):
            self.x = new_x
            self.y = new_y
            
        # Wrap around tunnel
        if self.y // TILE_SIZE == 9:
            if self.x < 0:
                self.x = SCREEN_WIDTH
            elif self.x > SCREEN_WIDTH:
                self.x = 0
                
    def draw(self, screen: pygame.Surface):
        color = self.color
        if self.state == "FRIGHTENED":
            if int(pygame.time.get_ticks() / 200) % 2 == 0:
                color = (0, 0, 255)  # Blue
            else:
                color = (255, 255, 255)  # White
                
        # Draw ghost body
        pygame.draw.circle(screen, color, (int(self.x), int(self.y)), 8)
        pygame.draw.rect(screen, color, (int(self.x) - 8, int(self.y), 16, 8))
        
        # Draw wavy bottom
        for i in range(4):
            x = int(self.x) - 6 + i * 4
            pygame.draw.circle(screen, BLACK, (x, int(self.y) + 6), 2)
            
        # Draw eyes
        pygame.draw.circle(screen, WHITE, (int(self.x) - 3, int(self.y) - 2), 3)
        pygame.draw.circle(screen, WHITE, (int(self.x) + 3, int(self.y) - 2), 3)
        pygame.draw.circle(screen, BLACK, (int(self.x) - 3, int(self.y) - 2), 1)
        pygame.draw.circle(screen, BLACK, (int(self.x) + 3, int(self.y) - 2), 1)

class Game:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Pac-Man - Yellow Edition")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        
        # Game objects
        self.pacman = Pacman(13, 23)
        self.ghosts = [
            Ghost(13, 11, RED, "Blinky"),
            Ghost(11, 11, PINK, "Pinky"),
            Ghost(15, 11, CYAN, "Inky"),
            Ghost(13, 13, ORANGE, "Clyde")
        ]
        
        # Game state
        self.pellets = self._create_pellets()
        self.power_pellets = self._create_power_pellets()
        self.mode = "CHASE"
        self.mode_timer = 0
        self.paused = False
        self.game_over = False
        self.level = 1
        
        # Mode timing
        self.mode_sequence = [
            (7, "SCATTER"),
            (20, "CHASE"),
            (7, "SCATTER"),
            (20, "CHASE"),
            (5, "SCATTER"),
            (999, "CHASE")
        ]
        self.mode_index = 0
        
    def _create_pellets(self) -> List[Tuple[int, int]]:
        pellets = []
        for y, row in enumerate(MAZE):
            for x, cell in enumerate(row):
                if cell == '.':
                    pellets.append((x, y))
        return pellets
        
    def _create_power_pellets(self) -> List[Tuple[int, int]]:
        power_pellets = []
        for y, row in enumerate(MAZE):
            for x, cell in enumerate(row):
                if cell == 'o':
                    power_pellets.append((x, y))
        return power_pellets
        
    def update_mode(self, dt: float):
        self.mode_timer += dt
        duration, mode = self.mode_sequence[self.mode_index]
        
        if self.mode_timer >= duration:
            self.mode_timer = 0
            self.mode_index = (self.mode_index + 1) % len(self.mode_sequence)
            self.mode = self.mode_sequence[self.mode_index][1]
            
    def check_collisions(self):
        # Check pellet collisions
        pacman_grid_x = int(self.pacman.x // TILE_SIZE)
        pacman_grid_y = int(self.pacman.y // TILE_SIZE)
        
        # Regular pellets
        for pellet in self.pellets[:]:
            if (pellet[0] == pacman_grid_x and pellet[1] == pacman_grid_y):
                self.pellets.remove(pellet)
                self.pacman.score += 10
                
        # Power pellets
        for pellet in self.power_pellets[:]:
            if (pellet[0] == pacman_grid_x and pellet[1] == pacman_grid_y):
                self.power_pellets.remove(pellet)
                self.pacman.score += 50
                # Make ghosts frightened
                for ghost in self.ghosts:
                    ghost.state = "FRIGHTENED"
                    ghost.frightened_timer = 6.0
                    
        # Ghost collisions
        pacman_rect = pygame.Rect(self.pacman.x - 8, self.pacman.y - 8, 16, 16)
        for ghost in self.ghosts:
            ghost_rect = pygame.Rect(ghost.x - 8, ghost.y - 8, 16, 16)
            if pacman_rect.colliderect(ghost_rect):
                if ghost.state == "FRIGHTENED":
                    # Eat ghost
                    ghost.state = "EATEN"
                    self.pacman.score += 200
                else:
                    # Lose life
                    self.pacman.lives -= 1
                    if self.pacman.lives <= 0:
                        self.game_over = True
                    else:
                        self._reset_positions()
                        
    def _reset_positions(self):
        self.pacman.x = 13 * TILE_SIZE + TILE_SIZE // 2
        self.pacman.y = 23 * TILE_SIZE + TILE_SIZE // 2
        self.pacman.direction = [1, 0]
        
        ghost_positions = [(13, 11), (11, 11), (15, 11), (13, 13)]
        for i, ghost in enumerate(self.ghosts):
            ghost.x = ghost_positions[i][0] * TILE_SIZE + TILE_SIZE // 2
            ghost.y = ghost_positions[i][1] * TILE_SIZE + TILE_SIZE // 2
            ghost.state = "CHASE"
            ghost.frightened_timer = 0
            
    def draw_maze(self):
        for y, row in enumerate(MAZE):
            for x, cell in enumerate(row):
                if cell == '#':
                    pygame.draw.rect(self.screen, BLUE, 
                                   (x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE))
                    
    def draw_pellets(self):
        # Animate pellets
        pulse = abs(math.sin(pygame.time.get_ticks() * 0.01))
        
        for pellet in self.pellets:
            x = pellet[0] * TILE_SIZE + TILE_SIZE // 2
            y = pellet[1] * TILE_SIZE + TILE_SIZE // 2
            pygame.draw.circle(self.screen, PELLET_COLOR, (x, y), 2)
            
        for pellet in self.power_pellets:
            x = pellet[0] * TILE_SIZE + TILE_SIZE // 2
            y = pellet[1] * TILE_SIZE + TILE_SIZE // 2
            radius = 4 + int(2 * pulse)
            pygame.draw.circle(self.screen, POWER_COLOR, (x, y), radius)
            
    def draw_ui(self):
        # Score
        score_text = self.font.render(f"Score: {self.pacman.score}", True, WHITE)
        self.screen.blit(score_text, (10, 10))
        
        # Lives
        lives_text = self.font.render(f"Lives: {self.pacman.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 50))
        
        # Level
        level_text = self.font.render(f"Level: {self.level}", True, WHITE)
        self.screen.blit(level_text, (10, 90))
        
        # Mode
        mode_text = self.small_font.render(f"Mode: {self.mode}", True, WHITE)
        self.screen.blit(mode_text, (10, 130))
        
        if self.paused:
            pause_text = self.font.render("PAUSED", True, WHITE)
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(pause_text, text_rect)
            
        if self.game_over:
            game_over_text = self.font.render("GAME OVER", True, RED)
            restart_text = self.small_font.render("Press R to restart", True, WHITE)
            text_rect = game_over_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20))
            restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20))
            self.screen.blit(game_over_text, text_rect)
            self.screen.blit(restart_text, restart_rect)
            
    def run(self):
        running = True
        while running:
            dt = self.clock.tick(60) / 1000.0
            
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_p:
                        self.paused = not self.paused
                    elif event.key == pygame.K_r and self.game_over:
                        self.__init__()
                        
            if not self.paused and not self.game_over:
                # Update game
                self.pacman.update(dt, MAZE)
                self.update_mode(dt)
                
                for ghost in self.ghosts:
                    if ghost.state != "EATEN":
                        ghost.update(dt, MAZE, self.pacman, self.mode)
                        
                self.check_collisions()
                
                # Check win condition
                if len(self.pellets) == 0 and len(self.power_pellets) == 0:
                    self.level += 1
                    self.pellets = self._create_pellets()
                    self.power_pellets = self._create_power_pellets()
                    self._reset_positions()
                    
            # Draw everything
            self.screen.fill(BLACK)
            self.draw_maze()
            self.draw_pellets()
            self.pacman.draw(self.screen)
            
            for ghost in self.ghosts:
                if ghost.state != "EATEN":
                    ghost.draw(self.screen)
                    
            self.draw_ui()
            
            pygame.display.flip()
            
        pygame.quit()

if __name__ == "__main__":
    game = Game()
    game.run()
