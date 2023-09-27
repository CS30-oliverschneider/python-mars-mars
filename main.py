import random
import math
import pygame
import pprint

pygame.init()
display_size = (900, 900)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption('Mars Mars')

mouse = [False, False]
gravity = 3
clock = pygame.time.Clock()
dt = 0

class Astronaut:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.w = 50
        self.h = 50

        self.vx = 0
        self.vy = 0

        self.x_thrust = 2
        self.y_thrust = 5

    def draw(self):
        pygame.draw.rect(screen, 'white', (self.x - game_window.x, self.y, self.w, self.h))

    def update(self):
        self.update_velocity()
        self.move()

    def move(self):
        self.x += self.vx * dt
        self.y += self.vy * dt

    def update_velocity(self):
        self.vy += gravity
    
        if mouse[0]:
            self.vy -= self.y_thrust
            self.vx += self.x_thrust
        if mouse[1]:
            self.vy -= self.y_thrust
            self.vx -= self.x_thrust

    def check_collision(self):
        check_vectors = []
        start_index = math.floor(self.x / terrain.max_length)

class Terrain:
    def __init__(self):
        self.vectors = [pygame.Vector2(10, 0)]
        self.draw_start = 0

        self.terrain_height = 300
        self.min_length = 10
        self.max_length = 50
        self.min_angle = -1.5
        self.max_angle = 1.5
        self.max_delta_angle = 0.5

        self.generate_terrain()

    def generate_terrain(self):
        vector = self.vectors[len(self.vectors) - 1]
        x = 0

        while x < display_size[0]:
            vector = self.new_vector(vector)
            self.vectors.append(vector)
            x += vector.x

    def new_vector(self, last_vector):
        angle = random_float(-self.max_delta_angle, self.max_delta_angle)
        new_angle = math.atan(last_vector.y / last_vector.x) + angle

        rotate_angle = angle
        if new_angle < self.min_angle or new_angle > self.max_angle:
            rotate_angle = -angle

        new_length = random_float(self.max_length, self.min_length)
    
        new_vector = last_vector.rotate_rad(rotate_angle)
        new_vector.scale_to_length(new_length)

        return new_vector
    
    def remove_vectors(self):
        if self.vectors[1].x < game_window.x:
            self.draw_start = self.draw_start + self.vectors[0].x
            self.vectors.pop(0)

            last_vector = self.vectors[-1]
            self.vectors.append(self.new_vector(last_vector))
    
    
    def draw(self):
        # self.remove_vectors()

        x1 = self.draw_start - game_window.x
        y1 = self.terrain_height

        for vector in self.vectors:
            x2 = x1 + vector.x
            y2 = y1 + vector.y

            pygame.draw.lines(screen, 'white', False, [(x1 - game_window.x, y1), (x2 - game_window.x, y2)])

            x1 = x2
            y1 = y2

class GameWindow:
    def __init__(self):
        self.x = 0
        self.y = 0


def random_float(max, min):
    return random.random() * (max - min) + min

def setup():
    global game_window
    global terrain
    global astronaut

    game_window = GameWindow()
    terrain = Terrain()
    astronaut = Astronaut()

setup()
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            setup()

    screen.fill('black')
    dt = clock.tick(60) / 1000

    pressed = pygame.mouse.get_pressed()
    mouse = (pressed[0], pressed[2])

    astronaut.update()
    astronaut.draw()

    terrain.draw()

    game_window.x += 1

    pygame.display.flip()