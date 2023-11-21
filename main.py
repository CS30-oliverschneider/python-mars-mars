import random
import math
import pygame
import noise

pygame.init()
display_size = (900, 900)
screen = pygame.display.set_mode(display_size)
pygame.display.set_caption("Mars Mars")


class Player:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.w = 40
        self.h = 40

        self.img = pygame.image.load("img/spritesheet.png")
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

        self.state = "landed"

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

            if self.current_frame <= 0:
                self.delta_frame = 0
                self.current_frame = 0
            elif self.current_frame == 6:
                self.delta_frame = 0
                self.launch()

        x = self.x - self.img_x - game_window.left
        y = self.y - self.img_y - game_window.top
        area = (
            self.frame_width * self.current_frame,
            0,
            self.frame_width,
            self.frame_height,
        )
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
        if self.state == "landed":
            if not mouse.down:
                self.state = "ready"
            return
        elif self.state == "ready":
            if mouse.down:
                self.delta_frame = 1
            return

        self.vy += gravity

        if self.state == "launched":
            if not mouse.down:
                self.state = "flying"
            return

        if self.fuel <= 0:
            return

        if mouse.left:
            self.vy -= self.y_thrust
            self.vx += self.x_thrust
            particle_generator.thrust(1)
        if mouse.right:
            self.vy -= self.y_thrust
            self.vx -= self.x_thrust
            particle_generator.thrust(-1)

        if mouse.down:
            self.fuel -= self.delta_fuel

    def launch(self):
        self.vx = self.launch_speed_x
        self.vy = self.launch_speed_y
        self.state = "launched"

        particle_generator.launch()

    def check_object_collision(self):
        for platform in world.platforms:
            check_collision(self, platform)

    def check_terrain_collision(self):
        if (self.state != "launched" and self.state != "flying") or world.highest > self.y + self.h:
            return

        highest_y = world.highest_in_range(self.x, self.x + self.w)

        if self.y + self.h > highest_y:
            player.die()

    def to_platform_center(self):
        dist = center_x(self.platform) - center_x(self)

        if (self.state == "landed" or self.state == "ready") and dist != 0:
            direction = dist / abs(dist)
            self.x += self.slide_speed * direction

            if direction * center_x(self) > direction * center_x(self.platform):
                self.x = center_x(self.platform) - self.w / 2

    def reset(self):
        self.y = self.platform.y - self.h
        self.vy = 0
        self.vx = 0
        self.state = "landed"
        self.fuel = 6

    def die(self):
        particle_generator.explosion()
        self.reset()

        world.platforms.clear()
        world.platforms.append(self.platform)
        world.terrain_points.clear()
        world.terrain_points.append(self.platform.terrain_point)

        self.x = center_x(self.platform) - self.w / 2
        self.delta_frame = 0
        self.current_frame = 0


