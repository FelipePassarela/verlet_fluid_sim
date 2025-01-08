import pygame as pg
from simulation import Simulation
import config
import cProfile
import pstats


def main():
    pg.init()
    screen = pg.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT))
    clock = pg.time.Clock()
    running = True

    simulation = Simulation(config.SCREEN_WIDTH, config.SCREEN_HEIGHT, config.NUM_PARTICLES)

    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_r:
                    simulation = Simulation(
                        config.SCREEN_WIDTH, 
                        config.SCREEN_HEIGHT, 
                        config.NUM_PARTICLES
                    )
                if event.key == pg.K_g:
                    config.GRAVITY = 0 if config.GRAVITY == 980 else 980
                if event.key == pg.K_d:  # Debug
                    config.RENDER_QUAD_TREE = not config.RENDER_QUAD_TREE

        delta_time = clock.get_time() / 1000.0
        simulation.update(delta_time)

        screen.fill(config.COLORS["background"])
        simulation.render(screen)

        # display debug infos
        fps = clock.get_fps()
        msg = f"FPS: {fps:.2f}"
        msg += f"  Particles: {config.NUM_PARTICLES}"
        msg += f"  Gravity: {config.GRAVITY}"

        font = pg.font.Font(None, 26)
        text = font.render(msg, True, pg.Color("white"))
        screen.blit(text, (10, 10))

        pg.display.flip()
        clock.tick(60)

    pg.quit()


if __name__ == '__main__':
    # profiler = cProfile.Profile()
    # profiler.enable()
    main()
    # profiler.disable()
    # stats = pstats.Stats(profiler).sort_stats('tottime')
    # stats.print_stats()