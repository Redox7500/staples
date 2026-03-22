import pygame
# from pygame import gfxdraw
import numpy as np

pygame.init()
pygame.font.init()

ARIAL = pygame.font.SysFont("Arial", 30)

SCREEN_WIDTH = 1600
SCREEN_HEIGHT = 800
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

CLOCK = pygame.time.Clock()
MAX_FPS = 1000
running = True
delta_time = 1000 / MAX_FPS

def aacircle(screen, position, radius, color):
    position = np.array(position, dtype=int)
    if position[0] + radius < 0 or position[0] + radius < 0 or position[1] - radius > SCREEN_WIDTH or position[1] - radius > SCREEN_HEIGHT:
        return
    
    # gfxdraw.aacircle(screen, *position, radius, color)
    # gfxdraw.filled_circle(screen, *position, radius, color)
    pygame.draw.circle(screen, color, position, radius)

# def get_static_rectangles_intersection(scene, position, new_position):
#     for object in scene.objects:
#         if type(object).__name__ != "StaticRectangle":
#             continue

#         rect = object.rect

#         clipped_line = rect.clipline(position, new_position)
#         if clipped_line:
#             return np.array(clipped_line[0])

#     return None

def is_within(value, end_1, end_2):
    return value > min(end_1, end_2) and value < max(end_1, end_2)

def get_intersection(line_1, line_2):
    m_1_numerator = (line_1[1][1] - line_1[0][1])
    m_2_numerator = (line_2[1][1] - line_2[0][1])
    m_1_denominator = (line_1[1][0] - line_1[0][0])
    m_2_denominator = (line_2[1][0] - line_2[0][0])

    if m_1_denominator == 0:
        if m_2_denominator == 0:
            return None
        if is_within(line_1[0][0], line_2[0][0], line_2[1][0]):
            return [line_1[0][0], line_2[0][1] - line_2[0][0] * m_2_numerator / m_2_denominator]
        else:
            return None
    if m_2_denominator == 0:
        if m_1_denominator == 0:
            return None
        if is_within(line_2[0][0], line_1[0][0], line_1[1][0]):
            return [line_2[0][0], line_1[0][1] - line_1[0][0] * m_1_numerator / m_1_denominator]
        else:
            return None
        
    m_1 = m_1_numerator / m_1_denominator
    m_2 = m_2_numerator / m_2_denominator
    
    m_difference = m_2 - m_1

    if m_difference == 0:
        return None

    b_1 = line_1[0][1] - line_1[0][0] * m_1
    b_2 = line_2[0][1] - line_2[0][0] * m_2

    b_difference = b_1 - b_2

    x = b_difference / m_difference

    line_1_min_x = min(line_1[0][0], line_1[1][0])
    line_2_min_x = min(line_2[0][0], line_2[1][0])
    range_min = max(line_1_min_x, line_2_min_x)

    line_1_max_x = max(line_1[0][0], line_1[1][0])
    line_2_max_x = max(line_2[0][0], line_2[1][0])
    range_max = min(line_1_max_x, line_2_max_x)

    if is_within(x, range_min, range_max):
        return [x, x * m_1 + b_1]
    else:
        return None
    
# print(get_intersection(np.array([[1, 1], [1, -1]])))

