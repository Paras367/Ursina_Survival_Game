"""
world.py
Procedurally builds the playable world: ground, road grid, trees, rocks,
buildings, a lake, a mountain ring around the play area, sky + clouds, and
scattered decorations. Also spawns coin collectibles and hands back their
list so main.py can check pickups against the player each frame.

Everything here uses Ursina's built-in primitive models (cube, sphere,
plane) so the game runs with zero external asset dependencies.
"""

import random
import math
from ursina import Entity, Vec3, color, Sky, scene

import settings


class World:
    def __init__(self):
        self.entities = []          # solid collidable world geometry
        self.coins = []              # collectible coin entities
        self.trees = []
        self.buildings = []
        random.seed()

        self._build_sky()
        self._build_ground()
        self._build_roads()
        self._build_water()
        self._build_mountains()
        self._build_trees()
        self._build_rocks()
        self._build_buildings()
        self._build_decorations()
        self._build_coins()

    # ------------------------------------------------------------------
    def _build_sky(self):
        Sky(color=color.rgb(120, 170, 220))
        # Simple procedural cloud puffs made of overlapping soft spheres
        for _ in range(18):
            x = random.uniform(-settings.WORLD_SIZE * 1.3, settings.WORLD_SIZE * 1.3)
            z = random.uniform(-settings.WORLD_SIZE * 1.3, settings.WORLD_SIZE * 1.3)
            y = random.uniform(28, 42)
            cluster_parent = Entity(position=(x, y, z))
            for _ in range(random.randint(3, 6)):
                Entity(
                    parent=cluster_parent,
                    model="sphere",
                    color=color.rgba(255, 255, 255, 230),
                    scale=random.uniform(3, 6),
                    position=(
                        random.uniform(-3, 3),
                        random.uniform(-0.5, 0.5),
                        random.uniform(-3, 3),
                    ),
                )

    def _build_ground(self):
        ground = Entity(
            model="plane",
            scale=(settings.WORLD_SIZE * 2, 1, settings.WORLD_SIZE * 2),
            color=settings.GROUND_COLOR,
            texture="white_cube",
            texture_scale=(settings.WORLD_SIZE, settings.WORLD_SIZE),
            collider="box",
        )
        self.entities.append(ground)

    def _build_roads(self):
        """A simple cross-shaped road grid through the middle of the map."""
        road_width = 6
        length = settings.WORLD_SIZE * 2
        h_road = Entity(
            model="cube", color=settings.ROAD_COLOR,
            scale=(length, 0.05, road_width), position=(0, 0.02, 0),
        )
        v_road = Entity(
            model="cube", color=settings.ROAD_COLOR,
            scale=(road_width, 0.05, length), position=(0, 0.02, 0),
        )
        self.entities += [h_road, v_road]

    def _build_water(self):
        water = Entity(
            model="plane",
            scale=(settings.WATER_SIZE, 1, settings.WATER_SIZE),
            color=color.rgba(50, 110, 200, 180),
            position=settings.WATER_POS,
        )
        self.entities.append(water)

    def _build_mountains(self):
        """A ring of large cone-like peaks (scaled cubes rotated 45deg to
        fake a rocky silhouette) surrounding the playable area as a natural
        boundary wall."""
        count = 26
        for i in range(count):
            angle = (i / count) * math.tau
            r = settings.MOUNTAIN_RING_RADIUS + random.uniform(-4, 4)
            x = math.cos(angle) * r
            z = math.sin(angle) * r
            height = random.uniform(18, 34)
            peak = Entity(
                model="cube",
                color=color.rgb(90, 85, 95).tint(random.uniform(-0.05, 0.05)),
                scale=(random.uniform(14, 22), height, random.uniform(14, 22)),
                position=(x, height / 2 - 2, z),
                rotation=(0, random.uniform(0, 45), 0),
                collider="box",
            )
            self.entities.append(peak)

    def _build_trees(self):
        for _ in range(settings.TREE_COUNT):
            pos = self._random_ground_point(avoid_center=8)
            if self._near_water(pos):
                continue
            trunk = Entity(
                model="cube", color=color.rgb(90, 60, 35),
                scale=(0.5, 2.2, 0.5), position=pos + Vec3(0, 1.1, 0),
                collider="box",
            )
            Entity(
                parent=trunk, model="sphere", color=color.rgb(40, 110, 50),
                scale=(3.2, 2.6, 3.2), position=(0, 1.6, 0),
            )
            self.trees.append(trunk)
            self.entities.append(trunk)

    def _build_rocks(self):
        for _ in range(settings.ROCK_COUNT):
            pos = self._random_ground_point(avoid_center=6)
            rock = Entity(
                model="cube",
                color=color.rgb(120, 120, 125).tint(random.uniform(-0.1, 0.1)),
                scale=(
                    random.uniform(0.6, 1.6),
                    random.uniform(0.5, 1.2),
                    random.uniform(0.6, 1.6),
                ),
                position=pos + Vec3(0, 0.3, 0),
                rotation=(0, random.uniform(0, 360), 0),
                collider="box",
            )
            self.entities.append(rock)

    def _build_buildings(self):
        for i in range(settings.BUILDING_COUNT):
            angle = (i / settings.BUILDING_COUNT) * math.tau
            r = random.uniform(20, settings.WORLD_SIZE * 0.6)
            x, z = math.cos(angle) * r, math.sin(angle) * r
            height = random.uniform(6, 14)
            width = random.uniform(5, 9)
            building = Entity(
                model="cube",
                color=color.rgb(200, 190, 175).tint(random.uniform(-0.1, 0.05)),
                scale=(width, height, width),
                position=(x, height / 2, z),
                collider="box",
            )
            # simple flat roof accent + a doorway marker
            Entity(parent=building, model="cube", color=color.rgb(120, 40, 40),
                   scale=(1.02, 0.06, 1.02), position=(0, 0.5, 0))
            Entity(parent=building, model="cube", color=color.rgb(60, 40, 25),
                   scale=(0.25, 0.4, 0.02), position=(0, -0.3, 0.505))
            self.buildings.append(building)
            self.entities.append(building)

    def _build_decorations(self):
        """Small non-collidable flavor props: bushes, flowers, lamp posts,
        crates, and fence posts to make the world feel populated."""
        for _ in range(settings.DECORATION_COUNT):
            pos = self._random_ground_point(avoid_center=4)
            kind = random.choice(["bush", "flower", "lamp", "crate", "fence"])
            if kind == "bush":
                Entity(model="sphere", color=color.rgb(50, 120, 60),
                       scale=random.uniform(0.6, 1.2), position=pos + Vec3(0, 0.4, 0))
            elif kind == "flower":
                Entity(model="cube", color=random.choice([color.red, color.yellow, color.violet]),
                       scale=(0.15, 0.3, 0.15), position=pos + Vec3(0, 0.15, 0))
            elif kind == "lamp":
                post = Entity(model="cube", color=color.rgb(40, 40, 40),
                              scale=(0.12, 2.4, 0.12), position=pos + Vec3(0, 1.2, 0))
                Entity(parent=post, model="sphere", color=color.rgba(255, 230, 150, 255),
                       scale=0.35, position=(0, 1.15, 0))
            elif kind == "crate":
                Entity(model="cube", color=color.rgb(140, 100, 60),
                       scale=0.8, position=pos + Vec3(0, 0.4, 0), collider="box")
            elif kind == "fence":
                Entity(model="cube", color=color.rgb(160, 140, 110),
                       scale=(1.6, 0.6, 0.08), position=pos + Vec3(0, 0.3, 0),
                       rotation=(0, random.uniform(0, 360), 0))

    def _build_coins(self):
        for _ in range(settings.COIN_COUNT):
            pos = self._random_ground_point(avoid_center=3)
            coin = Entity(
                model="sphere",
                color=color.gold,
                scale=0.4,
                position=pos + Vec3(0, 0.6, 0),
            )
            coin.collect_value = settings.COIN_VALUE
            self.coins.append(coin)

    # ------------------------------------------------------------------
    def _random_ground_point(self, avoid_center=5):
        while True:
            x = random.uniform(-settings.WORLD_SIZE * 0.9, settings.WORLD_SIZE * 0.9)
            z = random.uniform(-settings.WORLD_SIZE * 0.9, settings.WORLD_SIZE * 0.9)
            if math.hypot(x, z) > avoid_center:
                return Vec3(x, 0, z)

    def _near_water(self, pos, margin=4):
        return (
            abs(pos.x - settings.WATER_POS.x) < settings.WATER_SIZE / 2 + margin
            and abs(pos.z - settings.WATER_POS.z) < settings.WATER_SIZE / 2 + margin
        )

    def get_random_spawn_point(self):
        return self._random_ground_point(avoid_center=15) + Vec3(0, 1, 0)