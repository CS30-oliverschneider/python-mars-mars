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
        check_lines = []

        index = max(math.floor((self.x - game_window.x) / terrain.max_length - 1), 0)
        line = terrain.lines[index]

        while line.x1 < self.x + self.w:
            if line.x2 > self.x:
                check_lines.append(line)
                line.color = 'red'

            index += 1
            line = terrain.lines[index]
            line.color = 'white'

        
        if highest_point < self.y:
            setup()

class Terrain:
    def __init__(self):
        self.lines = [Line(0, 700, 0, 0)]

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

        self.p1 = (self.x1, self.y1)
        self.p2 = (self.x2, self.y2)

        self.color = 'white'

    def draw(self):
        pygame.draw.line(screen, self.color, self.p1, self.p2)


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