import random
from copy import deepcopy
from algoritmo_construtivo import algoritmo_clarke_wright

def custo_total(rotas, matriz_distancias, deposito):
    custo = 0
    for rota in rotas:
        if not rota:
            continue
        custo += matriz_distancias[deposito][rota[0]["origem"]]
        for i in range(len(rota) - 1):
            custo += matriz_distancias[rota[i]["destino"]][rota[i+1]["origem"]]
        custo += matriz_distancias[rota[-1]["destino"]][deposito]
    return custo

def busca_local_2opt(rotas, matriz_distancias, deposito, max_iter=5):
    # Aplica 2-opt em cada rota individualmente, limitado por max_iter
    for rota in rotas:
        if len(rota) < 4:
            continue
        iteracoes = 0
        melhorou = True
        while melhorou and iteracoes < max_iter:
            melhorou = False
            n = len(rota)
            for i in range(n - 1):
                for j in range(i + 2, n):
                    nova_rota = rota[:i+1] + rota[i+1:j+1][::-1] + rota[j+1:]
                    custo_antigo = (
                        matriz_distancias[deposito][rota[0]["origem"]] +
                        sum(matriz_distancias[rota[k]["destino"]][rota[k+1]["origem"]] for k in range(n-1)) +
                        matriz_distancias[rota[-1]["destino"]][deposito]
                    )
                    custo_novo = (
                        matriz_distancias[deposito][nova_rota[0]["origem"]] +
                        sum(matriz_distancias[nova_rota[k]["destino"]][nova_rota[k+1]["origem"]] for k in range(n-1)) +
                        matriz_distancias[nova_rota[-1]["destino"]][deposito]
                    )
                    if custo_novo < custo_antigo:
                        rota[:] = nova_rota
                        melhorou = True
                        break
                if melhorou:
                    break
            iteracoes += 1
    return rotas

def grasp(
    servicos,
    deposito,
    matriz_distancias,
    capacidade,
    max_iter=30,
    alpha=0.3
):
    melhor_solucao = None
    melhor_custo = float("inf")

    for _ in range(max_iter):
        # Randomização: embaralha os serviços antes do construtivo
        servicos_random = servicos[:]
        random.shuffle(servicos_random)

        # Construtivo guloso randomizado (pode adaptar o Clarke-Wright para usar alpha)
        rotas = algoritmo_clarke_wright(
            servicos_random,
            deposito=deposito,
            matriz_distancias=matriz_distancias,
            capacidade=capacidade
        )

        # Busca local (2-opt) otimizada
        rotas = busca_local_2opt(rotas, matriz_distancias, deposito, max_iter=5)

        custo = custo_total(rotas, matriz_distancias, deposito)
        if custo < melhor_custo:
            melhor_custo = custo
            melhor_solucao = deepcopy(rotas)

    return melhor_solucao