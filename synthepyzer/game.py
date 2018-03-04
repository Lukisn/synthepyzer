import sys
import pygame
pygame.init()


def main():
    print("start")
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                print(f"pressed {event.key} ('{event.unicode}') mod = {event.mod}")
                if event.key == pygame.K_ESCAPE:
                    running = False
            elif event.type == pygame.KEYUP:
                print(f"released {event.key} mod = {event.mod}")
    print("done.")


if __name__ == "__main__":
    main()