class World:
    def __init__(self):
        self.terrain_points = []
        self.platforms = []
        self.highest = float("inf")

        self.terrain_generator = TerrainGenerator(self)
        self.platform_generator = PlatformGenerator(self)

        self.terrain_generator.generate_terrain_points(1)

    def draw(self):
        self.terrain_generator.update()
        self.platform_generator.update()

        draw_points = [
            (point.x - game_window.left, point.y - game_window.top) for point in self.terrain_points
        ]
        pygame.draw.lines(screen, "white", False, draw_points)

        for platform in self.platforms:
            platform.draw()

    def highest_in_range(self, x_start, x_stop):
        y_values = []

        for i in range(len(self.terrain_points)):
            point = self.terrain_points[i]

            if point.x > x_stop and self.terrain_points[i - 1].x < x_start:
                y_values.append(self.get_y(x_start, i, i - 1))
                y_values.append(self.get_y(x_stop, i, i - 1))
                break
            elif point.x < x_start:
                continue
            elif point.x > x_stop:
                break

            if i < 0:
                print("too small")
            if i + 1 > len(self.terrain_points) - 1:
                print("too big")

            if len(y_values) == 0:
                y_values.append(self.get_y(x_start, i, i - 1))
            if self.terrain_points[i + 1].x > x_stop:
                y_values.append(self.get_y(x_stop, i, i + 1))

            y_values.append(point.y)

        if len(y_values) == 0:
            print(x_start, x_stop)
            for point in world.terrain_points:
                print(point.x)

        return min(y_values)

    def get_y(self, x, index1, index2):
        p1 = self.terrain_points[index1]
        p2 = self.terrain_points[index2]
        return (p2.y - p1.y) / (p2.x - p1.x) * (x - p2.x) + p2.y


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
        pygame.draw.line(screen, "blue", (self.x, self.y), (self.bob_x, self.bob_y), 5)
        pygame.draw.circle(screen, "blue", (self.bob_x, self.bob_y), 20)

    def update(self):
        self.update_velocity()
        self.move()

    def update_velocity(self):
        length = math.sqrt((self.bob_x - self.x) ** 2 + (self.bob_y - self.y) ** 2)
        stretch = length - self.rest_length
        sine = (self.bob_x - self.x) / length
        cosine = (self.bob_y - self.y) / length

        ax = -1 / self.bob_mass * stretch * sine - self.damping / self.bob_mass * self.bob_vx
        ay = (
            -1 / self.bob_mass * stretch * cosine
            - self.damping / self.bob_mass * self.bob_vy
            - self.acceleration_up
        )

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

        self.min_dist = 500
        self.max_dist = 800
        self.dist_right = random_float(self.max_dist, self.min_dist, 1)
        self.dist_left = random_float(self.max_dist, self.min_dist)

    def update(self):
        self.add_platforms()
        self.remove_platforms()

    def add_platforms(self):
        self.dist_right = random_float(self.max_dist, self.min_dist, self.platforms[-1].seed_offset + 1)
        self.dist_left = random_float(self.max_dist, self.min_dist, self.platforms[0].seed_offset)

        if self.platforms[-1].x + self.dist_right < game_window.right:
            new_seed_offset = self.platforms[-1].seed_offset + 1
            new_x = self.platforms[-1].x + self.dist_right
            self.platforms.append(Platform(new_x, new_seed_offset))
            self.dist_right = random_float(self.max_dist, self.min_dist, new_seed_offset + 1)

        if self.platforms[0].x + self.platforms[0].w - self.dist_left > game_window.left:
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
    def __init__(self, x, seed_offset=0):
        self.w = 50
        self.h = 10
        self.x = x
        self.y = world.highest_in_range(self.x, self.x + self.w) - self.h

        self.seed_offset = seed_offset

        for point in world.terrain_points:
            if point.x > self.x:
                self.terrain_point = point
                break

    def draw(self):
        pygame.draw.rect(
            screen,
            "green",
            (self.x - game_window.left, self.y - game_window.top, self.w, self.h),
        )

    def resolve_collision(self):
        if player.vy > player.max_landing_speed:
            return player.die()

        player.platform = self
        player.delta_frame = -1
        player.reset()


