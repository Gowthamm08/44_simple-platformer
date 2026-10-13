
import pygame

from game.game_engine import GameEngine


WIDTH = 800
HEIGHT = 500
FPS = 60

SKY = (100, 160, 220)


def main():
    pygame.init()

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Simple Platformer - Lab 4")

    clock = pygame.time.Clock()
    engine = GameEngine(WIDTH, HEIGHT)

    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                engine.handle_event(event)

        if not running:
            break

        engine.handle_input()
        engine.update()

        screen.fill(SKY)
        engine.render(screen)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
