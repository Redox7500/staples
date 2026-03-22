import pyglet
from pyglet.window import mouse
import numpy as np

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800
MAX_FPS = 120

WINDOW = pyglet.window.Window(width=1000, height=600, caption="staple")
BATCH = pyglet.graphics.Batch()

mouse_state = mouse.MouseStateHandler()
WINDOW.push_handlers(mouse_state)

objects = []
delta_time = 1000 / MAX_FPS

def is_within(value, end_1, end_2):
    return value > min(end_1, end_2) and value < max(end_1, end_2)

# def get_static_rectangles_intersection(position, new_position):
#     for object in objects:
#         if type(object).__name__ != "StaticRectangle":
#             continue

#         shape = object.shape

#         clipped_line = clipline(shape, [position, new_position])
#         if clipped_line.size != 0:
#             return clipped_line[0]

#     return None

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

# (b2 - b1) / (m1 - m2) = x
# -b / m = mx

# def get_intersection(line_1, line_2):
#     line_1_horizontal = line_1[0][0] == line_1[1][0]
#     line_1_vertical = line_1[0][1] == line_1[1][1]
#     line_2_horizontal = line_2[0][0] == line_2[0][0]
#     line_2_vertical = line_2[0][1] == line_2[1][1]
    
#     if (line_1_horizontal and line_2_horizontal) or (line_1_vertical and line_2_vertical):
#         return None
#     if line_1_horizontal:
#         line_2_vector = line_2[1] - line_2[0]
#         dy = line_2[0][1] - 0
#         return line_2[0] + line_2_vector * dy / line_2_vector[1]
#     if line_1_vertical:
#         line_2_vector = line_2[1] - line_2[0]
#         dx = line_2[0][0] - 0
#         return line_2[0] + line_2_vector * dx / line_2_vector[0]
#     if line_2_horizontal:
#         line_1_vector = line_1[1] - line_1[0]
#         dy = line_1[0][1] - 0
#         return line_1[0] + line_1_vector * dy / line_1_vector[1]
#     if line_2_vertical:
#         line_1_vector = line_1[1] - line_1[0]
#         dx = line_1[0][0] - 0
#         return line_1[0] + line_1_vector * dx / line_1_vector[0]

#     m_1 = (line_1[1][1] - line_1[0][1]) / (line_1[1][0] - line_1[0][0])
#     m_2 = (line_2[1][1] - line_2[0][1]) / (line_2[1][0] - line_2[0][0])

#     b_1 = line_1[0][1] - line_1[0][0] * m_1
#     b_2 = line_2[0][1] - line_2[0][0] * m_2

#     m_difference = m_2 - m_1
    
#     if m_difference == 0:
#         return None

#     b_difference = b_1 - b_2

#     x = b_difference / m_difference

#     line_1_min_x = min(line_1[0][0], line_1[1][0])
#     line_2_min_x = min(line_2[0][0], line_2[1][0])
#     range_min = max(line_1_min_x, line_2_min_x)

#     line_1_max_x = max(line_1[0][0], line_1[1][0])
#     line_2_max_x = max(line_2[0][0], line_2[1][0])
#     range_max = min(line_1_max_x, line_2_max_x)

#     if is_within(x, range_min, range_max):
#         return [x, x * m_1 + b_1]
#     else:
#         return None

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
    # line_1_vector = line_1[1] - line_1[0]
    # line_2_vector = line_2[1] - line_1[0]

    # cross_product_1 = cross_product(line_2[0] - line_1[0], line_2_vector)
    # cross_product_2 = cross_product(line_2[0] - line_1[0], line_1_vector)
    # cross_product_3 = cross_product(line_1_vector, line_2_vector)

    # if cross_product_3 == 0:
    #     if cross_product_2 == 0:
    #         # collinear
    #         return None
    # else:
    #     line_1_delta_scalar = cross_product_1 / cross_product_3
    #     line_2_delta_scalar = cross_product_2 / cross_product_3
    #     if line_1_delta_scalar >= 0 and line_1_delta_scalar <= 1 and line_2_delta_scalar >= 0 and line_2_delta_scalar <= 1:
    #         return line_1[0] + line_1_vector * line_1_delta_scalar
        
    return None

