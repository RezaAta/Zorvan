from ClassicMLP import ClassicMLP
import matplotlib.pyplot as plt
import numpy as np


X = np.array([[0,0],[0,1],[1,0],[1,1]])
y = np.array([[0],[1],[1],[0]])


# Initialize and train the model
mlp = ClassicMLP(
    input_size=X.shape[1],
    output_size=1,
    hidden_layers=[4],
    hidden_activation="sigmoid",
    output_activation="sigmoid",
    learning_rate=0.5,
    # initial_weight=1.0,
    use_bias= False
)
mse_history = mlp.train(X, y, epochs=5000, batch_size=1)

# Evaluate the model
mae = mlp.evaluate(X, y)
print(f"Test MAE: {mae:.4f}")

# Plot training loss
plt.plot(mse_history, label='Training Loss (MSE)')
plt.title('Training Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('Loss (MSE)')
plt.legend()
plt.show()
