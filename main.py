import numpy as np
import pyglet
from pyglet.window import mouse
from pyglet.window import key

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800
MAX_FPS = 120
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
        [np.array([left, bottom]), np.array([left, top])],
        [np.array([left, top]), np.array([right, top])],
        [np.array([right, top]), np.array([right, bottom])],
        [np.array([right, bottom]), np.array([left, bottom])]
    ]

def get_static_rectangles_intersection(current_position, new_position):
    for object in objects:
        if type(object).__name__ != "StaticRectangle":
            continue

        intersection = get_collision(get_rectangle_sides(object.shape), current_position, new_position)
        if intersection is not None:
            return intersection

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

        if 0 <= line_1_delta_scalar and line_1_delta_scalar <= 1 and 0 <= line_2_delta_scalar and line_2_delta_scalar <= 1:
            return line_1[0] + line_1_delta_scalar * line_1_delta
        
    return None

def get_collision(polygon_sides, current_position, new_position):
    least_distance_intersection = None
    least_distance = None
    for i in range(len(polygon_sides)):
        intersection = get_intersection(polygon_sides[i], [current_position, new_position])
        if intersection is not None:
            distance = np.linalg.norm(intersection - current_position)
            if least_distance_intersection is None or distance < least_distance:
                least_distance_intersection = intersection
                least_distance = distance
    
    return least_distance_intersection

def spring_force(position_1, position_2, resting_length, spring_constant):
    line_vector = position_2 - position_1
    distance = np.linalg.norm(line_vector)

    if not distance:
        return 0
    
    return -line_vector / distance * spring_constant * (resting_length - distance)

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

        self.gravity = gravity
        self.draggable = draggable
        self.selected = False

        objects.append(self)

    @property
    def position(self):
        return np.array(self.shape.position)
    
    @position.setter
    def position(self, value):
        self.shape.position = tuple(value)
    
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
        
        if self.gravity:
            self.apply_force(delta_time, self.gravity_force, use_previous_position=True)

