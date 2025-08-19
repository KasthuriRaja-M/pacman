from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Iterable

import pygame

from . import config
from .assets import draw_glow_rect


# Legend:
# '#': wall
# '.': pellet
# 'o': power pellet
# ' ': empty path
# 'G': ghost house door
# 'H': ghost house interior
# 'S': Pacman start
# 'B','I','P','C': ghost spawns (Blinky, Inky, Pinky, Clyde)

MAZE_LAYOUT = [
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
	"      .   #  S   #   .      ",
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
	"############################",
	"                            ",
	"                            ",
	"                            ",
]


@dataclass
class Maze:
	grid: List[str]
	pellets: List[Tuple[int, int]]
	power_pellets: List[Tuple[int, int]]
	pacman_start: Tuple[int, int]
	ghost_starts: dict
	ghost_house_door: Tuple[int, int]

	@classmethod
	def load(cls) -> "Maze":
		grid = MAZE_LAYOUT
		pellets: List[Tuple[int, int]] = []
		power: List[Tuple[int, int]] = []
		pacman = (13, 23)
		ghosts = {"B": (13, 11), "I": (15, 11), "P": (11, 11), "C": (13, 13)}
		door = (13, 13)
		for y, row in enumerate(grid):
			for x, ch in enumerate(row):
				if ch == ".":
					pellets.append((x, y))
				elif ch == "o":
					power.append((x, y))
				elif ch == "S":
					pacman = (x, y)
				elif ch in "BIPC":
					ghosts[ch] = (x, y)
				elif ch == "G":
					door = (x, y)
		return cls(grid, pellets, power, pacman, ghosts, door)

	def is_wall(self, tx: int, ty: int) -> bool:
		if ty < 0 or ty >= config.GRID_ROWS or tx < 0 or tx >= config.GRID_COLS:
			return True
		return self.grid[ty][tx] == "#"

	def is_tunnel(self, tx: int, ty: int) -> bool:
		return ty == 9 and (tx < 1 or tx > config.GRID_COLS - 2)

	def is_door(self, tx: int, ty: int) -> bool:
		return self.grid[ty][tx] == "G"

	def in_house(self, tx: int, ty: int) -> bool:
		return self.grid[ty][tx] == "H"

	def draw(self, surface: pygame.Surface, time_s: float) -> None:
		tile = config.TILE_SIZE
		# Background
		surface.fill(config.DARK_BG)
		# Walls with glow
		for y, row in enumerate(self.grid):
			for x, ch in enumerate(row):
				if ch == "#":
					rect = pygame.Rect(x * tile, y * tile, tile, tile)
					draw_glow_rect(surface, rect, config.WALL_BLUE, config.WALL_GLOW, thickness=2)

		# Pellets
		phase = (pygame.time.get_ticks() % 1000) / 1000.0
		for (px, py) in self.pellets:
			cx = px * tile + tile // 2
			cy = py * tile + tile // 2
			pygame.draw.circle(surface, config.PELLET_COLOR, (cx, cy), 2)
		for (px, py) in self.power_pellets:
			cx = px * tile + tile // 2
			cy = py * tile + tile // 2
			r = 5 + int(2 * abs(0.5 - phase) * 2)
			pygame.draw.circle(surface, config.POWER_COLOR, (cx, cy), r)

	def remove_pellet(self, tx: int, ty: int) -> bool:
		if (tx, ty) in self.pellets:
			self.pellets.remove((tx, ty))
			return True
		return False

	def remove_power(self, tx: int, ty: int) -> bool:
		if (tx, ty) in self.power_pellets:
			self.power_pellets.remove((tx, ty))
			return True
		return False

	def pellets_remaining(self) -> int:
		return len(self.pellets) + len(self.power_pellets)

	def neighbors4(self, tx: int, ty: int) -> Iterable[Tuple[int, int]]:
		for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
			ntx, nty = tx + dx, ty + dy
			if 0 <= ntx < config.GRID_COLS and 0 <= nty < config.GRID_ROWS and not self.is_wall(ntx, nty) and not self.is_door(ntx, nty):
				yield (ntx, nty)
