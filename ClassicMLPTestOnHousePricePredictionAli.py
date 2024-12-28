import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import SGD
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Load the dataset
data = fetch_california_housing()
X, y = data.data, data.target

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


# Define the model
model = Sequential([
    Dense(8, activation='sigmoid', input_shape=(X_train.shape[1],)),
    Dense(6, activation='sigmoid'),
    Dense(4, activation='sigmoid'),
    Dense(1, activation='linear')  # Output layer with linear activation for regression
])

# Compile the model with SGD optimizer (no momentum, similar to your code)
optimizer = SGD(learning_rate=0.01)  # Same behavior as your custom backprop
model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

# Train the model and capture the history
history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=500, batch_size=1)

# Evaluate the model
loss, mae = model.evaluate(X_test, y_test)
print(f"Test Loss (MSE): {loss:.4f}, Test MAE: {mae:.4f}")

# Plot training and validation loss
plt.plot(history.history['loss'], label='Training Loss (MSE)')
plt.plot(history.history['val_loss'], label='Validation Loss (MSE)')
plt.title('Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('Loss (MSE)')
plt.legend()
plt.show()