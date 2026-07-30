<div align="center">

# SKYREACH FRONTIER

### *A First-Person Survival Game built with Ursina Engine*

<p align="center">
<img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white">
<img src="https://img.shields.io/badge/Ursina-6.1.2+-00C853?style=for-the-badge">
<img src="https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge">
<img src="https://img.shields.io/badge/Status-Playable-success?style=for-the-badge">
</p>

---

</div>

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/readthedocs/readthedocs-original.svg" width="22"> Overview

`Skyreach Frontier` is a small open-world survival experience built in Python using the Ursina game engine. The player explores a procedurally generated map, collects coins, fights enemies, and can save/continue progress between sessions.

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/github/github-original.svg" width="22"> Features

- Procedural world generation with trees, rocks, buildings, mountains, water, and coins
- First-person movement with sprinting, jumping, and camera bob
- Two weapons: gun and sword
- Health, stamina, XP, level progression, score, and coin collection
- Save and continue support using `savegame.json`
- Pause, settings, game over, and victory menus

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="22"> Requirements

| Requirement | Version |
|-------------|---------|
| Python | **3.10+** *(recommended)* |
| Ursina | **6.1.2 or newer** |

Install dependencies with:

```bash
pip install -r requirements.txt
```

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/bash/bash-original.svg" width="22"> Running the Game

From the project root:

```bash
python main.py
```

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/chrome/chrome-original.svg" width="22"> Controls

| Action | Key |
|--------|-----|
| Move | `W` `A` `S` `D` |
| Jump | `Space` |
| Sprint | `Left Shift` |
| Fire Gun | `Left Mouse Button` |
| Sword Swing | `Right Mouse Button` |
| Switch Weapon | `Q` |
| Reload | `R` |
| Pause / Menu | `Escape` |
| Interact | `E` |

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/unity/unity-original.svg" width="22"> Objective

- Collect coins
- Defeat enemies to earn score and XP
- Reach the win conditions by meeting the score or coin target
- Save your progress from the pause menu and continue later from the main menu

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/vscode/vscode-original.svg" width="22"> Project Structure

```text
Skyreach Frontier/
│
├── main.py              # game entry point and state manager
├── settings.py          # game constants, world parameters, and keybind documentation
├── player.py            # player controller, weapons, stamina, health, progression
├── world.py             # procedural world generation and collectible placement
├── enemy.py             # enemy behavior, spawning, and combat
├── weapons.py           # gun and sword weapon logic
├── audio.py             # audio management and sound playback
├── effects.py           # visual effects, screen flash, and camera shake
├── save_system.py       # save/load game state to savegame.json
├── ui.py                # HUD and menu screens
└── requirements.txt     # Python dependency list
```

---

## <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/git/git-original.svg" width="22"> Notes

- The game stores save data in `savegame.json` in the project directory.
- If `savegame.json` is missing, the game starts a new session.

---

<div align="center">

### Built with Python using the Ursina Game Engine

*Enjoy playing and experimenting with the game settings in `settings.py`.*

</div>
