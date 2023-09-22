import random
import math
import pygame

pygame.init()
display_size = (400, 500)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption('Mars Mars')

mouse = [False, False]
gravity = 3
clock = pygame.time.Clock()
dt = 0
terrain = []

terrain_height = 300
min_length = 10
max_length = 100
max_delta_angle = 1
min_angle = -1.5
max_angle = 1.5

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
        pygame.draw.rect(screen, 'white', (self.x, self.y, self.w, self.h))

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

def random_float(max, min):
    return random.random() * (max - min) + min

def generate_terrain():
    vector = terrain[len(terrain) - 1]

    while vector[0] < display_size[0]:
        vector, angle = generate_vector(vector, angle)
        terrain.append(vector)
        print(vector)

def generate_vector(last_vector):
    random_angle = random_float(-max_delta_angle, max_delta_angle)
    new_length = random_float(max_length, min_length)

    return new_vector

generate_terrain()
astronaut = Astronaut()
 
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill('black')
    dt = clock.tick(60) / 1000

    pressed = pygame.mouse.get_pressed()
    mouse = (pressed[0], pressed[2])

    astronaut.update()
    astronaut.draw()

    pygame.draw.lines(screen, 'white', False, terrain)

    pygame.display.flip()