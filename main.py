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

        self.x_thrust = 150
        self.y_thrust = 250

        self.max_landing_speed = 150
        self.launch_speed_x = 150
        self.launch_speed_y = -300

        self.fuel = 6
        self.delta_fuel = 1

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

        self.vy += gravity * dt

        if self.state == "launched":
            if not mouse.down:
                self.state = "flying"
            return

        if self.fuel <= 0:
            return

        if mouse.left:
            self.vy -= self.y_thrust * dt
            self.vx += self.x_thrust * dt
            particle_generator.thrust(1)
        if mouse.right:
            self.vy -= self.y_thrust * dt
            self.vx -= self.x_thrust * dt
            particle_generator.thrust(-1)

        if mouse.down:
            self.fuel -= self.delta_fuel * dt

    def launch(self):
        self.vx = self.launch_speed_x
        self.vy = self.launch_speed_y
        self.state = "launched"

        particle_generator.launch()

    def check_object_collision(self):
        player_rect = (self.x, self.y, self.w, self.h)

        for platform in world.objects["platform"]:
            platform_rect = (platform.x, platform.y, platform.w, platform.h)
            if check_rr_collision(player_rect, platform_rect):
                platform.resolve_collision()

        for spring in world.objects["spring"]:
            spring_circle = (spring.bob_x, spring.bob_y, spring.bob_r)
            if check_cr_collision(player_rect, spring_circle):
                spring.resolve_collision()

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
                world.set_respawn_objects()

    def reset(self):
        self.y = self.platform.y - self.h
        self.vy = 0
        self.vx = 0
        self.state = "landed"
        self.fuel = 6

    def die(self):
        particle_generator.explosion()
        self.reset()
        self.x = center_x(self.platform) - self.w / 2
        self.delta_frame = 0
        self.current_frame = 0
        game_window.update()
        world.clear()


class World:
    def __init__(self):
        self.layers = []
        self.highest = float("inf")
        self.create_layers()
        self.terrain_generator = TerrainGenerator(self)

        self.objects = {"platform": [], "spring": []}

    def draw(self):
        for layer in reversed(self.layers):
            draw_points = [layer.draw_point(i) for i in range(len(layer.points))]

            draw_points.append((display_size[0], display_size[1]))
            draw_points.append((0, display_size[1]))

            pygame.draw.polygon(screen, layer.color, draw_points)

        for object_list in self.objects.values():
            for game_object in object_list:
                game_object.draw()

    def update(self):
        self.terrain_generator.update()
        for generator in self.object_generators.values():
            generator.update()
        for spring in self.objects["spring"]:
            spring.update()

    def create_generators(self):
        self.platform_generator = ObjectGenerator(Platform, self.objects["platform"], 500, 800)
        self.spring_generator = ObjectGenerator(Spring, self.objects["spring"], 200, 400)
        self.object_generators = {"platform": self.platform_generator, "spring": self.spring_generator}

    def create_layers(self):
        noise_params1 = NoiseParams(4, 0.6, 2, 0.001, 500, 0, 0)
        noise_params2 = NoiseParams(4, 0.6, 2, 0.001, 500, 10000, 0)
        noise_params3 = NoiseParams(4, 0.6, 2, 0.001, 500, 20000, 0)

        layer1 = TerrainLayer(0, 1, "#77160a", noise_params1)
        layer2 = TerrainLayer(1, 0.5, "#548a68", noise_params2)
        layer3 = TerrainLayer(2, 0.25, "#87c289", noise_params3)

        self.main_layer = layer1
        self.layers = [layer1, layer2, layer3]

    def highest_in_range(self, x_start, x_stop):
        y_values = []

        for i in range(len(self.main_layer.points)):
            point = self.main_layer.points[i]

            if point.x > x_stop and self.main_layer.points[i - 1].x < x_start:
                y_values.append(self.get_y(x_start, i, i - 1))
                y_values.append(self.get_y(x_stop, i, i - 1))
                break
            elif point.x < x_start:
                continue
            elif point.x > x_stop:
                break

            if len(y_values) == 0:
                y_values.append(self.get_y(x_start, i, i - 1))
            if self.main_layer.points[i + 1].x > x_stop:
                y_values.append(self.get_y(x_stop, i, i + 1))

            y_values.append(point.y)

        return min(y_values)

    def get_y(self, x, index1, index2):
        p1 = self.main_layer.points[index1]
        p2 = self.main_layer.points[index2]
        return (p2.y - p1.y) / (p2.x - p1.x) * (x - p2.x) + p2.y

    def clear(self):
        for layer in self.layers:
            layer.points.clear()
            layer.points.append(layer.respawn)
            self.terrain_generator.generate_terrain(1, layer)

        for key in self.objects:
            generator = self.object_generators[key]
            respawn = generator.respawn

            self.objects[key].clear()
            self.objects[key].append(generator.object_class(respawn["x"], respawn["seed_offset"]))
            generator.update_dist()

    def set_respawn_objects(self):
        for layer in self.layers:
            layer.respawn = layer.points[0]

        for key in self.objects:
            first_object = self.objects[key][0]
            respawn = {"x": first_object.x, "seed_offset": first_object.seed_offset}
            self.object_generators[key].respawn = respawn


