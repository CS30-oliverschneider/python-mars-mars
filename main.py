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
        self.w = 28
        self.h = 40

        self.mass = 1

        self.pieces = []
        self.img = pygame.image.load("img/spritesheet.png")
        self.img_x = 4
        self.img_y = 0

        self.frame_width = 40
        self.frame_height = 40
        self.anim_speed = 0.05
        self.current_frame = 0
        self.delta_frame = 0
        self.frame_timer = self.anim_speed

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
        for piece in self.pieces:
            piece.draw()

        if self.state == "dead":
            return

        self.frame_timer -= dt
        if self.delta_frame != 0 and self.frame_timer <= 0:
            self.frame_timer = self.anim_speed
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
        screen.blit(self.img, (x, y), area)

        for piece in self.pieces:
            piece.draw()

    def update(self):
        for piece in self.pieces:
            piece.update()

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

        for block in world.objects["blocks"]:
            player_p1 = (player.x, player.y)
            player_p2 = (player.x + player.w, player.y)
            player_p3 = (player.x + player.w, player.y + player.h)
            player_p4 = (player.x, player.y + player.h)
            player_rect = [player_p1, player_p2, player_p3, player_p4]

            block_rect = block.corners

            sat_info = sat(player_rect, block_rect)
            if sat_info:
                block.resolve_collision(sat_info)

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

    def create_pieces(self):
        self.pieces = [PlayerPiece(x, self.x, self.y) for x in range(6)]

    def reset(self):
        self.y = self.platform.y - self.h
        self.vy = 0
        self.vx = 0
        self.fuel = 6
        if self.state != "dead":
            self.state = "landed"

    def die(self):
        self.state = "dead"
        player.create_pieces()
        game_window.move_to_platform(self.platform)
        particle_generator.explosion()
        self.x = center_x(self.platform) - self.w / 2
        self.delta_frame = 0
        self.current_frame = 0


class PlayerPiece:
    def __init__(self, index, x, y):
        img_num = index + 1 if index != 5 else 5
        self.img = pygame.image.load(f"img/piece-{img_num}.png")
        self.x = 200
        self.y = 200
        self.angle = 0
        self.rotation = [-1, 1][random.randint(0, 1)] * random.uniform(50, 500)
        self.vx = [-1, 1][random.randint(0, 1)] * random.uniform(0, 100)
        self.vy = [-1, 1][random.randint(0, 1)] * random.uniform(50, 100)

        if index == 0:
            self.x = x
            self.y = y
        elif index == 1:
            self.x = x - 4
            self.y = y + 20
        elif index == 2:
            self.x = x
            self.y = y + 20
        elif index == 3:
            self.x = x + 32
            self.y = y + 20
        elif index == 4:
            self.x = x + 4
            self.y = y + 36
        elif index == 5:
            self.x = x + 20
            self.y = y + 36

    def draw(self):
        if self.y > display_size[1]:
            player.pieces.remove(self)
            return

        pos = (self.x - game_window.left, self.y - game_window.top)
        center = self.img.get_rect(topleft=pos).center
        screen.blit(*rotate_image(self.img, center, self.angle))

    def update(self):
        self.vy += gravity * dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.angle += self.rotation * dt


class World:
    def __init__(self):
        self.layers = []
        self.highest = float("inf")
        self.create_layers()
        self.terrain_generator = TerrainGenerator(self)

        self.objects = {"springs": [], "blocks": [], "platforms": []}

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
        platform_generator = ObjectGenerator(0, Platform, self.objects["platforms"], 1000, 1500)
        spring_generator = ObjectGenerator(1, Spring, self.objects["springs"], 1000, 1500)
        block_generator = ObjectGenerator(2, Block, self.objects["blocks"], 1000, 1500)

        self.object_generators = {
            "platforms": platform_generator,
            "springs": spring_generator,
            "blocks": block_generator,
        }

    def create_layers(self):
        noise_params1 = NoiseParams(3, 0.6, 2, 0.001, 500, 0, 0)
        noise_params2 = NoiseParams(3, 0.6, 2, 0.0015, 500, 10000, -70)
        noise_params3 = NoiseParams(3, 0.6, 2, 0.002, 500, 20000, -50)

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


