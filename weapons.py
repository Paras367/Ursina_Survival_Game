"""
weapons.py
Weapon system: a Sword (melee, raycast-based hit detection) and a Gun
(hitscan-style raycast projectile with a visible tracer + reload cycle).
Both weapons report hits back through a callback so player.py can route
damage into enemies without weapons.py needing to import enemy.py.
"""

from ursina import Entity, Vec3, color, raycast, camera, destroy, invoke, time, curve
import settings
from audio import audio_manager
from effects import spawn_burst, spawn_damage_number


class Weapon(Entity):
    """Base class for anything the player can hold and use."""

    def __init__(self, name, damage, **kwargs):
        super().__init__(parent=camera, **kwargs)
        self.weapon_name = name
        self.damage = damage
        self.enabled = False

    def show(self):
        self.enabled = True

    def hide(self):
        self.enabled = False


class Sword(Weapon):
    def __init__(self):
        super().__init__(
            name="sword",
            damage=settings.SWORD_DAMAGE,
            model="cube",
            color=color.rgb(190, 190, 200),
            scale=(0.08, 0.08, 0.9),
            position=(0.45, -0.35, 0.9),
            rotation=(0, 45, 0),
        )
        self.cooldown = 0
        self.swinging = False

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= time.dt

    def try_swing(self, hit_callback):
        """Melee swing: short raycast forward from the camera."""
        if self.cooldown > 0 or not self.enabled:
            return False
        self.cooldown = settings.SWORD_SWING_RATE
        self.swinging = True
        self.animate_rotation((0, -30, 0), duration=0.08, curve=curve.out_quad)
        invoke(setattr, self, "rotation", Vec3(0, 45, 0), delay=0.12)
        invoke(setattr, self, "swinging", False, delay=0.15)
        audio_manager.play("sword_swing")

        hit_info = raycast(
            origin=camera.world_position,
            direction=camera.forward,
            distance=settings.SWORD_RANGE,
            ignore=(self,),
        )
        if hit_info.hit and hasattr(hit_info.entity, "take_damage"):
            hit_info.entity.take_damage(self.damage)
            spawn_burst(hit_info.world_point, burst_color=color.red, count=8)
            spawn_damage_number(hit_info.world_point, self.damage)
            hit_callback(hit_info.entity, self.damage)
        return True


class Gun(Weapon):
    def __init__(self):
        super().__init__(
            name="gun",
            damage=settings.GUN_DAMAGE,
            model="cube",
            color=color.rgb(40, 40, 45),
            scale=(0.12, 0.12, 0.55),
            position=(0.4, -0.3, 0.8),
        )
        self.mag = settings.GUN_MAG_SIZE
        self.reserve_ammo = settings.GUN_MAG_SIZE * 4
        self.cooldown = 0
        self.reloading = False
        self.reload_timer = 0

    def update(self):
        if self.cooldown > 0:
            self.cooldown -= time.dt
        if self.reloading:
            self.reload_timer -= time.dt
            if self.reload_timer <= 0:
                self._finish_reload()

    def try_fire(self, hit_callback, shake_callback=None):
        if self.reloading or self.cooldown > 0 or not self.enabled:
            return False
        if self.mag <= 0:
            self.try_reload()
            return False

        self.cooldown = settings.GUN_FIRE_RATE
        self.mag -= 1
        audio_manager.play("gun_shot")
        self._muzzle_flash()
        if shake_callback:
            shake_callback(0.15)

        hit_info = raycast(
            origin=camera.world_position,
            direction=camera.forward,
            distance=settings.GUN_RANGE,
            ignore=(self,),
        )
        self._draw_tracer(hit_info.world_point if hit_info.hit else camera.world_position + camera.forward * settings.GUN_RANGE)

        if hit_info.hit and hasattr(hit_info.entity, "take_damage"):
            hit_info.entity.take_damage(self.damage)
            spawn_burst(hit_info.world_point, burst_color=color.yellow, count=10)
            spawn_damage_number(hit_info.world_point, self.damage)
            hit_callback(hit_info.entity, self.damage)
        return True

    def try_reload(self):
        if self.reloading or self.mag == settings.GUN_MAG_SIZE or self.reserve_ammo <= 0:
            return
        self.reloading = True
        self.reload_timer = settings.GUN_RELOAD_TIME
        audio_manager.play("gun_reload")

    def _finish_reload(self):
        needed = settings.GUN_MAG_SIZE - self.mag
        take = min(needed, self.reserve_ammo)
        self.mag += take
        self.reserve_ammo -= take
        self.reloading = False

    def _muzzle_flash(self):
        flash = Entity(
            parent=self, model="quad", color=color.yellow,
            scale=0.15, position=(0, 0, 0.4), billboard=True,
        )
        invoke(destroy, flash, delay=0.05)

    def _draw_tracer(self, end_point):
        start = camera.world_position + camera.forward * 0.6 - Vec3(0, 0.05, 0)
        direction = end_point - start
        length = direction.length()
        tracer = Entity(
            model="cube", color=color.rgba(255, 255, 150, 180),
            position=start + direction / 2,
            scale=(0.02, 0.02, length),
        )
        tracer.look_at(end_point)
        invoke(destroy, tracer, delay=0.05)