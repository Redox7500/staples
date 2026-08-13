import numpy as np
import pyglet
from pyglet.window import mouse
from pyglet.window import key

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800
MAX_FPS = 60
MIN_FPS = 10

WINDOW = pyglet.window.Window(width=1000, height=600, caption="staple")
BATCH = pyglet.graphics.Batch()

mouse_state = mouse.MouseStateHandler()
keyboard_state = key.KeyStateHandler()
WINDOW.push_handlers(mouse_state)
WINDOW.push_handlers(keyboard_state)

objects = []

def get_rectangle_sides(shape):
    left = shape.x
    top = shape.y + shape.height
    right = shape.x + shape.width
    bottom = shape.y
    return [
        [np.array([left , bottom]), np.array([left , top   ])],
        [np.array([left , top   ]), np.array([right, top   ])],
        [np.array([right, top   ]), np.array([right, bottom])],
        [np.array([right, bottom]), np.array([left , bottom])]
    ]

def get_static_rectangles_intersection(current_position, new_position):
    all_sides = []
    for object in objects:
        if object.__class__.__name__ != "StaticRectangle":
            continue

        all_sides += get_rectangle_sides(object.shape)
    
    return  get_first_collision(all_sides, current_position, new_position)

def cross_product(v, u):
    return v[0] * u[1] - v[1] * u[0]

def get_intersection(line_1, line_2):
    line_1_delta = line_1[1] - line_1[0]
    line_2_delta = line_2[1] - line_2[0]
    deltas_cross_product = cross_product(line_1_delta, line_2_delta)

    if deltas_cross_product != 0:
        first_points_delta = line_2[0] - line_1[0]
        line_1_delta_scalar = cross_product(first_points_delta, line_2_delta) / deltas_cross_product
        line_2_delta_scalar = cross_product(first_points_delta, line_1_delta) / deltas_cross_product

        if 0 <= line_1_delta_scalar <= 1 and 0 <= line_2_delta_scalar <= 1:
            return line_1[0] + line_1_delta_scalar * line_1_delta
        
    return None

def get_first_collision(polygon_sides, current_position, new_position):
    least_distance_intersection = None
    least_distance = np.inf
    for side in polygon_sides:
        intersection = get_intersection(side, [current_position, new_position])
        if intersection is not None:
            distance = np.linalg.norm(intersection - current_position)
            if distance < least_distance:
                least_distance_intersection = intersection
                least_distance = distance
    
    return least_distance_intersection

def spring_force(position_1, position_2, resting_length, spring_constant):
    line_vector = position_1 - position_2
    distance = np.linalg.norm(line_vector)

    return line_vector / distance * spring_constant * (resting_length - distance) if distance else 0

def angle_between_vectors(vector_1, vector_2):
    normalized_vector_1 = vector_1 / np.linalg.norm(vector_1)
    normalized_vector_2 = vector_2 / np.linalg.norm(vector_2)

    return np.arccos(np.dot(normalized_vector_1, normalized_vector_2))

class StaticRectangle:
    def __init__(self, position, size, color=(255, 255, 255)):
        self.shape = pyglet.shapes.Rectangle(*position, *size, color=color, batch=BATCH)
        
        objects.append(self)

    def update(self, delta_time):
        ...

class Point:
    def __init__(self, position, mass=100, radius=10, color=(255, 255, 255), gravity=True, draggable=False):
        self.previous_position = np.array(position)

        self.mass = mass
        self.gravity_force = np.array([0, -200 * self.mass])

        self.shape = pyglet.shapes.Circle(position[0], position[1], radius, color=color, batch=BATCH)

        self.use_gravity = gravity
        self.draggable = draggable
        self.selected = False

        objects.append(self)

    @property
    def position(self):
        return np.array(self.shape.position)
    
    @position.setter
    def position(self, value):
        self.shape.position = (value[0], value[1])
    
    def move_to(self, new_position, collides=True, prioritize=False):
        if not(self.selected) or prioritize:
            self.previous_position = self.position

            if collides:
                intersection = get_static_rectangles_intersection(self.position, new_position)
                if intersection is None:
                    self.position = new_position
                # else:
                #     vector = intersection - self.position
                #     radius_vector = vector / np.linalg.norm(vector) * self.shape.radius
                #     self.position = intersection - radius_vector
        
    def apply_force(self, delta_time, force, collides=True, prioritize=False, use_previous_position=False):
        if not(self.selected) or prioritize:
            new_position = self.position + force / self.mass * delta_time ** 2

            if use_previous_position:
                new_position += self.position - self.previous_position
                self.previous_position = self.position.copy()

            if collides:
                intersection = get_static_rectangles_intersection(self.position, new_position)
                if intersection is None:
                    self.position = new_position
                # else:
                #     vector = intersection - self.position
                #     print(vector / np.linalg.norm(vector))
                #     radius_vector = vector / np.linalg.norm(vector) * self.shape.radius
                #     self.position = intersection - radius_vector
    
    def update(self, delta_time):
        if self.draggable:
            if mouse_state[mouse.LEFT]:
                if np.linalg.norm(np.array([mouse_state.x, mouse_state.y]) - self.position) < self.shape.radius:
                    self.selected = True
            else:
                self.selected = False

            if self.selected:
                self.move_to(np.array([mouse_state.x, mouse_state.y]), prioritize=True)
        
        if self.use_gravity:
            self.apply_force(delta_time, self.gravity_force, use_previous_position=True)

