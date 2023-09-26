import random
import math
import pygame
import pprint

pygame.init()
display_size = (400, 500)
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

class Terrain:
    def __init__(self, terrain_height, min_length, max_length, min_angle, max_angle, max_delta_angle):
        self.vectors = [pygame.Vector2(10, 0)]

        self.terrain_height = terrain_height
        self.min_length = min_length
        self.max_length = max_length
        self.max_delta_angle = max_delta_angle
        self.min_angle = min_angle
        self.max_angle = max_angle

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
    
    
    def draw(self):
        x1 = 0
        y1 = self.terrain_height

        for vector in self.vectors:
            x2 = x1 + vector.x
            y2 = y1 + vector.y

            pygame.draw.lines(screen, 'white', False, [(x1, y2), (x2, y2)])

            x1 = x2
            y1 = y2



def random_float(max, min):
    return random.random() * (max - min) + min

terrain = Terrain(300, 10, 100, -1.5, 1.5, 0.5)
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

    terrain.draw()

    pygame.display.flip()