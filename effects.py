"""
effects.py
Visual juice: particle bursts, damage screen-flash, camera shake, and a
muzzle flash helper. All effects are self-destructing (they remove
themselves after their lifetime, so nothing needs manual cleanup).
"""

import random
from ursina import Entity, color, destroy, camera, Vec3, Text, invoke, scene


class Particle(Entity):
    """A single short-lived particle used for hit/death/coin bursts."""

    def __init__(self, position, particle_color, scale=0.15, speed=4, lifetime=0.6):
        super().__init__(
            model="cube",
            color=particle_color,
            position=position,
            scale=scale,
        )
        self.velocity = Vec3(
            random.uniform(-1, 1), random.uniform(0.5, 1.5), random.uniform(-1, 1)
        ) * speed
        self.lifetime = lifetime
        self.age = 0

    def update(self):
        self.age += 1 / 60
        self.position += self.velocity * (1 / 60)
        self.velocity.y -= 9.8 * (1 / 60)  # gravity pull on particle
        self.scale = max(0.001, self.scale * 0.94)
        if self.age >= self.lifetime:
            destroy(self)


def spawn_burst(position, burst_color=color.orange, count=10):
    """Spawn a small explosion of particles at a world position."""
    for _ in range(count):
        Particle(position=position, particle_color=burst_color)


class ScreenFlash(Entity):
    """Full-screen color overlay used when the player takes damage."""

    def __init__(self):
        super().__init__(
            parent=camera.ui,
            model="quad",
            scale=(2.5, 1.5),
            color=color.rgba(255, 0, 0, 0),
            z=-1,
        )

    def flash(self, flash_color=color.rgba(255, 0, 0, 110), duration=0.25):
        self.color = flash_color
        self.animate_color(color.rgba(255, 0, 0, 0), duration=duration)


class CameraShaker:
    """Adds temporary shake offsets to the camera, decaying over time."""

    def __init__(self, cam):
        self.cam = cam
        self.trauma = 0.0

    def add_trauma(self, amount):
        self.trauma = min(1.0, self.trauma + amount)

    def update(self, dt, decay):
        if self.trauma <= 0:
            return
        self.trauma = max(0, self.trauma - decay * dt)
        shake = self.trauma ** 2
        self.cam.shake_offset = Vec3(
            random.uniform(-1, 1) * shake * 0.3,
            random.uniform(-1, 1) * shake * 0.3,
            0,
        )


def spawn_damage_number(position, amount, dmg_color=color.yellow):
    """Floating combat text that rises and fades."""
    t = Text(
        parent=scene,
        text=str(int(amount)),
        origin=(0, 0),
        color=dmg_color,
        scale=1.3,
        billboard=True,
        position=position,
    )
    t.animate_position(position + Vec3(0, 1.2, 0), duration=0.7)
    t.animate("scale", t.scale * 1.4, duration=0.7)
    invoke(destroy, t, delay=0.75)