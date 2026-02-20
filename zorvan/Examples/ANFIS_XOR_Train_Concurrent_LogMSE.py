import matplotlib.pyplot as plt

from zorvan.Core.BackpropAnfisGraph import BackpropAnfisGraph
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPAnfisGraph import MLPAnfisGraph


def run_training_log(epochs=200, learning_rate=0.1):
    mlp = MLPAnfisGraph(numInputs=2, numOutputs=1, mfs_per_input=2)
    mlp.BuildMLP()
    back = BackpropAnfisGraph(mlp, learningRate=learning_rate)
    back.BuildBackprop()

    combined = Graph()
    for n in mlp.nodes:
        combined.AddNode(n)
    for n in back.nodes:
        combined.AddNode(n)

    gp = GraphProcessor(combined, verbose=False)

    # XOR samples (explicit list)
    Xs = [(0.0, 0.0), (0.0, 1.0), (1.0, 0.0), (1.0, 1.0)]
    Ys = [0.0, 1.0, 1.0, 0.0]

    network_steps = 6
    mse_history = []

    print("Epoch-by-epoch training (concurrent, per-sample updates)")
    for epoch in range(epochs):
        epoch_loss = 0.0
        for xi, yi in zip(Xs, Ys):
            # set inputs and label nodes via DataStreamNode.data to avoid index errors
            in0 = mlp.inputLayer[0][0]
            in1 = mlp.inputLayer[1][0]
            lab = mlp.labelLayer[0]
            in0.data = [xi[0]]
            in1.data = [xi[1]]
            lab.data = [yi]
            # reset stream indices so Operation reads the single-element list
            for node in (in0, in1, lab):
                node.streamIndex = 0
                node.iteration = 0
                node.lastStream = -1

            # run a few propagation steps so forward+backprop can occur
            gp.ComputeGraphSingleThread(network_steps)

            # read error node value (Subtraction node) and compute squared error
            err = mlp.errorLayer[0].value
            epoch_loss += err * err

        mse = epoch_loss / len(Xs)
        mse_history.append(mse)
        if epoch % 10 == 0 or epoch == epochs - 1:
            print(f"Epoch {epoch:4d} MSE={mse:.6f}")

    # Final evaluation
    print("Final outputs after training:")
    for xi, yi in zip(Xs, Ys):
        mlp.inputLayer[0][0].value = xi[0]
        mlp.inputLayer[1][0].value = xi[1]
        gp.ComputeGraphSingleThread(network_steps)
        yout = mlp.outputLayer[0][1].value
        print(f"in={xi} target={yi} out={yout:.4f}")

    # Plot MSE
    plt.plot(mse_history)
    plt.xlabel("Epoch")
    plt.ylabel("MSE")
    plt.title("ANFIS Concurrent Training MSE")
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    run_training_log(epochs=200, learning_rate=0.08)