class TerrainGenerator:
    def __init__(self, world):
        self.world = world

        self.window_offset = 50
        self.min_dist_x = 10
        self.max_dist_x = 50
        self.octaves = 4
        self.persistence = 0.6
        self.lacunarity = 2
        self.x_scale = 0.001
        self.y_scale = 500

        for layer in self.world.layers:
            x = game_window.left * layer.draw_scale - self.window_offset
            point = TerrainPoint(x, layer.index / 10, -1)

            layer.points.append(point)
            layer.respawn = point
            self.generate_terrain(1, layer)

    def update(self):
        for layer in self.world.layers:
            self.add_terrain_points(layer)
            self.remove_terrain_points(layer)

    def generate_terrain(self, direction, layer):
        if direction == 1:
            prev_index = -1
        elif direction == -1:
            prev_index = 0

        while (
            layer.draw_point(prev_index)[0] >= -self.window_offset - self.max_dist_x
            and layer.draw_point(prev_index)[0] <= display_size[0] + self.window_offset + self.max_dist_x
        ):
            terrain_point = self.new_terrain_point(layer.points[prev_index], direction, layer.noise_params)

            if direction == 1:
                layer.points.append(terrain_point)
            elif direction == -1:
                layer.points.insert(0, terrain_point)

            if terrain_point.y < self.world.highest:
                self.world.highest = terrain_point.y

            if (
                layer.draw_point(prev_index)[0] > display_size[0] + self.window_offset
                or layer.draw_point(prev_index)[0] < -self.window_offset
            ):
                return

    def new_terrain_point(self, prev_terrain_point, direction, noise_params):
        seed_offset = prev_terrain_point.seed_offset + direction

        if direction == 1:
            dist_x = random_float(self.max_dist_x, self.min_dist_x, seed_offset)
            x = prev_terrain_point.x + dist_x
        elif direction == -1:
            dist_x = random_float(self.max_dist_x, self.min_dist_x, seed_offset + 1)
            x = prev_terrain_point.x - dist_x

        y = self.perlin_noise(x, noise_params)

        return TerrainPoint(x, y, seed_offset)

    def perlin_noise(self, x, params):
        x = x * params.x_scale + params.x_offset + seed
        y = noise.pnoise1(x, params.octaves, params.persistence, params.lacunarity)
        return y * params.y_scale - params.y_offset

    def add_terrain_points(self, layer):
        if layer.draw_point(-1)[0] < display_size[0] + self.window_offset:
            self.generate_terrain(1, layer)
        if layer.draw_point(0)[0] > -self.window_offset:
            self.generate_terrain(-1, layer)

    def remove_terrain_points(self, layer):
        if layer.draw_point(1)[0] < -self.window_offset:
            layer.points.pop(0)
        if layer.draw_point(-2)[0] > display_size[1] + self.window_offset:
            layer.points.pop(-1)


