from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

import pygame

from . import config
from .assets import make_pacman_surface, make_ghost_surface, Sounds
from .effects import ping_pong
from .pathfinding import grid_to_pixel, pixel_to_grid, next_step_towards


Vec2 = Tuple[float, float]
Dir = Tuple[int, int]


def sign(value: float) -> int:
	return -1 if value < 0 else (1 if value > 0 else 0)


@dataclass
class Actor:
	x: float
	y: float
	vx: float
	vy: float
	direction: Dir
	speed: float

	def rect(self) -> pygame.Rect:
		return pygame.Rect(int(self.x) - 7, int(self.y) - 7, 14, 14)

	def center_tile(self) -> Tuple[int, int]:
		return pixel_to_grid(self.x, self.y)

	def at_tile_center(self) -> bool:
		px = self.x - (self.center_tile()[0] * config.TILE_SIZE + config.TILE_SIZE // 2)
		py = self.y - (self.center_tile()[1] * config.TILE_SIZE + config.TILE_SIZE // 2)
		return abs(px) < 1.0 and abs(py) < 1.0


class Pacman(Actor):
	mouth_phase: float = 0.0
	pending_dir: Dir = (0, 0)
	lives: int = 3
	score: int = 0
	respawning: bool = False

	def __init__(self, px: int, py: int):
		cx, cy = grid_to_pixel(px, py)
		super().__init__(cx, cy, 0.0, 0.0, (1, 0), config.PACMAN_SPEED)

	def handle_input(self, keys: pygame.key.ScancodeWrapper):
		dir_map = {
			pygame.K_LEFT: (-1, 0),
			pygame.K_RIGHT: (1, 0),
			pygame.K_UP: (0, -1),
			pygame.K_DOWN: (0, 1),
		}
		for k, d in dir_map.items():
			if keys[k]:
				self.pending_dir = d

	def try_turn(self, maze) -> None:
		if self.pending_dir == (0, 0):
			return
		if not self.at_tile_center():
			return
		tx, ty = self.center_tile()
		dx, dy = self.pending_dir
		ntx, nty = tx + dx, ty + dy
		if not maze.is_wall(ntx, nty) and not maze.is_door(ntx, nty):
			self.direction = self.pending_dir

	def move(self, maze, dt: float) -> None:
		self.try_turn(maze)
		dx, dy = self.direction
		speed = self.speed
		if maze.is_tunnel(*self.center_tile()):
			speed = config.TUNNEL_SPEED
		# Intended new position
		next_x = self.x + dx * speed * dt
		next_y = self.y + dy * speed * dt
		tx, ty = self.center_tile()
		cx = tx * config.TILE_SIZE + config.TILE_SIZE // 2
		cy = ty * config.TILE_SIZE + config.TILE_SIZE // 2
		# Horizontal collision against walls ahead, clamp to center
		if dx != 0:
			ahead_tile = (tx + dx, ty)
			if maze.is_wall(*ahead_tile) or maze.is_door(*ahead_tile):
				if dx > 0 and next_x > cx:
					next_x = cx
					dx = 0
				elif dx < 0 and next_x < cx:
					next_x = cx
					dx = 0
		# Vertical collision
		if dy != 0:
			ahead_tile = (tx, ty + dy)
			if maze.is_wall(*ahead_tile) or maze.is_door(*ahead_tile):
				if dy > 0 and next_y > cy:
					next_y = cy
					dy = 0
				elif dy < 0 and next_y < cy:
					next_y = cy
					dy = 0
		self.direction = (dx, dy)
		self.x = next_x
		self.y = next_y
		# Wrap tunnel
		if self.y // config.TILE_SIZE == 9:
			if self.x < -8:
				self.x = config.BASE_WIDTH + 8
			elif self.x > config.BASE_WIDTH + 8:
				self.x = -8

	def draw(self, surface: pygame.Surface, time_s: float) -> None:
		self.mouth_phase += 8.0 / 60.0
		mouth = 0.25 * abs(ping_pong(self.mouth_phase) - 0.5) * 2
		surf = make_pacman_surface(8, mouth, self.direction)
		rect = surf.get_rect(center=(int(self.x), int(self.y)))
		surface.blit(surf, rect)


class Ghost(Actor):
	name: str
	color: Tuple[int, int, int]
	state: str = "SCATTER"  # SCATTER, CHASE, FRIGHTENED, EATEN
	fright_time: float = 0.0
	blink: bool = False
	spawn_tile: Tuple[int, int]
	target_corner: Tuple[int, int]
	home_tile: Tuple[int, int]

	def __init__(self, name: str, color: Tuple[int, int, int], px: int, py: int, corner: Tuple[int, int]):
		cx, cy = grid_to_pixel(px, py)
		super().__init__(cx, cy, 0.0, 0.0, (-1, 0), config.GHOST_SPEED)
		self.name = name
		self.color = color
		self.spawn_tile = (px, py)
		self.target_corner = corner
		self.home_tile = (13, 11)

	def set_frightened(self):
		if self.state != "EATEN":
			self.state = "FRIGHTENED"
			self.fright_time = config.POWER_DURATION
			self.blink = False

	def update(self, maze, pac: Pacman, blinky: Optional["Ghost"], mode: str, dt: float):
		if self.state == "EATEN":
			# Go to house
			goal = self.home_tile
			self._move_towards_tile(maze, goal, dt, speed=self.speed * 1.2)
			if self.center_tile() == goal:
				self.state = mode
			return
		if self.state == "FRIGHTENED":
			self.fright_time -= dt
			self.blink = self.fright_time < (config.POWER_DURATION - config.FRIGHTENED_FLASH_START)
			# Randomish: head away from Pacman
			ptx, pty = pac.center_tile()
			tx, ty = self.center_tile()
			choices = []
			for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
				nt = (tx + dx, ty + dy)
				if not maze.is_wall(*nt) and not maze.is_door(*nt):
					choices.append(nt)
			if choices:
				choices.sort(key=lambda c: -(abs(c[0]-ptx)+abs(c[1]-pty)))
				next_tile = choices[0]
				self._move_to_next_tile(maze, next_tile, dt, speed=config.FRIGHTENED_SPEED)
			if self.fright_time <= 0:
				self.state = mode
			return
		# Normal (scatter/chase)
		if mode in ("SCATTER", "CHASE"):
			goal = self._compute_target_tile(maze, pac, blinky, mode)
			self._move_towards_tile(maze, goal, dt, speed=self.speed)

	def _compute_target_tile(self, maze, pac: Pacman, blinky: Optional["Ghost"], mode: str) -> Tuple[int, int]:
		if mode == "SCATTER":
			return self.target_corner
		# CHASE
		ptx, pty = pac.center_tile()
		dx, dy = pac.direction
		if self.name == "Blinky":
			return (ptx, pty)
		elif self.name == "Pinky":
			return (ptx + 4 * dx, pty + 4 * dy)
		elif self.name == "Inky":
			if blinky is None:
				return (ptx, pty)
			btx, bty = blinky.center_tile()
			ref = (ptx + 2 * dx, pty + 2 * dy)
			return (ref[0] + (ref[0] - btx), ref[1] + (ref[1] - bty))
		elif self.name == "Clyde":
			tx, ty = self.center_tile()
			dist = abs(tx - ptx) + abs(ty - pty)
			return (ptx, pty) if dist > 8 else self.target_corner
		return (ptx, pty)

	def _move_towards_tile(self, maze, goal_tile: Tuple[int, int], dt: float, speed: float):
		current = self.center_tile()
		next_tile = next_step_towards(current, goal_tile, lambda x,y: (0 <= x < 28 and 0 <= y < 31) and (not maze.is_wall(x, y)) and (not maze.is_door(x, y)))
		self._move_to_next_tile(maze, next_tile, dt, speed)

	def _move_to_next_tile(self, maze, next_tile: Tuple[int, int], dt: float, speed: float):
		tx, ty = self.center_tile()
		dx = sign(next_tile[0] - tx)
		dy = sign(next_tile[1] - ty)
		self.direction = (dx, dy)
		if maze.is_tunnel(*self.center_tile()):
			speed = config.TUNNEL_SPEED
		self.x += dx * speed * dt
		self.y += dy * speed * dt
		# Wrap tunnel
		if self.y // config.TILE_SIZE == 9:
			if self.x < -8:
				self.x = config.BASE_WIDTH + 8
			elif self.x > config.BASE_WIDTH + 8:
				self.x = -8

	def draw(self, surface: pygame.Surface, time_s: float) -> None:
		fright = self.state == "FRIGHTENED"
		blink = self.blink and (int(pygame.time.get_ticks() / 120) % 2 == 0)
		surf = make_ghost_surface(16, 16, self.color, frightened=fright, blink=blink)
		rect = surf.get_rect(center=(int(self.x), int(self.y)))
		surface.blit(surf, rect)