class TerrainGenerator:
    def __init__(self, world):
        self.world = world
        self.terrain_points = world.terrain_points

        self.window_offset = 50

        self.min_dist_x = 10
        self.max_dist_x = 50
        self.octaves = 4
        self.persistence = 0.6
        self.lacunarity = 2
        self.x_scale = 0.001
        self.y_scale = 500

        start = TerrainPoint(game_window.left - self.window_offset, 0, -1)
        self.terrain_points.append(self.new_terrain_point(start, 1))

    def update(self):
        self.add_terrain_points()
        self.remove_terrain_points()

    def generate_terrain_points(self, direction):
        if direction == 1:
            index = -1
        elif direction == -1:
            index = 0

        terrain_point = self.terrain_points[index]
        x = terrain_point.x

        while x >= game_window.left - self.window_offset and x <= game_window.right + self.window_offset:
            terrain_point = self.new_terrain_point(self.terrain_points[index], direction)
            x = terrain_point.x

            if direction == 1:
                self.terrain_points.append(terrain_point)
            elif direction == -1:
                self.terrain_points.insert(0, terrain_point)

            if terrain_point.y < self.world.highest:
                self.world.highest = terrain_point.y

    def new_terrain_point(self, last_terrain_point, direction):
        seed_offset = last_terrain_point.seed_offset + direction

        if direction == 1:
            dist_x = random_float(self.max_dist_x, self.min_dist_x, seed_offset)
            x = last_terrain_point.x + dist_x
        elif direction == -1:
            dist_x = random_float(self.max_dist_x, self.min_dist_x, seed_offset + 1)
            x = last_terrain_point.x - dist_x

        y = self.perlin_noise(x)

        return TerrainPoint(x, y, seed_offset)

    def perlin_noise(self, x):
        result = noise.pnoise1(x * self.x_scale + seed, self.octaves, self.persistence, self.lacunarity)
        return result * self.y_scale

    def add_terrain_points(self):
        if self.terrain_points[-1].x < game_window.right + self.window_offset:
            self.generate_terrain_points(1)
        if self.terrain_points[0].x > game_window.left - self.window_offset:
            self.generate_terrain_points(-1)

    def remove_terrain_points(self):
        if self.terrain_points[1].x < game_window.left - self.window_offset:
            self.terrain_points.pop(0)
        if self.terrain_points[-2].x > game_window.right + self.window_offset:
            self.terrain_points.pop(-1)


class TerrainPoint:
    def __init__(self, x, y, seed_offset):
        self.x = x
        self.y = y

        self.seed_offset = seed_offset

        self.color = "white"


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


class HUD:
    def __init__(self):
        self.fuel = FuelMeter()

        self.elements = [self.fuel]

    def draw(self):
        for element in self.elements:
            element.draw()

    def update(self):
        for element in self.elements:
            element.update()

class ParticleGenerator:
    def launch(self):
        options = {
            "num_range": (6, 10),
            "x": player.x + player.w / 2,
            "y": player.y + player.h * 0.75,
            "angle_range": (0.3, -0.3),
            "speed_range": (50, 30),
            "rotation_range": (1, 10),
            "growth_range": (0.4, 0.7),
            "grow_frames": 50,
            "shrink_frames": 10
        }
        self.create_particles(options)

        options["angle_range"] = (math.pi - 0.3, math.pi + 0.3)
        self.create_particles(options)
    
    def thrust(self, direction):
        delta_angle = math.pi / 4 * direction
        options = {
            "num_range": (1, 1),
            "x": player.x + player.w / 2,
            "y": player.y + player.h * 0.5,
            "angle_range": (0.5 * math.pi + delta_angle - 0.3, 0.5 * math.pi + delta_angle + 0.3),
            "speed_range": (50, 20),
            "rotation_range": (1, 10),
            "growth_range": (0.5, 1),
            "grow_frames": 20,
            "shrink_frames": 10
        }
        self.create_particles(options, True)

    def explosion(self):
        options = {
            "num_range": (6, 10),
            "x": player.x + player.w / 2,
            "y": player.y + player.h / 2,
            "angle_range": (-math.pi / 2 - 0.5, -math.pi / 2 + 0.5),
            "speed_range": (50, 30),
            "rotation_range": (1, 10),
            "growth_range": (3, 5),
            "grow_frames": 10,
            "shrink_frames": 100
        }
        self.create_particles(options)

    def create_particles(self, options, relative_speed = False):
        num_range = options["num_range"]
        x = options["x"]
        y = options["y"]
        angle_range = options["angle_range"]
        speed_range = options["speed_range"]
        rotation_range = options["rotation_range"]
        growth_range = options["growth_range"]
        grow_frames = options["grow_frames"]
        shrink_frames = options["shrink_frames"]

        random.seed(None)

        def get_random(range_param):
            return random.uniform(range_param[0], range_param[1])

        num = random.randint(num_range[0], num_range[1])
        for _ in range(num):
            angle = get_random(angle_range)
            speed = get_random(speed_range)
            vx = speed * math.cos(angle)
            vy = speed * math.sin(angle)
            rotation = get_random(rotation_range) * [-1, 1][random.randint(0, 1)]
            growth = get_random(growth_range)

            if relative_speed:
                vx += player.vx
                vy += player.vy

            particles.append(Particle(x, y, vx, vy, rotation, growth, grow_frames, shrink_frames))

