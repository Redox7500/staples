import numpy as np

class NeuralNetwork:
    def __init__(self, weights, biases):
        self.weights = weights
        self.weights_transpose = [weights.T for weights in self.weights]
        self.biases = biases

        self.weights_change = [np.zeros(weights.shape) for weights in self.weights]
        self.biases_change = [np.zeros(biases.shape) for biases in self.biases]
        self.trains_since_last_change = 0

        self.layer_count = len(weights) + 1
        
        self.learning_rate = 0.5
        self.learning_decay = 1

        self.activation = self.tanh
        self.activation_derivative = self.tanh_derivative

        self.cost = self.mean_squared_error
        self.cost_derivative = self.mean_squared_error_derivative
    
    @classmethod
    def new_zeros(cls, layer_sizes):
        return cls.new_from_functions(
            layer_sizes,
            lambda output_layer_size, input_layer_size: np.zeros((output_layer_size, input_layer_size)),
            lambda output_layer_size: np.zeros(output_layer_size)
        )
    
    @classmethod
    def new_random(cls, layer_sizes, weights_min=-1, weights_max=1, biases_min=-2, biases_max=2):
        RNG = np.random.default_rng()
        return cls.new_from_functions(
            layer_sizes,
            lambda output_layer_size, input_layer_size: RNG.uniform(weights_min, weights_max, (output_layer_size, input_layer_size)),
            lambda output_layer_size: RNG.uniform(biases_min, biases_max, output_layer_size)
        )
    
    @classmethod
    def new_from_functions(cls, layer_sizes, weights_function, biases_function):
        layer_count = len(layer_sizes) - 1

        weights = [weights_function(layer_sizes[i + 1], layer_sizes[i]) for i in range(layer_count)]
        biases = [biases_function(layer_sizes[i + 1]) for i in range(layer_count)]
        return cls(weights, biases)
    
    def tanh(self, x): return np.tanh(x)
    def tanh_derivative(self, x): return 1 - np.tanh(x) ** 2

    def hard_tanh(self, x): return np.clip(x, -1, 1)
    def hard_tanh_derivative(self, x): return np.where(-1 < x < 1, 1, 0)

    def sigmoid(self, x): return 1 / (1 + np.exp(-x))
    def sigmoid_derivative(self, x): a = np.exp(-x); return a / (a + 1) ** 2

    def mean_squared_error(self, y, y_expected): return (y - y_expected) ** 2
    def mean_squared_error_derivative(self, y, y_expected): return (y - y_expected) * 2
    
    # def logistic_error(self, y, y_expected): m = len(y_expected); 

    def evaluate(self, x):
        next_x = x.copy()
        for layer in range(self.layer_count - 1):
            next_x = self.activation(self.weights[layer] @ next_x + self.biases[layer])
        
        return next_x
    
    def train(self, x, y_expected):
        unnormalized_activations = [[] for _ in range(self.layer_count)]
        activations = [[] for _ in range(self.layer_count)]

        unnormalized_activations[0] = x
        activations[0] = x

        next_x = x.copy()
        for layer in range(self.layer_count - 1):
            unnormalized_activations[layer + 1] = self.weights[layer] @ next_x + self.biases[layer]
            next_x = self.activation(unnormalized_activations[layer + 1])
            activations[layer + 1] = next_x

        next_error = self.cost_derivative(next_x, y_expected)
        for layer in range(self.layer_count - 2, -1, -1):
            a = self.activation_derivative(unnormalized_activations[layer + 1]) * next_error
            self.weights_change[layer] -= a[:, None] @ activations[layer][None, :]
            self.biases_change[layer] -= a
            next_error = self.weights_transpose[layer] @ a
        
        self.trains_since_last_change += 1
    
    def update_parameters(self):
        if not self.trains_since_last_change:
            return
        
        multiplier = 1 / self.trains_since_last_change * self.learning_rate
        for layer in range(self.layer_count - 1):
            self.weights[layer] += self.weights_change[layer] * multiplier
            self.biases[layer] += self.biases_change[layer] * multiplier

            self.weights_change[layer].fill(0)
            self.biases_change[layer].fill(0)

        self.weights_transpose = [weights.T for weights in self.weights]
        self.learning_rate *= self.learning_decay
        self.trains_since_last_change = 0

training_data = [
    (np.array([-1, -1]), np.array([-1])),
    (np.array([-1, 1]), np.array([1])),
    (np.array([1, -1]), np.array([1])),
    (np.array([1, 1]), np.array([-1]))
]

for _ in range(10):
    neural_network = NeuralNetwork.new_random([2, 4, 1], weights_min=-1, weights_max=1, biases_min=-1, biases_max=1)
    for _ in range(2000):
        for x, y_expected in training_data:
            neural_network.train(x, y_expected)
        neural_network.update_parameters()
    print(", ".join([f"{neural_network.cost(y_expected, neural_network.evaluate(x))[0]:.10f}" for x, y_expected in training_data]))
    
# for x, y_expected in training_data:
#     print(neural_network.evaluate(x))