# def clipline(rectangle, line):
#     top_coordinate = rectangle.y + rectangle.height
#     right_coordinate = rectangle.x + rectangle.width
#     bottom_coordinate = rectangle.y
#     left_coordinate = rectangle.x

#     is_point_1_inside = is_within(line[0][0], top_coordinate, bottom_coordinate) and is_within(line[0][1], right_coordinate, left_coordinate)
#     is_point_2_inside = is_within(line[1][0], top_coordinate, bottom_coordinate) and is_within(line[1][1], right_coordinate, left_coordinate)

#     if is_point_1_inside and is_point_2_inside:
#         return line.copy()

#     top_side = np.array([[left_coordinate, top_coordinate], [right_coordinate, top_coordinate]])
#     right_side = np.array([[right_coordinate, top_coordinate], [right_coordinate, bottom_coordinate]])
#     bottom_side = np.array([[right_coordinate, bottom_coordinate], [left_coordinate, bottom_coordinate]])
#     left_side = np.array([[left_coordinate, bottom_coordinate], [left_coordinate, top_coordinate]])

#     top_intersection = get_intersection(line, top_side)
#     right_intersection = get_intersection(line, right_side)
#     bottom_intersection = get_intersection(line, bottom_side)
#     left_intersection = get_intersection(line, left_side)

#     intersections = [top_intersection, right_intersection, bottom_intersection, left_intersection]
#     intersections = [intersection for intersection in intersections if intersection != None]

#     if len(intersections) == 2:
#         if np.linalg.norm(intersections[0] - line[0]) < np.linalg.norm(intersections[1] - line[0]):
#             return np.array([intersections[0], intersections[1]])
#         else:
#             return np.array([intersections[1], intersections[0]])
#     elif len(intersections) == 1:
#         if is_point_1_inside:
#             return np.array([line[0], intersections[0]])
#         else:
#             return np.array([intersections[0], line[1]])
#     else:
#         return np.empty(0)

def get_collision(polygon_sides, current_position, new_position):
    least_distance_intersection = None
    least_distance = None
    for i in range(len(polygon_sides)):
        intersection = get_intersection(polygon_sides[i], [current_position, new_position])
        if not intersection is None:
            distance = np.linalg.norm(intersection - current_position)
            if least_distance_intersection is None or distance < least_distance:
                least_distance_intersection = i
                least_distance = distance
    
    return least_distance_intersection

class StaticRectangle:
    def __init__(self, position, size, color=(255, 255, 255)):
        self.shape = pyglet.shapes.Rectangle(*position, *size, color=color, batch=BATCH)
        
        objects.append(self)

    def update(self, delta_time):
        ...

class Point:
    def __init__(self, position, mass=100, radius=10, color=(255, 255, 255), draggable=False):
        self.previous_position = np.array(position)

        self.mass = mass
        self.gravity_force = np.array([0, -500 * self.mass])

        self.shape = pyglet.shapes.Circle(position[0], position[1], radius, color=color, batch=BATCH)

        self.draggable = draggable
        self.selected = False

        objects.append(self)

    @property
    def position(self):
        return np.array(self.shape.position)
    
    @position.setter
    def position(self, value):
        self.shape.position = tuple(value)
    
    def move_to(self, new_position, prioritize=False):
        if not(self.selected) or prioritize:
            self.previous_position = self.position
            intersection = get_static_rectangles_intersection(self.position, new_position)
            if intersection is None:
                self.position = new_position
            else:
                vector = intersection - self.position
                radius_vector = vector / np.linalg.norm(vector) * (self.shape.radius + 1)
                self.position = intersection - radius_vector
    
    def apply_force(self, delta_time, force, prioritize=False, use_previous_position=False):
        if not(self.selected) or prioritize:
            new_position = self.position + force / self.mass * delta_time ** 2

            if use_previous_position:
                new_position += self.position - self.previous_position
                self.previous_position = self.position.copy()

            intersection = get_static_rectangles_intersection(self.position, new_position)
            if intersection is None:
                self.position = new_position
            else:
                vector = intersection - self.position
                radius_vector = vector / np.linalg.norm(vector) * (self.shape.radius + 1)
                self.position = intersection - radius_vector
    
    def update(self, delta_time):
        if self.draggable:
            if mouse_state[mouse.LEFT]:
                if np.linalg.norm(np.array([mouse_state.x, mouse_state.y]) - self.position) < self.shape.radius:
                    self.selected = True
            else:
                self.selected = False

            if self.selected:
                self.move_to(np.array([mouse_state.x, mouse_state.y]), prioritize=True)

        self.apply_force(delta_time, self.gravity_force, use_previous_position=True)

