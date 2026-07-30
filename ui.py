"""
ui.py
All UI: in-game HUD (health/stamina/xp bars, ammo counter, coin counter,
crosshair, minimap), and full-screen menus (main menu, pause, settings,
game over, victory). Menus are built once and toggled via .enabled so
there's no re-instantiation cost when opening/closing them repeatedly.
"""

from ursina import Entity, Text, Button, camera, color, Vec2, Vec3, destroy
import settings
from audio import audio_manager


def _click(callback):
    """Wrap a menu button's callback so it also plays a UI click sound."""
    def wrapped():
        audio_manager.play("ui_click", volume=0.4)
        if callback:
            callback()
    return wrapped


class Bar(Entity):
    """A simple background+fill bar widget for health/stamina/xp."""

    def __init__(self, position, fill_color, width=0.3, height=0.025, label=""):
        super().__init__(parent=camera.ui, position=position)
        self.bg = Entity(parent=self, model="quad", color=color.rgba(0, 0, 0, 160),
                          scale=(width + 0.01, height + 0.01), origin=(-0.5, 0))
        self.fill = Entity(parent=self, model="quad", color=fill_color,
                            scale=(width, height), origin=(-0.5, 0), x=0.005)
        self.max_width = width
        if label:
            Text(parent=self, text=label, scale=0.6, position=(0, height + 0.01), origin=(-0.5, 0))

    def set_value(self, current, maximum):
        pct = max(0, min(1, current / maximum)) if maximum > 0 else 0
        self.fill.scale_x = self.max_width * pct


class HUD(Entity):
    def __init__(self):
        super().__init__(parent=camera.ui)

        self.health_bar = Bar(Vec2(-0.85, 0.45), settings.UI_HEALTH_COLOR, label="HEALTH")
        self.stamina_bar = Bar(Vec2(-0.85, 0.40), settings.UI_STAMINA_COLOR, label="STAMINA")
        self.xp_bar = Bar(Vec2(-0.85, 0.35), settings.UI_XP_COLOR, label="XP")

        self.level_text = Text(parent=self, text="Lv.1", position=(-0.85, 0.30), scale=1.1)
        self.coin_text = Text(parent=self, text="Coins: 0", position=(0.6, 0.46), scale=1.2,
                               color=color.gold)
        self.score_text = Text(parent=self, text="Score: 0", position=(0.6, 0.41), scale=1.1)
        self.ammo_text = Text(parent=self, text="12 / 48", position=(0.6, -0.46), scale=1.4,
                               origin=(0, 0))
        self.weapon_text = Text(parent=self, text="GUN", position=(0.6, -0.40), scale=1.0)

        # Crosshair
        self.crosshair_h = Entity(parent=self, model="quad", color=color.white,
                                   scale=(0.02, 0.002))
        self.crosshair_v = Entity(parent=self, model="quad", color=color.white,
                                   scale=(0.002, 0.02))

        # Minimap: a small top-down icon board in the corner
        self.minimap_bg = Entity(parent=self, model="quad", color=color.rgba(10, 10, 15, 180),
                                  scale=0.28, position=(0.72, 0.28))
        self.minimap_player = Entity(parent=self, model="quad", color=color.azure,
                                      scale=0.014, position=(0.72, 0.28))
        self.minimap_enemy_icons = []

        # Interaction prompt (e.g. "Press E to talk")
        self.prompt_text = Text(parent=self, text="", position=(0, -0.1), origin=(0, 0),
                                 scale=1.1, color=color.white)

        self.notification_text = Text(parent=self, text="", position=(0, 0.25), origin=(0, 0),
                                       scale=1.3, color=color.yellow)

    def update_stats(self, player):
        self.health_bar.set_value(player.health, player.max_health)
        self.stamina_bar.set_value(player.stamina, player.max_stamina)
        self.xp_bar.set_value(player.xp, settings.XP_PER_LEVEL)
        self.level_text.text = f"Lv.{player.level}"
        self.coin_text.text = f"Coins: {player.coins}"
        self.score_text.text = f"Score: {player.score}"

        weapon = player.weapons[player.active_weapon_index]
        self.weapon_text.text = weapon.weapon_name.upper()
        if weapon.weapon_name == "gun":
            self.ammo_text.text = f"{weapon.mag} / {weapon.reserve_ammo}"
            self.ammo_text.enabled = True
        else:
            self.ammo_text.text = "MELEE"

    def update_minimap(self, player, enemies, world_size):
        scale = 0.12 / world_size  # map world coords into the minimap quad
        self.minimap_player.rotation_z = -player.rotation_y

        for icon in self.minimap_enemy_icons:
            destroy(icon)
        self.minimap_enemy_icons = []

        for e in enemies:
            if e.state == "dead":
                continue
            dx = (e.x - player.x) * scale
            dz = (e.z - player.z) * scale
            icon = Entity(parent=self, model="quad", color=color.red, scale=0.01,
                           position=(0.72 + dx, 0.28 + dz))
            self.minimap_enemy_icons.append(icon)

    def show_prompt(self, text):
        self.prompt_text.text = text

    def clear_prompt(self):
        self.prompt_text.text = ""

    def notify(self, text, duration=2.0):
        self.notification_text.text = text
        from ursina import invoke
        invoke(setattr, self.notification_text, "text", "", delay=duration)


