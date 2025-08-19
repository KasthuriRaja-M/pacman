from __future__ import annotations

import math


def clamp(value: float, lo: float, hi: float) -> float:
	return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
	return a + (b - a) * t


def ease_in_out_sine(t: float) -> float:
	return -(math.cos(math.pi * t) - 1) / 2


def ping_pong(t: float) -> float:
	t = t % 2.0
	return t if t < 1.0 else 2.0 - t