def clipline(rectangle, line):
    # top_coordinate = rectangle.top
    # right_coordinate = rectangle.right
    # bottom_coordinate = rectangle.bottom
    # left_coordinate = rectangle.left

    is_point_1_inside = is_within(line[0][0], rectangle.left, rectangle.right) and is_within(line[0][1], rectangle.top, rectangle.bottom)
    is_point_2_inside = is_within(line[1][0], rectangle.left, rectangle.right) and is_within(line[1][1], rectangle.top, rectangle.bottom)

    if is_point_1_inside and is_point_2_inside:
        return line.copy()

    # top_side = np.array([[left_coordinate, top_coordinate], [right_coordinate, top_coordinate]])
    # right_side = np.array([[right_coordinate, top_coordinate], [right_coordinate, bottom_coordinate]])
    # bottom_side = np.array([[right_coordinate, bottom_coordinate], [left_coordinate, bottom_coordinate]])
    # left_side = np.array([[left_coordinate, bottom_coordinate], [left_coordinate, top_coordinate]])

    # top_intersection = get_intersection(line, top_side)
    # right_intersection = get_intersection(line, right_side)
    # bottom_intersection = get_intersection(line, bottom_side)
    # left_intersection = get_intersection(line, left_side)
    sides = [
        np.array([rectangle.topleft, rectangle.topright]),
        np.array([rectangle.topright, rectangle.bottomright]),
        np.array([rectangle.bottomright, rectangle.bottomleft]),
        np.array([rectangle.bottomleft, rectangle.topleft])
    ]

    intersections = []
    for side in sides:
        intersection = get_intersection(line, side)
        if intersection != None:
            intersections.append(intersection)

    # intersections = np.array([top_intersection, right_intersection, bottom_intersection, left_intersection])
    # # intersections = intersections[np.array([intersection.size > 0 for intersection in intersections])]
    # # intersections = list(filter(lambda x: x is not None, intersections))
    # intersections = intersections[intersections != None]

    if len(intersections) == 2:
        if np.linalg.norm(intersections[0] - line[0]) < np.linalg.norm(intersections[1] - line[0]):
            return np.array([intersections[0], intersections[1]])
        else:
            return np.array([intersections[1], intersections[0]])
    elif len(intersections) == 1:
        if is_point_1_inside:
            return np.array([line[0], intersections[0]])
        else:
            return np.array([intersections[0], line[1]])
    else:
        return np.empty(0)

def get_static_rectangles_intersection(scene, position, new_position):
    for object in scene.objects:
        if type(object).__name__ != "StaticRectangle":
            continue

        rect = object.rect

        clipped_line = clipline(rect, np.array([position, new_position]))
        if list(clipped_line):
            return np.array(clipped_line[0])
    
    return None

class Scene:
    def __init__(self, objects=[]):
        self.objects = objects
    
    def update(self, screen, events, delta_time):
        for object in self.objects:
            object.update(screen, events, delta_time)
    
    def draw(self, screen, events, delta_time):
        for object in self.objects:
            object.draw(screen, events, delta_time)

class StaticRectangle:
    def __init__(self, position, size, color=(255, 255, 255)):
        self.rect = pygame.Rect(*position, *size)
        self.color = color

    def update(self, screen, events, delta_time):
        ...
    
    def draw(self, screen, events, delta_time):
        pygame.draw.rect(screen, self.color, self.rect)

class Point:
    def __init__(self, position, mass=100, radius=10, color=(255, 255, 255), draggable=False):
        self.position = np.array(position)
        self.previous_position = self.position.copy()

        self.mass = mass
        self.gravity_force = np.array([0, 0.0005 * self.mass])

        self.radius = radius
        self.color = color

        self.draggable = draggable
        self.selected = False
    
    def move_to(self, new_position, prioritize=False):
        if not(self.selected) or prioritize:
            self.previous_position = self.position.copy()
            intersection = get_static_rectangles_intersection(scene, self.position, new_position)
            if intersection is None:
                self.position = new_position
            # else:
            #     vector = intersection - self.position
            #     radius_vector = np.linalg.norm(vector) * self.radius
            #     self.position = intersection - radius_vector
    
    def apply_force(self, screen, events, delta_time, force, use_previous_position=False, prioritize=False):
        if not(self.selected) or prioritize:
            new_position = self.position + force / self.mass * delta_time ** 2

            if use_previous_position:
                new_position += self.position - self.previous_position
                self.previous_position = self.position.copy()

            intersection = get_static_rectangles_intersection(scene, self.position, new_position)
            print(intersection)
            if intersection is None:
                self.position = new_position
            # else:
            #     vector = intersection - self.position
            #     radius_vector = vector / np.linalg.norm(vector) * self.radius
            #     self.position = intersection - radius_vector
    
    def update(self, screen, events, delta_time):
        mouse_position = np.array(pygame.mouse.get_pos())

        if self.draggable:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT and np.linalg.norm(np.array(mouse_position) - np.array(self.position)) < self.radius:
                    self.selected = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_LEFT:
                    self.selected = False

        if self.selected:
            self.move_to(mouse_position, prioritize=True)

        self.apply_force(screen, events, delta_time, self.gravity_force, use_previous_position=True)
    
    def draw(self, screen, events, delta_time):
        aacircle(screen, self.position, self.radius, self.color)

