import pygame as pg


class Boundary:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, particle):
        return (particle.pos[0] >= self.x - self.w and
                particle.pos[0] <= self.x + self.w and
                particle.pos[1] >= self.y - self.h and
                particle.pos[1] <= self.y + self.h)

    def intersects(self, range_):
        return not (range_.x - range_.w > self.x + self.w or
                   range_.x + range_.w < self.x - self.w or
                   range_.y - range_.h > self.y + self.h or
                   range_.y + range_.h < self.y - self.h)

    def render(self, screen):
        rect = (
            int(self.x - self.w), 
            int(self.y - self.h), 
            int(self.w * 2), 
            int(self.h * 2)
        )
        pg.draw.rect(screen, (50, 50, 50), rect, 1)


class QuadTree:
    def __init__(self, boundary, capacity=4):
        self.boundary = boundary
        self.capacity = capacity
        self.particles = []
        self.divided = False
        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None

    def subdivide(self):
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2

        nw = Boundary(x - w, y - h, w, h)
        ne = Boundary(x + w, y - h, w, h)
        sw = Boundary(x - w, y + h, w, h)
        se = Boundary(x + w, y + h, w, h)

        self.northwest = QuadTree(nw, self.capacity)
        self.northeast = QuadTree(ne, self.capacity)
        self.southwest = QuadTree(sw, self.capacity)
        self.southeast = QuadTree(se, self.capacity)
        self.divided = True

    def insert(self, particle):
        if not self.boundary.contains(particle):
            return False

        if len(self.particles) < self.capacity and not self.divided:
            self.particles.append(particle)
            return True

        if not self.divided:
            self.subdivide()

        return (self.northwest.insert(particle) or
                self.northeast.insert(particle) or
                self.southwest.insert(particle) or
                self.southeast.insert(particle))

    def query(self, range_, found=None):
        if found is None:
            found = []

        if not self.boundary.intersects(range_):
            return found

        for particle in self.particles:
            if range_.contains(particle):
                found.append(particle)

        if self.divided:
            self.northwest.query(range_, found)
            self.northeast.query(range_, found)
            self.southwest.query(range_, found)
            self.southeast.query(range_, found)

        return found

    def render(self, screen):
        self.boundary.render(screen)
        
        if self.divided:
            self.northwest.render(screen)
            self.northeast.render(screen)
            self.southwest.render(screen)
            self.southeast.render(screen)

    def clear(self):
        self.particles = []
        self.northwest = None
        self.northeast = None
        self.southwest = None
        self.southeast = None
        self.divided = False