import random
import math
import pygame
import time

pygame.init()
display_size = (900, 900)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption('Mars Mars')

class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.w = 40
        self.h = 40

        self.img = pygame.image.load('img/spritesheet.png')
        self.img_x = 0
        self.img_y = 0
        self.img_w = self.w
        self.img_h = self.h

        self.frame_width = 40
        self.frame_height = 40
        self.anim_speed = 3
        self.current_frame = 0
        self.delta_frame = 0

        self.platform = None
        self.slide_speed = 2

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

        x = self.x - self.img_x - game_window.left
        y = self.y - self.img_y - game_window.top
        area = (self.frame_width * self.current_frame, 0, self.frame_width, self.frame_height)
        screen.blit(self.img, (x, y, self.w, self.h), area)

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
        for platform in world.platforms:
            check_collision(self, platform)

    def check_terrain_collision(self):
        if (self.state != 'launched' and self.state != 'flying') or world.highest > self.y + self.h:
            return
        
        highest_y = world.highest_in_range(self.x, self.x + self.w)

        if self.y + self.h > highest_y:
            player.die()

    def to_platform_center(self):
        dist = center_x(self.platform) - center_x(self)

        if (self.state == 'landed' or self.state == 'ready') and dist != 0:
            direction = dist / abs(dist)
            self.x += self.slide_speed * direction

            if direction * center_x(self) > direction * center_x(self.platform):
                self.x = center_x(self.platform) - self.w / 2

    def reset(self):
        self.y = self.platform.y - self.h
        self.vy = 0
        self.vx = 0
        self.state = 'landed'
        self.fuel = 6
    
    def die(self):
        self.reset()
        world.platforms = [self.platform]
        world.terrain_lines = [self.platform.terrain_line]
        self.x = center_x(self.platform) - self.w / 2
        self.delta_frame = 0
        self.current_frame = 0

class World:
    def __init__(self):
        self.terrain_lines = []
        self.platforms = []
        self.highest = float('inf')

        self.terrain_line_generator = TerrainGenerator(self, 100)
        self.platform_generator = PlatformGenerator(self)

        self.terrain_line_generator.generate_terrain_lines(1)

    def draw(self):
        self.terrain_line_generator.update()
        self.platform_generator.update()

        for terrain_line in self.terrain_lines:
            terrain_line.draw()
        for platform in self.platforms:
            platform.draw()
    
    def highest_in_range(self, x_start, x_stop):
        terrain_lines = self.terrain_lines_in_range(x_start, x_stop)
        highest = float('inf')

        for i in range(len(terrain_lines)):
            terrain_line = terrain_lines[i]

            if i == 0:
                highest = min(highest, terrain_line.get_y(x_start), terrain_line.y2)
            elif i == len(terrain_lines) - 1:
                highest = min(highest, terrain_line.y1, terrain_line.get_y(x_stop))
            else:
                highest = min(highest, terrain_line.y1, terrain_line.y2)

        return highest
    
    def terrain_lines_in_range(self, x_start, x_stop):
        terrain_lines = []

        index = 0
        terrain_line = self.terrain_lines[index]

        while terrain_line.x1 <= x_stop:
            if terrain_line.x2 >= x_start:
                terrain_lines.append(terrain_line)

            index += 1
            terrain_line = self.terrain_lines[index]

        return terrain_lines

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

class PlatformGenerator:
    def __init__(self, world):
        self.world = world
        self.platforms = world.platforms

        self.min_dist = 100
        self.max_dist = 300
        self.dist_right = random_float(self.max_dist, self.min_dist, 1)
        self.dist_left = random_float(self.max_dist, self.min_dist)

    def update(self):
        self.platforms = self.world.platforms
        self.add_platforms()
        self.remove_platforms()
    
    def add_platforms(self):
        if self.platforms[-1].x + self.dist_right < game_window.right:
            self.dist_right = random_float(self.max_dist, self.min_dist, self.platforms[-1].seed_offset + 1)
            new_seed_offset = self.platforms[-1].seed_offset + 1
            new_x = self.platforms[-1].x + self.dist_right
            self.platforms.append(Platform(new_x, new_seed_offset))
            self.dist_right = random_float(self.max_dist, self.min_dist, new_seed_offset + 1)
        
        if self.platforms[0].x - self.dist_left > game_window.left:
            self.dist_left = random_float(self.max_dist, self.min_dist, self.platforms[0].seed_offset)
            new_seed_offset = self.platforms[0].seed_offset - 1
            dist = random_float(self.max_dist, self.min_dist, new_seed_offset + 1)
            new_x = self.platforms[0].x - dist
            self.platforms.insert(0, Platform(new_x, new_seed_offset))
            self.dist_left = random_float(self.max_dist, self.min_dist, new_seed_offset)

    def remove_platforms(self):
        if self.platforms[-1].x > game_window.right:
            self.platforms.pop()

        if self.platforms[0].x + self.platforms[0].w < game_window.left:
            self.platforms.pop(0)

class Platform:
    def __init__(self, x, seed_offset = 0):
        self.w = 50
        self.h = 10
        self.x = x
        self.y = world.highest_in_range(self.x, self.x + self.w) - self.h

        self.seed_offset = seed_offset

        self.terrain_line = world.terrain_lines_in_range(self.x, self.x + self.w)[0]

    def draw(self):
        pygame.draw.rect(screen, 'green', (self.x - game_window.left, self.y - game_window.top, self.w, self.h))

    def resolve_collision(self):
        if player.vy > player.max_landing_speed:
            return player.die()

        player.platform = self
        player.delta_frame = -1
        player.reset()

