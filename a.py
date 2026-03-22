import pygame
from pygame import gfxdraw
import numpy as np
import time

pygame.init()
screen_width = 1000
screen_height = 600
screen = pygame.display.set_mode((screen_width, screen_height))
running = True
clock = pygame.time.Clock()
max_fps = 120
delta_time = 1000 / max_fps
static_rectangles = []
start_time = time.time()

def aacircle(screen, x, y, radius, color):
    if x + radius < 0 or y + radius < 0 or x - radius > screen_width or y - radius > screen_height:
        return
    
    gfxdraw.aacircle(screen, int(x), int(y), radius, color)
    gfxdraw.filled_circle(screen, int(x), int(y), radius, color)

def get_static_rectangles_intersection(position, new_position, static_rectangles):
    for static_rectangle in static_rectangles:
        rect = static_rectangle.rect

        clipped_line = rect.clipline(position, new_position)
        if clipped_line:
            clipped_line_vector = pygame.Vector2(clipped_line[0])
            return clipped_line_vector

    return None

class Point:
    def __init__(self, x, y, mass=1, radius=8, color=(255, 255, 255), moveable=False):
        self.position = pygame.Vector2(x, y)
        self.previous_position = self.position.copy()

        self.mass = mass
        self.gravity_force = pygame.Vector2(0, 0.001 * self.mass)

        self.radius = radius
        self.color = color

        self.moveable = moveable
        self.selected = False
    
    def move_to(self, new_position, prioritize=False):
        if not(self.selected) or prioritize:
            intersection = get_static_rectangles_intersection(self.position, new_position, static_rectangles)

            self.previous_position = self.position.copy()
            if not intersection:
                self.position = new_position
    
    def apply_force(self, delta_time, force, use_previous_position=False, prioritize=False):
        if not(self.selected) or prioritize:
            new_position = self.position + force / self.mass * delta_time ** 2

            if use_previous_position:
                new_position += self.position - self.previous_position
                self.previous_position = self.position.copy()

            intersection = get_static_rectangles_intersection(self.position, new_position, static_rectangles)
            if not intersection:
                self.position = new_position
    
    def update(self, screen, events, delta_time):
        mouse_position = pygame.Vector2(pygame.mouse.get_pos())

        if self.moveable:
            for event in events:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == pygame.BUTTON_LEFT and np.linalg.norm(np.array(mouse_position) - np.array(self.position)) < 10:
                    self.selected = True
                if event.type == pygame.MOUSEBUTTONUP and event.button == pygame.BUTTON_LEFT:
                    self.selected = False

        if self.selected:
            self.move_to(mouse_position, prioritize=True)

        self.apply_force(delta_time, self.gravity_force, use_previous_position=True)
    
    def draw(self, screen, events, delta_time):
        aacircle(screen, *self.position, self.radius, self.color)

class StaticRectangle:
    def __init__(self, x, y, width, height, color=(255, 255, 255)):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color

    def update(self, screen, events, delta_time):
        pygame.draw.rect(screen, self.color, self.rect)

class Body:
    def __init__(self, points, connections, spring_constant=0.001, constraint_iterations=1000):
        self.points = points
        self.connections = []

        for point_index in range(len(self.points)):
            point = self.points[point_index]

            self.connections.append([])

            for neighbor_index in range(len(self.points)):
                neighbor = self.points[neighbor_index]

                self.connections[point_index].append(connections[point_index][neighbor_index] * point.position.distance_to(neighbor.position))

        self.spring_constant = spring_constant
        self.constraint_iterations = constraint_iterations
    
    def update(self, screen, events, delta_time):
        for point in self.points:
            point.update(screen, events, delta_time)

        for _ in range(self.constraint_iterations):
            for point_index in range(len(self.points)):
                point = self.points[point_index]

                for neighbor_index in range(len(self.points)):
                    length = self.connections[point_index][neighbor_index]
                    if length:
                        neighbor = self.points[neighbor_index]

                        points_distance = point.position.distance_to(neighbor.position)
                        if points_distance:
                            force = (point.position - neighbor.position) / points_distance * self.spring_constant * (length - points_distance)
                            point.apply_force(delta_time, force)
                            neighbor.apply_force(delta_time, -force)

    def draw(self, screen, events, delta_time):
        for point_index in range(len(self.points)):
            point = self.points[point_index]

            for neighbor_index in range(len(self.points)):
                if self.connections[point_index][neighbor_index]:
                    neighbor = self.points[neighbor_index]

                    pygame.draw.aaline(screen, (np.array(point.color) + np.array(neighbor.color)) / 2, point.position, neighbor.position)

        for point in self.points:
            point.draw(screen, events, delta_time)

body = Body([
    Point(0, 0, color=(255, 0, 0), moveable=True),
    Point(100, 0, color=(255, 255, 0), moveable=True),
    Point(100, 100, color=(0, 255, 0), moveable=True),
    Point(0, 100, color=(0, 0, 255), moveable=True),
], [
    [0, 1, 0, 1],
    [1, 0, 1, 0],
    [0, 1, 0, 1],
    [1, 0, 1, 0]
])
static_rectangles.append(StaticRectangle(-5000, 500, 10000, 100))

while running:
    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            running = False

    screen.fill("#222230")
    body.update(screen, events, delta_time)
    body.draw(screen, events, delta_time)

    for static_rectangle in static_rectangles:
        static_rectangle.update(screen, events, delta_time)

    pygame.display.flip()
    delta_time = clock.tick()

pygame.quit()