class Line:
    def __init__(self, point_1, point_2, spring_constant=5000, constraint_iterations=10, attached_points=[], attached_points_spring_constant=None, attached_points_constraint_iterations=1, tension=0):
        self.point_1 = point_1
        self.point_2 = point_2
        self.attached_points = attached_points
        # if self.attached_points:
        #     self.attached_point_constraint_1 = Line(self.point_1, Point(self.point_1.position.copy(), self.point_1.mass, 0))
        #     self.attached_point_constraint_2 = Line(self.point_2, Point(self.point_2.position.copy(), self.point_1.mass, 0))

        self._resting_length = np.linalg.norm(self.point_2.position - self.point_1.position)
        self.tension_resting_length = self._resting_length / (1 + tension)

        vertical_axis = self.point_2.position - self.point_1.position
        horizontal_axis = np.array([-vertical_axis[1], vertical_axis[0]])
        axes_matrix = np.column_stack((horizontal_axis, vertical_axis))
        self.attached_points_offsets = [np.linalg.solve(axes_matrix, point.position - self.point_1.position) for point in self.attached_points]
        # self.attached_points_offsets = [(point.position - self.point_1.position) / self.tension_resting_length for point in self.attached_points]

        self.shape = pyglet.shapes.Line(*self.point_1.shape.position, *self.point_2.shape.position, 1, np.array((np.array(self.point_1.shape.color) + np.array(self.point_2.shape.color)) / 2, dtype=int), batch=BATCH)

        self.spring_constant = spring_constant
        self.constraint_iterations = constraint_iterations
        self.attached_points_spring_constant = attached_points_spring_constant if attached_points_spring_constant is not None else self.spring_constant
        self.attached_points_constraint_iterations = attached_points_constraint_iterations

        objects.append(self)
    
    @property
    def tension(self):
        return 1 - self._resting_length / self.tension_resting_length

    @tension.setter
    def tension(self, value):
        self.tension_resting_length = self._resting_length / (1 + value)

    @property
    def resting_length(self):
        return self._resting_length

    @resting_length.setter
    def resting_length(self, value):
        self.tension_resting_length = value / (1 + self.tension)
        self._resting_length = value
        self.attached_points_offsets = [(point.position - self.point_1.position) / self.tension_resting_length for point in self.attached_points]

    def constrain_points(self, delta_time):
        # new_b = a1 + t(a2 - a1)

        distance = np.linalg.norm(self.point_2.position - self.point_1.position)
        if distance:
            force = spring_force(self.point_1.position, self.point_2.position, self.tension_resting_length, self.spring_constant)
            self.point_1.apply_force(delta_time, force)
            self.point_2.apply_force(delta_time, -force)

            # line_vector = self.point_2.position - self.point_1.position
            # distance = np.linalg.norm(line_vector)
            # normalized_line_vector = line_vector / distance
            vertical_axis = self.point_2.position - self.point_1.position
            horizontal_axis = np.array([-vertical_axis[1], vertical_axis[0]])
            axes_matrix = np.column_stack((horizontal_axis, vertical_axis))
            for _ in range(self.attached_points_constraint_iterations):
                for attached_point, offset in zip(self.attached_points, self.attached_points_offsets):
                    # (attached_point.position - point_1.position) / distance = offset
                    # force = spring_force(attached_point.position, self.point_1.position + offset * (self.point_2.position - self.point_1.position), 0, self.spring_constant)
                    force = spring_force(attached_point.position, self.point_1.position + np.matmul(axes_matrix, offset), 0, self.attached_points_spring_constant)
                    attached_point.apply_force(delta_time, force * 5)
                    self.point_1.apply_force(delta_time, -force)
                    self.point_2.apply_force(delta_time, -force)

        # f(2.5) = 60.26
        # f(2) = 140.26
        #

        # f(2.5) = 0.6026
        # f(2) = 0.5
        # f(1.5) = 1.6714
        # f(1) = 2
        # f(0.5) = 3
        # f(0) = infinity
        # f(x) = 

        # line_vector = self.point_2.position - self.point_1.position
        # normalized_line_vector = line_vector / np.linalg.norm(line_vector)
        # target_length_change = self.tension_resting_length / 2 * normalized_line_vector - line_vector
        # target_point_1_position = self.point_1.position - target_length_change

        # distance = np.linalg.norm(target_point_1_position - self.point_1.position)

        # if distance:
        #     force = (self.point_1.position - target_point_1_position) / distance * self.spring_constant * (self.tension_resting_length / 2 - distance)
        #     self.point_1.apply_force(delta_time, force)
        #     self.point_2.apply_force(delta_time, -force)
        
        # new_b  = a1 + t(a2 - a1)
        # new_a1 = b - t(a2 - a1)
        # new_a2 = b + (1 - t)(a2 - a1)

        # target_point_1 = self.point_1.position - (self.tension_resting_length - np.linalg.norm(self.point_2.position - self.point_1.position)) / 2

        # distance = np.linalg.norm((np.linalg.norm(self.point_2.position - self.point_1.position - self.tension_resting_length)) / 2)

        # if distance:
        #     force = (self.point_1.position - target_point_1) / distance * self.spring_constant * (self.tension_resting_length - distance)
        #     self.point_1.apply_force(delta_time, force)
        #     self.point_2.apply_force(delta_time, -force)

        # distance = np.linalg.norm(self.point_2.position - self.point_1.position)
        # imaginary line parallel to this line but lines up with attached point, spring between corresponding ends of real and imaginary lines
        # if distance:
        #     force = (self.point_1.position - self.point_2.position) / distance * self.spring_constant * (self.tension_resting_length - distance)
        #     # self.point_1.apply_force(delta_time, force + self.point_1_position + offset * distance)
        #     self.point_1.apply_force(delta_time, force)
        #     self.point_2.apply_force(delta_time, -force)

        #     new_distance = np.linalg.norm(self.point_2.position - self.point_1.position)

        #     for point, offset in zip(self.attached_points, self.attached_points_offsets):
        #         position = point.position
                
        #         # self.attached_point_constraint_1.point_2.move_to(position - offset * new_distance, collides=False)
        #         # self.attached_point_constraint_2.point_2.move_to(position - offset * new_distance + new_distance, collides=False)
        #         # self.attached_point_constraint_1.constrain_points(delta_time)
        #         # self.attached_point_constraint_2.constrain_points(delta_time)
                

        #     # for point, offset in zip(self.attached_points, self.attached_points_offsets):
        #     #     point.move_to(self.point_1.position + offset * distance)
    
    def update(self, delta_time):
        self.shape.position = self.point_1.shape.position
        self.shape.x2, self.shape.y2 = self.point_2.shape.position