class Line:
    def __init__(self, point_1, point_2, spring_constant=30000, constraint_iterations=2, resting_length=None, attached_points=[], attached_points_spring_constant=30000, attached_points_constraint_iterations=1, attached_points_offsets=[], draggable_override=None):
        self.point_1 = point_1
        self.point_2 = point_2
        self.attached_points = attached_points

        self._resting_length = np.linalg.norm(self.point_2.position - self.point_1.position) if resting_length is None else resting_length

        vertical_axis = self.point_2.position - self.point_1.position
        axes_matrix = np.column_stack(([vertical_axis[1], vertical_axis[0]], vertical_axis))
        attached_points_offsets = [attached_points_offsets[i] if len(attached_points_offsets) > i else None for i in range(len(self.attached_points))]
        self.attached_points_offsets = [np.linalg.solve(axes_matrix, attached_point.position - self.point_1.position) if offset is None else offset for attached_point, offset in zip(self.attached_points, attached_points_offsets)]

        self.shape = pyglet.shapes.Line(*self.point_1.shape.position, *self.point_2.shape.position, 1, np.array((np.array(self.point_1.shape.color) + np.array(self.point_2.shape.color)) / 2, dtype=int), batch=BATCH)

        self.spring_constant = spring_constant
        self.constraint_iterations = constraint_iterations
        self.attached_points_spring_constant = attached_points_spring_constant if attached_points_spring_constant is not None else self.spring_constant
        self.attached_points_constraint_iterations = attached_points_constraint_iterations

        self.draggable_override = None

        objects.append(self)

    @property
    def resting_length(self):
        return self._resting_length

    @resting_length.setter
    def resting_length(self, value):
        self.attached_points_offsets = [attached_point_offset / self.resting_length * value for attached_point_offset in self.attached_points_offsets]
        self._resting_length = value

    @property
    def draggable_override(self):
        return self._draggable_override

    @draggable_override.setter
    def draggable_override(self, value):
        self._draggable_override = value
        if self.draggable_override is not None:
            self.point_1.draggable = self.point_2.draggable = self.draggable_override

    def constrain_points(self, delta_time):
        distance = np.linalg.norm(self.point_2.position - self.point_1.position)
        if distance:
            force = spring_force(self.point_1.position, self.point_2.position, self.resting_length, self.spring_constant)
            self.point_1.apply_force(delta_time, force)
            self.point_2.apply_force(delta_time, -force)
            
            vertical_axis = self.point_2.position - self.point_1.position
            axes_matrix = np.column_stack(([vertical_axis[1], vertical_axis[0]], vertical_axis))
            for _ in range(self.attached_points_constraint_iterations):
                for attached_point, offset in zip(self.attached_points, self.attached_points_offsets):
                    force = spring_force(attached_point.position, self.point_1.position + np.matmul(axes_matrix, offset), 0, self.attached_points_spring_constant)
                    attached_point.apply_force(delta_time, force)
                    self.point_1.apply_force(delta_time, -force)
                    self.point_2.apply_force(delta_time, -force)
    
    def update(self, delta_time):
        self.shape.position = self.point_1.shape.position
        self.shape.x2, self.shape.y2 = self.point_2.shape.position

