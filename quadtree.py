import pygame as pg
from typing import List, Optional
from particle import Particle


class Boundary:
    """
    A rectangular boundary used by QuadTree to subdivide space.

    Attributes:
        x (float): X-coordinate of the center
        y (float): Y-coordinate of the center
        w (float): Half-width of the boundary
        h (float): Half-height of the boundary
    """

    def __init__(self, x: float, y: float, w: float, h: float) -> None:
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    def contains(self, particle: Particle) -> bool:
        """
        Check if a particle is within this boundary.

        Args:
            particle: Particle object with pos attribute

        Returns:
            bool: True if particle is inside boundary, False otherwise
        """
        return (particle.pos[0] >= self.x - self.w and
                particle.pos[0] <= self.x + self.w and
                particle.pos[1] >= self.y - self.h and
                particle.pos[1] <= self.y + self.h)

    def intersects(self, range_: 'Boundary') -> bool:
        """
        Check if this boundary intersects with another boundary.

        Args:
            range_: Another Boundary object to check intersection with

        Returns:
            bool: True if boundaries intersect, False otherwise
        """
        return not (range_.x - range_.w > self.x + self.w or
                   range_.x + range_.w < self.x - self.w or
                   range_.y - range_.h > self.y + self.h or
                   range_.y + range_.h < self.y - self.h)

    def render(self, screen: pg.Surface, color: pg.Color = pg.Color("gray20")) -> None:
        """
        Draw the boundary rectangle on the screen.

        Args:
            screen: Pygame surface to draw on
        """
        rect = (
            int(self.x - self.w), 
            int(self.y - self.h), 
            int(self.w * 2), 
            int(self.h * 2)
        )
        pg.draw.rect(screen, color, rect, 1)


class QuadTree:
    """
    A QuadTree data structure for efficient spatial partitioning and querying.

    The QuadTree recursively subdivides space into four quadrants, allowing for
    efficient spatial queries and collision detection.

    Attributes:
        boundary (Boundary): The rectangular boundary of this node
        capacity (int): Maximum number of particles before subdivision
        particles (list): List of particles in this node
        divided (bool): Whether this node has been subdivided
        northwest, northeast, southwest, southeast (QuadTree): Child nodes
    """

    def __init__(self, boundary: Boundary, capacity: int = 4) -> None:
        self.boundary = boundary
        self.capacity = capacity
        self.particles = []
        self.divided = False
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None

    def subdivide(self) -> None:
        """
        Subdivide this node into four child nodes, creating a new QuadTree for each quadrant.
        """
        x = self.boundary.x
        y = self.boundary.y
        w = self.boundary.w / 2
        h = self.boundary.h / 2

        nw = Boundary(x - w, y - h, w, h)
        ne = Boundary(x + w, y - h, w, h)
        sw = Boundary(x - w, y + h, w, h)
        se = Boundary(x + w, y + h, w, h)

        self.nw = QuadTree(nw, self.capacity)
        self.ne = QuadTree(ne, self.capacity)
        self.sw = QuadTree(sw, self.capacity)
        self.se = QuadTree(se, self.capacity)
        self.divided = True

    def insert(self, particle: Particle) -> bool:
        """
        Insert a particle into the QuadTree.

        Args:
            particle: Particle object to insert

        Returns:
            bool: True if particle was inserted, False otherwise
        """
        if not self.boundary.contains(particle):
            return False

        if len(self.particles) < self.capacity and not self.divided:
            self.particles.append(particle)
            return True

        if not self.divided:
            self.subdivide()

        return (self.nw.insert(particle) or
                self.ne.insert(particle) or
                self.sw.insert(particle) or
                self.se.insert(particle))

    def query(self, range_: Boundary, found: Optional[List[Particle]] = None) -> List[Particle]:
        """
        Find all particles within a given boundary range.

        Args:
            range_: Boundary object defining the search area
            found (list, optional): List to store found particles

        Returns:
            list: List of particles found within the range
        """
        if found is None:
            found = []

        if not self.boundary.intersects(range_):
            return found

        for particle in self.particles:
            if range_.contains(particle):
                found.append(particle)

        if self.divided:
            self.nw.query(range_, found)
            self.ne.query(range_, found)
            self.sw.query(range_, found)
            self.se.query(range_, found)

        return found
    
    def get_boundary(self, pos: List[float]) -> Boundary:
        """
        Get the boundary that contains the given position.

        Args:
            pos (list): Position to check

        Returns:
            Boundary: Boundary object containing the position
        """
        temp_particle = Particle(pos)

        if self.divided:
            if self.nw.boundary.contains(temp_particle):
                return self.nw.get_boundary(pos)
            if self.ne.boundary.contains(temp_particle):
                return self.ne.get_boundary(pos)
            if self.sw.boundary.contains(temp_particle):
                return self.sw.get_boundary(pos)
            if self.se.boundary.contains(temp_particle):
                return self.se.get_boundary(pos)

        return self.boundary

    def render(self, screen: pg.Surface) -> None:
        """
        Recursively render the QuadTree structure on the screen.

        Args:
            screen: Pygame surface to draw on
        """
        self.boundary.render(screen)
        
        if self.divided:
            self.nw.render(screen)
            self.ne.render(screen)
            self.sw.render(screen)
            self.se.render(screen)

    def clear(self) -> None:
        """
        Clear all particles and subdivisions from the QuadTree.
        """
        self.particles = []
        self.nw = None
        self.ne = None
        self.sw = None
        self.se = None
        self.divided = False