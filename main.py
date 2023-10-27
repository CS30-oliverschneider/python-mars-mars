import random
import math
import pygame
import time

pygame.init()
display_size = (900, 900)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption('Mars Mars')

class Player:
    def __init__(self, platform):
        self.w = 50
        self.h = 50
        self.x = platform.x + platform.w / 2 - self.w / 2
        self.y = platform.y - self.h

        self.box = BoundingBox(self, 0, 0, self.w, self.h)

        self.state = 'landed'
        self.platform = platform

        self.vx = 0
        self.vy = 0

        self.x_thrust = 2
        self.y_thrust = 5

        self.max_landing_speed = 150
        self.launch_speed_x = 150
        self.launch_speed_y = -300

        self.fuel = 6
        self.delta_fuel = 0.05

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
        if self.state == 'landed':
            if not mouse.down:
                self.state = 'ready'
            return
        elif self.state == 'ready':
            if mouse.down:
                self.vx = self.launch_speed_x
                self.vy = self.launch_speed_y
                self.state = 'launched'
            return
        
        self.vy += gravity

        if self.state == 'launched':
            if not mouse.down:
                self.state = 'flying'
            return

        if self.fuel <= 0:
            return
    
        if mouse.left:
            self.vy -= self.y_thrust
            self.vx += self.x_thrust
        if mouse.right:
            self.vy -= self.y_thrust
            self.vx -= self.x_thrust

        if mouse.down:
            self.fuel -= self.delta_fuel

    def check_object_collision(self):
        for game_object in game_objects:
            box_collision(self.box, game_object.box)

    def check_terrain_collision(self):
        if terrain.highest > self.y + self.h:
            return
        
        highest_line = terrain.highest_in_range(self.x, self.x + self.w)

        highest_point = min(highest_line.y1, highest_line.y2)
        if highest_point > self.y + self.h:
            return
        
        left_below = highest_line.get_y(self.x) < self.y + self.h
        right_below = highest_line.get_y(self.x + self.w) < self.y + self.h
        if left_below or right_below:
            setup()

class PlatformGenerator:
    def __init__(self, terrain):
        self.terrain = terrain

        self.platform_min_dist = 100
        self.platform_max_dist = 300

class Platform:
    def __init__(self, x):
        self.x = x
        self.w = 50
        self.h = 10

        highest_line = terrain.highest_in_range(self.x, self.x + self.w)
        self.y = min(highest_line.y1, highest_line.y2) - self.h

        self.box = BoundingBox(self, 0, 0, self.w, self.h)

    def resolve_collision(self):
        if player.vy < player.max_landing_speed:
            player.box.y = self.box.y - player.box.h
            player.vy = 0
            player.vx = 0
            player.state = 'landed'
            player.platform_x = self.x
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

        self.line_generator = LineGenerator(self)
        self.platform_generator = PlatformGenerator(self)

        self.line_generator.generate_lines()

    def get_min_index(self, x):
        return math.floor((x - game_window.x) / self.line_generator.max_length) - 1
    
    def highest_in_range(self, x_start, x_stop):
        lines = []

        index = self.get_min_index(x_start)
        line = self.lines[index]

        while line.x1 < x_stop:
            if line.x2 > x_start:
                lines.append(line)
            index += 1
            line = self.lines[index]

        for line in self.lines:
            line.color = 'white'

        for line in lines:
            line.color = 'red'

        return min(lines, key = lambda line: min(line.y1, line.y2))
    
    def draw(self):
        self.line_generator.update()

        for line in self.lines:
            line.draw()

class LineGenerator:
    def __init__(self, terrain):
        self.terrain = terrain
        self.lines = terrain.lines

        self.min_length = 10
        self.max_length = 50
        self.min_angle = -1
        self.max_angle = 1
        self.max_delta_angle = 0.5

    def generate_lines(self):
        line = self.lines[-1]
        x = self.lines[-1].x2

        while x < game_window.x + display_size[0]:
            line = self.new_line()
            self.lines.append(line)
            x += line.dx

            highest = min(line.y1, line.y2)
            if highest < self.terrain.highest:
                self.terrain.highest = highest

    def new_line(self):
        last_line = self.lines[-1]

        delta_angle = random_float(-self.max_delta_angle, self.max_delta_angle, last_line.x2)
        new_angle = last_line.angle + delta_angle

        if new_angle < self.min_angle or new_angle > self.max_angle:
            new_angle = last_line.angle - delta_angle

        new_length = random_float(self.max_length, self.min_length, last_line.x2)

        return Line(last_line.x2, last_line.y2, new_length, new_angle)
    
    def add_lines(self):
        if self.lines[-1].x2 < game_window.x + display_size[0]:
            self.generate_lines()

    def remove_lines(self):
        if self.lines[0].x2 < game_window.x:
            self.lines.pop(0)

    def update(self):
        self.add_lines()
        self.remove_lines()

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

    def get_y(self, x):
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

class Mouse:
    def __init__(self):
        self.left = False
        self.right = False
        self.down = False

    def update(self):
        pressed = pygame.mouse.get_pressed()

        self.left = pressed[0]
        self.right = pressed[2]
        self.down = self.left or self.right

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
        self.x = 30
        self.y = 30
        self.img = pygame.image.load('./img/fuel.png')

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

    def update(self):
        def hex_points(length, center):
            points = [(center[0] - length, center[1])]

            for i in range(1, 6):
                angle = -120 * math.pi / 180 + i * 60 * math.pi / 180
                x = length * math.cos(angle) + points[i - 1][0]
                y = length * math.sin(angle) + points[i - 1][1]

                points.append((x, y))

            points.append(points.pop(0))

            return points

        center = (self.x + 18, self.y + 17)    
        big_hex = hex_points(38, center)
        small_hex = hex_points(30, center)
        
        pygame.draw.polygon(screen, 'white', big_hex, 1)
        pygame.draw.polygon(screen, 'white', small_hex, 1)

        for n in range(6):
            index1 = n
            index2 = (n + 1) % 6

            if math.floor(player.fuel) < 5 - n:
                continue
            elif math.floor(player.fuel) == 5 - n:
                if player.fuel % 1 <= 0:
                    continue

                width = 1 - (player.fuel % 1)

                def between_points(p1, p2):
                    x = p1[0] + (p2[0] - p1[0]) * width
                    y = p1[1] + (p2[1] - p1[1]) * width
                    return (x, y)

                big_hex_point = between_points(big_hex[index1], big_hex[index2])
                small_hex_point = between_points(small_hex[index1], small_hex[index2])
                
                points = [big_hex_point, big_hex[index2], small_hex[index2], small_hex_point]
            else:
                points = [big_hex[index1], big_hex[index2], small_hex[index2], small_hex[index1]]

            pygame.draw.polygon(screen, 'white', points)

def box_collision(box1, box2):
    check_x = box1.x + box1.w > box2.x and box1.x < box2.x + box2.w
    check_y = box1.y + box1.h > box2.y and box1.y < box2.y + box2.h
    if check_x and check_y:
        box2.parent.resolve_collision()

def random_float(max, min, seed_offset = 0):
    random.seed(seed + seed_offset)
    return random.random() * (max - min) + min

def setup():
    global game_window
    global terrain
    global boxes
    global game_objects
    global player

    game_window = GameWindow()
    terrain = Terrain()
    boxes = []
    platform = Platform(100)
    game_objects = [platform]
    player = Player(platform)

# Global Variables
gui = GUI()
mouse = Mouse()
gravity = 3
clock = pygame.time.Clock()
dt = 0
seed = time.time()

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

    mouse.update()
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