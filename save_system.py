"""
save_system.py
Simple JSON-based save/load system. Stores player stats, position, coins,
score, XP/level, and the last checkpoint so a session can be resumed.
"""

import json
import os
from settings import SAVE_FILE_PATH


def save_game(player):
    """Serialize the player's current state to disk."""
    data = {
        "position": [player.x, player.y, player.z],
        "health": player.health,
        "stamina": player.stamina,
        "coins": player.coins,
        "score": player.score,
        "xp": player.xp,
        "level": player.level,
        "inventory": player.inventory,
        "checkpoint": getattr(player, "checkpoint", [player.x, player.y, player.z]),
    }
    try:
        with open(SAVE_FILE_PATH, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except OSError:
        return False


def load_game():
    """Return the saved state dict, or None if no save file exists / it's corrupt."""
    if not os.path.exists(SAVE_FILE_PATH):
        return None
    try:
        with open(SAVE_FILE_PATH, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return None


def delete_save():
    if os.path.exists(SAVE_FILE_PATH):
        try:
            os.remove(SAVE_FILE_PATH)
        except OSError:
            pass


def has_save():
    return os.path.exists(SAVE_FILE_PATH)