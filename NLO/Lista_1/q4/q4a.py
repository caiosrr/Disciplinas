from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np


PASTA_FIGURAS = Path(__file__).resolve().parent / "figures"

# Troque para True se quiser abrir as figuras ao rodar o script.
MOSTRAR_GRAFICOS = False


def equacoes_sfg(xi, y):
    """
    Equações de SFG para Delta k = 0, usando xi = g z.
    O vetor y contém as amplitudes complexas (a1, a2, a3).
    """

    a1, a2, a3 = y

    da1_dxi = 1j * np.conj(a2) * a3
    da2_dxi = 1j * np.conj(a1) * a3
    da3_dxi = 1j * a1 * a2

    return [da1_dxi, da2_dxi, da3_dxi]


def rk4(f, y0, xi):
    """Integra dy/dxi = f(xi, y) usando RK4 com passo fixo."""
    y0 = np.asarray(y0, dtype=complex)
    y = np.zeros((len(y0), len(xi)), dtype=complex)
    y[:, 0] = y0

    for n in range(len(xi) - 1):
        h = xi[n + 1] - xi[n]
        yn = y[:, n]

        k1 = np.asarray(f(xi[n], yn), dtype=complex)
        k2 = np.asarray(f(xi[n] + h / 2, yn + h * k1 / 2), dtype=complex)
        k3 = np.asarray(f(xi[n] + h / 2, yn + h * k2 / 2), dtype=complex)
        k4 = np.asarray(f(xi[n] + h, yn + h * k3), dtype=complex)

        y[:, n + 1] = yn + h * (k1 + 2 * k2 + 2 * k3 + k4) / 6

    return y


def resolver_sfg(y0, xi_max, n_pontos=1000):
    """Resolve o sistema em uma malha uniforme de xi."""
    xi_eval = np.linspace(0, xi_max, n_pontos)
    y = rk4(equacoes_sfg, y0, xi_eval)

    return SimpleNamespace(t=xi_eval, y=y)


def fluxos(sol):
    """Calcula os fluxos Phi_j = |a_j|^2."""
    a1 = sol.y[0]
    a2 = sol.y[1]
    a3 = sol.y[2]

    phi1 = np.abs(a1) ** 2
    phi2 = np.abs(a2) ** 2
    phi3 = np.abs(a3) ** 2

    return phi1, phi2, phi3


# Condições iniciais: sinal fraco, bomba forte e sem campo soma.
a1_0 = 1.0 + 0j
a2_0 = 20 + 0j
a3_0 = 0.0 + 0j

y0 = [a1_0, a2_0, a3_0]

# Um período da aproximação analítica ocorre em tau = |a2(0)| xi de 0 a pi.
xi_max = np.pi / abs(a2_0)
sol = resolver_sfg(y0, xi_max)
phi1, phi2, phi3 = fluxos(sol)

eta = phi3 / phi1[0]

tau = abs(a2_0) * sol.t
eta_analitica = np.sin(tau)**2

PASTA_FIGURAS.mkdir(exist_ok=True)

fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(tau, eta, label="Solução numérica")
ax.plot(tau, eta_analitica, "--", label="Aproximação analítica")

ax.set_xlabel(r"$g|a_2(0)|z$")
ax.set_ylabel(r"$\eta_{\mathrm{SFG}}$")
ax.legend()
ax.grid(True)

fig.tight_layout()
fig.savefig(PASTA_FIGURAS / "q4a_sfg_eficiencia.png", dpi=300, bbox_inches="tight")

conservacao_13 = phi1 + phi3
conservacao_23 = phi2 + phi3

erro_13 = np.max(np.abs(conservacao_13 - conservacao_13[0]))
erro_23 = np.max(np.abs(conservacao_23 - conservacao_23[0]))
deplecao_bomba = 1 - np.min(phi2) / phi2[0]

print(f"Erro máximo em Phi1 + Phi3: {erro_13:.2e}")
print(f"Erro máximo em Phi2 + Phi3: {erro_23:.2e}")
print(f"Depleção máxima relativa da bomba: {100 * deplecao_bomba:.3f}%")


# Intervalo maior para visualizar a troca de fluxo entre as três ondas.
xi_max_longo = 4 * np.pi / abs(a2_0)
sol_longo = resolver_sfg(y0, xi_max_longo, n_pontos=2000)
phi1_longo, phi2_longo, phi3_longo = fluxos(sol_longo)
tau_longo = abs(a2_0) * sol_longo.t

fig, ax = plt.subplots(figsize=(8, 5))

ax.plot(tau_longo, phi1_longo / phi1_longo[0], label=r"$\Phi_1/\Phi_1(0)$")
ax.plot(tau_longo, phi3_longo / phi1_longo[0], label=r"$\Phi_3/\Phi_1(0)$")
ax.plot(tau_longo, phi2_longo / phi2_longo[0], label=r"$\Phi_2/\Phi_2(0)$")

ax.set_xlabel(r"$g|a_2(0)|z$")
ax.set_ylabel("Fluxos normalizados")
ax.legend()
ax.grid(True)

fig.tight_layout()
fig.savefig(PASTA_FIGURAS / "q4a_sfg_fluxos_longo.png", dpi=300, bbox_inches="tight")

if MOSTRAR_GRAFICOS:
    plt.show()
else:
    plt.close("all")
