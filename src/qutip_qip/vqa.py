import numpy as np
from qutip.qip.circuit import QubitCircuit, Gate, Measurement
from qutip_qip.operations import *
from scipy.optimize import minimize

class VQA:
    def __init__(self):
        # defaults for now
        self.n_layers = 1
        self.blocks = []
        self.n_qubits = 2
        self.user_gates = {}
        user_gates = {}
        self._cost_methods = ["OBSERVABLE", "STATE", "BITSTRING"]
        self.cost_method = "OBSERVABLE"
        self.cost_func = None
        self.cost_observable = None
    def add_block(self, block):
        if not block.name:
            block.name = "U" + len(self.blocks)
        if block.name in list(map(lambda b: b.name, self.blocks)):
            raise ValueError("Duplicate Block name in self.blocks")
        self.blocks.append(block)
        # TODO: allow for inbuilt qutip gates
        self.user_gates = {block.name: block.get_unitary}
    def get_free_parameters(self):
        """
        Computes the number of free parameters required
        to evaluate the circuit.

        Returns
        -------
        num_params : int
            number of free parameters
        """
        return len(filter(lambda b: not b.is_unitary, self.blocks))
    def construct_circuit(self, thetas):
        circ = QubitCircuit(self.n_qubits)
        for layer_num in range(self.n_layers):
            for block in self.blocks:
                if block.is_unitary:
                    circ.add_gate(block.name, targets=[i for i in range(self.n_qubits)])
                else:
                    # TODO: arg_value not properly set
                    circ.add_gate(block.name, arg_value=thetas[0], targets=[i for i in range(self.n_qubits)])
        return circ
    def get_initial_state(self):
        """
        Returns the initial circuit state
        """
        initial_state = basis(2, 0)
        for i in range(self.n_qubits - 1):
            state = tensor(state, basis(2, 0))
        return initial_state
    def get_final_state(self, thetas):
        """
        Returns final state of circuit from initial state
        """
        circ = self.construct_circuit(thetas)
        initial_state = self.get_initial_state()
        final_state = circ.run(initial_state)
        return final_state
    def evaluate_parameters(self, thetas):
        """
        Constructs a circuit with given parameters
        and returns a cost from evaluating the circuit
        """
        final_state = self.get_final_state(thetas)
    def export_image(self, filename="circuit.png"):
        circ = self.construct_circuit([1])
        f = open(filename, 'wb+')
        f.write(circ.png.data)
        f.close()
        print(f"Image saved to ./{filename}")


class VQA_Block:
    """
    A "Block" is a constitutent part of a "layer"
    that contains a single Hamiltonian/Unitary
    specified by the user. In the case that a Unitary
    is given, there is no associated circuit parameter
    for the block.
    A "layer" is given by the product of all blocks.
    """
    def __init__(self, O, is_unitary=False, name=None):
        self.operator = O
        self.is_unitary = is_unitary
        self.name = name
    def get_unitary(self, theta=None):
        if self.is_unitary:
            return self.operator
        else:
            if theta == None:
                # TODO: raise better exception?
                raise TypeError("No parameter given")
            return (-1j * theta * self.operator).expm()
