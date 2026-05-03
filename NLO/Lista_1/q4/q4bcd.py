from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np


PASTA_FIGURAS = Path(__file__).resolve().parent / "figures"

# Troque para True se quiser abrir as figuras ao rodar o script.
MOSTRAR_GRAFICOS = False

# Tomamos g = 1 no codigo, pois o eixo dos graficos e gz.
g = 1.0


def equacoes_shg(z, y):
    """Equações de SHG para Delta k = 0."""
    aw, a2w = y

    daw_dz = 2j * g * np.conj(aw) * a2w
    da2w_dz = 1j * g * aw**2

    return [daw_dz, da2w_dz]


def rk4(f, y0, z):
    """Integra dy/dz = f(z, y) usando RK4 com passo fixo."""
    y0 = np.asarray(y0, dtype=complex)
    y = np.zeros((len(y0), len(z)), dtype=complex)
    y[:, 0] = y0

    for n in range(len(z) - 1):
        h = z[n + 1] - z[n]
        yn = y[:, n]

        k1 = np.asarray(f(z[n], yn), dtype=complex)
        k2 = np.asarray(f(z[n] + h / 2, yn + h * k1 / 2), dtype=complex)
        k3 = np.asarray(f(z[n] + h / 2, yn + h * k2 / 2), dtype=complex)
        k4 = np.asarray(f(z[n] + h, yn + h * k3), dtype=complex)

        y[:, n + 1] = yn + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6

    return y


def resolver_shg(y0, gz_max, n_pontos=2000):
    """Resolve o sistema em uma malha uniforme de z."""
    z_eval = np.linspace(0, gz_max / g, n_pontos)
    y = rk4(equacoes_shg, y0, z_eval)

    return SimpleNamespace(t=z_eval, gz=g * z_eval, y=y)


def fluxos(sol):
    """Calcula os fluxos Phi_w = |a_w|^2 e Phi_2w = |a_2w|^2."""
    aw = sol.y[0]
    a2w = sol.y[1]

    phiw = np.abs(aw) ** 2
    phi2w = np.abs(a2w) ** 2

    return phiw, phi2w


def erro_manley_rowe(phiw, phi2w):
    """Calcula o erro relativo na conservação de M."""
    M = phiw + 2 * phi2w
    return np.max(np.abs(M / M[0] - 1))


def q4b():
    """Item 4.b: SHG partindo apenas da fundamental."""
    sol = resolver_shg([1.0 + 0j, 0.0 + 0j], gz_max=3, n_pontos=3000)
    phiw, phi2w = fluxos(sol)

    phiw0 = phiw[0]
    M = phiw + 2 * phi2w

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(sol.gz, phiw / phiw0, label=r"$\Phi_\omega/\Phi_\omega(0)$")
    ax.plot(sol.gz, phi2w / phiw0, label=r"$\Phi_{2\omega}/\Phi_\omega(0)$")
    ax.plot(sol.gz, M / phiw0, color="black", linestyle="--", label=r"$M/\Phi_\omega(0)$")

    ax.set_xlabel(r"$gz$")
    ax.set_ylabel("Frações normalizadas")
    ax.set_ylim(-0.03, 1.08)
    ax.legend()
    ax.grid(True)

    fig.tight_layout()
    fig.savefig(PASTA_FIGURAS / "q4b_shg_manley_rowe.png", dpi=300, bbox_inches="tight")

    print("4.b)")
    print(f"Phi_w final / Phi_w(0): {phiw[-1] / phiw0:.6f}")
    print(f"Phi_2w final / Phi_w(0): {phi2w[-1] / phiw0:.6f}")
    print(f"2 Phi_2w final / Phi_w(0): {2 * phi2w[-1] / phiw0:.6f}")
    print(f"Erro máximo em M/M0: {erro_manley_rowe(phiw, phi2w):.2e}")