class TerrainGenerator:
    def __init__(self, world):
        self.world = world

        self.window_offset = 60
        self.min_dist_x = 10
        self.max_dist_x = 50

        for layer in self.world.layers:
            x = game_window.left * layer.draw_scale - self.window_offset
            point = TerrainPoint(x, layer.index / 10, -1)

            layer.points.append(point)
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
            layer.draw_point(prev_index)[0] >= -self.window_offset
            and layer.draw_point(prev_index)[0] <= display_size[0] + self.window_offset
        ):
            terrain_point = self.new_terrain_point(layer.points[prev_index], direction, layer.noise_params)

            if direction == 1:
                layer.points.append(terrain_point)
            elif direction == -1:
                layer.points.insert(0, terrain_point)

            if terrain_point.y < self.world.highest:
                self.world.highest = terrain_point.y

    def new_terrain_point(self, prev_terrain_point, direction, noise_params):
        seed_offset = prev_terrain_point.seed_offset + direction

        if direction == 1:
            dist_x = random_float(self.min_dist_x, self.max_dist_x, seed_offset)
            x = prev_terrain_point.x + dist_x
        elif direction == -1:
            dist_x = random_float(self.min_dist_x, self.max_dist_x, seed_offset + 1)
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
    def __init__(self, index, object_class, objects, min_dist, max_dist):
        self.object_class = object_class
        self.objects = objects
        self.min_dist = min_dist
        self.max_dist = max_dist

        self.object_w = self.object_class(0, 0).w

        self.seed_offset = index / 10

        x = random_float(min_dist / 2, max_dist / 2, self.seed_offset)
        self.right = {"x": x, "seed_offset": 0}
        self.left = {"x": x, "seed_offset": 0}

        self.dist_right = random_float(min_dist, max_dist, self.seed_offset + 0.5)
        self.dist_left = random_float(min_dist, max_dist, self.seed_offset - 0.5)

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

        if (
            len(self.objects) == 0
            and self.right["x"] + self.object_w > game_window.left
            and self.right["x"] < game_window.right
        ):
            self.objects.append(self.object_class(self.right["x"], self.right["seed_offset"]))

    def remove_objects(self):
        if not len(self.objects):
            return

        if self.objects[-1].x > game_window.right:
            self.objects.pop()
            self.update_dist()

        if not len(self.objects):
            return

        if self.objects[0].x + self.objects[0].w < game_window.left:
            self.objects.pop(0)
            self.update_dist()

    def update_dist(self):
        if not len(self.objects):
            return

        self.right = {"x": self.objects[-1].x, "seed_offset": self.objects[-1].seed_offset}
        self.left = {"x": self.objects[0].x, "seed_offset": self.objects[0].seed_offset}

        offset = self.seed_offset + self.right["seed_offset"] + 0.5
        self.dist_right = random_float(self.min_dist, self.max_dist, offset)
        offset = self.seed_offset + self.left["seed_offset"] - 0.5
        self.dist_left = random_float(self.min_dist, self.max_dist, offset)


class Spring:
    def __init__(self, x, seed_offset):
        self.x = x
        self.seed_offset = seed_offset

        self.stop_length = 200
        self.line_width = 5
        self.bob_r = 30
        self.acceleration_up = 40
        self.damping = 5
        self.mass = 2
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
        self.vx = 0
        self.vy = 0

        self.rest_y = self.acceleration_up * self.mass / -self.k + self.stop_length

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
        spring_x = -self.k * (self.bob_x - self.anchor_x) / self.mass
        damping_x = self.damping * self.vx / self.mass

        spring_y = -self.k * (self.bob_y - (self.anchor_y - self.rest_y)) / self.mass
        damping_y = self.damping * self.vy / self.mass

        ax = spring_x - damping_x
        ay = spring_y - damping_y - self.acceleration_up

        self.vx += ax * dt
        self.vy += ay * dt

    def move(self):
        self.bob_x += self.vx * dt
        self.bob_y += self.vy * dt

        if pygame.mouse.get_pressed()[1]:
            mouse_coords = pygame.mouse.get_pos()
            self.bob_x = mouse_coords[0] + game_window.left
            self.bob_y = mouse_coords[1] + game_window.top

            self.vx = 0
            self.vy = 0

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

        elastic_collision(player, self, normal, self.min_bounce, self.friction)


class Block:
    def __init__(self, x, seed_offset):
        self.img = pygame.image.load("img/cow.png")
        self.rotated_w = 95
        self.rotated_h = 67
        self.min_bounce = 50

        points = world.main_layer.points
        for i in range(len(points)):
            if points[i].x > x:
                line = [points[i], points[i + 1]]
                break

        angle = math.atan2(line[1].y - line[0].y, line[1].x - line[0].x)
        self.corners = rotated_rect((line[0].x, line[0].y), self.rotated_w, self.rotated_h, angle)

        self.img_x = 0
        self.img_y = -8

        center_x = (self.corners[0][0] + self.corners[2][0]) / 2 + self.img_x
        center_y = (self.corners[0][1] + self.corners[2][1]) / 2 + self.img_y
        self.img, self.rect = rotate_image(self.img, (center_x, center_y), math.degrees(-angle))

        self.x = x
        self.w = math.sqrt(self.rotated_w**2 + self.rotated_h**2)

        self.seed_offset = seed_offset

    def draw(self):
        x = self.rect.x - game_window.left
        y = self.rect.y - game_window.top
        screen.blit(self.img, (x, y, self.rect.w, self.rect.h))

    def resolve_collision(self, sat_info):
        player.x += sat_info["move_vector"][0]
        player.y += sat_info["move_vector"][1]
        bounce_off(player, sat_info["normal"], self.min_bounce)


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


