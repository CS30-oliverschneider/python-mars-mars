import random
import math
from typing import Any
import pygame
import pprint

pygame.init()
display_size = (900, 900)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption('Mars Mars')

game_objects = []
boxes = []
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

        self.box = BoundingBox(self, 0, 0, self.w, self.h)

        self.vx = 0
        self.vy = 0

        self.x_thrust = 2
        self.y_thrust = 5

    def draw(self):
        pygame.draw.rect(screen, 'white', (self.x - game_window.x, self.y - game_window.y, self.w, self.h))

    def update(self):
        self.update_velocity()
        self.move()
        self.check_object_collision()
        self.check_terrain_collision()

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

    def check_object_collision(self):
        for game_object in game_objects:
            box_collision(self.box, game_object.box)

    def check_terrain_collision(self):
        if terrain.highest > self.y + self.h:
            return
        
        check_lines = []

        index = max(math.floor((self.x - game_window.x) / terrain.max_length - 1), 0)
        line = terrain.lines[index]

        while line.x1 < self.x + self.w:
            if line.x2 > self.x:
                check_lines.append(line)
            index += 1
            line = terrain.lines[index]

        for line in terrain.lines:
            line.color = 'white'

        for line in check_lines:
            line.color = 'red'

        highest_line = min(check_lines, key = lambda line: min(line.y1, line.y2))

        highest_point = min(highest_line.y1, highest_line.y2)
        if highest_point > self.y + self.h:
            return
        
        left_below = highest_line.getY(self.x) < self.y + self.h
        right_below = highest_line.getY(self.x + self.w) < self.y + self.h
        if left_below or right_below:
            setup()


class Platform:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.w = 50
        self.h = 10

        self.box = BoundingBox(self, 0, 0, self.w, self.h)

    def resolve_collision(self, box):
        box.y = self.box.y - box.h

    def draw(self):
        pygame.draw.rect(screen, 'green', (self.x - game_window.x, self.y - game_window.y, self.w, self.h))

class BoundingBox:
    def __init__(self, parent, relative_x, relative_y, w, h):
        self.parent = parent

        self.relative_x = relative_x
        self.relative_y = relative_y
        self.w = w
        self.h = h

        boxes.append(self)
    
    def __setattr__(self, name, value):
        if name == 'x':
            self.parent.x += value - self.x
        elif name == 'y':
            self.parent.y += value - self.y
        else:
            super().__setattr__(name, value)

    def __getattribute__(self, name):
        if name == 'x':
            return self.parent.x + self.relative_x
        elif name == 'y':
            return self.parent.y + self.relative_y
        else:
            return super().__getattribute__(name)
    
    def draw(self):
        pygame.draw.rect(screen, 'red', (self.x - game_window.x, self.y - game_window.y, self.w, self.h), 1)

class Terrain:
    def __init__(self):
        self.lines = [Line(0, 700, 0, 0)]
        self.highest = float('inf')

        self.min_length = 10
        self.max_length = 50
        self.min_angle = -1
        self.max_angle = 1
        self.max_delta_angle = 0.5

        self.generate_terrain()

    def generate_terrain(self):
        line = self.lines[-1]
        x = self.lines[-1].x2

        while x < game_window.x + display_size[0]:
            line = self.new_line()
            self.lines.append(line)
            x += line.dx

            highest = min(line.y1, line.y2)
            if highest < self.highest:
                self.highest = highest

    def new_line(self):
        last_line = self.lines[-1]

        delta_angle = random_float(-self.max_delta_angle, self.max_delta_angle)
        new_angle = last_line.angle + delta_angle

        if new_angle < self.min_angle or new_angle > self.max_angle:
            new_angle = last_line.angle - delta_angle

        new_length = random_float(self.max_length, self.min_length)

        return Line(last_line.x2, last_line.y2, new_length, new_angle)
    
    def remove_vectors(self):
        if self.lines[0].x2 < game_window.x:
            self.lines.pop(0)

    def add_vectors(self):
        if self.lines[-1].x2 < game_window.x + display_size[0]:
            self.generate_terrain()
    
    
    def draw(self):
        self.remove_vectors()
        self.add_vectors()

        for line in self.lines:
            line.draw()

class Line:
    def __init__(self, x1, y1, length, angle):
        self.x1 = x1
        self.y1 = y1
        self.length = length
        self.angle = angle

        self.y2 = y1 + length * math.sin(angle)
        self.x2 = x1 + length * math.cos(angle)
        self.dx = self.x2 - self.x1

        self.color = 'white'

    def getY(self, x):
        if x < self.x1 or x > self.x2:
            return float('inf')
        else:
            return ((self.y2 - self.y1) / (self.x2 - self.x1)) * (x - self.x1) + self.y1

    def draw(self):
        p1 = (self.x1 - game_window.x, self.y1 - game_window.y)
        p2 = (self.x2 - game_window.x, self.y2 - game_window.y)
        pygame.draw.line(screen, self.color, p1, p2)


class GameWindow:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self):
        self.x += astronaut.vx * dt
        self.y += astronaut.vy * dt

def box_collision(box1, box2):
    check_x = box1.x + box1.w > box2.x and box1.x < box2.x + box2.w
    check_y = box1.y + box1.h > box2.y and box1.y < box2.y + box2.h
    if check_x and check_y:
        box2.parent.resolve_collision(box1)

def random_float(max, min):
    return random.random() * (max - min) + min

def setup():
    global game_window
    global terrain
    global astronaut
    global game_objects
    global boxes

    boxes = []
    game_objects = [Platform(100, 400)]
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
    game_window.update()

    terrain.draw()
    for game_object in game_objects:
        game_object.draw()
    astronaut.draw()

    for box in boxes:
        box.draw()

    pygame.display.flip()