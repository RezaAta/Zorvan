"""ANFIS-style zero-order Sugeno demo (concurrent processing).

This example builds a small ANFIS-like network for XOR using:
- two inputs (DisplayNode sources)
- two Gaussian membership functions per input (learnable via ContainerNode parameters)
- four rules (min of memberships), constant consequents (ContainerNode)
- weighted-average defuzzification via Addition/Division nodes

Training: simple finite-difference gradient descent applied to ContainerNode parameters.
This avoids changing existing fuzzy nodes and does not modify repo backprop graphs.
"""

from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Nodes import (
    AdditionNode,
    DisplayNode,
    DivisionNode,
    InitializableContainerNode,
    MinNode,
    MultiplicationNode,
)
from zorvan.Nodes.GaussianMembershipNode import GaussianMembershipNode


def build_anfis_xor():
    g = Graph()
    gp = GraphProcessor(g, verbose=False)

    # Input sources
    x1 = DisplayNode("x1", value=0.0)
    x2 = DisplayNode("x2", value=0.0)
    g.AddNode(x1, x2)

    # Membership parameter containers (centers and sigmas)
    # Two MFs per input
    params = []
    centers = []
    sigmas = []
    for i in range(2):
        c = InitializableContainerNode(
            f"c_x1_m{i}", value=0.0 if i == 0 else 1.0, init_low=-1.0, init_high=1.0
        )
        s = InitializableContainerNode(
            f"s_x1_m{i}", value=0.5, init_low=0.1, init_high=2.0
        )
        centers.append(c)
        sigmas.append(s)
        params.extend([c, s])
        g.AddNode(c, s)

    for i in range(2):
        c = InitializableContainerNode(
            f"c_x2_m{i}", value=0.0 if i == 0 else 1.0, init_low=-1.0, init_high=1.0
        )
        s = InitializableContainerNode(
            f"s_x2_m{i}", value=0.5, init_low=0.1, init_high=2.0
        )
        centers.append(c)
        sigmas.append(s)
        params.extend([c, s])
        g.AddNode(c, s)

    # Gaussian membership nodes
    gx1m = []
    gx2m = []
    for i in range(2):
        m = GaussianMembershipNode(f"G_x1_m{i}")
        m.AddPreNode(x1, centers[i], sigmas[i])
        gx1m.append(m)
        g.AddNode(m)

    for i in range(2):
        m = GaussianMembershipNode(f"G_x2_m{i}")
        m.AddPreNode(x2, centers[2 + i], sigmas[2 + i])
        gx2m.append(m)
        g.AddNode(m)

    # Rules: min between corresponding MFs (product rule could be used instead)
    rules = []
    for i in range(2):
        for j in range(2):
            r = MinNode(f"R_{i}{j}")
            r.AddPreNode(gx1m[i], gx2m[j])
            rules.append(r)
            g.AddNode(r)

    # Consequents (zero-order Sugeno): constants as ContainerNodes
    consequents = []
    for k in range(4):
        c = InitializableContainerNode(f"q{k}", value=0.0, init_low=-1.0, init_high=1.0)
        consequents.append(c)
        params.append(c)
        g.AddNode(c)

    # Multiply rule strength by consequent
    products = []
    for k, rule in enumerate(rules):
        p = MultiplicationNode(f"P{k}")
        p.AddPreNode(rule, consequents[k])
        products.append(p)
        g.AddNode(p)

    # Numerator (sum of products) and denominator (sum of rule strengths)
    numerator = AdditionNode("Numerator", 0.0)
    numerator.AddPreNode(*products)
    denominator = AdditionNode("Denominator", 0.0)
    denominator.AddPreNode(*rules)
    g.AddNode(numerator, denominator)

    # Final output
    output = DivisionNode("Output", 0.0)
    output.AddPreNode(numerator, denominator)
    g.AddNode(output)

    # Add all nodes to graph (graph.AddNode used throughout, but ensure ordering)
    g.UpdateAdjacencyMatrix()
    return g, gp, x1, x2, output, params


def evaluate_sample(gp, output_node, x1_val, x2_val, iters=6):
    # set inputs and run a few iterations to converge values
    # The GraphProcessor used in concurrent mode; use single-threaded to be deterministic
    # It's expected that running several iterations ensures the values propagate
    gp.graph.nodes[0].value  # touch
    gp.graph.nodes[0].value = gp.graph.nodes[0].value
    gp.graph.nodes[0]
    gp.ComputeGraphSingleThread(iters)
    return output_node.value


def run_training(epochs=200, lr=0.5, eps=1e-3):
    g, gp, x1, x2, out, params = build_anfis_xor()

    # XOR dataset
    data = [((0.0, 0.0), 0.0), ((0.0, 1.0), 1.0), ((1.0, 0.0), 1.0), ((1.0, 1.0), 0.0)]

    # helper to compute loss for a single sample
    def loss_for_sample(xa, xb, target):
        x1.value = xa
        x2.value = xb
        gp.ComputeGraphSingleThread(8)
        y = out.value
        return 0.5 * ((y - target) ** 2)

    print("Starting simple finite-difference ANFIS training (concurrent)")
    for epoch in range(epochs):
        total_loss = 0.0
        for (xa, xb), tgt in data:
            # baseline loss
            L0 = loss_for_sample(xa, xb, tgt)
            total_loss += L0

            # update each parameter via central finite difference
            for p in params:
                original = p.value
                p.value = original + eps
                Lp = loss_for_sample(xa, xb, tgt)
                p.value = original - eps
                Lm = loss_for_sample(xa, xb, tgt)
                p.value = original
                grad = (Lp - Lm) / (2.0 * eps)
                # simple gradient descent step
                p.value = original - lr * grad

        if epoch % 10 == 0 or epoch == epochs - 1:
            print(f"Epoch {epoch:4d}: loss={total_loss:.6f}")

    # Final evaluation
    print("Final outputs:")
    for (xa, xb), tgt in data:
        x1.value = xa
        x2.value = xb
        gp.ComputeGraphSingleThread(8)
        print(f"in=({xa},{xb}) target={tgt} out={out.value:.4f}")


if __name__ == "__main__":
    run_training(epochs=120, lr=0.3, eps=1e-4)
