from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Tuple

import pygame


def clamp(value: float, lo: float, hi: float) -> float:
	return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
	return a + (b - a) * t


def ease_in_out_sine(t: float) -> float:
	return -(math.cos(math.pi * t) - 1) / 2


def ping_pong(t: float) -> float:
	t = t % 2.0
	return t if t < 1.0 else 2.0 - t


@dataclass
class Particle:
	x: float
	y: float
	vx: float
	vy: float
	life: float
	color: Tuple[int, int, int]
	radius: float

	def update(self, dt: float) -> bool:
		self.x += self.vx * dt
		self.y += self.vy * dt
		self.vy += 20.0 * dt
		self.life -= dt
		return self.life > 0

	def draw(self, surf: pygame.Surface) -> None:
		alpha = int(255 * clamp(self.life / 0.5, 0.0, 1.0))
		col = (*self.color, alpha)
		temp = pygame.Surface((int(self.radius*2+2), int(self.radius*2+2)), pygame.SRCALPHA)
		pygame.draw.circle(temp, col, (int(self.radius)+1, int(self.radius)+1), int(self.radius))
		surf.blit(temp, (self.x - self.radius - 1, self.y - self.radius - 1))


class ParticleSystem:
	def __init__(self):
		self.particles: List[Particle] = []

	def burst(self, x: float, y: float, color: Tuple[int, int, int], count: int = 6):
		for i in range(count):
			angle = (i / count) * math.tau
			spd = 30 + 40 * (i % 3) / 2
			vx = math.cos(angle) * spd
			vy = math.sin(angle) * spd
			self.particles.append(Particle(x, y, vx, vy, 0.5, color, 2))

	def update(self, dt: float):
		self.particles = [p for p in self.particles if p.update(dt)]

	def draw(self, surf: pygame.Surface):
		for p in self.particles:
			p.draw(surf)


def screen_shake_offset(timer: float) -> Tuple[int, int]:
	if timer <= 0:
		return (0, 0)
	mag = 2
	return (int(math.sin(timer * 60) * mag), int(math.cos(timer * 40) * mag))