class Line:
    def __init__(self, point_1, point_2, attached_points=[], spring_constant=0.1, constraint_iterations=100):
        self.point_1 = point_1
        self.point_2 = point_2
        self.attached_points = attached_points
        self.attached_point_offsets = [point.position - self.point_1.position for point in self.attached_points]

        self.resting_length = np.linalg.norm(self.point_2.position - self.point_1.position)
        self.color = (np.array(self.point_1.color) + np.array(self.point_2.color)) / 2

        self.spring_constant = spring_constant
        self.constraint_iterations = constraint_iterations

    def constrain_points(self, screen, events, delta_time):
        distance = np.linalg.norm(self.point_2.position - self.point_1.position)
        if distance:
            force = (self.point_1.position - self.point_2.position) / distance * self.spring_constant * (self.resting_length - distance)
            self.point_1.apply_force(screen, events, delta_time, force)
            self.point_2.apply_force(screen, events, delta_time, -force)
        
            for point, offset in zip(self.attached_points, self.attached_point_offsets):
                point.move_to(self.point_1.position + offset)
    
    def draw(self, screen, events, delta_time):
        pygame.draw.aaline(screen, self.color, self.point_1.position, self.point_2.position)

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
    
    def update(self, screen, events, delta_time):
        for point in self.points:
            point.update(screen, events, delta_time)

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
                    line.constrain_points(screen, events, delta_time)
                else:
                    lines_remaining.remove(line)
            
        # for i in range(self.max_constraint_iterations):
        #     for line in self.lines:
        #         if i < line.constraint_iterations:
        #             line.constrain_points(screen, events, delta_time)

    def draw(self, screen, events, delta_time):
        for line in self.lines:
            line.draw(screen, events, delta_time)

            line.point_1.draw(screen, events, delta_time)
            line.point_2.draw(screen, events, delta_time)

# points = [
#     Point(0, 0, color=(255, 0, 0), draggable=True),
#     Point(100, 0, color=(255, 0, 0), draggable=True),
#     Point(100, 100, color=(0, 0, 255), draggable=True),
#     Point(0, 100, color=(0, 0, 255), draggable=True),
#     Point(50, 50, color=(255, 255, 0), draggable=True)
# ]
# body = Body([
#     Line(
#         points[0],
#         points[1]
#     ),
#     Line(
#         points[1],
#         points[2]
#     ),
#     Line(
#         points[2],
#         points[3]
#     ),
#     Line(
#         points[3],
#         points[0]
#     ),
#     Line(
#         points[0],
#         points[4]
#     ),
#     Line(
#         points[1],
#         points[4]
#     ),
#     Line(
#         points[2],
#         points[4]
#     ),
#     Line(
#         points[3],
#         points[4]
#     )
# ])
scene = Scene()
scene.objects.append(Body.create_soft_body([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2], 150, 3))

wall_width = 1
scene.objects.append(StaticRectangle([0, SCREEN_HEIGHT - wall_width], [SCREEN_WIDTH, wall_width]))
scene.objects.append(StaticRectangle([0, 0], [wall_width, SCREEN_HEIGHT]))
scene.objects.append(StaticRectangle([SCREEN_WIDTH - wall_width, 0], [wall_width, SCREEN_HEIGHT]))
scene.objects.append(StaticRectangle([0, 0], [SCREEN_WIDTH, wall_width]))

while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    SCREEN.fill("#222230")
    scene.update(SCREEN, events, delta_time)
    scene.draw(SCREEN, events, delta_time)
    
    SCREEN.blit(ARIAL.render(f"{1000 / delta_time:.2f} fps", True, (255, 255, 255)), (0, 0))

    pygame.display.flip()
    delta_time = CLOCK.tick(MAX_FPS)

pygame.quit()