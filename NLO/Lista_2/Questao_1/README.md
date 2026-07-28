# Questão 1 — critério de Boyd--Kleinman

Simulação numérica da integral de sobreposição para geração de segundo harmônico com feixes gaussianos.

O programa otimiza a função

```text
h(xi, sigma) = |integral(exp(i sigma tau)/(1 + i tau), -xi, xi)|² / (4 xi)
```

Uma busca numa malha ampla, seguida por uma malha fina ao redor do maior
ponto, encontra aproximadamente

```text
xi ótimo    = 2.8371
sigma ótimo = 0.5737
h máximo    = 1.0677
```

A convergência é verificada repetindo a quadratura com 120, 240 e 480
pontos. Os valores acima não mudam de forma relevante.

## Execução

O script requer Python, NumPy e Matplotlib:

```bash
python -m pip install numpy matplotlib
python q1_boyd_kleinman.py
```

As figuras são gravadas na pasta `figures/`.

## Arquivos

- `q1_boyd_kleinman.py`: integração, otimização e geração dos gráficos
- `figures/q1_boyd_kleinman_mapa.png`: mapa bidimensional da função de focalização
- `figures/q1_boyd_kleinman_cortes.png`: cortes mostrando a focalização ótima e a compensação da fase de Gouy
