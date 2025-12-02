import matplotlib.pyplot as plt
import numpy as np


def piecewise_linear(x, xs, mus):
    """
    General piecewise‐linear membership function.
    - xs: strictly increasing list of breakpoints [x0, x1, …, xn]
    - mus: corresponding membership values [mu0, mu1, …, mun]
    Returns 0.0 for x < x0 or x > xn;
    returns mui if x == xi;
    otherwise linearly interpolates between the two enclosing knots.
    """
    x = float(x)
    xs = np.array(xs, dtype=float)
    mus = np.array(mus, dtype=float)

    if x < xs[0] or x > xs[-1]:
        return 0.0

    exact_idx = np.where(np.isclose(xs, x))[0]
    if exact_idx.size > 0:
        return float(mus[exact_idx[0]])

    pos = np.searchsorted(xs, x)
    i0 = pos - 1
    i1 = pos
    x0, x1 = xs[i0], xs[i1]
    mu0, mu1 = mus[i0], mus[i1]
    return float(mu0 + (mu1 - mu0) * (x - x0) / (x1 - x0))


def compute_fanspeed(temperature, humidity):
    """
    Computes fanspeed using the specified Mamdani fuzzy rules:
      1. If humidity is high AND temperature is hot → fanspeed is HIGH (100)
      2. If (humidity is low AND temperature is hot) OR (humidity is high AND temperature is cold) → fanspeed is MODERATE (50)
      3. If humidity is low AND temperature is cold → fanspeed is LOW (25)
    Defuzzification: weighted average over rule strengths.
    """
    mu_hot = piecewise_linear(
        temperature, xs=[-20, 5, 25, 45, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
    )
    mu_cold = piecewise_linear(
        temperature, xs=[-20, 5, 25, 45, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0]
    )
    mu_high_hum = piecewise_linear(
        humidity, xs=[0, 25, 50, 75, 100], mus=[0.0, 0.0, 0.5, 1.0, 1.0]
    )
    mu_low_hum = piecewise_linear(
        humidity, xs=[0, 25, 50, 75, 100], mus=[1.0, 1.0, 0.5, 0.0, 0.0]
    )

    a1 = min(mu_high_hum, mu_hot)
    a2a = min(mu_low_hum, mu_hot)
    a2b = min(mu_high_hum, mu_cold)
    a2 = max(a2a, a2b)
    a3 = min(mu_low_hum, mu_cold)

    z1, z2, z3 = 100.0, 50.0, 25.0
    numerator = a1 * z1 + a2 * z2 + a3 * z3
    denominator = a1 + a2 + a3
    return numerator / denominator if denominator != 0 else 0.0


def plot_piecewise_curve(
    xs,
    mus,
    domain_min,
    domain_max,
    title="Membership Curve",
    xlabel="x",
    ylabel="mu(x)",
):
    """
    Plots a single piecewise‐linear membership curve.
    - xs: list of breakpoints
    - mus: list of membership values at those breakpoints
    - domain_min, domain_max: plotting range
    - title, xlabel, ylabel: labels for the plot
    """
    domain = np.linspace(domain_min, domain_max, 500)
    values = [piecewise_linear(x, xs, mus) for x in domain]

    plt.figure()
    plt.plot(domain, values, color="tab:orange")
    plt.title(title)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.grid(True)
    plt.show()


if __name__ == "__main__":
    # Example: compute fanspeed for temperature=12, humidity=45
    hum_test = 94
    temp_test = 12
    fanspeed = compute_fanspeed(temp_test, hum_test)
    print(
        f"For Temperature={temp_test}, Humidity={hum_test} → Fanspeed ≈ {fanspeed:.3f}"
    )

    # Plot each membership curve individually
    plot_piecewise_curve(
        xs=[-20, 5, 25, 45, 100],
        mus=[0.0, 0.0, 0.5, 1.0, 1.0],
        domain_min=-20,
        domain_max=100,
        title="Hot Temperature Membership",
        xlabel="Temperature",
        ylabel="mu_hot",
    )

    plot_piecewise_curve(
        xs=[-20, 5, 25, 45, 100],
        mus=[1.0, 1.0, 0.5, 0.0, 0.0],
        domain_min=-20,
        domain_max=100,
        title="Cold Temperature Membership",
        xlabel="Temperature",
        ylabel="mu_cold",
    )

    plot_piecewise_curve(
        xs=[0, 25, 50, 75, 100],
        mus=[0.0, 0.0, 0.5, 1.0, 1.0],
        domain_min=0,
        domain_max=100,
        title="High Humidity Membership",
        xlabel="Humidity",
        ylabel="mu_high_hum",
    )

    plot_piecewise_curve(
        xs=[0, 25, 50, 75, 100],
        mus=[1.0, 1.0, 0.5, 0.0, 0.0],
        domain_min=0,
        domain_max=100,
        title="Low Humidity Membership",
        xlabel="Humidity",
        ylabel="mu_low_hum",
    )