class Body:
    def __init__(self, lines, constraint_iterations_override=None, draggable_override=None):
        self.lines = lines

        self._draggable_override = draggable_override

        self.points = []
        for line in self.lines:
            line.draggable_override = self.draggable_override
            if line.point_1 not in self.points:
                self.points.append(line.point_1)
            if line.point_2 not in self.points:
                self.points.append(line.point_2)

        self.max_constraint_iterations = max([line.constraint_iterations for line in self.lines])
        self.constraint_iterations_override = constraint_iterations_override

        objects.append(self)
    
    @property
    def draggable_override(self):
        return self._draggable_override
    
    @draggable_override.setter
    def draggable_override(self, value):
        self._draggable_override = value
        for line in self.lines:
            line.draggable_override = self.draggable_override
    
    @classmethod
    def create_rope(cls, position, sections, length):
        points = []
        for i in range(sections + 1):
            points.append(Point([position[0] + length / sections * i, position[1]], draggable=True))

        lines = []
        for i in range(len(points) - 1):
            lines.append(Line(
                points[i],
                points[i + 1],
            ))
        
        return cls(lines)
    
    @classmethod
    def create_soft_body(cls, position, radius, sides, ring_count=2, spiral=False):
        rings = [[] for i in range(ring_count)]
        rings[0] = [Point(position, draggable=True)]
        lines = []

        radius_between = radius / (ring_count - 1)
        delta_angle = np.pi * 2 / sides
        for i in range(1, ring_count):
            ring_radius = radius_between * i
            spiral_angle = np.pi / 2 / sides * i if spiral else 0
            for j in range(sides):
                angle = delta_angle * j + spiral_angle
                rings[i].append(Point(position + np.array([np.cos(angle), np.sin(angle)]) * ring_radius, draggable=True))
        
        for i in range(1, ring_count):
            for j, point in enumerate(rings[i]):
                point_2_index = j % len(rings[i - 1])
                lines.append(Line(point, rings[i][j - 1]))
                lines.append(Line(point, rings[i - 1][point_2_index]))

        return cls(lines)
    
    def update(self, delta_time):
        for point in self.points:
            point.update(delta_time)

        if self.constraint_iterations_override is None:
            lines_remaining = self.lines.copy()
            for i in range(self.max_constraint_iterations):
                for line in lines_remaining:
                    if i < line.constraint_iterations:
                        line.constrain_points(delta_time)
                    else:
                        lines_remaining.remove(line)
        else:
            for _ in range(self.constraint_iterations_override):
                for line in self.lines:
                    line.constrain_points(delta_time)

class Staple(Body):
    def __init__(self, position, leg_1_length, body_length, leg_2_length, constraint_iterations_override=None, draggable=False):
        self.foot_1 = Point(position, draggable=draggable)
        self.shoulder_1 = Point((position[0], position[1] + leg_1_length), draggable=draggable)
        self.shoulder_2 = Point((position[0] + body_length, position[1] + leg_2_length), draggable=draggable)
        self.foot_2 = Point((position[0] + body_length, position[1]), draggable=draggable)

        self.leg_1_muscle_point = Point((position[0], position[1] + leg_1_length / 2), draggable=draggable)
        self.body_muscle_point = Point((position[0] + body_length / 2, position[1] + (leg_1_length + leg_2_length) / 2), draggable=draggable)
        self.leg_2_muscle_point = Point((position[0] + body_length, position[1] + leg_2_length / 2), draggable=True)

        self.leg_1 = Line(self.foot_1, self.shoulder_1, attached_points=[self.leg_1_muscle_point])
        self.body = Line(self.shoulder_1, self.shoulder_2, attached_points=[self.body_muscle_point])
        self.leg_2 = Line(self.foot_2, self.shoulder_2, attached_points=[self.leg_2_muscle_point])

        self.muscle_1 = Line(self.leg_1_muscle_point, self.body_muscle_point)
        self.muscle_2 = Line(self.leg_2_muscle_point, self.body_muscle_point)

        super().__init__([
            self.leg_1, self.body, self.leg_2,
            self.muscle_1, self.muscle_2
        ], constraint_iterations_override=constraint_iterations_override)

@WINDOW.event
def on_draw():
    WINDOW.clear()

    BATCH.draw()

def update(delta_time):
    if delta_time > 1 / MIN_FPS:
        return
    
    for object in objects:
        object.update(delta_time)
    FPS_TEXT.text = f"FPS: {1 / delta_time:.2f}"

    if keyboard_state[key.W]:
        staple.muscle_1.resting_length += 3
    if keyboard_state[key.S]:
        staple.muscle_1.resting_length -= 3
    if keyboard_state[key.UP]:
        staple.muscle_2.resting_length += 3
    if keyboard_state[key.DOWN]:
        staple.muscle_2.resting_length -= 3

FPS_TEXT = pyglet.text.Label(f"FPS: NaN", font_name="Arial", font_size=36, x=0, y=WINDOW.height, anchor_x="left", anchor_y="top", batch=BATCH)

StaticRectangle((0, 0), (2000, 100))
staple = Staple((1000, 1000), 300, 300, 300, constraint_iterations_override=2)
for _ in range(14):
    Staple((1000, 1000), 10, 10, 10, constraint_iterations_override=2)

pyglet.clock.schedule_interval(update, 1 / MAX_FPS)
pyglet.app.run()