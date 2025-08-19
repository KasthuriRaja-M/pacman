# Pac-Man (Python, Pygame)

A production-quality, fully playable 2D Pac-Man implemented with Pygame. It features smooth animations, procedural sprites, ghost AI (scatter/chase/frightened), juicy UI with glow effects, and synthesized retro sounds.

## Features
- Classic maze with pellets and power pellets
- 4 ghosts with differentiated chase behaviors (Blinky, Pinky, Inky, Clyde)
- Scatter/Chase mode timer and frightened mode with blinking
- Smooth movement with tunnel wrap and precise wall collisions
- Procedural sprites (no external assets) and soft-glow wall aesthetic
- HUD: score, lives, level; pause overlay; game over and restart

## Requirements
- Python 3.10+ recommended
- Windows, macOS, or Linux with a working SDL2 (Pygame) environment

## Install
On Windows without Python in PATH, install Python from Microsoft Store or `python.org` and check "Add to PATH".

Then in a terminal from the repo root:

```bash
python -m pip install -r pacman/requirements.txt
```

If `python` is not found, try:

```bash
py -3 -m pip install -r pacman/requirements.txt
```

## Run
From repo root:

```bash
python pacman\run.py
```

Or with the Windows launcher:

```bash
py -3 pacman\run.py
```

## Controls
- Arrow keys: Move
- P: Pause
- R: Restart (after Game Over)
- Esc: Quit

## Notes
- The game renders to a base canvas and scales to window size. Resize freely.
- Sounds are generated procedurally; mute system sound if needed.

## Project Structure
- `pacman/game/` core modules (config, entities, maze, pathfinding, ui, assets, game)
- `pacman/run.py` entrypoint
- `pacman/requirements.txt` pinned dependencies

Enjoy!