class TerrainPoint:
    def __init__(self, x, y, seed_offset):
        self.x = x
        self.y = y
        self.seed_offset = seed_offset


class TerrainLayer:
    def __init__(self, index, draw_scale, color, noise_params):
        self.index = index
        self.draw_scale = draw_scale
        self.color = color
        self.noise_params = noise_params
        self.points = []

    def draw_point(self, index):
        point = self.points[index]
        x = point.x - game_window.left * self.draw_scale
        y = point.y - game_window.top * self.draw_scale
        return (x, y)


class NoiseParams:
    def __init__(self, octaves, persistence, lacunarity, x_scale, y_scale, x_offset, y_offset):
        self.octaves = octaves
        self.persistence = persistence
        self.lacunarity = lacunarity
        self.x_scale = x_scale
        self.y_scale = y_scale
        self.x_offset = x_offset
        self.y_offset = y_offset


class ObjectGenerator:
    def __init__(self, object_class, objects, min_dist, max_dist):
        self.object_class = object_class
        self.objects = objects

        self.min_dist = min_dist
        self.max_dist = max_dist

        self.right = {"x": 0, "seed_offset": 0}
        self.left = {"x": 0, "seed_offset": 0}
        self.object_w = self.object_class(0, 0).w
        self.dist_right = random_float(self.max_dist, self.min_dist, 0.5)
        self.dist_left = random_float(self.max_dist, self.min_dist, -0.5)

        self.respawn = self.right

    def update(self):
        self.add_objects()
        self.remove_objects()

    def add_objects(self):
        if self.right["x"] + self.dist_right < game_window.right:
            new_seed_offset = self.right["seed_offset"] + 1
            new_x = self.right["x"] + self.dist_right
            self.objects.append(self.object_class(new_x, new_seed_offset))
            self.update_dist()

        if self.left["x"] + self.object_w - self.dist_left > game_window.left:
            new_seed_offset = self.left["seed_offset"] - 1
            new_x = self.left["x"] - self.dist_left
            self.objects.insert(0, self.object_class(new_x, new_seed_offset))
            self.update_dist()

    def remove_objects(self):
        if self.objects[-1].x > game_window.right:
            self.objects.pop()
            self.update_dist()

        if self.objects[0].x + self.objects[0].w < game_window.left:
            self.objects.pop(0)
            self.update_dist()

    def update_dist(self):
        self.right = {"x": self.objects[-1].x, "seed_offset": self.objects[-1].seed_offset}
        self.left = {"x": self.objects[0].x, "seed_offset": self.objects[0].seed_offset}

        self.dist_right = random_float(self.max_dist, self.min_dist, self.right["seed_offset"] + 0.5)
        self.dist_left = random_float(self.max_dist, self.min_dist, self.left["seed_offset"] - 0.5)


