from __future__ import annotations

import os
from dataclasses import dataclass
from typing import List, Optional, Set

import pygame

from . import config
from .assets import Sounds
from .entities import Pacman, Ghost, Fruit
from .maze import Maze
from .ui import UI
from .effects import ParticleSystem, screen_shake_offset


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
		self.show_fps = False
		self.high_score = self._load_high_score()
		self.particles = ParticleSystem()
		self.shake_timer = 0.0
		self.fruits: List[Fruit] = []
		self.spawned_thresholds: Set[int] = set()

	def _load_high_score(self) -> int:
		try:
			base = os.path.dirname(os.path.dirname(__file__))
			path = os.path.join(base, "highscore.txt")
			if os.path.exists(path):
				with open(path, "r", encoding="utf-8") as f:
					return int(f.read().strip() or "0")
		except Exception:
			pass
		return 0

	def _save_high_score(self) -> None:
		try:
			base = os.path.dirname(os.path.dirname(__file__))
			path = os.path.join(base, "highscore.txt")
			with open(path, "w", encoding="utf-8") as f:
				f.write(str(self.high_score))
		except Exception:
			pass

	def _add_score(self, points: int):
		self.pacman.score += points
		if self.pacman.score > self.high_score:
			self.high_score = self.pacman.score
			self._save_high_score()

	def on_key_down(self, key: int) -> None:
		if key == config.KEY_PAUSE:
			self.paused = not self.paused
		elif key == config.KEY_RESTART and self.game_over:
			self.__init__()
		elif key == config.KEY_MUTE:
			Sounds.set_muted(not Sounds.muted)
		elif key == config.KEY_TOGGLE_FPS:
			self.show_fps = not self.show_fps

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
		self.fruits.clear()

	def _maybe_spawn_fruit(self):
		remaining = self.maze.pellets_remaining()
		for threshold in config.FRUIT_SPAWN_THRESHOLDS:
			if remaining == threshold and threshold not in self.spawned_thresholds:
				tile = config.FRUIT_SPAWN_TILES[0]
				self.fruits.append(Fruit(tile))
				self.spawned_thresholds.add(threshold)

	def update(self, dt: float) -> None:
		if self.paused or self.game_over:
			return
		self._handle_input()
		mode = self._update_mode(dt)
		self.shake_timer = max(0.0, self.shake_timer - dt)

		self.pacman.move(self.maze, dt)

		# Pellets
		tx, ty = self.pacman.center_tile()
		if self.maze.remove_pellet(tx, ty):
			self._add_score(10)
			self.particles.burst(self.pacman.x, self.pacman.y, config.PELLET_COLOR, count=4)
			Sounds.play_waka()
		if self.maze.remove_power(tx, ty):
			self._add_score(50)
			for g in self.ghosts:
				g.set_frightened()
			self.particles.burst(self.pacman.x, self.pacman.y, config.POWER_COLOR, count=10)
			Sounds.play_power()

		# Fruits lifecycle
		self._maybe_spawn_fruit()
		self.fruits = [f for f in self.fruits if f.update(dt)]

		# Ghosts
		blinky = next((g for g in self.ghosts if g.name == "Blinky"), None)
		for g in self.ghosts:
			g.update(self.maze, self.pacman, blinky, mode, dt)

		# Collisions with ghosts
		p_rect = self.pacman.rect()
		for g in self.ghosts:
			if p_rect.colliderect(g.rect()):
				if g.state == "FRIGHTENED":
					g.state = "EATEN"
					self._add_score(200)
					self.particles.burst(g.x, g.y, g.color, count=12)
					self.shake_timer = max(self.shake_timer, 0.25)
					Sounds.play_eat_ghost()
				else:
					self.pacman.lives -= 1
					self.particles.burst(self.pacman.x, self.pacman.y, (255, 255, 255), count=20)
					self.shake_timer = max(self.shake_timer, 0.6)
					if self.pacman.lives <= 0:
						self.game_over = True
						return
					self._reset_positions()
					return

		# Fruit pickup
		for f in list(self.fruits):
			if p_rect.colliderect(f.rect()):
				self._add_score(config.FRUIT_SCORE)
				self.particles.burst(f.x, f.y, config.FRUIT_COLOR, count=16)
				Sounds.play_extra()
				self.fruits.remove(f)

		# Win condition
		if self.maze.pellets_remaining() == 0:
			self.level += 1
			self.maze = Maze.load()
			self._reset_positions()
			self.spawned_thresholds.clear()
			Sounds.play_extra()

		# Particles
		self.particles.update(dt)

	def draw(self, window: pygame.Surface, fps_value: float | None = None) -> None:
		# Render at base resolution
		base = pygame.Surface((config.BASE_WIDTH, config.BASE_HEIGHT))
		self.maze.draw(base, pygame.time.get_ticks() / 1000.0)
		for f in self.fruits:
			f.draw(base)
		for g in self.ghosts:
			g.draw(base, pygame.time.get_ticks() / 1000.0)
		self.pacman.draw(base, pygame.time.get_ticks() / 1000.0)
		self.particles.draw(base)
		self.ui.draw_hud(base, self.pacman.score, self.pacman.lives, self.level, self.paused, self.high_score, fps_value if self.show_fps else None)

		# Scale to fit window while preserving aspect, with screenshake in screen-space
		w, h = window.get_size()
		scaled = pygame.transform.smoothscale(base, (w, h))
		window.fill(config.DARK_BG)
		offx, offy = screen_shake_offset(self.shake_timer)
		window.blit(scaled, (offx, offy))

		if self.game_over:
			self.ui.draw_message(window, "GAME OVER - Press R to restart")
