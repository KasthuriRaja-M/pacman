from __future__ import annotations

import math
import struct
from typing import Dict, Tuple

import pygame

from . import config


class SurfaceCache:
	_surfaces: Dict[Tuple[str, Tuple], pygame.Surface] = {}

	@classmethod
	def get(cls, key: Tuple[str, Tuple], factory) -> pygame.Surface:
		if key not in cls._surfaces:
			cls._surfaces[key] = factory()
		return cls._surfaces[key]


def make_pacman_surface(radius: int, mouth_ratio: float, facing: Tuple[int, int]) -> pygame.Surface:
	def factory() -> pygame.Surface:
		diameter = radius * 2
		surf = pygame.Surface((diameter, diameter), pygame.SRCALPHA)
		mouth_angle = max(0.0, min(0.45, mouth_ratio)) * math.pi
		start_angle = mouth_angle
		end_angle = 2 * math.pi - mouth_angle
		# Facing adjustments
		if facing == (1, 0):
			rotation = 0
		elif facing == (-1, 0):
			rotation = math.pi
		elif facing == (0, -1):
			rotation = -math.pi / 2
		else:
			rotation = math.pi / 2
		start_angle += rotation
		end_angle += rotation
		points = [(radius, radius)]
		segments = 40
		for i in range(segments + 1):
			angle = start_angle + (end_angle - start_angle) * (i / segments)
			x = radius + radius * math.cos(angle)
			y = radius + radius * math.sin(angle)
			points.append((x, y))
		pygame.draw.polygon(surf, config.PACMAN_COLOR, points)
		return surf

	key = ("pacman", (radius, round(mouth_ratio, 3), facing))
	return SurfaceCache.get(key, factory)


def make_ghost_surface(width: int, height: int, color: Tuple[int, int, int], frightened: bool = False, blink: bool = False) -> pygame.Surface:
	def factory() -> pygame.Surface:
		surf = pygame.Surface((width, height), pygame.SRCALPHA)
		body_color = color
		if frightened:
			body_color = config.FRIGHTENED_WHITE if blink else config.FRIGHTENED_BLUE
		# Body
		radius = width // 2
		pygame.draw.circle(surf, body_color, (radius, radius), radius)
		pygame.draw.rect(surf, body_color, pygame.Rect(0, radius, width, height - radius))
		# Wavy bottom
		bumps = 4
		bump_w = width / bumps
		for i in range(bumps):
			cx = int((i + 0.5) * bump_w)
			cy = height - radius // 3
			pygame.draw.circle(surf, (0, 0, 0, 0), (cx, cy), radius // 3)
		# Eyes
		eye_w = width // 4
		eye_h = height // 3
		eye_y = height // 2
		pygame.draw.ellipse(surf, (255, 255, 255), pygame.Rect(width // 4 - eye_w // 2, eye_y - eye_h // 2, eye_w, eye_h))
		pygame.draw.ellipse(surf, (255, 255, 255), pygame.Rect(3 * width // 4 - eye_w // 2, eye_y - eye_h // 2, eye_w, eye_h))
		pupil_r = max(2, width // 12)
		for ex in (width // 4, 3 * width // 4):
			pygame.draw.circle(surf, (40, 60, 200), (ex, eye_y), pupil_r)
		return surf

	key = ("ghost", (width, height, color, frightened, blink))
	return SurfaceCache.get(key, factory)


def draw_glow_rect(surface: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], glow_color: Tuple[int, int, int], thickness: int = 2):
	pygame.draw.rect(surface, color, rect, thickness, border_radius=2)
	# Soft glow
	for i in range(1, 6):
		alpha = max(10, 60 - i * 10)
		glow = pygame.Surface((rect.width + i * 4, rect.height + i * 4), pygame.SRCALPHA)
		pygame.draw.rect(glow, (*glow_color, alpha), glow.get_rect(), width=2, border_radius=2)
		surface.blit(glow, (rect.x - i * 2, rect.y - i * 2))


# Simple sound synthesis without numpy

def _tone(frequency: float, duration: float, volume: float = 0.5) -> pygame.mixer.Sound:
	sample_rate = 44100
	num_samples = max(1, int(sample_rate * duration))
	amplitude = int(32767 * volume)
	frames = bytearray()
	for i in range(num_samples):
		phase = 2.0 * math.pi * frequency * (i / sample_rate)
		value = amplitude if math.sin(phase) >= 0.0 else -amplitude
		frames += struct.pack('<hh', value, value)  # stereo
	return pygame.mixer.Sound(buffer=bytes(frames))


class Sounds:
	initialized = False
	waka_toggle = False
	waka1: pygame.mixer.Sound | None = None
	waka2: pygame.mixer.Sound | None = None
	power: pygame.mixer.Sound | None = None
	eat_ghost: pygame.mixer.Sound | None = None
	extra: pygame.mixer.Sound | None = None

	@classmethod
	def init(cls) -> None:
		if cls.initialized:
			return
		cls.waka1 = _tone(440, 0.05, 0.3)
		cls.waka2 = _tone(520, 0.05, 0.3)
		cls.power = _tone(220, 0.2, 0.25)
		cls.eat_ghost = _tone(880, 0.2, 0.35)
		cls.extra = _tone(1320, 0.15, 0.4)
		cls.initialized = True

	@classmethod
	def play_waka(cls):
		if not cls.initialized:
			cls.init()
		(cls.waka1 if cls.waka_toggle else cls.waka2).play()
		cls.waka_toggle = not cls.waka_toggle

	@classmethod
	def play_power(cls):
		if not cls.initialized:
			cls.init()
		cls.power.play()

	@classmethod
	def play_eat_ghost(cls):
		if not cls.initialized:
			cls.init()
		cls.eat_ghost.play()

	@classmethod
	def play_extra(cls):
		if not cls.initialized:
			cls.init()
		cls.extra.play()
