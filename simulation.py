from particle import Particle
import config
import numpy as np
import pygame as pg
from quadtree import QuadTree, Boundary


class Simulation:
    def __init__(self, width: int, height: int, num_particles: int):
        self.width = width
        self.height = height
        self.num_particles = num_particles
        self.particles = self.initialize_particle_grid()

        self.boundary = Boundary(self.width/2, self.height/2, self.width/2, self.height/2)
        self.quad_tree = QuadTree(self.boundary, capacity=config.QUADTREE_CAPACITY)

    def initialize_particle_grid(self):
        particles = np.empty(self.num_particles, dtype=Particle)
        radius = config.PARTICLE["MAX_RADIUS"]

        total = self.num_particles
        cols = int(np.ceil(np.sqrt(total)))
        rows = (total + cols - 1) // cols

        origin_x = self.width // 2 - cols * radius
        origin_y = self.height // 2 - rows * radius

        count = 0
        for r in range(rows):
            for c in range(cols):
                if count >= total:
                    break

                noise = np.random.uniform(-0.1, 0.1, 2)
                particle = Particle(
                    pos=[origin_x + c * radius * 2, origin_y + r * radius * 2 ] + noise,
                    vel=[0, 0],
                    acc=[0, 0],
                    color=pg.Color("blue"),
                    radius=np.random.uniform(radius // 2, radius)
                )
                particles.put(count, particle)
                count += 1

        return particles
    
    def update(self, delta_time):
        # Sub-steps to improve stability
        sub_steps = config.SUB_STEPS
        sub_dt = delta_time / sub_steps
        
        for _ in range(sub_steps):
            for particle in self.particles:
                self.apply_gravity(particle)
                self.apply_drag(particle)
                self.apply_viscosity(particle)

                mouse_pos = pg.mouse.get_pos()
                if pg.mouse.get_pressed()[0]:
                    self.apply_mouse_force(mouse_pos, 250, 6000, particle)
                elif pg.mouse.get_pressed()[2]:
                    self.apply_mouse_force(mouse_pos, 250, -6000, particle)

                particle.update(sub_dt)
            
            self.resolve_collisions()
            
            for particle in self.particles:
                self.apply_boundary(particle)

    def render(self, screen):
        for particle in self.particles:
            particle.render(screen)
        
        if config.RENDER_QUAD_TREE:
            self.render_quad_tree(screen)

            mouse_pos = pg.mouse.get_pos()
            mouse_bound = self.quad_tree.get_boundary(mouse_pos)
            mouse_bound.render(screen, pg.Color("red"))

            found_particles = self.quad_tree.query(mouse_bound)
            for p in found_particles:
                pg.draw.circle(screen, pg.Color("white"), p.pos, p.radius, 1)

    def render_quad_tree(self, screen):
        self.quad_tree.render(screen)

    def apply_boundary(self, particle: Particle):
        if particle.pos[0] - particle.radius < 0:
            particle.pos[0] = particle.radius
            particle.vel[0] = -particle.vel[0]
        if particle.pos[0] + particle.radius > self.width:
            particle.pos[0] = self.width - particle.radius
            particle.vel[0] = -particle.vel[0]
        if particle.pos[1] - particle.radius < 0:
            particle.pos[1] = particle.radius
            particle.vel[1] = -particle.vel[1]
        if particle.pos[1] + particle.radius > self.height:
            particle.pos[1] = self.height - particle.radius
            particle.vel[1] = -particle.vel[1]

    def apply_gravity(self, particle: Particle):
        particle.acc[1] = config.GRAVITY

    def apply_force(self, force, particle: Particle):
        particle.acc += force

    def apply_drag(self, particle: Particle):
        drag = -0.5 * config.DRAG * particle.vel * np.abs(particle.vel)
        self.apply_force(drag, particle)

    def apply_viscosity(self, particle: Particle):
        # Stokes force: F = -6 * pi * r * η * v
        viscous_force = -6 * np.pi * particle.radius * config.VISCOSITY * particle.vel
        self.apply_force(viscous_force, particle)

    def apply_mouse_force(self, mouse_pos, radius, strength_factor, particle: Particle):
        direction = np.array(mouse_pos) - particle.pos
        distance = np.linalg.norm(direction)
        if distance == 0:
            return

        if distance < radius:
            direction /= distance
            strength = (1 - distance / radius) ** 2 * strength_factor
            self.apply_force(strength * direction, particle)

    def resolve_collisions(self):
        """
        Resolve particle collisions within the simulation.

        This method constructs a QuadTree based on the current set of particles,
        enumerates potential collisions by querying particles within a search range,
        and delegates the collision response to the corresponding handler. Each
        particle is checked against neighbors to detect overlaps and apply
        appropriate resolution.

        Args:
            None
        Returns:
            None
        """
        
        self.quad_tree.clear()

        for particle in self.particles:
            self.quad_tree.insert(particle)
            
        for particle in self.particles:
            search_range = Boundary(
                particle.pos[0], 
                particle.pos[1], 
                particle.radius + config.PARTICLE["MAX_RADIUS"],
                particle.radius + config.PARTICLE["MAX_RADIUS"]
            )

            nearby = self.quad_tree.query(search_range)

            for other in nearby:
                if particle is other:
                    continue
                self.handle_collision(particle, other)

    def handle_collision(self, p1: Particle, p2: Particle):
        """
        Handles the collision between two Particle objects by checking if they overlap
        and, if necessary, adjusting their positions and velocities to prevent
        further overlap and to model a collision based on an elastic impulse.

        Args:
            p1 (Particle): The first particle involved in the collision.
            p2 (Particle): The second particle involved in the collision.
        Notes:
            - Uses a simple Axis-Aligned Bounding Box (AABB) check before more
              expensive calculations.
            - If particles are overlapping beyond a minimum allowed distance, they
              will be separated.
            - Applies a velocity adjustment (impulse) to simulate an elastic collision.
            - Takes into account a defined minimum collision velocity and a restitution
              coefficient from config.COLLISION.
        """

        # Early return if the particles are too far apart (AABB)
        dx = p1.pos[0] - p2.pos[0]
        dy = p1.pos[1] - p2.pos[1]
        min_dist = p1.radius + p2.radius
        
        if abs(dx) > min_dist or abs(dy) > min_dist:
            return
        
        dist_sq = dx * dx + dy * dy
        min_dist_sq = min_dist * min_dist

        if dist_sq >= min_dist_sq or dist_sq < config.COLLISION["MIN_DISTANCE"]:
            return
            
        dist = np.sqrt(dist_sq)
        inv_dist = 1.0 / dist if dist > 0 else 0
        nx = dx * inv_dist
        ny = dy * inv_dist
        
        # Calculate the mass ratio of the particles
        p1_mass = p1.radius ** 2
        p2_mass = p2.radius ** 2
        total_mass = p1_mass + p2_mass
        p1_mass_ratio = p2_mass / total_mass
        p2_mass_ratio = p1_mass / total_mass

        # Move the particles apart so they don't overlap
        delta = min_dist - dist
        p1.pos[0] += nx * delta * p1_mass_ratio
        p1.pos[1] += ny * delta * p1_mass_ratio
        p2.pos[0] -= nx * delta * p2_mass_ratio
        p2.pos[1] -= ny * delta * p2_mass_ratio
        
        rvx = p1.vel[0] - p2.vel[0]
        rvy = p1.vel[1] - p2.vel[1]
        vel_normal = rvx * nx + rvy * ny
        
        # Early return if the particles are moving apart
        if vel_normal > -config.COLLISION["MIN_VELOCITY"]:
            return
            
        # Calculate the impulse to apply
        impulse = -(1 + config.COLLISION["RESTITUTION"]) * vel_normal
        impulse_vec = np.array([nx, ny]) * impulse
        p1.vel += impulse_vec * p1_mass_ratio
        p2.vel -= impulse_vec * p2_mass_ratio
        p1.old_pos = p1.pos - p1.vel
        p2.old_pos = p2.pos - p2.vel
