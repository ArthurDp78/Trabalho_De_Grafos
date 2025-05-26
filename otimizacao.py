def swap_entre_rotas(rotas, matriz_distancias, capacidade, deposito, max_iter=100):
    """
    Tenta trocar pares de serviços entre rotas diferentes para reduzir o custo total.
    """
    def demanda_rota(rota):
        return sum(servico["demanda"] for servico in rota)

    def custo_rota(rota):
        if not rota:
            return 0
        custo = matriz_distancias[deposito][rota[0]["origem"]]
        for i in range(len(rota) - 1):
            custo += matriz_distancias[rota[i]["destino"]][rota[i+1]["origem"]]
        custo += matriz_distancias[rota[-1]["destino"]][deposito]
        return custo

    iteracoes = 0
    melhorou = True
    while melhorou and iteracoes < max_iter:
        melhorou = False
        for i in range(len(rotas)):
            for j in range(i+1, len(rotas)):
                rota_a = rotas[i]
                rota_b = rotas[j]
                for idx_a, serv_a in enumerate(rota_a):
                    for idx_b, serv_b in enumerate(rota_b):
                        # Testa swap
                        nova_rota_a = rota_a[:idx_a] + [serv_b] + rota_a[idx_a+1:]
                        nova_rota_b = rota_b[:idx_b] + [serv_a] + rota_b[idx_b+1:]
                        if (demanda_rota(nova_rota_a) <= capacidade and
                            demanda_rota(nova_rota_b) <= capacidade):
                            custo_antigo = custo_rota(rota_a) + custo_rota(rota_b)
                            custo_novo = custo_rota(nova_rota_a) + custo_rota(nova_rota_b)
                            if custo_novo < custo_antigo:
                                rotas[i] = nova_rota_a
                                rotas[j] = nova_rota_b
                                melhorou = True
                                break
                    if melhorou:
                        break
                if melhorou:
                    break
            if melhorou:
                break
        iteracoes += 1
    return rotas