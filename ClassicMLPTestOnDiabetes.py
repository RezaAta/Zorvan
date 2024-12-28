import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import SGD
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
import numpy as np

# Load Diabetes Dataset
data = load_diabetes()
X = data.data  # Features
y = data.target  # Target reshaped to 2D

# Detect and remove outliers using IQR
q1 = np.percentile(y, 25, axis=0)  # First quartile
q3 = np.percentile(y, 75, axis=0)  # Third quartile
iqr = q3 - q1  # Interquartile range
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

# Mask for filtering non-outliers
non_outlier_mask = (y >= lower_bound) & (y <= upper_bound)
X = X[non_outlier_mask.flatten()]
y = y[non_outlier_mask.flatten()]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Scale the features
scaler = StandardScaler()
X_train = scaler.fit_transform(X_train)
X_test = scaler.transform(X_test)


def ones_initializer(shape, dtype=None):
    return tf.ones(shape, dtype=dtype)

# Define the model with weights initialized to 1
model = Sequential([
    Dense(8, activation='sigmoid', input_shape=(X_train.shape[1],), 
          kernel_initializer=ones_initializer, use_bias = False),
    Dense(4, activation='sigmoid', 
          kernel_initializer=ones_initializer, use_bias = False),
    Dense(2, activation='sigmoid', 
          kernel_initializer=ones_initializer, use_bias = False),
    Dense(1, activation='linear', 
          kernel_initializer=ones_initializer, use_bias = False)
])

# Compile the model with SGD optimizer (no momentum, similar to your code)
optimizer = SGD(learning_rate=0.00001)  # Same behavior as your custom backprop
model.compile(optimizer=optimizer, loss='mse', metrics=['mae'])

# Train the model and capture the history
history = model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=500 , batch_size=1)

# Evaluate the model
loss, mae = model.evaluate(X_test, y_test)
print(f"Test Loss (MSE): {loss:.4f}, Test MAE: {mae:.4f}")


# Plot training and validation loss
plt.plot(history.history['loss'], label='Training Loss (MSE)')
# plt.plot(history.history['val_loss'], label='Validation Loss (MSE)')
plt.title('Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('Loss (MSE)')
plt.legend()
plt.show()