def q4c():
    """Item 4.c: mesmos fluxos iniciais e fases relativas diferentes."""
    casos = [
        (r"$a_{2\omega}(0)=+i$", 1.0 + 0j, 1j, "tab:orange"),
        (r"$a_{2\omega}(0)=-i$", 1.0 + 0j, -1j, "tab:purple"),
        (r"$a_{2\omega}(0)=1$", 1.0 + 0j, 1.0 + 0j, "tab:green"),
    ]

    fig, ax = plt.subplots(figsize=(8, 5))

    print("\n4.c)")
    for label, aw0, a2w0, cor in casos:
        sol = resolver_shg([aw0, a2w0], gz_max=3, n_pontos=2000)
        phiw, phi2w = fluxos(sol)

        ax.plot(sol.gz, phi2w / phi2w[0], color=cor, label=label)

        print(label.replace("$", ""))
        print(f"  Phi_2w final / Phi_2w(0): {phi2w[-1] / phi2w[0]:.6f}")
        print(f"  Phi_2w min / Phi_2w(0): {phi2w.min() / phi2w[0]:.6f}")
        print(f"  Phi_2w max / Phi_2w(0): {phi2w.max() / phi2w[0]:.6f}")
        print(f"  Erro máximo em M/M0: {erro_manley_rowe(phiw, phi2w):.2e}")

    ax.axhline(1, color="black", linestyle=":", linewidth=1)
    ax.set_xlabel(r"$gz$")
    ax.set_ylabel(r"$\Phi_{2\omega}/\Phi_{2\omega}(0)$")
    ax.set_title(r"$a_\omega(0)=1$ fixo, $\left|a_{2\omega}(0)\right|=1$")
    ax.set_xlim(0, 3)
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(PASTA_FIGURAS / "q4c_amplificacao_sensivel_fase.png", dpi=300, bbox_inches="tight")


def q4d():
    """Item 4.d: limite de semente fundamental cada vez menor."""
    fluxos_w0 = [1.0, 0.3, 0.05, 0.0]
    cores = ["tab:purple", "tab:green", "tab:blue", "black"]

    # Mantemos o campo em 2w e a fase que inicia a deamplificação.
    a2w0 = -1j
    phi2w0 = abs(a2w0) ** 2

    fig, ax = plt.subplots(figsize=(8, 5))

    print("\n4.d)")
    for phiw0, cor in zip(fluxos_w0, cores):
        aw0 = np.sqrt(phiw0) + 0j
        sol = resolver_shg([aw0, a2w0], gz_max=0.5, n_pontos=2000)
        phiw, phi2w = fluxos(sol)

        ax.plot(
            sol.gz,
            phi2w / phi2w0,
            color=cor,
            label=rf"$\Phi_\omega(0)={phiw0:g}$",
        )

        print(rf"Phi_w(0)={phiw0:g}")
        print(f"  Phi_2w final / Phi_2w(0): {phi2w[-1] / phi2w0:.6f}")
        print(f"  Phi_2w min / Phi_2w(0): {phi2w.min() / phi2w0:.6f}")
        print(f"  Erro máximo em M/M0: {erro_manley_rowe(phiw, phi2w):.2e}")

    ax.axhline(1, color="black", linestyle=":", linewidth=1)
    ax.set_xlabel(r"$gz$")
    ax.set_ylabel(r"$\Phi_{2\omega}/\Phi_{2\omega}(0)$")
    ax.set_title(r"$a_{2\omega}(0)=-i$ fixo e $\Phi_\omega(0)$ decrescente")
    ax.set_xlim(0, 0.5)
    ax.set_ylim(-0.05, 1.08)
    ax.grid(True)
    ax.legend()

    fig.tight_layout()
    fig.savefig(PASTA_FIGURAS / "q4d_limite_semente_fundamental.png", dpi=300, bbox_inches="tight")


def main():
    PASTA_FIGURAS.mkdir(exist_ok=True)
    q4b()
    q4c()
    q4d()

    if MOSTRAR_GRAFICOS:
        plt.show()
    else:
        plt.close("all")


if __name__ == "__main__":
    main()
