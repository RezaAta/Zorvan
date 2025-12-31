from Experiments.exp_compare_diabetes_multi_trial import prepare_data, run_single_trial

X_train, X_test, y_train, y_test = prepare_data()

c_hist, g_hist = run_single_trial(
    999, X_train, y_train, [10], 1e-5, epochs=6, batch_size=1, use_bias=True
)
print("classic len", len(c_hist))
print("graph len", len(g_hist))
print("\nclassic first 8:", c_hist[:8])
print("\ngraph first 8:", g_hist[:8])