class Spring:
    def __init__(self, x, seed_offset):
        self.x = x
        self.seed_offset = seed_offset

        self.stop_length = 200
        self.line_width = 5
        self.bob_r = 30
        self.acceleration_up = 20
        self.damping = 0.2
        self.bob_mass = 0.1

        check_range = (self.x + self.bob_r - self.line_width / 2, self.x + self.bob_r + self.line_width / 2)
        self.y = world.highest_in_range(check_range[0], check_range[1]) - self.stop_length - self.bob_r
        self.w = self.bob_r * 2

        self.anchor_x = self.x + self.bob_r
        self.anchor_y = self.y + self.bob_r + self.stop_length

        self.bob_x = self.anchor_x
        self.bob_y = self.anchor_y - self.stop_length
        self.bob_vx = 0
        self.bob_vy = 0

        self.rest_y = self.stop_length - self.acceleration_up * self.bob_mass

    def draw(self):
        anchor_x = self.anchor_x - game_window.left
        anchor_y = self.anchor_y - game_window.top
        bob_x = self.bob_x - game_window.left
        bob_y = self.bob_y - game_window.top

        pygame.draw.line(screen, "blue", (anchor_x, anchor_y), (bob_x, bob_y), self.line_width)
        pygame.draw.circle(screen, "blue", (bob_x, bob_y), self.bob_r)

    def update(self):
        self.update_velocity()
        self.move()

    def update_velocity(self):
        spring_x = (self.anchor_x - self.bob_x) / self.bob_mass
        damping_x = self.damping * self.bob_vx / self.bob_mass

        spring_y = ((self.anchor_y - self.rest_y) - self.bob_y) / self.bob_mass
        damping_y = self.damping * self.bob_vy / self.bob_mass

        ax = spring_x - damping_x
        ay = spring_y - damping_y - self.acceleration_up

        self.bob_vx += ax * dt
        self.bob_vy += ay * dt

    def move(self):
        self.bob_x += self.bob_vx * dt
        self.bob_y += self.bob_vy * dt

        if pygame.mouse.get_pressed()[1]:
            mouse_coords = pygame.mouse.get_pos()
            self.bob_x = mouse_coords[0] + game_window.left
            self.bob_y = mouse_coords[1] + game_window.top

            self.bob_vx = 0
            self.bob_vy = 0

    def resolve_collision(self):
        dx = max(player.x - self.bob_x, 0, self.bob_x - (player.x + player.w))
        dy = max(player.y - self.bob_y, 0, self.bob_y - (player.y + player.h))

        sign_x = 1 if self.bob_x < player.x + player.w / 2 else -1
        sign_y = 1 if self.bob_y < player.y + player.h / 2 else -1

        theta = math.atan2(dy * sign_y, dx * sign_x)

        player.vx += 300 * math.cos(theta)
        player.vy += 300 * math.sin(theta)

        self.bob_vx += 300 * math.cos(theta + math.pi) + player.vx * 0.5
        self.bob_vy += 300 * math.sin(theta + math.pi) + player.vy * 0.5


class Platform:
    def __init__(self, x, seed_offset):
        self.w = 50
        self.h = 10
        self.x = x
        self.y = world.highest_in_range(self.x, self.x + self.w) - self.h

        self.seed_offset = seed_offset

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
            "angle_range": (0.2, -0.2),
            "speed_range": (50, 200),
            "rotation_range": (1, 10),
            "growth_range": (50, 75),
            "grow_time": 0.4,
            "shrink_time": 0.6,
        }
        self.create_particles(options)

        options["angle_range"] = (math.pi - 0.3, math.pi + 0.3)
        self.create_particles(options)

    def thrust(self, direction):
        delta_angle = math.atan2(player.y_thrust, player.x_thrust) * direction
        options = {
            "num_range": (1, 1),
            "x": player.x + player.w / 2,
            "y": player.y + player.h * 0.7,
            "angle_range": (0.5 * math.pi + delta_angle - 0.3, 0.5 * math.pi + delta_angle + 0.3),
            "speed_range": (50, 80),
            "rotation_range": (1, 10),
            "growth_range": (20, 40),
            "grow_time": 0.4,
            "shrink_time": 0.6,
        }
        self.create_particles(options, True)

    def explosion(self):
        options = {
            "num_range": (4, 6),
            "x": player.x + player.w / 2,
            "y": player.y + player.h / 2,
            "angle_range": (-math.pi / 2 - 1, -math.pi / 2 + 1),
            "speed_range": (80, 100),
            "rotation_range": (1, 10),
            "growth_range": (150, 250),
            "grow_time": 0.2,
            "shrink_time": 2,
        }
        self.create_particles(options)

    def create_particles(self, options, relative_speed=False):
        num_range = options["num_range"]
        x = options["x"]
        y = options["y"]
        angle_range = options["angle_range"]
        speed_range = options["speed_range"]
        rotation_range = options["rotation_range"]
        growth_range = options["growth_range"]
        grow_time = options["grow_time"]
        shrink_time = options["shrink_time"]

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

            particles.append(Particle(x, y, vx, vy, rotation, growth, grow_time, shrink_time))


