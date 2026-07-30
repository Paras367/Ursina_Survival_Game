"""
player.py
The player character: extends Ursina's FirstPersonController (which already
gives us mouse-look, WASD movement, gravity and jumping via its built-in
raycast-based ground check) and layers on sprint/stamina, health & damage,
camera bob, weapon switching, inventory, coins, score, XP/levels, and a
checkpoint/save hook.
"""

import math
from typing import Any
from ursina import Vec3, held_keys, mouse, time as ursina_time, camera, invoke, color
from ursina.prefabs.first_person_controller import FirstPersonController

ursina_time: Any = ursina_time

import settings
from audio import audio_manager
from effects import ScreenFlash, CameraShaker, spawn_burst
from weapons import Gun, Sword


class Player(FirstPersonController):
    def __init__(self, on_death=None, on_win_check=None, **kwargs):
        super().__init__(
            position=settings.PLAYER_START_POS,
            speed=settings.PLAYER_WALK_SPEED,
            jump_height=settings.PLAYER_JUMP_HEIGHT,
            jump_duration=settings.PLAYER_JUMP_DURATION,
            gravity=settings.PLAYER_GRAVITY,
            mouse_sensitivity=settings.PLAYER_MOUSE_SENSITIVITY,
            **kwargs,
        )
        self.cursor.visible = False

        # --- Stats -----------------------------------------------------
        self.max_health = settings.PLAYER_MAX_HEALTH
        self.health = self.max_health
        self.max_stamina = settings.PLAYER_MAX_STAMINA
        self.stamina = self.max_stamina
        self.is_sprinting = False
        self.alive = True

        # --- Progression -------------------------------------------------
        self.coins = 0
        self.score = 0
        self.xp = 0
        self.level = 1
        self.inventory = []          # list of item name strings
        self.checkpoint = list(settings.PLAYER_START_POS)

        # --- Callbacks back to the GameManager --------------------------
        self.on_death = on_death
        self.on_win_check = on_win_check

        # --- Weapons -----------------------------------------------------
        self.gun = Gun()
        self.sword = Sword()
        self.weapons = [self.gun, self.sword]
        self.active_weapon_index = 0
        self.gun.show()
        self.sword.hide()

        # --- Visual effects ------------------------------------------------
        self.screen_flash = ScreenFlash()
        self.camera_shaker = CameraShaker(camera)

        # --- Camera bob state --------------------------------------------
        self._bob_timer = 0
        self._default_cam_y = camera.y
        self._footstep_timer = 0

        self.invincible = False

    # ------------------------------------------------------------------
    # MAIN LOOP
    # ------------------------------------------------------------------
    def update(self):
        if not self.alive:
            return

        self._handle_sprint()
        super().update()  # base FirstPersonController movement/gravity/jump
        self._handle_camera_bob()
        self._handle_footsteps()
        self._regen_stamina()

        for w in self.weapons:
            w.update()

        self.camera_shaker.update(ursina_time.dt, settings.CAMERA_SHAKE_DECAY)
        if hasattr(camera, "shake_offset"):
            camera.x += camera.shake_offset.x * ursina_time.dt * 30
            camera.y += camera.shake_offset.y * ursina_time.dt * 30

    def input(self, key):
        if not self.alive:
            return
        if key == "left mouse down":
            self._use_active_weapon()
        if key == "right mouse down" and self.active_weapon_index == 1:
            self.sword.try_swing(self._on_weapon_hit)
        if key == "r":
            self.gun.try_reload()
        if key == "q":
            self._switch_weapon()

    # ------------------------------------------------------------------
    # SPRINT / STAMINA
    # ------------------------------------------------------------------
    def _handle_sprint(self):
        wants_to_sprint = held_keys["shift"] and self._is_moving()
        can_sprint = self.stamina > settings.STAMINA_MIN_TO_SPRINT
        self.is_sprinting = wants_to_sprint and can_sprint

        if self.is_sprinting:
            self.speed = settings.PLAYER_RUN_SPEED
            self.stamina = max(0, self.stamina - settings.STAMINA_DRAIN_PER_SEC * time.dt)
        else:
            self.speed = settings.PLAYER_WALK_SPEED

    def _regen_stamina(self):
        if not self.is_sprinting and self.stamina < self.max_stamina:
            self.stamina = min(self.max_stamina, self.stamina + settings.STAMINA_REGEN_PER_SEC * ursina_time.dt)

    def _is_moving(self):
        return held_keys.get("w") or held_keys.get("a") or held_keys.get("s") or held_keys.get("d")

    # ------------------------------------------------------------------
    # CAMERA BOB + FOOTSTEPS
    # ------------------------------------------------------------------
    def _handle_camera_bob(self):
        if self._is_moving() and self.grounded:
            bob_speed = settings.CAMERA_BOB_SPEED * (1.6 if self.is_sprinting else 1.0)
            self._bob_timer += ursina_time.dt * bob_speed
            offset = abs(math.sin(self._bob_timer)) * settings.CAMERA_BOB_AMOUNT
            camera.y = self._default_cam_y + offset
        else:
            self._bob_timer = 0
            camera.y = self._default_cam_y

    def _handle_footsteps(self):
        if self._is_moving() and self.grounded:
            self._footstep_timer -= ursina_time.dt
            if self._footstep_timer <= 0:
                audio_manager.play("footstep", volume=0.25)
                self._footstep_timer = 0.28 if self.is_sprinting else 0.42
        else:
            self._footstep_timer = 0

    def jump(self):
        super().jump()
        audio_manager.play("jump")

    # ------------------------------------------------------------------
    # WEAPONS
    # ------------------------------------------------------------------
    def _switch_weapon(self):
        self.weapons[self.active_weapon_index].hide()
        self.active_weapon_index = (self.active_weapon_index + 1) % len(self.weapons)
        self.weapons[self.active_weapon_index].show()
        audio_manager.play("ui_click", volume=0.3)

    def _use_active_weapon(self):
        active = self.weapons[self.active_weapon_index]
        if isinstance(active, Gun):
            active.try_fire(self._on_weapon_hit, shake_callback=self.camera_shaker.add_trauma)
        elif isinstance(active, Sword):
            active.try_swing(self._on_weapon_hit)

    def _on_weapon_hit(self, entity, damage):
        """Fired whenever a weapon successfully damages something."""
        pass  # enemy.py's take_damage already handles death/score via GameManager hooks

    # ------------------------------------------------------------------
    # HEALTH / DAMAGE
    # ------------------------------------------------------------------
    def take_damage(self, amount):
        if not self.alive or self.invincible:
            return
        self.health -= amount
        self.screen_flash.flash()
        self.camera_shaker.add_trauma(0.4)
        audio_manager.play("player_hurt")
        spawn_burst(self.world_position + Vec3(0, 1, 0), burst_color=color.red, count=6)

        if self.health <= 0:
            self.health = 0
            self._die()

    def heal(self, amount):
        self.health = min(self.max_health, self.health + amount)

    def _die(self):
        self.alive = False
        self.cursor.visible = False
        if self.on_death:
            self.on_death()

    def respawn_at_checkpoint(self):
        self.position = Vec3(*self.checkpoint)
        self.health = self.max_health
        self.stamina = self.max_stamina
        self.alive = True

    # ------------------------------------------------------------------
    # PROGRESSION
    # ------------------------------------------------------------------
    def add_coin(self, value=None):
        self.coins += 1
        self.score += value if value is not None else settings.COIN_VALUE
        audio_manager.play("coin_pickup", volume=0.4)
        self._check_win()

    def add_score(self, amount):
        self.score += amount
        self._check_win()

    def add_xp(self, amount):
        self.xp += amount
        while self.xp >= settings.XP_PER_LEVEL:
            self.xp -= settings.XP_PER_LEVEL
            self.level += 1
            self.max_health += 10
            self.health = self.max_health
            audio_manager.play("ui_click", volume=0.5)

    def add_item(self, item_name):
        self.inventory.append(item_name)

    def set_checkpoint(self):
        self.checkpoint = [self.x, self.y, self.z]

    def _check_win(self):
        if self.on_win_check:
            self.on_win_check(self.score, self.coins)