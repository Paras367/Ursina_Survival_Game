# Skyreach Frontier

A first-person survival game built with Ursina.

## Overview

`Skyreach Frontier` is a small open-world survival experience built in Python using the Ursina game engine. The player explores a procedurally generated map, collects coins, fights enemies, and can save/continue progress between sessions.

## Features

- Procedural world generation with trees, rocks, buildings, mountains, water, and coins
- First-person movement with sprinting, jumping, and camera bob
- Two weapons: gun and sword
- Health, stamina, XP, level progression, score, and coin collection
- Save and continue support using `savegame.json`
- Pause, settings, game over, and victory menus

## Requirements

- Python 3.10+ (recommended)
- `ursina` 6.1.2 or newer

Install dependencies with:

```bash
pip install -r requirements.txt
```

## Running the Game

From the project root:

```bash
python main.py
```

## Controls

- Move: `W`, `A`, `S`, `D`
- Jump: `Space`
- Sprint: `Left Shift`
- Fire Gun: `Left Mouse Button`
- Sword Swing: `Right Mouse Button`
- Switch Weapon: `Q`
- Reload: `R`
- Pause / Menu: `Escape`
- Interact: `E`

## Objective

- Collect coins
- Defeat enemies to earn score and XP
- Reach the win conditions by meeting the score or coin target
- Save your progress from the pause menu and continue later from the main menu

## Project Structure

- `main.py` - game entry point and state manager
- `settings.py` - game constants, world parameters, and keybind documentation
- `player.py` - player controller, weapons, stamina, health, progression
- `world.py` - procedural world generation and collectible placement
- `enemy.py` - enemy behavior, spawning, and combat
- `weapons.py` - gun and sword weapon logic
- `audio.py` - audio management and sound playback
- `effects.py` - visual effects, screen flash, and camera shake
- `save_system.py` - save/load game state to `savegame.json`
- `ui.py` - HUD and menu screens
- `requirements.txt` - Python dependency list

## Notes

- The game stores save data in `savegame.json` in the project directory.
- If `savegame.json` is missing, the game starts a new session.

Enjoy playing and experimenting with the game settings in `settings.py`!
