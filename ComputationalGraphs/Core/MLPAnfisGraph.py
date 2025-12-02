from ComputationalGraphs.Core.MLPGraph import MLPGraph
from ComputationalGraphs.Core.Graph import Graph
from ComputationalGraphs.Nodes import (
    DisplayNode,
    ContainerNode,
    MinNode,
    MultiplicationNode,
    AdditionNode,
    DivisionNode,
    DataStreamNode,
)
from ComputationalGraphs.Nodes.GaussianMembershipNode import GaussianMembershipNode


class MLPAnfisGraph(MLPGraph):
    """MLP-style wrapper that builds an ANFIS zero-order Sugeno network.

    This class extends `MLPGraph` only to reuse input/label handling and
    starting node conventions. It overrides `BuildMLP` to construct a
    fuzzy micro-architecture instead of classical weighted sums.
    """

    def __init__(self, numInputs, numOutputs=1, mfs_per_input=2):
        # Initialize MLPGraph internals (we won't use hidden layers)
        super().__init__(numInputs=numInputs, numOutputs=numOutputs, numHiddenLayers=0)
        self.mfs_per_input = mfs_per_input if isinstance(mfs_per_input, (list, tuple)) else [mfs_per_input] * numInputs
        self.memberships = []
        self.rule_nodes = []
        self.consequents = []

    def BuildMLP(self):
        """Construct ANFIS-style graph.

        Structure:
        - Input `DataStreamNode`s (via parent helper)
        - For each input: create `m` ContainerNode center/sigma pairs and `GaussianMembershipNode`s
        - Create rules as cartesian product of input MFs -> `MinNode` antecedents
        - Create consequent ContainerNodes (zero-order Sugeno)
        - Weighted-average defuzzification via Addition/Division
        """
        # Create input layer similar to MLPGraph
        self._CreateInputLayer()

        # Build memberships for each input
        self.memberships = []  # list of lists per input
        for inp_idx in range(self.numInputs):
            mfs = []
            for mf_idx in range(self.mfs_per_input[inp_idx]):
                c = ContainerNode(name=f"c_x{inp_idx}_m{mf_idx}", value=0.0 if mf_idx == 0 else 1.0)
                s = ContainerNode(name=f"s_x{inp_idx}_m{mf_idx}", value=0.5)
                g = GaussianMembershipNode(name=f"G_x{inp_idx}_m{mf_idx}")
                # connect: input data node is inputLayer[inp_idx][0]
                g.AddPreNode(self.inputLayer[inp_idx][0], c, s)
                self.AddNode(c, s, g)
                mfs.append((c, s, g))
            self.memberships.append(mfs)

        # Build rules: cartesian product of MF indices across inputs
        # Use product t-norm (multiplicative rule) implemented by chaining MultiplicationNode
        from itertools import product
        from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode

        self.rule_nodes = []
        for combo in product(*[range(len(mfs)) for mfs in self.memberships]):
            preds = [self.memberships[i][combo[i]][2] for i in range(len(combo))]
            # chain multiplications to support N-ary product
            if not preds:
                continue
            current = preds[0]
            for idx in range(1, len(preds)):
                mult = MultiplicationNode(name=f"R_{''.join(str(i) for i in combo)}_m{idx}")
                mult.AddPreNode(current, preds[idx])
                self.AddNode(mult)
                current = mult
            # `current` is the final product node representing rule strength
            self.rule_nodes.append(current)

        # Consequents: zero-order Sugeno constants per rule
        self.consequents = []
        for k in range(len(self.rule_nodes)):
            q = ContainerNode(name=f"q{k}", value=0.0)
            self.consequents.append(q)
            self.AddNode(q)

        # Multiply rule strength by consequent
        products = []
        for k, r in enumerate(self.rule_nodes):
            p = MultiplicationNode(name=f"P{k}")
            p.AddPreNode(r, self.consequents[k])
            self.AddNode(p)
            products.append(p)

        # Numerator and denominator
        numerator = AdditionNode("Numerator", 0.0)
        numerator.AddPreNode(*products)
        denominator = AdditionNode("Denominator", 0.0)
        denominator.AddPreNode(*self.rule_nodes)
        self.AddNode(numerator, denominator)

        # Output(s): create one DivisionNode per declared output (supports numOutputs)
        self.outputLayer = []
        for out_i in range(self.numOutputs):
            out = DivisionNode(name=f"y{out_i}")
            # For now assume same numerator/denominator used for all outputs (single-output ANFIS)
            out.AddPreNode(numerator, denominator)
            self.outputLayer.append((numerator, out))
            self.AddNode(out)

        # Labels
        self._CreateLabelLayer()
        self._CreateErrorLayer()

        # Starting nodes: input data streams + labels
        self.starting_nodes = []
        for input_pair in self.inputLayer:
            self.starting_nodes.append(input_pair[0])
        for label in self.labelLayer:
            self.starting_nodes.append(label)

        self.UpdateAdjacencyMatrix()
