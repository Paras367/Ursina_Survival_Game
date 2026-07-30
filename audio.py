"""
audio.py
Central audio manager. Every sound is loaded defensively: if the audio file
is missing from assets/audio/, the game keeps running silently instead of
crashing. Drop matching filenames into assets/audio/ to hear real sound.

Expected files (all optional):
    assets/audio/music_ambient.ogg
    assets/audio/footstep.wav
    assets/audio/jump.wav
    assets/audio/gun_shot.wav
    assets/audio/gun_reload.wav
    assets/audio/sword_swing.wav
    assets/audio/enemy_hit.wav
    assets/audio/enemy_death.wav
    assets/audio/enemy_growl.wav
    assets/audio/player_hurt.wav
    assets/audio/coin_pickup.wav
    assets/audio/ui_click.wav
    assets/audio/victory.wav
    assets/audio/game_over.wav
"""

import os
from ursina import Audio


class AudioManager:
    def __init__(self):
        self._cache = {}
        self.muted = False
        self.music = self._safe_load("music_ambient", loop=True, autoplay=False, volume=0.35)

    def _safe_load(self, name, loop=False, autoplay=False, volume=0.6):
        """Attempt to load a sound; return None if the file does not exist."""
        path = f"assets/audio/{name}"
        found = False
        for ext in (".wav", ".ogg", ".mp3"):
            if os.path.exists(path + ext):
                found = True
                break
        if not found:
            return None
        try:
            snd = Audio(name, loop=loop, autoplay=autoplay, volume=volume)
            return snd
        except Exception:
            return None

    def play(self, name, volume=0.6):
        """Play a one-shot sound effect by base filename (no extension)."""
        if self.muted:
            return
        if name not in self._cache:
            self._cache[name] = self._safe_load(name, loop=False, autoplay=False, volume=volume)
        snd = self._cache[name]
        if snd is not None:
            snd.play()

    def start_music(self):
        if self.music is not None and not self.muted:
            self.music.play()

    def stop_music(self):
        if self.music is not None:
            self.music.stop()

    def set_muted(self, muted):
        self.muted = muted
        if muted:
            self.stop_music()
        else:
            self.start_music()


# Singleton instance shared across the whole game
audio_manager = AudioManager()