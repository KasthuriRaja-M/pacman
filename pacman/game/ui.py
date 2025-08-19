from __future__ import annotations

import pygame

from . import config


class UI:
	def __init__(self):
		self.font = pygame.font.SysFont("Arial", 14)
		self.big = pygame.font.SysFont("Arial", 24, bold=True)

	def draw_hud(self, surface: pygame.Surface, score: int, lives: int, level: int, paused: bool, high_score: int, fps: float | None = None):
		w = surface.get_width()
		h = surface.get_height()
		# HUD bar background
		pygame.draw.rect(surface, (10, 10, 30), pygame.Rect(0, h - config.HUD_HEIGHT, w, config.HUD_HEIGHT))
		text = self.font.render(f"Score: {score}", True, config.HUD_TEXT)
		surface.blit(text, (8, h - config.HUD_HEIGHT + 8))
		hs = self.font.render(f"High: {high_score}", True, config.HUD_TEXT)
		surface.blit(hs, (120, h - config.HUD_HEIGHT + 8))
		lvl = self.font.render(f"Level: {level}", True, config.HUD_DIM)
		surface.blit(lvl, (w // 2 - 30, h - config.HUD_HEIGHT + 8))
		# Lives
		for i in range(lives):
			pygame.draw.circle(surface, config.PACMAN_COLOR, (w - 18 - i * 18, h - config.HUD_HEIGHT // 2), 6)

		if fps is not None:
			fps_text = self.font.render(f"{fps:.0f} FPS", True, (180, 255, 180))
			surface.blit(fps_text, (w - 70, h - config.HUD_HEIGHT + 8))

		if paused:
			overlay = pygame.Surface((w, h), pygame.SRCALPHA)
			overlay.fill((0, 0, 0, 120))
			surface.blit(overlay, (0, 0))
			p = self.big.render("PAUSED", True, (255, 255, 255))
			surface.blit(p, p.get_rect(center=(w // 2, h // 2)))

	def draw_message(self, surface: pygame.Surface, text: str):
		w = surface.get_width()
		h = surface.get_height()
		msg = self.big.render(text, True, (255, 255, 255))
		surface.blit(msg, msg.get_rect(center=(w // 2, h // 2 - 40)))
