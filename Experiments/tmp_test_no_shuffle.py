from Experiments.exp_compare_diabetes_multi_trial import prepare_data, run_single_trial

X_train, X_test, y_train, y_test = prepare_data()

# Run short test with shuffle disabled
c_epochs, g_epochs, c_mae, g_mae, init_cmp, post_cmp = run_single_trial(
    seed=42424,
    X_train=X_train,
    y_train=y_train,
    hidden_layers=[10],
    learning_rate=1e-5,
    epochs=4,
    batch_size=1,
    use_bias=True,
    shuffle=False,
    X_test=X_test,
    y_test=y_test,
)

print("\nPer-epoch MSE (Classic):", c_epochs)
print("Per-epoch MSE (Graph):", g_epochs)
print("\nMAEs -> Classic:", c_mae, "Graph:", g_mae)
print("\nInit cmp summary:", init_cmp)
print("\nPost cmp summary:", post_cmp)
