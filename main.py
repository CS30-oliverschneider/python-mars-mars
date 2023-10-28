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
        self.w = 40
        self.h = 40
        self.x = platform.x + platform.w / 2 - self.w / 2
        self.y = platform.y - self.h

        self.img = pygame.image.load('img/spritesheet.png')
        self.frame_width = 40
        self.frame_height = 40
        self.anim_speed = 3
        self.current_frame = 0
        self.delta_frame = 0

        self.platform = platform
        self.slide_speed = 2
        self.box = BoundingBox(self, 0, 0, self.w, self.h)

        self.state = 'landed'

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
        if self.delta_frame != 0 and frame_count % self.anim_speed == 0:
            self.current_frame += self.delta_frame

            if self.current_frame == 0:
                self.delta_frame = 0
            elif self.current_frame == 6:
                self.delta_frame = 0
                self.launch()

        screen.blit(self.img, (self.x - game_window.x, self.y - game_window.y, self.w, self.h), (self.frame_width * self.current_frame, 0, self.frame_width, self.frame_height))

    def update(self):
        self.update_velocity()
        self.move()
        self.check_object_collision()
        self.check_terrain_collision()
        self.to_platform_center()

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
                self.delta_frame = 1
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

    def launch(self):
        self.vx = self.launch_speed_x
        self.vy = self.launch_speed_y
        self.state = 'launched'

    def check_object_collision(self):
        for game_object in game_objects:
            box_collision(self.box, game_object.box)

    def check_terrain_collision(self):
        if (self.state != 'launched' and self.state != 'flying') or terrain.highest > self.y + self.h:
            return
        
        highest_y = terrain.highest_in_range(self.x, self.x + self.w)

        if self.y + self.h > highest_y:
            setup()

    def to_platform_center(self):
        def center(obj):
            return obj.x + obj.w / 2
        
        dist = center(self.platform) - center(self)

        if (self.state == 'landed' or self.state == 'ready') and dist != 0:
            direction = dist / abs(dist)
            self.x += self.slide_speed * direction

            if direction * center(self) > direction * center(self.platform):
                self.x = center(self.platform) - self.w / 2

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

        self.y = terrain.highest_in_range(self.x, self.x + self.w) - self.h

        self.box = BoundingBox(self, 0, 0, self.w, self.h)

    def draw(self):
        pygame.draw.rect(screen, 'green', (self.x - game_window.x, self.y - game_window.y, self.w, self.h))

    def resolve_collision(self):
        if player.vy < player.max_landing_speed:
            player.box.y = self.box.y - player.box.h
            player.vy = 0
            player.vx = 0
            player.state = 'landed'
            player.platform = self
            player.delta_frame = -1
            player.fuel = 6
        else:
            setup()

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
        self.lines = []
        self.highest = float('inf')

        self.line_generator = LineGenerator(self)
        self.platform_generator = PlatformGenerator(self)

        self.line_generator.generate_lines(1)

    def draw(self):
        self.line_generator.update()

        for line in self.lines:
            line.draw()

    def get_min_index(self, x):
        return math.floor((x - game_window.x) / self.line_generator.max_length) - 1
    
    def highest_in_range(self, x_start, x_stop):
        y_values = []

        index = self.get_min_index(x_start)
        line = self.lines[index]

        while line.x1 <= x_stop:
            if line.x2 >= x_start:
                if len(y_values) == 0:
                    y_values.extend((line.get_y(x_start), line.y2))
                elif line.x2 > x_stop:
                    y_values.extend((line.y1, line.get_y(x_stop)))
                else:
                    y_values.extend((line.y1, line.y2))

            index += 1
            line = self.lines[index]

        return min(y_values)

class Spring:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.stop_length = 200
        self.acceleration_up = 10
        self.damping = 3

        self.bob_mass = 50
        self.bob_x = x
        self.bob_y = self.y - self.stop_length
        self.bob_vx = 0
        self.bob_vy = 0

        self.rest_length = self.stop_length - self.acceleration_up * self.bob_mass

    def draw(self):
        pygame.draw.line(screen, 'blue', (self.x, self.y), (self.bob_x, self.bob_y), 5)
        pygame.draw.circle(screen, 'blue', (self.bob_x, self.bob_y), 20)

    def update(self):
        self.update_velocity()
        self.move()

    def update_velocity(self):
        length = math.sqrt((self.bob_x - self.x)**2 + (self.bob_y - self.y)**2)
        stretch = length - self.rest_length
        sine = (self.bob_x - self.x) / length
        cosine = (self.bob_y - self.y) / length

        ax = -1 / self.bob_mass * stretch * sine - self.damping / self.bob_mass * self.bob_vx
        ay = -1 / self.bob_mass * stretch * cosine - self.damping / self.bob_mass * self.bob_vy - self.acceleration_up

        self.bob_vx += ax
        self.bob_vy += ay

    def move(self):
        self.bob_x += self.bob_vx
        self.bob_y += self.bob_vy

        if abs(self.bob_vx) < 0.01 and abs(self.bob_vy) < 0.01:
            self.bob_x = self.x
            self.bob_y = self.y - self.stop_length

        if mouse.left:
            mouse_coords = pygame.mouse.get_pos()
            self.bob_x = mouse_coords[0]
            self.bob_y = mouse_coords[1]

            self.bob_vx = 0
            self.bob_vy = 0