class Body:
    def __init__(self, lines, constraint_iterations_override=None):
        self.lines = lines

        self.points = []
        for line in self.lines:
            if not line.point_1 in self.points:
                self.points.append(line.point_1)
            if not line.point_2 in self.points:
                self.points.append(line.point_2)

        self.max_constraint_iterations = max([line.constraint_iterations for line in self.lines])
        self.constraint_iterations_override = constraint_iterations_override

        objects.append(self)
    
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
            for i in range(self.constraint_iterations_override):
                for line in self.lines:
                    line.constrain_points(delta_time)

class Staple(Body):
    def __init__(self, position, width, height, constraint_iterations_override=None):
        self.foot_1 = Point(position, draggable=True)
        self.shoulder_1 = Point((position[0], position[1] + height), draggable=True)
        self.shoulder_2 = Point((position[0] + width, position[1] + height), draggable=True)
        self.foot_2 = Point((position[0] + width, position[1]), draggable=True)

        self.leg_1_muscle_point = Point((position[0], position[1] + height / 2), draggable=True)
        self.body_muscle_point = Point((position[0] + width / 2, position[1] + height), draggable=True)
        self.leg_2_muscle_point = Point((position[0] + width, position[1] + height / 2), draggable=True)

        self.leg_1 = Line(self.foot_1, self.shoulder_1, attached_points=[self.leg_1_muscle_point])
        self.body = Line(self.shoulder_1, self.shoulder_2, attached_points=[self.body_muscle_point])
        self.leg_2 = Line(self.foot_2, self.shoulder_2, attached_points=[self.leg_2_muscle_point])

        self.muscle_1 = Line(self.leg_1_muscle_point, self.body_muscle_point)
        self.muscle_2 = Line(self.leg_2_muscle_point, self.body_muscle_point)

        # self.leg_1_muscle_point_connection_1 = Line(self.foot_1, self.leg_1_muscle_point, tension=0.03)
        # self.leg_1_muscle_point_connection_2 = Line(self.shoulder_1, self.leg_1_muscle_point, tension=0.03)
        # self.body_muscle_point_connection_1 = Line(self.shoulder_1, self.body_muscle_point, tension=0.03)
        # self.body_muscle_point_connection_2 = Line(self.shoulder_2, self.body_muscle_point, tension=0.03)
        # self.leg_2_muscle_point_connection_1 = Line(self.foot_2, self.leg_2_muscle_point, tension=0.03)
        # self.leg_2_muscle_point_connection_2 = Line(self.shoulder_2, self.leg_2_muscle_point, tension=0.03)

        super().__init__([
            self.leg_1, self.body, self.leg_2,
            self.muscle_1, self.muscle_2,
            # self.leg_1_muscle_point_connection_1, self.leg_1_muscle_point_connection_2,
            # self.body_muscle_point_connection_1, self.body_muscle_point_connection_2,
            # self.leg_2_muscle_point_connection_1, self.leg_2_muscle_point_connection_2
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
    FPS_TEXT.text = f"FPS: {1 / delta_time * 1000}"

    if keyboard_state[key.UP]:
        staple.muscle_1.resting_length += 4
    if keyboard_state[key.DOWN]:
        staple.muscle_1.resting_length -= 4

FPS_TEXT = pyglet.text.Label(f"FPS: {MAX_FPS}", font_name="Arial", anchor_x="left", anchor_y="top", batch=BATCH)

StaticRectangle((0, 0), (2000, 100))
# for i in range(10):
#     Staple((0, 1000), 100, 100, constraint_iterations_override=1)
staple = Staple((1000, 1000), 300, 300)#, constraint_iterations_override=1)
# staple = Body.create_rope((200, 200), 1, 100)
# Body.create_rope((400, 200), 1, 100)

pyglet.clock.schedule_interval(update, 1 / MAX_FPS)
pyglet.app.run()