def elastic_collision(obj1, obj2, normal, min_bounce, friction):
    total_mass = obj1.mass + obj2.mass

    # Find the parallel and perpendicular velocity components along the normal
    obj1_angle = math.atan2(obj1.vy, obj1.vx)
    obj1_speed = math.sqrt(obj1.vx**2 + obj1.vy**2)
    obj1_v1 = obj1_speed * math.cos(obj1_angle - normal)
    obj1_v2 = obj1_speed * math.sin(obj1_angle - normal)

    obj2_angle = math.atan2(obj2.vy, obj2.vx)
    obj2_speed = math.sqrt(obj2.vx**2 + obj2.vy**2)
    obj2_v1 = obj2_speed * math.cos(obj2_angle - normal)
    obj2_v2 = obj2_speed * math.sin(obj2_angle - normal)

    # Find new parallel velocities after an elastic collision
    new_obj1_v1 = obj1_v1 * (obj1.mass - obj2.mass) / total_mass + obj2_v1 * 2 * obj2.mass / total_mass
    new_obj2_v1 = obj2_v1 * (obj2.mass - obj1.mass) / total_mass + obj1_v1 * 2 * obj1.mass / total_mass
    new_obj1_v1 += min_bounce

    new_obj1_v2 = obj1_v2 * (1 - friction)
    new_obj2_v2 = obj2_v2 + obj1_v2 * friction

    # Update velocities
    obj1.vx = new_obj1_v1 * math.cos(normal) + new_obj1_v2 * math.cos(normal + math.pi / 2)
    obj1.vy = new_obj1_v1 * math.sin(normal) + new_obj1_v2 * math.sin(normal + math.pi / 2)
    obj2.vx = new_obj2_v1 * math.cos(normal) + new_obj2_v2 * math.cos(normal + math.pi / 2)
    obj2.vy = new_obj2_v1 * math.sin(normal) + new_obj2_v2 * math.sin(normal + math.pi / 2)


def bounce_off(rect, normal, min_bounce):
    v_normal = -(rect.vx * math.cos(normal) + rect.vy * math.sin(normal)) + min_bounce
    v_perpendicular = -rect.vx * math.sin(normal) + rect.vy * math.cos(normal)

    rect.vx = v_normal * math.cos(normal) - v_perpendicular * math.sin(normal)
    rect.vy = v_normal * math.sin(normal) + v_perpendicular * math.cos(normal)


def sat(rect1, rect2):
    rects = [rect1, rect2]

    normals = []
    for rect in rects:
        normals.append(calc_normal(rect[0], rect[1]))
        normals.append(calc_normal(rect[1], rect[2]))

    overlaps = []
    for normal in normals:
        bounds = []

        for rect in rects:
            bounds.append([])
            dists = []

            for corner in rect:
                vector = project_vector(corner, normal)
                sign = math.copysign(1, math.cos(normal)) * math.copysign(1, vector[0])
                dist = sign * length(vector)
                dists.append(dist)
            bounds[-1] = [round(min(dists), 4), round(max(dists), 4)]

        if bounds[0][1] <= bounds[1][0] or bounds[1][1] <= bounds[0][0]:
            return False
        else:
            overlaps.append(calc_overlap(bounds))

    dist = min(overlaps, key=abs)
    angle = normals[overlaps.index(dist)]
    move_vector = (dist * math.cos(angle), dist * math.sin(angle))

    return {"normal": angle, "move_vector": move_vector}


def rotate_image(img, center, angle):
    rotated_image = pygame.transform.rotate(img, angle)
    new_rect = rotated_image.get_rect(center=center)
    return rotated_image, new_rect


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


def random_float(min, max, seed_offset=0):
    random.seed(seed + seed_offset)
    return random.random() * (max - min) + min


def center_x(obj):
    return obj.x + obj.w / 2


def center_y(obj):
    return obj.y + obj.h / 2


def rotated_rect(point, w, h, angle):
    def rotate(corner):
        temp_x = corner[0] - point[0]
        temp_y = corner[1] - point[1]

        rotated_x = temp_x * math.cos(angle) - temp_y * math.sin(angle)
        rotated_y = temp_x * math.sin(angle) + temp_y * math.cos(angle)

        return (rotated_x + point[0], rotated_y + point[1])

    c1 = (point[0], point[1] - h)
    c2 = (point[0] + w, point[1] - h)
    c3 = (point[0] + w, point[1])
    c4 = (point[0], point[1])

    return [rotate(c1), rotate(c2), rotate(c3), rotate(c4)]


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

    generator = world.object_generators["platforms"]
    generator.right["x"] = platform.x
    generator.left["x"] = platform.x

    player.platform = platform
    player.y = platform.y - player.h


# Global Variables
hud = HUD()
mouse = Mouse()
gravity = 150
clock = pygame.time.Clock()
dt = 0
seed = random.random() * 100000
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

    screen.fill((140, 190, 200))
    dt = clock.tick(60) / 1000

    game_window.update()
    world.update()
    mouse.update()
    player.update()
    for particle in particles:
        particle.update()

    world.draw()
    for particle in particles:
        particle.draw()
    player.draw()
    hud.draw()

    pygame.display.flip()