class TerrainGenerator:
    def __init__(self, world, window_offset):
        self.world = world
        self.terrain_lines = world.terrain_lines

        self.window_offset = window_offset

        self.min_length = 10
        self.max_length = 50
        self.min_angle = -1
        self.max_angle = 1
        self.max_delta_angle = 0.5

        start = TerrainLine(game_window.left - window_offset, 700, game_window.left - window_offset, 700, -1)
        self.terrain_lines.append(self.new_terrain_line(start, 1))

    def update(self):
        self.terrain_lines = self.world.terrain_lines
        self.add_terrain_lines()
        self.remove_terrain_lines()

    def generate_terrain_lines(self, direction):
        if direction == 1:
            index = -1
            terrain_line = self.terrain_lines[index]
            x = terrain_line.x2
        elif direction == -1:
            index = 0
            terrain_line = self.terrain_lines[index]
            x = terrain_line.x1

        while x >= game_window.left - self.window_offset and x <= game_window.right + self.window_offset:
            terrain_line = self.new_terrain_line(self.terrain_lines[index], direction)

            if direction == 1:
                self.terrain_lines.append(terrain_line)
                x = terrain_line.x2
            elif direction == -1:
                self.terrain_lines.insert(0, terrain_line)
                x = terrain_line.x1

            highest = min(terrain_line.y1, terrain_line.y2)
            if highest < self.world.highest:
                self.world.highest = highest

    def new_terrain_line(self, last_terrain_line, direction):
        seed_offset = last_terrain_line.seed_offset + direction

        delta_angle = random_float(-self.max_delta_angle, self.max_delta_angle, seed_offset)
        new_angle = last_terrain_line.angle + delta_angle

        if new_angle < self.min_angle or new_angle > self.max_angle:
            new_angle = last_terrain_line.angle - delta_angle

        new_length = random_float(self.max_length, self.min_length, seed_offset)

        if direction == 1:
            x1 = last_terrain_line.x2
            y1 = last_terrain_line.y2

            x2 = x1 + new_length * math.cos(new_angle)
            y2 = y1 + new_length * math.sin(new_angle)
        elif direction == -1:
            x2 = last_terrain_line.x1
            y2 = last_terrain_line.y1

            x1 = x2 - new_length * math.cos(new_angle)
            y1 = y2 - new_length * math.sin(new_angle)

        return TerrainLine(x1, y1, x2, y2, seed_offset)
    
    def add_terrain_lines(self):
        if self.terrain_lines[-1].x2 < game_window.right + self.window_offset:
            self.generate_terrain_lines(1)
        if self.terrain_lines[0].x1 > game_window.left - self.window_offset:
            self.generate_terrain_lines(-1)

    def remove_terrain_lines(self):
        if self.terrain_lines[0].x2 < game_window.left - self.window_offset:
            self.terrain_lines.pop(0)
        if self.terrain_lines[-1].x1 > game_window.right + self.window_offset:
            self.terrain_lines.pop(-1)

class TerrainLine:
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
        p1 = (self.x1 - game_window.left, self.y1 - game_window.top)
        p2 = (self.x2 - game_window.left, self.y2 - game_window.top)
        pygame.draw.line(screen, self.color, p1, p2)

    def get_y(self, x):
        if x < self.x1 or x > self.x2:
            return float('inf')
        else:
            return ((self.y2 - self.y1) / (self.x2 - self.x1)) * (x - self.x1) + self.y1

class GameWindow:
    def __init__(self):
        self.spacing = 200

        self.left = -self.spacing
        self.right = self.left + display_size[0]
        self.top = 0
        self.bottom = self.top + display_size[1]

    def update(self):
        self.left = player.x - self.spacing
        self.right = self.left + display_size[0]
        self.top = center_y(player) - display_size[1] / 2
        self.bottom = self.left + display_size[1]

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

def check_collision(obj1, obj2):
    check_x = obj1.x + obj1.w > obj2.x and obj1.x < obj2.x + obj2.w
    check_y = obj1.y + obj1.h > obj2.y and obj1.y < obj2.y + obj2.h
    if check_x and check_y:
        obj2.resolve_collision()

def random_float(max, min, seed_offset = 0):
    random.seed(seed + seed_offset)
    return random.random() * (max - min) + min

def center_x(obj):
    return obj.x + obj.w / 2

def center_y(obj):
    return obj.y + obj.h / 2

# Global Variables
gui = GUI()
mouse = Mouse()
gravity = 3
clock = pygame.time.Clock()
dt = 0
seed = time.time()
frame_count = 0
game_window = GameWindow()
world = World()
player = Player()
platform = Platform(0)
world.platforms.append(platform)

# Initial Setup
platform.x = player.w / 2 - platform.w / 2
platform.y = world.highest_in_range(platform.x, platform.x + platform.w) - platform.h
player.platform = platform
player.y = platform.y - player.h

# Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player.die()

    frame_count += 1
    screen.fill('black')
    dt = clock.tick(60) / 1000

    mouse.update()
    gui.update()
    player.update()
    game_window.update()

    gui.draw()
    world.draw()
    player.draw()

    pygame.display.flip()