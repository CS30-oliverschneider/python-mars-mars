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

        self.mass = 1

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
        if self.state == "dead":
            return

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
        if self.state == "dead" or self.state == "waiting":
            return

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

        for platform in world.objects["platforms"]:
            platform_rect = (platform.x, platform.y, platform.w, platform.h)
            if check_rr_collision(player_rect, platform_rect):
                platform.resolve_collision()

        for spring in world.objects["springs"]:
            spring_circle = (spring.bob_x, spring.bob_y, spring.bob_r)
            if check_cr_collision(player_rect, spring_circle):
                spring.resolve_collision()

    def check_terrain_collision(self):
        if (self.state != "launched" and self.state != "flying") or world.highest > self.y + self.h:
            return

        highest_y = world.highest_in_range(self.x, self.x + self.w)

        if self.y + self.h > highest_y:
            self.die()

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
        self.fuel = 6
        if self.state != "dead":
            self.state = "landed"

    def die(self):
        self.state = "dead"
        game_window.move_to_platform(self.platform)
        particle_generator.explosion()
        self.x = center_x(self.platform) - self.w / 2
        self.delta_frame = 0
        self.current_frame = 0


class World:
    def __init__(self):
        self.layers = []
        self.highest = float("inf")
        self.create_layers()
        self.terrain_generator = TerrainGenerator(self)

        self.objects = {"platforms": [], "springs": []}

    def draw(self):
        for layer in reversed(self.layers):
            self.draw_terrain_layer(layer)

        for object_list in self.objects.values():
            for game_object in object_list:
                game_object.draw()

    def update(self):
        self.terrain_generator.update()
        for generator in self.object_generators.values():
            generator.update()
        for spring in self.objects["springs"]:
            spring.update()

    def draw_terrain_layer(self, layer):
        draw_points = [layer.draw_point(i) for i in range(len(layer.points))]

        draw_points.append((display_size[0], display_size[1]))
        draw_points.append((0, display_size[1]))

        pygame.draw.polygon(screen, layer.color, draw_points)

    def create_generators(self):
        self.platform_generator = ObjectGenerator(Platform, self.objects["platforms"], 500, 800)
        self.spring_generator = ObjectGenerator(Spring, self.objects["springs"], 200, 400)
        self.object_generators = {
            "platforms": self.platform_generator,
            "springs": self.spring_generator,
        }

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

        self.window_offset = 60
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
        self.right = {
            "x": self.objects[-1].x,
            "seed_offset": self.objects[-1].seed_offset,
        }
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
        self.acceleration_up = 40
        self.damping = 5
        self.bob_mass = 2
        self.k = 100
        self.min_bounce = 100
        self.friction = 0.1

        check_range = (
            self.x + self.bob_r - self.line_width / 2,
            self.x + self.bob_r + self.line_width / 2,
        )
        self.w = self.bob_r * 2

        self.anchor_x = self.x + self.bob_r
        self.anchor_y = world.highest_in_range(check_range[0], check_range[1]) + 10

        self.bob_x = self.anchor_x
        self.bob_y = self.anchor_y - self.stop_length
        self.bob_vx = 0
        self.bob_vy = 0

        self.rest_y = self.acceleration_up * self.bob_mass / -self.k + self.stop_length

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
        self.x = min(self.bob_x - self.bob_r, self.anchor_x - self.line_width / 2)
        self.w = max(self.bob_x + self.bob_r, self.anchor_x + self.line_width / 2) - self.x

    def update_velocity(self):
        spring_x = -self.k * (self.bob_x - self.anchor_x) / self.bob_mass
        damping_x = self.damping * self.bob_vx / self.bob_mass

        spring_y = -self.k * (self.bob_y - (self.anchor_y - self.rest_y)) / self.bob_mass
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
        # Calculate the distance between the player and the bob
        dx = max(player.x - self.bob_x, 0, self.bob_x - (player.x + player.w))
        dy = max(player.y - self.bob_y, 0, self.bob_y - (player.y + player.h))
        dist = math.sqrt(dx**2 + dy**2)

        # Calculate the overlap and the normal between the player and the bob
        sign_x = 1 if player.x + player.w / 2 > self.bob_x else -1
        sign_y = 1 if player.y + player.h / 2 > self.bob_y else -1
        overlap = self.bob_r - dist
        normal = math.atan2(dy * sign_y, dx * sign_x)
        move_x = overlap * math.cos(normal)
        move_y = overlap * math.sin(normal)

        # Separate the player and the bob
        self.bob_x -= move_x / 2
        self.bob_y -= move_y / 2
        player.x += move_x / 2
        player.y += move_y / 2

        total_mass = player.mass + self.bob_mass

        # Find the parallel and perpendicular velocity components along the normal
        player_angle = math.atan2(player.vy, player.vx)
        player_speed = math.sqrt(player.vx**2 + player.vy**2)
        player_v1 = player_speed * math.cos(player_angle - normal)
        player_v2 = player_speed * math.sin(player_angle - normal)

        bob_angle = math.atan2(self.bob_vy, self.bob_vx)
        bob_speed = math.sqrt(self.bob_vx**2 + self.bob_vy**2)
        bob_v1 = bob_speed * math.cos(bob_angle - normal)
        bob_v2 = bob_speed * math.sin(bob_angle - normal)

        # Find new parallel velocities after an elastic collision
        new_player_v1 = (
            player_v1 * (player.mass - self.bob_mass) / total_mass
            + bob_v1 * 2 * self.bob_mass / total_mass
            + self.min_bounce
        )
        new_player_v2 = player_v2 * (1 - self.friction)
        new_bob_v1 = (
            bob_v1 * (self.bob_mass - player.mass) / total_mass + player_v1 * 2 * player.mass / total_mass
        )
        new_bob_v2 = bob_v2 + player_v2 * self.friction

        # Update velocities
        player.vx = new_player_v1 * math.cos(normal) + new_player_v2 * math.cos(normal + math.pi / 2)
        player.vy = new_player_v1 * math.sin(normal) + new_player_v2 * math.sin(normal + math.pi / 2)
        self.bob_vx = new_bob_v1 * math.cos(normal) + new_bob_v2 * math.cos(normal + math.pi / 2)
        self.bob_vy = new_bob_v1 * math.sin(normal) + new_bob_v2 * math.sin(normal + math.pi / 2)


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

        self.wait = 0.8
        self.timer = self.wait
        self.target = None
        self.move_speed = None
        self.move_angle = None
        self.dist_function = None
        self.move_x = None

    def update(self):
        if self.target:
            self.move()
        else:
            self.left = player.x - self.spacing
            self.top = center_y(player) - display_size[1] / 2

        self.right = self.left + display_size[0]
        self.bottom = self.left + display_size[1]

    def move(self):
        if self.timer > 0:
            self.timer -= dt
            return

        if self.timer != float("-inf"):
            player.reset()
            player.state = "waiting"
            self.timer = float("-inf")

        dy = self.top - self.target[1]
        dx = self.left - self.target[0]

        if self.move_angle is None:
            self.move_angle = math.atan2(dy, dx)
        if self.dist_function is None:
            dist = math.sqrt(dy**2 + dx**2)
            self.move_x = (dist / self.move_speed) ** (1 / 4)
            self.dist_function = lambda x: self.move_speed * x**4

        new_dist = self.dist_function(self.move_x)
        self.left = self.target[0] + new_dist * math.cos(self.move_angle)
        self.top = self.target[1] + new_dist * math.sin(self.move_angle)

        self.move_x -= dt

        if self.move_x < 0.2:
            player.state = "landed"
            self.timer = self.wait
            self.target = None
            self.move_speed = None
            self.move_angle = None
            self.dist_function = None
            self.move_x = None

    def move_to_platform(self, platform):
        target_x = platform.x + platform.w / 2 - player.w / 2 - self.spacing
        target_y = platform.y - player.h / 2 - display_size[1] / 2
        self.target = (target_x, target_y)

        dx = target_x - self.left
        dy = target_y - self.top
        dist = math.sqrt(dx**2 + dy**2)
        self.move_speed = dist * 0.2


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
            "angle_range": (
                0.5 * math.pi + delta_angle - 0.3,
                0.5 * math.pi + delta_angle + 0.3,
            ),
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
            self.x - game_window.left,
            self.y - game_window.top,
            self.radius,
            self.rotation,
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
    dx = max(rect[0] - circle[0], 0, circle[0] - (rect[0] + rect[2]))
    dy = max(rect[1] - circle[1], 0, circle[1] - (rect[1] + rect[3]))
    dist = math.sqrt(dx**2 + dy**2)

    if dist < circle[2]:
        return True
    return False


