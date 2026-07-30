"""
settings.py
Centralized constants for the whole game. Change values here to customize
gameplay balance, world size, keybinds, colors, etc. without touching logic.
"""

from ursina import Vec3, color

# ---------------------------------------------------------------------------
# WINDOW / ENGINE
# ---------------------------------------------------------------------------
WINDOW_TITLE = "Skyreach Frontier"
FULLSCREEN = False
VSYNC = True
FOV = 90

# ---------------------------------------------------------------------------
# PLAYER
# ---------------------------------------------------------------------------
PLAYER_START_POS = Vec3(0, 5, 0)
PLAYER_WALK_SPEED = 5
PLAYER_RUN_SPEED = 9
PLAYER_JUMP_HEIGHT = 2.0
PLAYER_JUMP_DURATION = 0.5
PLAYER_GRAVITY = 1.0
PLAYER_MOUSE_SENSITIVITY = Vec3(40, 40, 0)

PLAYER_MAX_HEALTH = 100
PLAYER_MAX_STAMINA = 100
STAMINA_DRAIN_PER_SEC = 25       # while sprinting
STAMINA_REGEN_PER_SEC = 15       # while not sprinting
STAMINA_MIN_TO_SPRINT = 5

CAMERA_BOB_SPEED = 8
CAMERA_BOB_AMOUNT = 0.035
CAMERA_SHAKE_DECAY = 4

# ---------------------------------------------------------------------------
# WEAPONS
# ---------------------------------------------------------------------------
GUN_DAMAGE = 18
GUN_FIRE_RATE = 0.18          # seconds between shots
GUN_MAG_SIZE = 12
GUN_RELOAD_TIME = 1.4
GUN_RANGE = 60
GUN_PROJECTILE_SPEED = 90

SWORD_DAMAGE = 35
SWORD_RANGE = 2.6
SWORD_SWING_RATE = 0.45

# ---------------------------------------------------------------------------
# ENEMIES
# ---------------------------------------------------------------------------
ENEMY_TYPES = {
    "grunt": dict(health=40, speed=2.2, damage=8, detect_range=14, attack_range=1.8,
                  attack_rate=1.2, color=color.rgb(180, 60, 60), score=10, xp=15),
    "brute": dict(health=90, speed=1.4, damage=18, detect_range=12, attack_range=2.2,
                  attack_rate=1.8, color=color.rgb(90, 40, 90), score=25, xp=35),
    "scout": dict(health=25, speed=3.4, damage=6, detect_range=18, attack_range=1.5,
                  attack_rate=0.9, color=color.rgb(60, 140, 90), score=15, xp=20),
}
ENEMY_RESPAWN_TIME = 12
ENEMY_PATROL_RADIUS = 8
ENEMY_COUNT = 10

# ---------------------------------------------------------------------------
# WORLD
# ---------------------------------------------------------------------------
WORLD_SIZE = 80              # half-extent of playable ground (square)
TREE_COUNT = 45
ROCK_COUNT = 30
BUILDING_COUNT = 6
DECORATION_COUNT = 60
COIN_COUNT = 25
MOUNTAIN_RING_RADIUS = 95
WATER_LEVEL = -0.4
WATER_SIZE = 22
WATER_POS = Vec3(-45, WATER_LEVEL, 45)

GROUND_COLOR = color.rgb(70, 120, 55)
ROAD_COLOR = color.rgb(60, 60, 65)

# ---------------------------------------------------------------------------
# SCORE / PROGRESSION
# ---------------------------------------------------------------------------
COIN_VALUE = 5
XP_PER_LEVEL = 100
WIN_SCORE_TARGET = 150        # score needed to trigger the win condition
WIN_COINS_TARGET = 20         # OR collect this many coins to win

# ---------------------------------------------------------------------------
# UI / COLORS
# ---------------------------------------------------------------------------
UI_HEALTH_COLOR = color.rgb(210, 40, 50)
UI_STAMINA_COLOR = color.rgb(60, 170, 210)
UI_XP_COLOR = color.rgb(230, 190, 60)
UI_BG_COLOR = color.rgba(10, 10, 15, 200)

# ---------------------------------------------------------------------------
# SAVE FILE
# ---------------------------------------------------------------------------
SAVE_FILE_PATH = "savegame.json"

# ---------------------------------------------------------------------------
# KEYBINDS (reference only - Ursina uses held_keys / input directly,
# these are documented here for the settings menu display)
# ---------------------------------------------------------------------------
KEYBINDS_DISPLAY = {
    "Move": "W A S D",
    "Jump": "Space",
    "Sprint": "Left Shift",
    "Fire Gun": "Left Mouse Button",
    "Sword Swing": "Right Mouse Button",
    "Switch Weapon": "Q",
    "Reload": "R",
    "Pause": "Escape",
    "Interact": "E",
}