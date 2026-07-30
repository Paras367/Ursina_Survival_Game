"""
main.py

Entry point. Boots the Ursina app, sets up lighting/shadows, and runs a
GameManager that owns the finite-state game flow:

    MAIN_MENU -> PLAYING <-> PAUSED
    PLAYING -> GAME_OVER -> (restart) -> PLAYING
    PLAYING -> VICTORY   -> (restart) -> PLAYING

Run with:  python main.py
"""

from ursina import (
    Ursina, Entity, Vec3, color, time, held_keys, application,
    DirectionalLight, AmbientLight, mouse, destroy, invoke, distance, Text, camera
)

import settings
from audio import audio_manager
from effects import spawn_burst
from player import Player
from enemy import Enemy
from world import World
from save_system import save_game, load_game, has_save
import ui as ui_module


class GameManager(Entity):
    STATE_MAIN_MENU = "main_menu"
    STATE_PLAYING = "playing"
    STATE_PAUSED = "paused"
    STATE_GAME_OVER = "game_over"
    STATE_VICTORY = "victory"

    def __init__(self):
        super().__init__()
        self.state = GameManager.STATE_MAIN_MENU

        self.world = None
        self.player = None
        self.enemies = []
        self.hud = None
        self._resuming_from_save = False

        self._setup_lighting()
        self._build_static_menus()
        self.main_menu.show()

        # NPC + shop placeholders (created once the world exists)
        self.npc = None
        self.shop = None

    # ------------------------------------------------------------------
    def _setup_lighting(self):
        self.sun = DirectionalLight(shadows=True)
        self.sun.rotation = (45, -35, 0)
        self.sun.color = color.rgba(255, 250, 235, 255)
        AmbientLight(color=color.rgba(140, 150, 170, 100))

    def _build_static_menus(self):
        self.main_menu = ui_module.MainMenu(
            on_start=self.start_new_game,
            on_continue=self.continue_game,
            on_settings=lambda: self._open_settings(self.main_menu),
            on_quit=application.quit,
            has_save=has_save(),
        )
        self.pause_menu = ui_module.PauseMenu(
            on_resume=self.resume_game,
            on_settings=lambda: self._open_settings(self.pause_menu),
            on_save=self.save_current_game,
            on_main_menu=self.return_to_main_menu,
        )
        self.settings_menu = ui_module.SettingsMenu(
            on_back=self._close_settings,
            on_toggle_mute=lambda: audio_manager.set_muted(not audio_manager.muted),
            audio_manager_ref=audio_manager,
        )
        self.game_over_menu = ui_module.GameOverMenu(
            on_restart=self.start_new_game,
            on_main_menu=self.return_to_main_menu,
        )
        self.victory_menu = ui_module.VictoryMenu(
            on_restart=self.start_new_game,
            on_main_menu=self.return_to_main_menu,
        )
        self._settings_return_to = None

    def _open_settings(self, return_to):
        self._settings_return_to = return_to
        return_to.hide()
        self.settings_menu.show()

    def _close_settings(self):
        self.settings_menu.hide()
        if self._settings_return_to:
            self._settings_return_to.show()

    # ------------------------------------------------------------------
    # GAME LIFECYCLE
    # ------------------------------------------------------------------
    def start_new_game(self, load_data=None):
        self._teardown_level()
        self.main_menu.hide()
        self.game_over_menu.hide()
        self.victory_menu.hide()

        self.world = World()
        self.player = Player(on_death=self.on_player_death, on_win_check=self.check_win_condition)
        self.hud = ui_module.HUD()

        if load_data:
            self._apply_save_data(load_data)

        self._spawn_enemies()
        self._spawn_npc_and_shop()

        self.state = GameManager.STATE_PLAYING
        mouse.locked = True
        audio_manager.start_music()
        self.hud.notify("Collect coins and defeat enemies to win!", duration=3.5)

    def continue_game(self):
        data = load_game()
        if data:
            self.start_new_game(load_data=data)
        else:
            self.start_new_game()

    def _apply_save_data(self, data):
        p = self.player
        if p is None:
            return

        p.position = Vec3(*data.get("position", settings.PLAYER_START_POS))
        p.health = data.get("health", getattr(p, "max_health", 100))
        p.stamina = data.get("stamina", getattr(p, "max_stamina", 100))
        p.coins = data.get("coins", 0)
        p.score = data.get("score", 0)
        p.xp = data.get("xp", 0)
        p.level = data.get("level", 1)
        p.inventory = data.get("inventory", [])
        # checkpoint should default to current position if not provided
        cp = data.get("checkpoint")
        p.checkpoint = cp if cp is not None else list(p.position)

    def save_current_game(self):
        if self.player:
            success = save_game(self.player)
            if self.hud:
                self.hud.notify("Game Saved" if success else "Save Failed", duration=1.5)
            else:
                # fallback if hud is not available
                print("Game Saved" if success else "Save Failed")

    def _teardown_level(self):
        if self.world:
            for e in list(self.world.entities) + list(self.world.coins):
                destroy(e)
        for e in list(self.enemies):
            destroy(e)
        self.enemies = []
        if self.player:
            destroy(self.player)
        if self.hud:
            destroy(self.hud)
        if self.npc:
            destroy(self.npc)
        if self.shop:
            destroy(self.shop)
        self.npc = None
        self.shop = None

    def return_to_main_menu(self):
        self._teardown_level()
        self.state = GameManager.STATE_MAIN_MENU
        self.pause_menu.hide()
        self.game_over_menu.hide()
        self.victory_menu.hide()
        audio_manager.stop_music()
        mouse.locked = False
        # refresh "continue" availability
        self.main_menu.hide()
        self.main_menu = ui_module.MainMenu(
            on_start=self.start_new_game,
            on_continue=self.continue_game,
            on_settings=lambda: self._open_settings(self.main_menu),
            on_quit=application.quit,
            has_save=has_save(),
        )
        self.main_menu.show()

    # ------------------------------------------------------------------
    # PAUSE
    # ------------------------------------------------------------------
    def toggle_pause(self):
        if self.state == GameManager.STATE_PLAYING:
            self.state = GameManager.STATE_PAUSED
            mouse.locked = False
            self.pause_menu.show()
        elif self.state == GameManager.STATE_PAUSED:
            self.resume_game()

    def resume_game(self):
        self.pause_menu.hide()
        self.settings_menu.hide()
        self.state = GameManager.STATE_PLAYING
        mouse.locked = True

    # ------------------------------------------------------------------
    # ENEMIES
    # ------------------------------------------------------------------
    def _spawn_enemies(self):
        # ensure world exists before attempting to spawn
        if not self.world:
            return
        types = list(settings.ENEMY_TYPES.keys())
        if not types:
            return
        for i in range(settings.ENEMY_COUNT):
            enemy_type = types[i % len(types)]
            pos = self.world.get_random_spawn_point()
            self._spawn_single_enemy(enemy_type, pos)

    def _spawn_single_enemy(self, enemy_type, pos):
        e = Enemy(
            enemy_type=enemy_type,
            position=pos,
            player=self.player,
            world_bounds=settings.WORLD_SIZE,
            on_death=self.on_enemy_death,
        )
        self.enemies.append(e)
        return e

    def on_enemy_death(self, enemy):
        if not self.player:
            return

        self.player.add_score(enemy.score_value)
        self.player.add_xp(enemy.xp_value)
        if self.hud:
            self.hud.notify(f"+{enemy.score_value} score", duration=1.0)

        enemy_type = enemy.enemy_type

        def respawn():
            if self.state != GameManager.STATE_PLAYING:
                return
            if enemy in self.enemies:
                self.enemies.remove(enemy)
            if not self.world:
                return
            new_pos = self.world.get_random_spawn_point()
            self._spawn_single_enemy(enemy_type, new_pos)

        invoke(respawn, delay=settings.ENEMY_RESPAWN_TIME)

    # ------------------------------------------------------------------
    # NPC + SHOP (simple dialogue / trade system)
    # ------------------------------------------------------------------
    def _spawn_npc_and_shop(self):
        if not self.world:
            return

        npc_pos = self.world.get_random_spawn_point()
        self.npc = Entity(
            model="cube",
            color=(80/255, 130/255, 200/255, 1),
            scale=Vec3(0.9, 1.9, 0.9),
            position=npc_pos,
            collider="box",
        )
        self.npc.dialogue = (
            "Traveler, beware the frontier beasts. "
            "Collect coins and thin their numbers to prove your worth."
        )

        shop_pos = self.world.get_random_spawn_point()
        self.shop = Entity(
            model="cube",
            color=(160/255, 130/255, 60/255, 1),
            scale=(1.2, 1.6, 1.2),
            position=shop_pos,
            collider="box",
        )

    def _handle_interactions(self):
        if not self.player or not self.player.alive:
            return
        near_npc = self.npc and distance(self.player.position, self.npc.position) < 3
        near_shop = self.shop and distance(self.player.position, self.shop.position) < 3

        # guard against missing HUD (e.g. during teardown)
        is_pressing_e = False
        try:
            is_pressing_e = held_keys.get("e", False)
        except Exception:
            is_pressing_e = False

        if near_npc:
            if self.hud:
                self.hud.show_prompt("Press E to talk")
            if is_pressing_e and self.hud and self.npc:
                self.hud.notify(self.npc.dialogue, duration=3.0)
        elif near_shop:
            if self.hud:
                self.hud.show_prompt("Press E to buy Health Potion (10 coins)")
            if is_pressing_e and self.player.coins >= 10:
                self.player.coins -= 10
                self.player.heal(30)
                self.player.add_item("Health Potion")
                if self.hud:
                    self.hud.notify("Purchased Health Potion (+30 HP)", duration=1.5)
        else:
            if self.hud:
                self.hud.clear_prompt()

    # ------------------------------------------------------------------
    # COINS
    # ------------------------------------------------------------------
    def _handle_coin_pickups(self):
        if not self.world or not self.player:
            return
        for coin in list(self.world.coins):
            if distance(self.player.position, coin.position) < 1.2:
                spawn_burst(coin.world_position, burst_color=color.gold, count=8)
                self.world.coins.remove(coin)
                destroy(coin)
                self.player.add_coin()

    # ------------------------------------------------------------------
    # WIN / LOSE
    # ------------------------------------------------------------------
    def check_win_condition(self, score, coins):
        if self.state != GameManager.STATE_PLAYING:
            return
        if score >= settings.WIN_SCORE_TARGET or coins >= settings.WIN_COINS_TARGET:
            self._trigger_victory()

    def _trigger_victory(self):
        self.state = GameManager.STATE_VICTORY
        mouse.locked = False
        audio_manager.stop_music()
        audio_manager.play("victory", volume=0.7)
        if self.player:
            self.victory_menu.set_stats(self.player.score, self.player.coins, self.player.level)
        else:
            self.victory_menu.set_stats(0, 0, 1)
        self.victory_menu.show()

    def on_player_death(self):
        self.state = GameManager.STATE_GAME_OVER
        mouse.locked = False
        audio_manager.stop_music()
        audio_manager.play("game_over", volume=0.7)
        if self.player:
            self.game_over_menu.set_stats(self.player.score, self.player.coins, self.player.level)
        else:
            self.game_over_menu.set_stats(0, 0, 1)
        self.game_over_menu.show()

    # ------------------------------------------------------------------
    # MAIN UPDATE LOOP
    # ------------------------------------------------------------------
    def update(self):
        if self.state != GameManager.STATE_PLAYING or not self.player:
            return
        self._handle_coin_pickups()
        self._handle_interactions()
        if self.hud:
            self.hud.update_stats(self.player)
            self.hud.update_minimap(self.player, self.enemies, settings.WORLD_SIZE)

        # Fell off the world / into a hole -> respawn at last checkpoint
        if self.player.y < -25:
            self.player.respawn_at_checkpoint()

        # Periodically drop a checkpoint at the player's current position
        # (every time they are safely grounded and healthy)
        if self.player.grounded and self.player.health == self.player.max_health:
            self.player.set_checkpoint()

    def input(self, key):
        if key == "escape":
            if self.state == GameManager.STATE_PLAYING:
                self.toggle_pause()
            elif self.state == GameManager.STATE_PAUSED:
                self.resume_game()


def main():
    app = Ursina(title=settings.WINDOW_TITLE, borderless=False, fullscreen=settings.FULLSCREEN,
                 vsync=settings.VSYNC)
    camera.fov = settings.FOV

    manager = GameManager()

    app.run()


if __name__ == "__main__":
    main()