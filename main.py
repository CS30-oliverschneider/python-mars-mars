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
        pygame.draw.rect(screen, 'white', (self.x - game_window.x, self.y - game_window.y, self.w, self.h))

    def update(self):
        self.update_velocity()
        self.move()
        self.check_collision()

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

        x = terrain.vectors[start_index].x
        index = start_index

        while x < self.x + self.w:
            vector = terrain.vectors[index]
            x += vector.x
            index += 1

            if x > self.x:
                check_vectors.append(vector)

                if index % 2 == 0:
                    terrain.colors[vector.x] = 'red'
                else:
                    terrain.colors[vector.x] = 'orange'

        # for n in range(1, 5):
        #     terrain.colors[terrain.vectors[start_index - n].x] = 'white'

class Terrain:
    def __init__(self):
        self.vectors = [pygame.Vector2(10, 0)]
        
        self.start_x = 0
        self.end_x = 0
        self.start_y = 300

        self.min_length = 10
        self.max_length = 50
        self.min_angle = -1
        self.max_angle = 1
        self.max_delta_angle = 0.5

        self.colors = {10.0: 'white'}

        self.generate_terrain()

    def generate_terrain(self):
        vector = self.vectors[len(self.vectors) - 1]
        x = self.end_x

        while x < game_window.x + display_size[0]:
            vector = self.new_vector(vector)
            self.vectors.append(vector)
            self.colors[vector.x] = 'white'
            x += vector.x

        self.end_x = x

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
        if self.start_x + self.vectors[0].x < game_window.x:
            self.start_x = self.start_x + self.vectors[0].x
            self.start_y = self.start_y + self.vectors[0].y

            self.vectors.pop(0)

    def add_vectors(self):
        if self.end_x < game_window.x + display_size[0]:
            self.generate_terrain()
    
    
    def draw(self):
        self.remove_vectors()
        self.add_vectors()

        x1 = self.start_x
        y1 = self.start_y

        for vector in self.vectors:
            x2 = x1 + vector.x
            y2 = y1 + vector.y

            point1 = (x1 - game_window.x, y1 - game_window.y)
            point2 = (x2 - game_window.x, y2 - game_window.y)
            pygame.draw.lines(screen, self.colors.get(vector.x), False, [point1, point2])

            x1 = x2
            y1 = y2

class GameWindow:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self):
        self.x += astronaut.vx * dt
        self.y += astronaut.vy * dt


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
    # game_window.update()

    astronaut.draw()
    terrain.draw()


    pygame.display.flip()