from pathlib import Path
from types import SimpleNamespace

import matplotlib.pyplot as plt
import numpy as np


PASTA_FIGURAS = Path(__file__).resolve().parent / "figures"

# Troque para True se quiser abrir as figuras ao rodar o script.
MOSTRAR_GRAFICOS = False


def indice_extraordinario_ln(lambda_um):
    """
    Indice extraordinario do LiNbO3 congruente a temperatura ambiente.

    A forma usada e uma parametrizacao de Sellmeier comum para o eixo
    extraordinario:
        n_e^2 = 4.5820 + 0.099169/(lambda^2 - 0.04443) - 0.021950 lambda^2
    com lambda em micrometros.
    """
    lambda2 = lambda_um**2
    return np.sqrt(4.5820 + 0.099169 / (lambda2 - 0.04443) - 0.021950 * lambda2)


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


def resolver_spdc(y0, z, g):
    """
    Resolve as equacoes de tres ondas para DFG/SPDC com Delta k = 0.

    As amplitudes sao normalizadas de modo que Phi_j = |a_j|^2 e o fluxo de
    fotons. A onda 3 e a bomba, enquanto as ondas 1 e 2 sao sinal e idler.
    """

    def equacoes(_z, y):
        a1, a2, a3 = y

        da1_dz = 1j * g * np.conj(a2) * a3
        da2_dz = 1j * g * np.conj(a1) * a3
        da3_dz = 1j * g * a1 * a2

        return [da1_dz, da2_dz, da3_dz]

    y = rk4(equacoes, y0, z)
    return SimpleNamespace(z=z, y=y)


def fluxos(sol):
    """Calcula Phi_j = |a_j|^2."""
    return np.abs(sol.y[0]) ** 2, np.abs(sol.y[1]) ** 2, np.abs(sol.y[2]) ** 2


def erro_manley_rowe(phi1, phi2, phi3):
    """Erro relativo nas duas relacoes de Manley-Rowe nao degeneradas."""
    m13 = phi1 + phi3
    m23 = phi2 + phi3
    erro_13 = np.max(np.abs(m13 / m13[0] - 1))
    erro_23 = np.max(np.abs(m23 / m23[0] - 1))
    return max(erro_13, erro_23)


