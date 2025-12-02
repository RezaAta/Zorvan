from ComputationalGraphs.Core.BackpropGraph import BackpropGraph
from ComputationalGraphs.Nodes.AdditionNode import AdditionNode
from ComputationalGraphs.Nodes.BufferNode import BufferNode
from ComputationalGraphs.Nodes.DisplayNode import DisplayNode
from ComputationalGraphs.Nodes.DivisionNode import DivisionNode
from ComputationalGraphs.Nodes.GaussianCenterDerivativeNode import (
    GaussianCenterDerivativeNode,
)
from ComputationalGraphs.Nodes.GaussianSigmaDerivativeNode import (
    GaussianSigmaDerivativeNode,
)
from ComputationalGraphs.Nodes.MultiplicationNode import MultiplicationNode
from ComputationalGraphs.Nodes.SubtractionNode import SubtractionNode


class BackpropAnfisGraph(BackpropGraph):
    """Backprop adaptor for `MLPAnfisGraph`.

    This class builds gradient wiring for zero-order Sugeno ANFIS built by
    `MLPAnfisGraph`. It currently attaches gradients for consequent
    ContainerNodes (q_k). MF parameter (center/sigma) gradients require
    differentiable antecedent operators (e.g., product t-norm) and are
    left for a later extension.
    """

    def __init__(self, anfis_graph, learningRate=0.01):
        super().__init__(anfis_graph, learningRate)
        self.anfis_graph = anfis_graph

    def BuildBackprop(self):
        # Create LR node
        self.lrNode = DisplayNode(name="LearningRate", value=self.learning_rate)
        self.AddNode(self.lrNode)

        # Find denominator and output division node
        denom = None
        output_node = None
        numerator = None
        for n in self.mlp_graph.nodes:
            if n.name == "Denominator":
                denom = n
            if n.name == "Numerator":
                numerator = n
            if (
                hasattr(n, "__class__")
                and n.__class__.__name__ == "DivisionNode"
                and n.name.startswith("y")
            ):
                output_node = n

        if denom is None or output_node is None:
            raise RuntimeError(
                "Could not find required ANFIS output/denominator nodes in graph."
            )

        # Use the output error node (assumes single output)
        if not self.mlp_graph.errorLayer:
            raise RuntimeError(
                "ANFIS graph has no errorLayer; ensure _CreateErrorLayer() ran."
            )
        error_node = self.mlp_graph.errorLayer[0]

        # For every consequent ContainerNode q_k, build normalized-rule -> gradient -> lr chain
        # Also compute gradients for rule strengths and propagate to MF params (centers/sigmas)
        for k, q in enumerate(self.mlp_graph.consequents):
            w_k = self.mlp_graph.rule_nodes[k]

            # Gradient for consequent q_k (same as before)
            norm_node = DivisionNode(name=f"NormRule_{k}")
            norm_node.AddPreNode(w_k, denom)
            grad_q = MultiplicationNode(name=f"EG_q{k}")
            grad_q.AddPreNode(norm_node, error_node)
            lr_mult_q = MultiplicationNode(name=f"LRMult_q{k}")
            lr_mult_q.AddPreNode(grad_q, self.lrNode)
            q.AddPreNode(lr_mult_q)
            self.AddNode(norm_node, grad_q, lr_mult_q)

            # Gradient wrt rule strength w_k: grad_wk = (q_k - y)/denom * error
            # tmp = q_k - y
            tmp_sub = SubtractionNode(name=f"qdiff_{k}")
            tmp_sub.AddPreNode(q, output_node)
            div = DivisionNode(name=f"qdiff_div_{k}")
            div.AddPreNode(tmp_sub, denom)
            grad_wk = MultiplicationNode(name=f"grad_wk_{k}")
            grad_wk.AddPreNode(div, error_node)
            self.AddNode(tmp_sub, div, grad_wk)

            # For each MF in the rule, propagate gradient to center and sigma
            # Need to find which MF nodes contributed to this rule: search rule predecessors
            # For product-chain, find leaf MF predecessors by traversing back
            def collect_mf_preds(node):
                # recursively collect GaussianMembershipNode leaves
                preds = []
                if hasattr(node, "predecessors") and node.predecessors:
                    for p in node.predecessors:
                        # GaussianMembershipNode className
                        if p.__class__.__name__ == "GaussianMembershipNode":
                            preds.append(p)
                        else:
                            preds.extend(collect_mf_preds(p))
                return preds

            mf_preds = collect_mf_preds(w_k)

            for i, mu_node in enumerate(mf_preds):
                # compute other = w_k / mu_i  (product of other mus)
                other = DivisionNode(name=f"otherprod_{k}_{i}")
                other.AddPreNode(w_k, mu_node)
                self.AddNode(other)

                # center derivative node for this MF
                dmu_dc = GaussianCenterDerivativeNode(name=f"dmu_dc_k{k}_m{i}")
                dmu_dc.AddPreNode(
                    mu_node.predecessors[0],
                    mu_node.predecessors[1],
                    mu_node.predecessors[2],
                )
                self.AddNode(dmu_dc)

                # sigma derivative
                dmu_ds = GaussianSigmaDerivativeNode(name=f"dmu_ds_k{k}_m{i}")
                dmu_ds.AddPreNode(
                    mu_node.predecessors[0],
                    mu_node.predecessors[1],
                    mu_node.predecessors[2],
                )
                self.AddNode(dmu_ds)

                # grad contribution to center: grad_wk * other * dmu_dc
                mult1 = MultiplicationNode(name=f"gw_other_{k}_{i}")
                mult1.AddPreNode(grad_wk, other)
                mult2 = MultiplicationNode(name=f"dCcontrib_{k}_{i}")
                mult2.AddPreNode(mult1, dmu_dc)
                lr_mult_c = MultiplicationNode(name=f"LRMult_c_k{k}_m{i}")
                lr_mult_c.AddPreNode(mult2, self.lrNode)
                # add to center ContainerNode (which is mf_node.predecessors[1])
                center_container = mu_node.predecessors[1]
                center_container.AddPreNode(lr_mult_c)
                self.AddNode(mult1, mult2, lr_mult_c)

                # grad contribution to sigma: grad_wk * other * dmu_ds
                mult3 = MultiplicationNode(name=f"gw_other_s_{k}_{i}")
                mult3.AddPreNode(grad_wk, other)
                mult4 = MultiplicationNode(name=f"dScontrib_{k}_{i}")
                mult4.AddPreNode(mult3, dmu_ds)
                lr_mult_s = MultiplicationNode(name=f"LRMult_s_k{k}_m{i}")
                lr_mult_s.AddPreNode(mult4, self.lrNode)
                sigma_container = mu_node.predecessors[2]
                sigma_container.AddPreNode(lr_mult_s)
                self.AddNode(mult3, mult4, lr_mult_s)

        # Finalize adjacency
        self.UpdateAdjacencyMatrix()