def sat(rect1, rect2):
    rects = [rect1, rect2]

    normals = []
    for rect in rects:
        normals.append(calc_normal(rect.corners[0], rect.corners[1]))
        normals.append(calc_normal(rect.corners[1], rect.corners[2]))

    overlaps = []
    for normal in normals:
        bounds = []

        for rect in rects:
            bounds.append([])
            dists = []

            for corner in rect.corners:
                vector = project_vector(corner, normal)
                sign = math.copysign(1, math.cos(normal)) * math.copysign(1, vector[0])
                dist = sign * length(vector)
                dists.append(dist)
            bounds[-1] = [round(min(dists), 4), round(max(dists), 4)]

        if bounds[0][1] <= bounds[1][0] or bounds[1][1] <= bounds[0][0]:
            return
        else:
            overlaps.append(calc_overlap(bounds))

    separate(rects, normals, overlaps)


def separate(rects, normals, overlaps):
    dist = min(overlaps, key=abs)
    angle = normals[overlaps.index(dist)]

    dx_1 = dist / 2 * math.cos(angle)
    dy_1 = dist / 2 * math.sin(angle)
    dx_2 = dist / 2 * math.cos(angle + math.pi)
    dy_2 = dist / 2 * math.sin(angle + math.pi)

    rects[0].move(dx_1, dy_1)
    rects[1].move(dx_2, dy_2)


def calc_overlap(bounds):
    middle1 = (bounds[0][0] + bounds[0][1]) / 2
    middle2 = (bounds[1][0] + bounds[1][1]) / 2
    sign = math.copysign(1, middle1 - middle2)

    minimum = min(bounds[0][1], bounds[1][1])
    maximum = max(bounds[0][0], bounds[1][0])

    return sign * (minimum - maximum)


def project_vector(p, a):
    u = (math.cos(a), math.sin(a))
    dot = dot_product(p, u)
    return (dot * u[0], dot * u[1])


def dot_product(a, b):
    return a[0] * b[0] + a[1] * b[1]


def calc_normal(p1, p2):
    dx = p1[0] - p2[0]
    dy = p1[1] - p2[1]
    return math.atan2(dy, dx)


def length(p):
    return math.sqrt(p[0] ** 2 + p[1] ** 2)


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
    world.objects["platforms"].append(platform)
    platform.x = player.w / 2 - platform.w / 2
    platform.y = world.highest_in_range(platform.x, platform.x + platform.w) - platform.h
    world.object_generators["platforms"].respawn["x"] = platform.x
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
