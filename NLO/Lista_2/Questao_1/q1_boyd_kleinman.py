"""Otimização numérica da integral de Boyd--Kleinman para SHG.

O modelo considera feixes Gaussianos colineares, foco no centro do cristal,
ausência de walk-off e aproximação de bomba não depletada. A normalização é

    xi = L / b,                 b = 2 z_R
    sigma = Delta_k b / 2
    h(xi, sigma) = |integral_{-xi}^{xi}
                    exp(i sigma tau)/(1+i tau) d tau|^2 / (4 xi).

Para executar:
    python q1_boyd_kleinman.py

As figuras são gravadas em ../figuras_lno/.
"""

from pathlib import Path
from functools import lru_cache

import matplotlib.pyplot as plt
import numpy as np


PASTA_FIGURAS = Path(__file__).resolve().parent / "figures"
MOSTRAR_GRAFICOS = False


@lru_cache(maxsize=None)
def nos_legendre(n_pontos):
    """Reutiliza os nós e pesos em todas as avaliações da otimização."""
    return np.polynomial.legendre.leggauss(n_pontos)


def integral_bk(xi, sigma, n_pontos=240):
    """Integral complexa de sobreposição por quadratura de Gauss-Legendre."""
    nos, pesos = nos_legendre(n_pontos)
    tau = xi * nos
    integrando = np.exp(1j * sigma * tau) / (1.0 + 1j * tau)
    return xi * np.sum(pesos * integrando)


def h_bk(xi, sigma, n_pontos=240):
    """Função de focalização de Boyd--Kleinman (sem walk-off)."""
    if xi <= 0:
        raise ValueError("xi deve ser positivo.")
    return abs(integral_bk(xi, sigma, n_pontos)) ** 2 / (4.0 * xi)


def secao_aurea_maximo(funcao, a, b, tolerancia=1e-8):
    """Maximiza uma função unimodal no intervalo [a,b], sem usar SciPy."""
    razao = (np.sqrt(5.0) - 1.0) / 2.0
    c = b - razao * (b - a)
    d = a + razao * (b - a)
    fc, fd = funcao(c), funcao(d)

    while b - a > tolerancia:
        if fc > fd:
            b, d, fd = d, c, fc
            c = b - razao * (b - a)
            fc = funcao(c)
        else:
            a, c, fc = c, d, fd
            d = a + razao * (b - a)
            fd = funcao(d)

    x = (a + b) / 2.0
    return x, funcao(x)


def otimizar_bk():
    """Otimização aninhada em sigma e xi."""
    def melhor_sigma(xi):
        sigma, h = secao_aurea_maximo(
            lambda valor: h_bk(xi, valor), -1.0, 2.0, tolerancia=2e-7
        )
        return sigma, h

    xi_otimo, _ = secao_aurea_maximo(
        lambda valor: melhor_sigma(valor)[1],
        0.10,
        8.0,
        tolerancia=2e-6,
    )
    sigma_otimo, h_otimo = melhor_sigma(xi_otimo)
    return xi_otimo, sigma_otimo, h_otimo


def gerar_figuras(xi_otimo, sigma_otimo, h_otimo):
    PASTA_FIGURAS.mkdir(exist_ok=True)

    # Mapa bidimensional. A quadratura vetorizada deixa esta etapa rápida.
    xis = np.linspace(0.10, 6.0, 260)
    sigmas = np.linspace(-1.0, 2.0, 240)
    nos, pesos = nos_legendre(180)
    mapa = np.empty((len(sigmas), len(xis)))

    for j, xi in enumerate(xis):
        tau = xi * nos
        base = pesos / (1.0 + 1j * tau)
        integrais = xi * (
            np.exp(1j * np.outer(sigmas, tau)) @ base
        )
        mapa[:, j] = np.abs(integrais) ** 2 / (4.0 * xi)

    fig, ax = plt.subplots(figsize=(8.2, 5.4))
    contorno = ax.contourf(xis, sigmas, mapa / h_otimo, 40, cmap="viridis")
    fig.colorbar(contorno, ax=ax, label=r"$h(\xi,\sigma)/h_{\max}$")
    ax.plot(
        xi_otimo,
        sigma_otimo,
        "r*",
        ms=14,
        label=rf"máximo: $\xi={xi_otimo:.3f}$, $\sigma={sigma_otimo:.3f}$",
    )
    ax.set(
        xlabel=r"parâmetro de focalização $\xi=L/b$",
        ylabel=r"descasamento normalizado $\sigma=\Delta k\,b/2$",
        title="Otimização da integral de Boyd–Kleinman",
    )
    ax.legend(loc="upper right")
    fig.tight_layout()
    fig.savefig(PASTA_FIGURAS / "q1_boyd_kleinman_mapa.png", dpi=220)

    # Cortes que tornam visíveis tanto o ótimo em xi quanto o deslocamento
    # do casamento de fase devido à fase de Gouy.
    h_xi_otimo = np.array([h_bk(xi, sigma_otimo, 180) for xi in xis])
    h_xi_delta_k_zero = np.array([h_bk(xi, 0.0, 180) for xi in xis])
    sigma_corte = np.linspace(-1.0, 2.0, 350)
    h_sigma = np.array(
        [h_bk(xi_otimo, sigma, 180) for sigma in sigma_corte]
    )

    fig, eixos = plt.subplots(1, 2, figsize=(10.4, 4.1))
    eixos[0].plot(xis, h_xi_otimo, label=rf"$\sigma={sigma_otimo:.3f}$")
    eixos[0].plot(xis, h_xi_delta_k_zero, "--", label=r"$\sigma=0$")
    eixos[0].axvline(xi_otimo, color="0.35", ls=":", lw=1)
    eixos[0].set(
        xlabel=r"$\xi=L/b$",
        ylabel=r"$h(\xi,\sigma)$",
        title="Otimização da focalização",
    )
    eixos[0].legend()

    eixos[1].plot(sigma_corte, h_sigma)
    eixos[1].axvline(sigma_otimo, color="0.35", ls=":", lw=1)
    eixos[1].axvline(0.0, color="tab:red", ls="--", lw=1, label=r"$\Delta k=0$")
    eixos[1].set(
        xlabel=r"$\sigma=\Delta k\,b/2$",
        ylabel=r"$h(\xi_{\rm opt},\sigma)$",
        title="Compensação da fase de Gouy",
    )
    eixos[1].legend()
    fig.tight_layout()
    fig.savefig(PASTA_FIGURAS / "q1_boyd_kleinman_cortes.png", dpi=220)

    if MOSTRAR_GRAFICOS:
        plt.show()
    else:
        plt.close("all")


def main():
    xi_otimo, sigma_otimo, h_otimo = otimizar_bk()
    h_delta_k_zero = h_bk(xi_otimo, 0.0)

    print(f"xi ótimo       = {xi_otimo:.6f}")
    print(f"sigma ótimo    = {sigma_otimo:.6f}")
    print(f"h máximo       = {h_otimo:.6f}")
    print(f"h(xi ótimo, 0) = {h_delta_k_zero:.6f}")
    print(
        "ganho pela compensação de Gouy = "
        f"{100 * (h_otimo / h_delta_k_zero - 1):.2f}%"
    )

    gerar_figuras(xi_otimo, sigma_otimo, h_otimo)
    print(f"Figuras gravadas em: {PASTA_FIGURAS}")


if __name__ == "__main__":
    main()
