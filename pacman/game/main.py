from __future__ import annotations

import sys
import pygame

from . import config
from .game import Game


def main() -> int:
	pygame.mixer.pre_init(44100, -16, 2, 512)
	pygame.init()
	pygame.font.init()

	flags = pygame.SCALED | pygame.RESIZABLE
	window = pygame.display.set_mode((config.BASE_WIDTH * config.WINDOW_SCALE, config.BASE_HEIGHT * config.WINDOW_SCALE), flags)
	pygame.display.set_caption("Pacman - Python Edition")

	clock = pygame.time.Clock()
	game = Game()

	running = True
	while running:
		dt = clock.tick(config.TARGET_FPS) / 1000.0

		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				running = False
			elif event.type == pygame.KEYDOWN:
				if event.key == pygame.K_ESCAPE:
					running = False
				game.on_key_down(event.key)

		game.update(dt)
		game.draw(window)
		pygame.display.flip()

	pygame.quit()
	return 0


if __name__ == "__main__":
	sys.exit(main())