class Line:
    def __init__(self, point_1, point_2, attached_points=[], spring_constant=0.1, constraint_iterations=200):
        self.point_1 = point_1
        self.point_2 = point_2
        self.attached_points = attached_points
        self.attached_point_offsets = [point.position - self.point_1.position for point in self.attached_points]

        self.resting_length = np.linalg.norm(self.point_2.position - self.point_1.position)
        self.color = (np.array(self.point_1.color) + np.array(self.point_2.color)) / 2

        self.shape = pyglet.shapes.Line(*self.point_1.position, *self.point_2.position, 1, self.color, batch=BATCH)

        self.spring_constant = spring_constant
        self.constraint_iterations = constraint_iterations

        objects.append(self)

    def constrain_points(self, delta_time):
        distance = np.linalg.norm(self.point_2.position - self.point_1.position)
        if distance:
            force = (self.point_1.position - self.point_2.position) / distance * self.spring_constant * (self.resting_length - distance)
            self.point_1.apply_force(delta_time, force)
            self.point_2.apply_force(delta_time, -force)
        
            for point, offset in zip(self.attached_points, self.attached_point_offsets):
                point.move_to(self.point_1.position + offset)
    
    def update(self, delta_time):
        self.shape.position = self.point_1.position
        self.shape.x1, self.shape.y1 = self.point_2.position

class Body:
    def __init__(self, lines):
        self.lines = lines

        self.points = []
        for line in self.lines:
            if not line.point_1 in self.points:
                self.points.append(line.point_1)
            if not line.point_2 in self.points:
                self.points.append(line.point_2)

        self.max_constraint_iterations = max([line.constraint_iterations for line in self.lines])

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
        position = np.array(position)
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

        # constraint_iterations = [line.constraint_iterations for line in self.lines]
        # sorted_indices = np.argsort(constraint_iterations)
        # while len(sorted_indices):
        #     for i in range(self.lines[sorted_indices[0]].constraint_iterations):
        #         [self.lines[line_index].constrain_points(screen, events, delta_time) for line_index in sorted_indices]

        #     sorted_indices = sorted_indices[1:]

        lines_remaining = self.lines.copy()
        for i in range(self.max_constraint_iterations):
            for line in lines_remaining:
                if i < line.constraint_iterations:
                    line.constrain_points(delta_time)
                else:
                    lines_remaining.remove(line)
        
        # for line in self.lines:
        #     line.update(delta_time)

        #     line.point_1.update(delta_time)
        #     line.point_2.update(delta_time)
            
        # for i in range(self.max_constraint_iterations):
        #     for line in self.lines:
        #         if i < line.constraint_iterations:
        #             line.constrain_points(screen, events, delta_time)


@WINDOW.event
def on_draw():
    WINDOW.clear()

    BATCH.draw()

def update(delta_time):
    for object in objects:
        object.update(delta_time)
    FPS_TEXT.text = f"FPS: {1 / delta_time * 1000}"

FPS_TEXT = pyglet.text.Label(f"FPS: {MAX_FPS}", font_name="Arial", anchor_y="top", batch=BATCH)

StaticRectangle((0, 0), (2000, 100))
Point((100, 1000), radius=50, draggable=True)

pyglet.clock.schedule_interval(update, 1 / MAX_FPS)
pyglet.app.run()