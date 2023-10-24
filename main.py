import random
import math
from typing import Any
import pygame
from gui_elements import add_gui_elements

pygame.init()
display_size = (900, 900)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption('Mars Mars')

class Player:
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

        self.max_landing_speed = 150

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

    def resolve_collision(self):
        if player.vy < player.max_landing_speed:
            player.box.y = self.box.y - player.box.h
            player.vy = 0
            player.vx = 0
        else:
            setup()

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
        self.x += player.vx * dt
        self.y += player.vy * dt

class GUI:
    def __init__(self):
        self.fuel = FuelGUI()

        self.elements = [self.fuel]

    def draw(self):
        for element in self.elements:
            element.draw()

    def update(self):
        for element in self.elements:
            element.update()

class FuelGUI:
    def __init__(self):
        self.x = 20
        self.y = 20
        self.img = pygame.image.load('./img/fuel.png')

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

    def update(self):
        filled = 5.5
        def hex_points(length, center):
            points = [(center[0] - length, center[1] - length)]
            pygame.draw.rect(screen, 'green', (points[0][0], points[0][1], 10, 10))

            for i in range(1, 6):
                angle = -60 * math.pi / 180 + i * 60 * math.pi / 180
                x = length * math.cos(angle) + points[i - 1][0]
                y = length * math.sin(angle) + points[i - 1][1]

                points.append((x, y))
            
            points.append(points.pop(0))

            return points
                
        big_hex = hex_points(30, (0, 0))
        # small_hex = hex_points(20, (100, 50))
        
        pygame.draw.polygon(screen, 'white', big_hex, 2)
        # pygame.draw.polygon(screen, 'white', small_hex, 2)
        # for n in range(6):
        #     index1 = n
        #     index2 = (n + 1) % 6

        #     if math.floor(filled) == 5 - n:
        #         width = filled % 1

        #         x1 = (big_hex[index1][0] + big_hex[index2][0]) * width
        #         y1 = (big_hex[index1][1] + big_hex[index2][1]) * width

        #         x2 = (small_hex[index1][0] + small_hex[index2][0]) * width
        #         y2 = (small_hex[index1][1] + small_hex[index2][1]) * width

        #         points = [(x1, y1), big_hex[index2], small_hex[index2], (x2, y2)]
        #     elif math.floor(filled) < 5 - n:
        #         continue
        #     else:
        #         points = [big_hex[index1], big_hex[index2], small_hex[index2], small_hex[index1]]

        #     pygame.draw.polygon(screen, 'white', points)

def box_collision(box1, box2):
    check_x = box1.x + box1.w > box2.x and box1.x < box2.x + box2.w
    check_y = box1.y + box1.h > box2.y and box1.y < box2.y + box2.h
    if check_x and check_y:
        box2.parent.resolve_collision()

def random_float(max, min):
    return random.random() * (max - min) + min

def setup():
    global boxes
    global game_objects
    global game_window
    global terrain
    global player

    boxes = []
    game_objects = [Platform(100, 400)]
    game_window = GameWindow()
    terrain = Terrain()
    player = Player()

# Global Variables
gui = GUI()
mouse = [False, False]
gravity = 3
clock = pygame.time.Clock()
dt = 0

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

    gui.update()
    player.update()
    game_window.update()

    gui.draw()
    terrain.draw()
    for game_object in game_objects:
        game_object.draw()
    player.draw()

    for box in boxes:
        box.draw()

    pygame.display.flip()