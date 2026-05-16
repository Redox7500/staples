import numpy as np
import timeit

RNG = np.random.default_rng()

class NeuralNetwork:
    def __init__(self, weights, biases):
        self.weights = weights
        self.biases = biases
    
    @classmethod
    def new_zeros(cls, layer_sizes):
        return cls.new_from_functions(
            layer_sizes,
            lambda output_layer_size, input_layer_size: np.zeros((output_layer_size, input_layer_size)),
            lambda output_layer_size: np.zeros(output_layer_size)
        )
    
    @classmethod
    def new_random(cls, layer_sizes):
        return cls.new_from_functions(
            layer_sizes,
            lambda output_layer_size, input_layer_size: RNG.uniform(-1, 1, (output_layer_size, input_layer_size)),
            lambda output_layer_size: RNG.uniform(-2, 2, output_layer_size)
        )
    
    @classmethod
    def new_from_functions(cls, layer_sizes, weights_function, biases_function):
        layer_count = len(layer_sizes) - 1

        weights = [weights_function(layer_sizes[i + 1], layer_sizes[i]) for i in range(layer_count)]
        biases = [biases_function(layer_sizes[i + 1]) for i in range(layer_count)]
        return cls(weights, biases)

    def evaluate(self, inputs):
        next_inputs = inputs.copy()
        for weights, biases in zip(self.weights, self.biases):
            next_inputs = self.activation(np.matmul(weights, next_inputs) + biases)
        
        return next_inputs
    
    def activation(self, inputs):
        return np.tanh(inputs)

neural_network = NeuralNetwork.new_random([8, 16, 16, 16, 2])
print(f"took {timeit.timeit(lambda: neural_network.evaluate(RNG.uniform(-1, 1, 8)), number=100000) / 100000:.9f}")