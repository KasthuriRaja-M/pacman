from __future__ import annotations

import sys
import os
import time
import pygame

from . import config
from .game import Game


def _save_screenshot(window: pygame.Surface) -> None:
	os.makedirs(config.SCREENSHOT_DIR, exist_ok=True)
	ts = time.strftime("%Y%m%d-%H%M%S")
	path = os.path.join(config.SCREENSHOT_DIR, f"screenshot-{ts}.png")
	pygame.image.save(window, path)
	print(f"Saved screenshot: {path}")


def main() -> int:
	pygame.mixer.pre_init(44100, -16, 2, 512)
	pygame.init()
	pygame.font.init()

	flags = pygame.SCALED | pygame.RESIZABLE
	window = pygame.display.set_mode((config.BASE_WIDTH * config.WINDOW_SCALE, config.BASE_HEIGHT * config.WINDOW_SCALE), flags)
	pygame.display.set_caption("Pacman - Python Edition")

	clock = pygame.time.Clock()
	game = Game()
	fullscreen = False

	running = True
	while running:
		dt = clock.tick(config.TARGET_FPS) / 1000.0

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				elif event.key == config.KEY_FULLSCREEN:
					fullscreen = not fullscreen
					if fullscreen:
						window = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
					else:
						window = pygame.display.set_mode((config.BASE_WIDTH * config.WINDOW_SCALE, config.BASE_HEIGHT * config.WINDOW_SCALE), pygame.SCALED | pygame.RESIZABLE)
				elif event.key == config.KEY_SCREENSHOT:
					# Save the already-rendered frame on next flip; here we capture the current backbuffer
					_save_screenshot(window)
				else:
					game.on_key_down(event.key)

		fps_val = clock.get_fps()
		game.update(dt)
		game.draw(window, fps_value=fps_val)
		pygame.display.flip()

	pygame.quit()
	return 0


if __name__ == "__main__":
	sys.exit(main())