class MenuScreen(Entity):
    """Base full-screen menu with a dark backdrop and a title."""

    def __init__(self, title):
        super().__init__(parent=camera.ui, enabled=False)
        self.backdrop = Entity(parent=self, model="quad", color=color.rgba(5, 5, 10, 235),
                                scale=(2.2, 1.3))
        self.title_text = Text(parent=self, text=title, position=(0, 0.32), origin=(0, 0),
                                scale=2.4, color=color.rgb(230, 200, 130))
        self.buttons = []

    def add_button(self, text, callback, y):
        btn = Button(parent=self, text=text, position=(0, y), scale=(0.32, 0.07),
                     color=color.rgb(35, 35, 45), highlight_color=color.rgb(55, 55, 70))
        btn.on_click = _click(callback)
        self.buttons.append(btn)
        return btn

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False


class MainMenu(MenuScreen):
    def __init__(self, on_start, on_continue, on_settings, on_quit, has_save=False):
        super().__init__("SKYREACH FRONTIER")
        Text(parent=self, text="A luxury of danger awaits", position=(0, 0.24), origin=(0, 0),
             scale=1.1, color=color.rgba(255, 255, 255, 180))
        self.add_button("New Game", on_start, 0.08)
        if has_save:
            self.add_button("Continue", on_continue, -0.02)
        self.add_button("Settings", on_settings, -0.12 if has_save else -0.02)
        self.add_button("Quit", on_quit, -0.22 if has_save else -0.12)


class PauseMenu(MenuScreen):
    def __init__(self, on_resume, on_settings, on_save, on_main_menu):
        super().__init__("PAUSED")
        self.add_button("Resume", on_resume, 0.10)
        self.add_button("Save Game", on_save, 0.0)
        self.add_button("Settings", on_settings, -0.10)
        self.add_button("Main Menu", on_main_menu, -0.20)


class SettingsMenu(MenuScreen):
    def __init__(self, on_back, on_toggle_mute, audio_manager_ref):
        super().__init__("SETTINGS")
        self.mute_label_text = Text(parent=self, text="", position=(0, 0.12), origin=(0, 0), scale=1.2)
        self._audio = audio_manager_ref
        self._refresh_mute_label()

        def toggle():
            on_toggle_mute()
            self._refresh_mute_label()

        self.add_button("Toggle Sound", toggle, 0.0)

        keybind_lines = "\n".join(f"{k}: {v}" for k, v in settings.KEYBINDS_DISPLAY.items())
        Text(parent=self, text=keybind_lines, position=(0, -0.05), origin=(0, 0.5), scale=0.85,
             color=color.rgba(255, 255, 255, 200))

        self.add_button("Back", on_back, -0.32)

    def _refresh_mute_label(self):
        self.mute_label_text.text = "Sound: MUTED" if self._audio.muted else "Sound: ON"


class GameOverMenu(MenuScreen):
    def __init__(self, on_restart, on_main_menu):
        super().__init__("YOU DIED")
        self.title_text.color = color.rgb(200, 40, 40)
        self.stats_text = Text(parent=self, text="", position=(0, 0.15), origin=(0, 0), scale=1.2)
        self.add_button("Restart", on_restart, -0.02)
        self.add_button("Main Menu", on_main_menu, -0.14)

    def set_stats(self, score, coins, level):
        self.stats_text.text = f"Final Score: {score}   Coins: {coins}   Level: {level}"


class VictoryMenu(MenuScreen):
    def __init__(self, on_restart, on_main_menu):
        super().__init__("VICTORY!")
        self.title_text.color = color.rgb(230, 200, 60)
        self.stats_text = Text(parent=self, text="", position=(0, 0.15), origin=(0, 0), scale=1.2)
        self.add_button("Play Again", on_restart, -0.02)
        self.add_button("Main Menu", on_main_menu, -0.14)

    def set_stats(self, score, coins, level):
        self.stats_text.text = f"Final Score: {score}   Coins: {coins}   Level: {level}"