spring = Spring(300, 500)

class LineGenerator:
    def __init__(self, terrain):
        self.terrain = terrain
        self.lines = terrain.lines

        self.min_length = 10
        self.max_length = 50
        self.min_angle = -1
        self.max_angle = 1
        self.max_delta_angle = 0.5

        self.lines.append(Line(0, 700, 0, 700, 0))

    def update(self):
        self.add_lines()
        self.remove_lines()

    def generate_lines(self, direction):
        index = -1
        line = self.lines[index]
        x = line.x2

        if direction == -1:
            index = 0
            x = line.x1

        while x >= game_window.x and x < game_window.x + display_size[0]:
            line = self.new_line(self.lines[index], direction)

            if direction == 1:
                self.lines.append(line)
                x = line.x2
            elif direction == -1:
                self.lines.insert(0, line)
                x = line.x1

            highest = min(line.y1, line.y2)
            if highest < self.terrain.highest:
                self.terrain.highest = highest

    def new_line(self, last_line, direction):
        seed_offset = last_line.seed_offset + direction

        delta_angle = random_float(-self.max_delta_angle, self.max_delta_angle, seed_offset)
        new_angle = last_line.angle + delta_angle

        if new_angle < self.min_angle or new_angle > self.max_angle:
            new_angle = last_line.angle - delta_angle

        new_length = random_float(self.max_length, self.min_length, seed_offset)

        if direction == 1:
            x1 = last_line.x2
            y1 = last_line.y2

            x2 = x1 + new_length * math.cos(new_angle)
            y2 = y1 + new_length * math.sin(new_angle)
        elif direction == -1:
            x2 = last_line.x1
            y2 = last_line.y1

            x1 = x2 - new_length * math.cos(new_angle)
            y1 = y2 - new_length * math.sin(new_angle)

        return Line(x1, y1, x2, y2, seed_offset)
    
    def add_lines(self):
        if self.lines[-1].x2 < game_window.x + display_size[0]:
            self.generate_lines(1)
        elif self.lines[0].x1 > game_window.x:
            self.generate_lines(-1)

    def remove_lines(self):
        if self.lines[0].x2 < game_window.x:
            self.lines.pop(0)
        elif self.lines[-1].x1 > game_window.x + display_size[0]:
            self.lines.pop(-1)

class Line:
    def __init__(self, x1, y1, x2, y2, seed_offset):
        self.x1 = x1
        self.y1 = y1
        self.x2 = x2
        self.y2 = y2

        self.seed_offset = seed_offset

        self.angle = math.atan2(y2 - y1, x2 - x1)
        self.dx = self.x2 - self.x1

        self.color = 'white'

    def draw(self):
        p1 = (self.x1 - game_window.x, self.y1 - game_window.y)
        p2 = (self.x2 - game_window.x, self.y2 - game_window.y)
        pygame.draw.line(screen, self.color, p1, p2)

    def get_y(self, x):
        if x < self.x1 or x > self.x2:
            return float('inf')
        else:
            return ((self.y2 - self.y1) / (self.x2 - self.x1)) * (x - self.x1) + self.y1

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
    game_objects = [platform, Platform(800)]
    player = Player(platform)

    game_window.y = player.y + player.h / 2 - display_size[1] / 2

# Global Variables
gui = GUI()
mouse = Mouse()
gravity = 3
clock = pygame.time.Clock()
dt = 0
seed = time.time()
frame_count = 0

setup()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            setup()

    frame_count += 1
    screen.fill('black')
    dt = clock.tick(60) / 1000

    mouse.update()
    gui.update()
    player.update()
    game_window.update()
    # spring.update()

    gui.draw()
    terrain.draw()
    for game_object in game_objects:
        game_object.draw()
    player.draw()

    # for box in boxes:
    #     box.draw()
    spring.draw()

    pygame.display.flip()