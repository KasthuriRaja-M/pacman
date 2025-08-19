from __future__ import annotations

from collections import deque
from typing import Dict, Iterable, List, Optional, Tuple

from . import config


def grid_to_pixel(tx: int, ty: int) -> Tuple[int, int]:
	x = tx * config.TILE_SIZE + config.TILE_SIZE // 2
	y = ty * config.TILE_SIZE + config.TILE_SIZE // 2
	return x, y


def pixel_to_grid(px: float, py: float) -> Tuple[int, int]:
	tx = int(px // config.TILE_SIZE)
	ty = int(py // config.TILE_SIZE)
	return tx, ty


def bfs(start: Tuple[int, int], goal: Tuple[int, int], passable) -> List[Tuple[int, int]]:
	if start == goal:
		return [start]
	frontier = deque([start])
	came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
	while frontier:
		current = frontier.popleft()
		if current == goal:
			break
		cx, cy = current
		for dx, dy in ((1,0),(-1,0),(0,1),(0,-1)):
			nx, ny = cx + dx, cy + dy
			if (nx, ny) not in came_from and passable(nx, ny):
				came_from[(nx, ny)] = current
				frontier.append((nx, ny))
	if goal not in came_from:
		return [start]
	# Reconstruct
	path = []
	node = goal
	while node is not None:
		path.append(node)
		node = came_from[node]
	path.reverse()
	return path


def next_step_towards(start: Tuple[int, int], goal: Tuple[int, int], passable) -> Tuple[int, int]:
	path = bfs(start, goal, passable)
	if len(path) >= 2:
		return path[1]
	return start
