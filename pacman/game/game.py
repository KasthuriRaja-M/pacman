from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import pygame

from . import config
from .assets import Sounds
from .entities import Pacman, Ghost
from .maze import Maze
from .ui import UI


@dataclass
class ModeTimer:
	segments: List[tuple]
	idx: int = 0
	remaining: float = 0.0

	def __init__(self, segments: List[tuple]):
		self.segments = segments
		self.idx = 0
		self.remaining = segments[0][0]

	def current(self) -> str:
		return self.segments[self.idx][1]

	def update(self, dt: float) -> str:
		self.remaining -= dt
		if self.remaining <= 0 and self.idx < len(self.segments) - 1:
			self.idx += 1
			self.remaining = self.segments[self.idx][0]
		return self.current()


class Game:
	def __init__(self):
		self.maze = Maze.load()
		self.ui = UI()
		self.level = 1
		self.pacman = Pacman(*self.maze.pacman_start)
		self.ghosts: List[Ghost] = [
			Ghost("Blinky", config.GHOST_RED, *self.maze.ghost_starts.get("B", (13, 11)), corner=(25, 1)),
			Ghost("Pinky", config.GHOST_PINK, *self.maze.ghost_starts.get("P", (11, 11)), corner=(2, 1)),
			Ghost("Inky", config.GHOST_CYAN, *self.maze.ghost_starts.get("I", (15, 11)), corner=(25, 29)),
			Ghost("Clyde", config.GHOST_ORANGE, *self.maze.ghost_starts.get("C", (13, 13)), corner=(2, 29)),
		]
		self.mode_timer = ModeTimer(config.SCATTER_CHASE_TIMINGS)
		self.paused = False
		self.game_over = False

	def on_key_down(self, key: int) -> None:
		if key == config.KEY_PAUSE:
			self.paused = not self.paused
		elif key == config.KEY_RESTART and self.game_over:
			self.__init__()

	def _handle_input(self):
		keys = pygame.key.get_pressed()
		self.pacman.handle_input(keys)

	def _update_mode(self, dt: float) -> str:
		return self.mode_timer.update(dt)

	def _reset_positions(self):
		self.pacman = Pacman(*self.maze.pacman_start)
		starts = self.maze.ghost_starts
		self.ghosts = [
			Ghost("Blinky", config.GHOST_RED, *starts.get("B", (13, 11)), corner=(25, 1)),
			Ghost("Pinky", config.GHOST_PINK, *starts.get("P", (11, 11)), corner=(2, 1)),
			Ghost("Inky", config.GHOST_CYAN, *starts.get("I", (15, 11)), corner=(25, 29)),
			Ghost("Clyde", config.GHOST_ORANGE, *starts.get("C", (13, 13)), corner=(2, 29)),
		]

	def update(self, dt: float) -> None:
		if self.paused or self.game_over:
			return
		self._handle_input()
		mode = self._update_mode(dt)

		self.pacman.move(self.maze, dt)

		# Pellets
		tx, ty = self.pacman.center_tile()
		if self.maze.remove_pellet(tx, ty):
			self.pacman.score += 10
			Sounds.play_waka()
		if self.maze.remove_power(tx, ty):
			self.pacman.score += 50
			for g in self.ghosts:
				g.set_frightened()
			Sounds.play_power()

		# Ghosts
		blinky = next((g for g in self.ghosts if g.name == "Blinky"), None)
		for g in self.ghosts:
			g.update(self.maze, self.pacman, blinky, mode, dt)

		# Collisions
		p_rect = self.pacman.rect()
		for g in self.ghosts:
			if p_rect.colliderect(g.rect()):
				if g.state == "FRIGHTENED":
					g.state = "EATEN"
					self.pacman.score += 200
					Sounds.play_eat_ghost()
				else:
					self.pacman.lives -= 1
					if self.pacman.lives <= 0:
						self.game_over = True
						return
					self._reset_positions()
					return

		# Win condition
		if self.maze.pellets_remaining() == 0:
			self.level += 1
			self.maze = Maze.load()
			self._reset_positions()
			Sounds.play_extra()

	def draw(self, window: pygame.Surface) -> None:
		# Render at base resolution then scale with the window
		base = pygame.Surface((config.BASE_WIDTH, config.BASE_HEIGHT))
		self.maze.draw(base, pygame.time.get_ticks() / 1000.0)
		for g in self.ghosts:
			g.draw(base, pygame.time.get_ticks() / 1000.0)
		self.pacman.draw(base, pygame.time.get_ticks() / 1000.0)
		self.ui.draw_hud(base, self.pacman.score, self.pacman.lives, self.level, self.paused)

		# Scale to fit window while preserving aspect
		w, h = window.get_size()
		scaled = pygame.transform.smoothscale(base, (w, h))
		window.blit(scaled, (0, 0))

		if self.game_over:
			self.ui.draw_message(window, "GAME OVER - Press R to restart")