class Particle:
    def __init__(self, x, y, vx, vy, rotate, growth, grow_frames, shrink_frames):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.rotate = rotate
        self.growth = growth
        self.grow_frames = grow_frames
        self.shrink_frames = shrink_frames

        self.rotation = 0
        self.radius = 0
        self.frame_count = 0
        self.max_radius = 0

    def draw(self):
        if self.radius < 0:
            return
        
        points = hexagon_points(self.x - game_window.left, self.y - game_window.top, self.radius, self.rotation)
        pygame.draw.polygon(screen, 'white', points)

    def update(self):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotate * dt

        if self.frame_count < self.grow_frames:
            self.radius += self.growth
            self.max_radius = self.radius
        else:
            self.radius -= self.max_radius / self.shrink_frames

        if self.radius < 0:
            particles.remove(self)

        self.frame_count += 1

class FuelMeter:
    def __init__(self):
        self.x = 30
        self.y = 30
        self.img = pygame.image.load("./img/fuel.png")

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

    def update(self):
        center = (self.x + 18, self.y + 17)
        big_hex = hexagon_points(center[0], center[1], 38)
        small_hex = hexagon_points(center[0], center[1], 30)

        pygame.draw.polygon(screen, "white", big_hex, 1)
        pygame.draw.polygon(screen, "white", small_hex, 1)

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

                points = [
                    big_hex_point,
                    big_hex[index2],
                    small_hex[index2],
                    small_hex_point,
                ]
            else:
                points = [
                    big_hex[index1],
                    big_hex[index2],
                    small_hex[index2],
                    small_hex[index1],
                ]

            pygame.draw.polygon(screen, "white", points)


def check_collision(obj1, obj2):
    check_x = obj1.x + obj1.w > obj2.x and obj1.x < obj2.x + obj2.w
    check_y = obj1.y + obj1.h > obj2.y and obj1.y < obj2.y + obj2.h
    if check_x and check_y:
        obj2.resolve_collision()


def random_float(max, min, seed_offset=0):
    random.seed(seed + seed_offset)
    return random.random() * (max - min) + min


def center_x(obj):
    return obj.x + obj.w / 2


def center_y(obj):
    return obj.y + obj.h / 2


def hexagon_points(center_x, center_y, radius, rotation = 0):
    points = []

    for n in range(6):
        angle = (n * 60 - 120) * math.pi / 180 + rotation
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append((x, y))

    return points

def setup():
    platform = Platform(0)
    world.platforms.append(platform)
    platform.x = player.w / 2 - platform.w / 2
    platform.y = world.highest_in_range(platform.x, platform.x + platform.w) - platform.h
    player.platform = platform
    player.y = platform.y - player.h

# Global Variables
hud = HUD()
mouse = Mouse()
gravity = 3
clock = pygame.time.Clock()
dt = 0
seed = random.random() * 100000
frame_count = 0
game_window = GameWindow()
world = World()
player = Player()
particle_generator = ParticleGenerator()
particles = []
setup()

# Main Loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
            player.die()

    frame_count += 1
    screen.fill("black")
    dt = clock.tick(60) / 1000

    mouse.update()
    hud.update()
    player.update()
    game_window.update()

    hud.draw()
    world.draw()
    for particle in particles:
        particle.update()
        particle.draw()
    player.draw()

    pygame.display.flip()