def main():
    # Parametros fisicos do problema.
    hbar = 1.054571817e-34
    epsilon0 = 8.8541878128e-12
    c = 299792458.0

    comprimento_cristal = 20e-3
    potencia_bomba = 1e-3
    raio_feixe = 50e-6
    area = np.pi * raio_feixe**2

    # Hipotese degenerada em telecom: 775 nm -> 1550 nm + 1550 nm.
    lambda1 = 1550e-9
    lambda2 = 1550e-9
    lambda3 = 775e-9

    omega1 = 2 * np.pi * c / lambda1
    omega2 = 2 * np.pi * c / lambda2
    omega3 = 2 * np.pi * c / lambda3

    n1 = indice_extraordinario_ln(lambda1 * 1e6)
    n2 = indice_extraordinario_ln(lambda2 * 1e6)
    n3 = indice_extraordinario_ln(lambda3 * 1e6)

    d33 = 27e-12
    d_eff = 2 * d33 / np.pi

    # Constante de acoplamento para amplitudes normalizadas em fluxo de fotons.
    g = d_eff * np.sqrt(
        hbar * omega1 * omega2 * omega3
        / (2 * epsilon0 * c**3 * area * n1 * n2 * n3)
    )

    fluxo_bomba = potencia_bomba / (hbar * omega3)

    # Energia de vacuo por modo: U = (1/2) hbar omega.
    # Para uma janela temporal tau = 1/Delta_nu, isso corresponde a
    # Phi_vac = U/(hbar omega tau) = Delta_nu/2.
    largura_banda = 100e9
    tau = 1 / largura_banda
    fluxo_vacuo = 1 / (2 * tau)

    z = np.linspace(0, comprimento_cristal, 3000)

    # A fase do vacuo nao e definida. Fazemos uma media deterministica sobre
    # a fase relativa entre os campos semente para remover a amplificacao
    # sensivel a fase de uma realizacao especifica.
    n_fases = 128
    fases = np.linspace(0, 2 * np.pi, n_fases, endpoint=False)

    phi1_media = np.zeros_like(z)
    phi2_media = np.zeros_like(z)
    phi3_media = np.zeros_like(z)
    erro_mr = 0.0

    for fase in fases:
        y0 = [
            np.sqrt(fluxo_vacuo) * np.exp(1j * fase),
            np.sqrt(fluxo_vacuo),
            np.sqrt(fluxo_bomba),
        ]
        sol = resolver_spdc(y0, z, g)
        phi1, phi2, phi3 = fluxos(sol)

        phi1_media += phi1 / n_fases
        phi2_media += phi2 / n_fases
        phi3_media += phi3 / n_fases
        erro_mr = max(erro_mr, erro_manley_rowe(phi1, phi2, phi3))

    ganho = g * np.sqrt(fluxo_bomba) * z
    fluxo_gerado_analitico = largura_banda * np.sinh(ganho) ** 2

    fluxo_sinal_gerado = phi1_media - fluxo_vacuo
    fluxo_idler_gerado = phi2_media - fluxo_vacuo
    fluxo_pares_final = 0.5 * (fluxo_sinal_gerado[-1] + fluxo_idler_gerado[-1])
    fluxo_pares_analitico = fluxo_gerado_analitico[-1]
    deplecao_bomba = (fluxo_bomba - phi3_media[-1]) / fluxo_bomba

    PASTA_FIGURAS.mkdir(exist_ok=True)

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(z * 1e3, fluxo_sinal_gerado, label="Sinal, media numerica")
    ax.plot(z * 1e3, fluxo_idler_gerado, "--", label="Idler, media numerica")
    ax.plot(z * 1e3, fluxo_gerado_analitico, ":", color="black", label="Aproximacao analitica")
    ax.set_xlabel("z (mm)")
    ax.set_ylabel("Fluxo gerado acima do vacuo (fotons/s)")
    ax.grid(True)
    ax.legend()
    fig.tight_layout()
    fig.savefig(PASTA_FIGURAS / "q4e_spdc_fluxo.png", dpi=300, bbox_inches="tight")

    print("4.e)")
    print(f"lambda_sinal = lambda_idler = {lambda1 * 1e9:.1f} nm")
    print(f"lambda_bomba = {lambda3 * 1e9:.1f} nm")
    print(f"n1 = n2 = {n1:.4f}, n3 = {n3:.4f}")
    print(f"d_eff = {d_eff * 1e12:.2f} pm/V")
    print(f"g = {g:.3e} m^-1 (fotons/s)^-1/2")
    print(f"Fluxo da bomba: {fluxo_bomba:.3e} fotons/s")
    print(f"Fluxo de vacuo por modo: {fluxo_vacuo:.3e} fotons/s")
    print(f"Ganho parametrico r = g sqrt(Phi_bomba) L: {ganho[-1]:.3e}")
    print(f"Fluxo final do sinal: {phi1_media[-1]:.6e} fotons/s")
    print(f"Fluxo final do idler: {phi2_media[-1]:.6e} fotons/s")
    print(f"Fluxo SPDC gerado, numerico: {fluxo_pares_final:.3e} pares/s")
    print(f"Fluxo SPDC gerado, analitico: {fluxo_pares_analitico:.3e} pares/s")
    print(f"Deplecao relativa da bomba: {deplecao_bomba:.3e}")
    print(f"Erro maximo nas relacoes de Manley-Rowe: {erro_mr:.2e}")

    if MOSTRAR_GRAFICOS:
        plt.show()
    else:
        plt.close("all")


if __name__ == "__main__":
    main()
