import numpy as np
import pyglet
from pyglet.window import mouse
from pyglet.window import key

from neural_networks import NeuralNetwork

SCREEN_WIDTH  = 3200
SCREEN_HEIGHT = 1600
MAX_FPS = 60
MIN_FPS = 10

WINDOW = pyglet.window.Window(width=SCREEN_WIDTH / 2, height=SCREEN_HEIGHT / 2, caption="inverted pendulum")
BATCH = pyglet.graphics.Batch()

mouse_state    = mouse.MouseStateHandler()
keyboard_state = key.KeyStateHandler()
WINDOW.push_handlers(mouse_state)
WINDOW.push_handlers(keyboard_state)

objects = []

def apply_force(delta_time, current_position, previous_position, force, mass, drag=0):
    a = 2 * current_position - previous_position
    b = 1 / mass * delta_time ** 2
    new_position_no_drag = a + force * b
    if drag == 0:
        return new_position_no_drag
    
    velocity = (new_position_no_drag - current_position) / delta_time
    force_with_drag = force - velocity * drag
    return a + force_with_drag * b

class Pendulum:
    def __init__(self, pivot_position=np.array([SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2]), pivot_mass=100, bob_mass=50, resting_length=300, starting_angle=-np.pi / 2, spring_constant=30000, constraint_iterations=2):
        self.resting_length = resting_length
        self.current_length = self.resting_length
        self.spring_constant = spring_constant
        self.constraint_iterations = constraint_iterations

        self.pivot_shape = pyglet.shapes.Circle(*pivot_position, 1, color=(255, 255, 255), batch=BATCH)
        self.pivot_previous_position = self.pivot_position
        self.pivot_mass = pivot_mass
        self.pivot_force = np.zeros(2)
        self.pivot_drag = 200

        self.bob_shape = pyglet.shapes.Circle(pivot_position[0] + self.resting_length * np.cos(starting_angle), pivot_position[1] + self.resting_length * np.sin(starting_angle), 1, color=(255, 255, 255), batch=BATCH)
        self.bob_previous_position = self.bob_position
        self.bob_mass = bob_mass
        self.bob_gravity = np.array([0, -2000])
        self.bob_drag = 0

        self.bob_angular_velocity = 0

        self.shape = pyglet.shapes.Line(*pivot_position, *self.bob_position, color=(255, 255, 255), batch=BATCH)

        objects.append(self)
    
    @property
    def pivot_position(self):
        return np.array(self.pivot_shape.position)
    
    @pivot_position.setter
    def pivot_position(self, value):
        self.pivot_shape.x, self.pivot_shape.y = value
    
    @property
    def bob_position(self):
        return np.array(self.bob_shape.position)

    @bob_position.setter
    def bob_position(self, value):
        self.bob_shape.x, self.bob_shape.y = value

    @property
    def bob_angle(self):
        return (np.atan2(*(self.bob_position - self.pivot_position)[::-1]) / np.pi + 0.5) % 2 - 1

    def update(self, delta_time):
        delta_time_squared = delta_time ** 2

        previous_bob_angle = self.bob_angle

        bob_new_position = apply_force(delta_time, self.bob_position, self.bob_previous_position, self.bob_gravity, self.bob_mass, drag=self.bob_drag)
        self.bob_previous_position = self.bob_position
        self.bob_position = bob_new_position
        
        pivot_new_position = apply_force(delta_time, self.pivot_position, self.pivot_previous_position, self.pivot_force, self.pivot_mass, drag=self.pivot_drag)
        self.pivot_previous_position = self.pivot_position
        self.pivot_position = pivot_new_position

        self.bob_angular_velocity = (self.bob_angle - previous_bob_angle) / delta_time

        for _ in range(self.constraint_iterations):
            line_vector = np.array(self.pivot_shape.position) - self.bob_position
            distance = np.linalg.norm(line_vector)
            if distance:
                force = line_vector / distance * self.spring_constant * (self.resting_length - distance)
                self.pivot_position[0] += force[0] / self.pivot_mass * delta_time_squared
                self.bob_position      -= force    / self.bob_mass   * delta_time_squared
        
        self.shape.x = self.pivot_position[0]
        self.shape.x2, self.shape.y2 = self.bob_position

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

    # print(pendulum.bob_angle)

    if keyboard_state[key.LEFT]:
        pendulum.pivot_force[0] -= 10000
    if keyboard_state[key.RIGHT]:
        pendulum.pivot_force[0] += 10000

    output_force = neural_network.evaluate(np.array([pendulum.bob_angle, min(pendulum.bob_angular_velocity, 2 - pendulum.bob_angular_velocity)]))[0]
    print(output_force)
    pendulum.pivot_force[0] += output_force * 2000

FPS_TEXT = pyglet.text.Label(f"FPS: NaN", font_name="Arial", font_size=36, x=0, y=WINDOW.height, anchor_x="left", anchor_y="top", batch=BATCH)
pendulum = Pendulum()

neural_network = NeuralNetwork(
    np.array([
        [
            [-1, -4]
        ]
    ]),
    np.array([
        [
            0
        ]
    ])
)

pyglet.clock.schedule_interval(update, 1 / MAX_FPS)
pyglet.app.run()