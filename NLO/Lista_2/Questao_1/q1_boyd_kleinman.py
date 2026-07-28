"""Busca numérica do máximo da função de Boyd--Kleinman para SHG."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


PASTA_FIGURAS = Path(__file__).resolve().parent / "figures"
MOSTRAR_GRAFICOS = False


def mapa_boyd_kleinman(xis, sigmas, n_pontos=240):
    """Calcula h(xi,sigma) numa malha usando quadratura de Gauss--Legendre."""
    nos, pesos = np.polynomial.legendre.leggauss(n_pontos)
    mapa = np.empty((len(sigmas), len(xis)))

    for j, xi in enumerate(xis):
        tau = xi * nos
        integrais = xi * (
            np.exp(1j * np.outer(sigmas, tau))
            @ (pesos / (1.0 + 1j * tau))
        )
        mapa[:, j] = np.abs(integrais) ** 2 / (4.0 * xi)

    return mapa


def localizar_maximo(xis, sigmas, mapa):
    """Retorna xi, sigma e h no maior elemento da malha."""
    i_sigma, i_xi = np.unravel_index(np.argmax(mapa), mapa.shape)
    return xis[i_xi], sigmas[i_sigma], mapa[i_sigma, i_xi]


def otimizar(n_pontos=240):
    """Faz uma busca grosseira e depois refina ao redor do melhor ponto."""
    xis_grossos = np.linspace(0.10, 6.0, 120)
    sigmas_grossos = np.linspace(-1.0, 2.0, 121)
    mapa_grosso = mapa_boyd_kleinman(
        xis_grossos, sigmas_grossos, n_pontos
    )
    xi_c, sigma_c, _ = localizar_maximo(
        xis_grossos, sigmas_grossos, mapa_grosso
    )

    passo_xi = xis_grossos[1] - xis_grossos[0]
    passo_sigma = sigmas_grossos[1] - sigmas_grossos[0]
    xis_finos = np.linspace(xi_c - passo_xi, xi_c + passo_xi, 301)
    sigmas_finos = np.linspace(
        sigma_c - passo_sigma, sigma_c + passo_sigma, 301
    )
    mapa_fino = mapa_boyd_kleinman(xis_finos, sigmas_finos, n_pontos)

    return localizar_maximo(xis_finos, sigmas_finos, mapa_fino)


def h_em_pontos(xis, sigmas, n_pontos=240):
    """Avalia h em pares (xi,sigma), sem construir uma malha cartesiana."""
    nos, pesos = np.polynomial.legendre.leggauss(n_pontos)
    valores = []

    for xi, sigma in zip(xis, sigmas):
        tau = xi * nos
        integral = xi * np.sum(
            pesos * np.exp(1j * sigma * tau) / (1.0 + 1j * tau)
        )
        valores.append(abs(integral) ** 2 / (4.0 * xi))

    return np.asarray(valores)


def gerar_figuras(xi_otimo, sigma_otimo, h_otimo):
    PASTA_FIGURAS.mkdir(exist_ok=True)

    xis = np.linspace(0.10, 6.0, 220)
    sigmas = np.linspace(-1.0, 2.0, 220)
    mapa = mapa_boyd_kleinman(xis, sigmas)

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

    xis_corte = np.linspace(0.10, 6.0, 300)
    h_xi_otimo = h_em_pontos(
        xis_corte, np.full_like(xis_corte, sigma_otimo)
    )
    h_xi_delta_k_zero = h_em_pontos(
        xis_corte, np.zeros_like(xis_corte)
    )
    sigmas_corte = np.linspace(-1.0, 2.0, 350)
    h_sigma = h_em_pontos(
        np.full_like(sigmas_corte, xi_otimo), sigmas_corte
    )

    fig, eixos = plt.subplots(1, 2, figsize=(10.4, 4.1))
    eixos[0].plot(
        xis_corte, h_xi_otimo, label=rf"$\sigma={sigma_otimo:.3f}$"
    )
    eixos[0].plot(
        xis_corte, h_xi_delta_k_zero, "--", label=r"$\sigma=0$"
    )
    eixos[0].axvline(xi_otimo, color="0.35", ls=":", lw=1)
    eixos[0].set(
        xlabel=r"$\xi=L/b$",
        ylabel=r"$h(\xi,\sigma)$",
        title="Otimização da focalização",
    )
    eixos[0].legend()

    eixos[1].plot(sigmas_corte, h_sigma)
    eixos[1].axvline(sigma_otimo, color="0.35", ls=":", lw=1)
    eixos[1].axvline(
        0.0, color="tab:red", ls="--", lw=1, label=r"$\Delta k=0$"
    )
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
    resultados = {}
    for n_pontos in (120, 240, 480):
        resultados[n_pontos] = otimizar(n_pontos)
        xi, sigma, h = resultados[n_pontos]
        print(
            f"{n_pontos:3d} pontos: "
            f"xi={xi:.6f}, sigma={sigma:.6f}, h={h:.6f}"
        )

    xi_otimo, sigma_otimo, h_otimo = resultados[240]
    h_delta_k_zero = h_em_pontos([xi_otimo], [0.0])[0]
    print(f"h(xi ótimo, 0) = {h_delta_k_zero:.6f}")

    gerar_figuras(xi_otimo, sigma_otimo, h_otimo)
    print(f"Figuras gravadas em: {PASTA_FIGURAS}")


if __name__ == "__main__":
    main()
