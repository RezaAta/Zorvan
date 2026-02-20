# Moved from CompareDiabetes.py — renamed to Experiments/exp_compare_diabetes.py
# Purpose: Performance comparison scripts on the Diabetes dataset

"""
3-Way Performance Comparison on Diabetes Dataset:
1. Classic (Pure NumPy - NO computational graphs)
2. Default Computational Graph (BufferNodes + temporal delays)
3. Forward Processing (New computational graph - NO buffers, NO delays)
"""

import time

import numpy as np
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

from ClassicMLP import ClassicMLP
from zorvan.Core.BackpropGraph import BackpropGraph
from zorvan.Core.BackpropGraphForwardProcessing import BackpropGraphForwardProcessing
from zorvan.Core.Graph import Graph
from zorvan.Core.GraphProcessor import GraphProcessor
from zorvan.Core.MLPGraph import MLPGraph
from zorvan.Core.MLPGraphForwardProcessing import MLPGraphForwardProcessing
from zorvan.Nodes.SigmoidNode import SigmoidNode

print("=" * 80)
print("DIABETES DATASET - PERFORMANCE COMPARISON")
print("=" * 80)

# Load and preprocess Diabetes Dataset
data = load_diabetes()
X = data.data
y = data.target.reshape(-1, 1)

# Detect and remove outliers using IQR
q1 = np.percentile(y, 25, axis=0)
q3 = np.percentile(y, 75, axis=0)
iqr = q3 - q1
lower_bound = q1 - 1.5 * iqr
upper_bound = q3 + 1.5 * iqr

non_outlier_mask = (y >= lower_bound) & (y <= upper_bound)
X = X[non_outlier_mask.flatten()]
y = y[non_outlier_mask.flatten()]

# Split and scale
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)
scaler_X = StandardScaler()
X_train = scaler_X.fit_transform(X_train)
X_test = scaler_X.transform(X_test)

print(f"\nDataset Info:")
print(f"  Training samples: {len(X_train)}")
print(f"  Test samples: {len(X_test)}")
print(f"  Features: {X_train.shape[1]}")

# Configuration
hidden_layers = [8, 4, 2]
learning_rate = 0.00001
epochs = 100  # Reduced for faster comparison
batch_size = 1

total_iterations = epochs * len(X_train) * batch_size

# ... rest of file unchanged ...

print(
    "\nScript moved: run Experiments/exp_compare_diabetes.py to execute full benchmark"
)
