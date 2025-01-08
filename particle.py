import pygame as pg
import numpy as np


class Particle:
    def __init__(
        self,
        pos: list, 
        vel: list=[0, 0], 
        acc: list=[0, 0], 
        color: pg.Color=pg.Color("blue"), 
        radius: int=5
    ):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.acc = np.array(acc, dtype=float)
        self.old_pos = self.pos - vel
        self.color = color
        self.radius = radius

    def update(self, delta_time):
        # Verlet integration
        self.vel = self.pos - self.old_pos
        self.old_pos = self.pos.copy()
        self.pos += self.vel + self.acc * delta_time ** 2
        self.acc = np.zeros(2, dtype=float)

        self.color = self.vel_to_color()

    def render(self, screen):
        pg.draw.circle(screen, self.color, self.pos, self.radius)

    def vel_to_color(self):
        max_speed = 10
        speed = np.linalg.norm(self.vel)
        speed = min(speed, max_speed)
        speed /= max_speed  # Normalize to [0, 1]

        # Map speed to radians in hsl color space
        hue = 0.66 - speed * 0.66
        color = pg.Color(0)
        color.hsla = (hue * 360, 100, 50, 100)

        return color
