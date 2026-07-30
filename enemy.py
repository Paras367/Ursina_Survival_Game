"""
enemy.py
Enemy AI: a single Enemy class parameterized by an "enemy type" dict from
settings.ENEMY_TYPES, so grunts/brutes/scouts are all the same class with
different stats. Implements a simple finite state machine:

    PATROL -> (player within detect_range) -> CHASE
    CHASE  -> (player within attack_range) -> ATTACK
    CHASE  -> (player leaves detect_range * 1.5) -> RETURN
    RETURN -> (reaches patrol anchor) -> PATROL
    (on death) -> DEAD -> (after respawn timer) -> new Enemy spawned by manager
"""

import random
import math
from ursina import Entity, Vec3, color, time, destroy, invoke, distance, curve

import settings
from audio import audio_manager
from effects import spawn_burst, spawn_damage_number


class Enemy(Entity):
    STATE_PATROL = "patrol"
    STATE_CHASE = "chase"
    STATE_ATTACK = "attack"
    STATE_RETURN = "return"
    STATE_DEAD = "dead"

    def __init__(self, enemy_type, position, player, world_bounds, on_death=None):
        stats = settings.ENEMY_TYPES[enemy_type]
        super().__init__(
            model="cube",
            color=stats["color"],
            scale=(0.9, 1.8, 0.9),
            position=position,
            collider="box",
        )
        self.enemy_type = enemy_type
        self.max_health = stats["health"]
        self.health = self.max_health
        self.speed = stats["speed"]
        self.damage = stats["damage"]
        self.detect_range = stats["detect_range"]
        self.attack_range = stats["attack_range"]
        self.attack_rate = stats["attack_rate"]
        self.score_value = stats["score"]
        self.xp_value = stats["xp"]

        self.player = player
        self.world_bounds = world_bounds
        self.on_death = on_death

        self.anchor = Vec3(position)
        self.patrol_target = self._random_patrol_point()
        self.state = Enemy.STATE_PATROL
        self._attack_cooldown = 0
        self._stuck_timer = 0
        self._last_pos = Vec3(position)

        # Simple eye/health-bar indicator above the enemy's head
        self.health_bar_bg = Entity(parent=self, model="cube", color=color.black33,
                                     scale=(1.1, 0.12, 0.12), position=(0, 1.3, 0), billboard=True)
        self.health_bar = Entity(parent=self, model="cube", color=color.lime,
                                  scale=(1.05, 0.09, 0.09), position=(0, 1.3, -0.01), billboard=True)

    # ------------------------------------------------------------------
    def _random_patrol_point(self):
        angle = random.uniform(0, math.tau)
        r = random.uniform(2, settings.ENEMY_PATROL_RADIUS)
        offset = Vec3(math.cos(angle) * r, 0, math.sin(angle) * r)
        target = self.anchor + offset
        b = self.world_bounds
        target.x = max(-b, min(b, target.x))
        target.z = max(-b, min(b, target.z))
        return target

    # ------------------------------------------------------------------
    def update(self):
        if self.state == Enemy.STATE_DEAD:
            return

        dist_to_player = distance(self.position, self.player.position)

        if self.state == Enemy.STATE_PATROL:
            self._do_patrol()
            if dist_to_player <= self.detect_range and self.player.alive:
                self.state = Enemy.STATE_CHASE
                audio_manager.play("enemy_growl", volume=0.3)

        elif self.state == Enemy.STATE_CHASE:
            if not self.player.alive:
                self.state = Enemy.STATE_RETURN
            elif dist_to_player <= self.attack_range:
                self.state = Enemy.STATE_ATTACK
            elif dist_to_player > self.detect_range * 1.6:
                self.state = Enemy.STATE_RETURN
            else:
                self._move_toward(self.player.position)

        elif self.state == Enemy.STATE_ATTACK:
            self._face(self.player.position)
            if dist_to_player > self.attack_range * 1.2:
                self.state = Enemy.STATE_CHASE
            else:
                self._attack_cooldown -= time.dt
                if self._attack_cooldown <= 0:
                    self._attack_cooldown = self.attack_rate
                    if self.player.alive:
                        self.player.take_damage(self.damage)

        elif self.state == Enemy.STATE_RETURN:
            self._move_toward(self.anchor)
            if distance(self.position, self.anchor) < 1.5:
                self.state = Enemy.STATE_PATROL
                self.patrol_target = self._random_patrol_point()

        self._update_health_bar()
        self._unstick_check()

    # ------------------------------------------------------------------
    def _do_patrol(self):
        if distance(self.position, self.patrol_target) < 1.0:
            self.patrol_target = self._random_patrol_point()
        else:
            self._move_toward(self.patrol_target, speed_mult=0.5)

    def _move_toward(self, target_pos, speed_mult=1.0):
        direction = Vec3(target_pos.x - self.x, 0, target_pos.z - self.z)
        if direction.length() < 0.01:
            return
        direction = direction.normalized()
        self.position += direction * self.speed * speed_mult * time.dt
        self._face(target_pos)

    def _face(self, target_pos):
        direction = Vec3(target_pos.x - self.x, 0, target_pos.z - self.z)
        if direction.length() > 0.01:
            angle = math.degrees(math.atan2(direction.x, direction.z))
            self.rotation_y = angle

    def _unstick_check(self):
        """Basic stuck-avoidance: if barely moved while chasing, nudge sideways
        to avoid getting permanently wedged against world obstacles."""
        if self.state in (Enemy.STATE_CHASE, Enemy.STATE_RETURN):
            moved = distance(self.position, self._last_pos)
            if moved < 0.01:
                self._stuck_timer += time.dt
                if self._stuck_timer > 0.6:
                    nudge_angle = random.uniform(0, math.tau)
                    self.position += Vec3(math.cos(nudge_angle), 0, math.sin(nudge_angle)) * 0.5
                    self._stuck_timer = 0
            else:
                self._stuck_timer = 0
        self._last_pos = Vec3(self.position)

    def _update_health_bar(self):
        pct = max(0, self.health / self.max_health)
        self.health_bar.scale_x = 1.05 * pct
        self.health_bar.color = color.lime if pct > 0.5 else (color.yellow if pct > 0.25 else color.red)

    # ------------------------------------------------------------------
    def take_damage(self, amount):
        if self.state == Enemy.STATE_DEAD:
            return
        self.health -= amount
        audio_manager.play("enemy_hit", volume=0.35)
        if self.health <= 0:
            self._die()
        else:
            # Being hit interrupts patrol and provokes a chase
            if self.state == Enemy.STATE_PATROL:
                self.state = Enemy.STATE_CHASE

    def _die(self):
        self.state = Enemy.STATE_DEAD
        audio_manager.play("enemy_death", volume=0.5)
        spawn_burst(self.world_position + Vec3(0, 0.9, 0), burst_color=color.rgb(80, 20, 20), count=14)

        # simple death animation: sink + fade, then destroy
        self.animate_position(self.position + Vec3(0, -1.6, 0), duration=0.6, curve=curve.in_quad)
        self.animate_scale(self.scale * 0.1, duration=0.6)
        destroy(self.health_bar_bg)
        destroy(self.health_bar)

        if self.on_death:
            self.on_death(self)

        invoke(destroy, self, delay=0.65)