class Particle:
    def __init__(self, x, y, vx, vy, rotate, growth, grow_time, shrink_time):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.rotate = rotate
        self.growth = growth
        self.grow_time = grow_time
        self.shrink_time = shrink_time

        self.rotation = 0
        self.radius = 0
        self.time = 0
        self.max_radius = 0

    def draw(self):
        if self.radius <= 0:
            return

        points = hexagon_points(
            self.x - game_window.left, self.y - game_window.top, self.radius, self.rotation
        )
        pygame.draw.polygon(screen, "white", points)

    def update(self):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.rotation += self.rotate * dt

        if self.time < self.grow_time:
            self.radius += self.growth * dt
            self.max_radius = self.radius
        else:
            self.radius -= self.max_radius / self.shrink_time * dt

        if self.radius <= 0:
            return particles.remove(self)

        self.time += dt


class FuelMeter:
    def __init__(self):
        self.x = 30
        self.y = 30
        self.img = pygame.image.load("./img/fuel.png")

    def draw(self):
        screen.blit(self.img, (self.x, self.y))

        center = (self.x + 18, self.y + 17)
        big_hex = hexagon_points(center[0], center[1], 38)
        small_hex = hexagon_points(center[0], center[1], 30)

        pygame.draw.polygon(screen, "white", big_hex, 1)
        pygame.draw.polygon(screen, "white", small_hex, 1)
        self.draw_bar(big_hex, small_hex)

    def draw_bar(self, big_hex, small_hex):
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


def check_rr_collision(rect1, rect2):
    left = round(rect1[0] + rect1[2], 6) > round(rect2[0], 6)
    right = round(rect1[0], 6) < round(rect2[0] + rect2[2], 6)
    top = round(rect1[1] + rect1[3], 6) > round(rect2[1], 6)
    bottom = round(rect1[1], 6) < round(rect2[1] + rect2[3], 6)

    if left and right and top and bottom:
        return True


def check_cr_collision(rect, circle):
    test_x = circle[0]
    test_y = circle[1]

    if circle[0] < rect[0]:
        test_x = rect[0]
    elif circle[0] > rect[0] + rect[2]:
        test_x = rect[0] + rect[2]

    if circle[1] < rect[1]:
        test_y = rect[1]
    elif circle[1] > rect[1] + rect[3]:
        test_y = rect[1] + rect[3]

    dist_x = circle[0] - test_x
    dist_y = circle[1] - test_y
    dist = math.sqrt(dist_x**2 + dist_y**2)

    if dist < circle[2]:
        return True
    return False


def random_float(max, min, seed_offset=0):
    random.seed(seed + seed_offset)
    return random.random() * (max - min) + min


def center_x(obj):
    return obj.x + obj.w / 2


def center_y(obj):
    return obj.y + obj.h / 2


def hexagon_points(center_x, center_y, radius, rotation=0):
    points = []

    for n in range(6):
        angle = (n * 60 - 120) * math.pi / 180 + rotation
        x = center_x + radius * math.cos(angle)
        y = center_y + radius * math.sin(angle)
        points.append((x, y))

    return points


def setup():
    platform = Platform(0, 0)
    world.objects["platform"].append(platform)
    platform.x = player.w / 2 - platform.w / 2
    platform.y = world.highest_in_range(platform.x, platform.x + platform.w) - platform.h
    world.object_generators["platform"].respawn["x"] = platform.x
    player.platform = platform
    player.y = platform.y - player.h


# Global Variables
hud = HUD()
mouse = Mouse()
gravity = 150
clock = pygame.time.Clock()
dt = 0
seed = random.random() * 100000
frame_count = 0
game_window = GameWindow()
world = World()
world.create_generators()
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
    screen.fill((140, 190, 200))
    dt = clock.tick(60) / 1000

    world.update()
    mouse.update()
    player.update()
    game_window.update()
    for particle in particles:
        particle.update()

    world.draw()
    for particle in particles:
        particle.draw()
    player.draw()
    hud.draw()

    pygame.display.flip()
