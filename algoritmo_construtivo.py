import random
import copy

def construir_rotas_iniciais(servicos, deposito, matriz_distancias, capacidade):
    rotas = []
    demandas = []
    for serv in servicos:
        demanda = serv['demanda']
        rotas.append([serv])
        demandas.append(demanda)
    return rotas, demandas

def rota_custo(rota, matriz_distancias, deposito):
    if not rota:
        return 0
    custo_servico = sum(serv['custo_servico'] for serv in rota)
    destinos = [serv['destino'] for serv in rota]
    custo_transporte = matriz_distancias[deposito][destinos[0]]
    for i in range(len(destinos) - 1):
        custo_transporte += matriz_distancias[destinos[i]][destinos[i+1]]
    custo_transporte += matriz_distancias[destinos[-1]][deposito]
    return custo_servico + custo_transporte

def calcular_savings(servicos, deposito, matriz_distancias):
    savings = []
    n = len(servicos)
    for i in range(n):
        for j in range(i+1, n):
            s_i = servicos[i]
            s_j = servicos[j]
            saving = (
                matriz_distancias[deposito][s_i['destino']]
                + matriz_distancias[deposito][s_j['destino']]
                - matriz_distancias[s_i['destino']][s_j['destino']]
            )
            savings.append((saving, i, j))
    savings.sort(reverse=True)
    return savings

def clarke_wright(servicos, deposito, matriz_distancias, capacidade):
    rotas, demandas = construir_rotas_iniciais(servicos, deposito, matriz_distancias, capacidade)
    savings = calcular_savings(servicos, deposito, matriz_distancias)
    for saving, i, j in savings:
        # Encontra as rotas onde estão os serviços i e j
        idx_i = idx_j = None
        for idx, rota in enumerate(rotas):
            if rota and rota[0]['id_servico'] == servicos[i]['id_servico']:
                idx_i = idx
            if rota and rota[-1]['id_servico'] == servicos[j]['id_servico']:
                idx_j = idx
        if idx_i is not None and idx_j is not None and idx_i != idx_j:
            # Verifica se pode unir as rotas
            if demandas[idx_i] + demandas[idx_j] <= capacidade:
                # Junta as rotas
                rotas[idx_i] = rotas[idx_i] + rotas[idx_j]
                demandas[idx_i] += demandas[idx_j]
                rotas[idx_j] = []
                demandas[idx_j] = 0
    # Remove rotas vazias
    rotas = [r for r in rotas if r]
    demandas = [d for r, d in zip(rotas, demandas) if r]
    return rotas, demandas

def relocate(rotas, demandas, capacidade, matriz_distancias, deposito):
    melhorou = True
    while melhorou:
        melhorou = False
        for i in range(len(rotas)):
            for j in range(len(rotas)):
                if i == j or not rotas[i]:
                    continue
                for idx, serv in enumerate(rotas[i]):
                    if demandas[j] + serv['demanda'] <= capacidade:
                        nova_rota_i = rotas[i][:idx] + rotas[i][idx+1:]
                        nova_rota_j = rotas[j] + [serv]
                        if not nova_rota_i:
                            continue
                        custo_antigo = rota_custo(rotas[i], matriz_distancias, deposito) + rota_custo(rotas[j], matriz_distancias, deposito)
                        custo_novo = rota_custo(nova_rota_i, matriz_distancias, deposito) + rota_custo(nova_rota_j, matriz_distancias, deposito)
                        if custo_novo < custo_antigo:
                            rotas[i] = nova_rota_i
                            rotas[j] = nova_rota_j
                            demandas[i] -= serv['demanda']
                            demandas[j] += serv['demanda']
                            melhorou = True
                            break
                if melhorou:
                    break
            if melhorou:
                break
    rotas = [r for r in rotas if r]
    demandas = [d for r, d in zip(rotas, demandas) if r]
    return rotas, demandas

def two_opt(rota, matriz_distancias, deposito):
    if len(rota) < 3:
        return rota
    melhorou = True
    melhor_rota = rota[:]
    while melhorou:
        melhorou = False
        for i in range(1, len(melhor_rota) - 1):
            for j in range(i + 1, len(melhor_rota)):
                nova_rota = melhor_rota[:i] + melhor_rota[i:j][::-1] + melhor_rota[j:]
                if rota_custo(nova_rota, matriz_distancias, deposito) < rota_custo(melhor_rota, matriz_distancias, deposito):
                    melhor_rota = nova_rota
                    melhorou = True
        if melhorou:
            break
    return melhor_rota

def vnd(rotas, demandas, capacidade, matriz_distancias, deposito):
    rotas, demandas = relocate(rotas, demandas, capacidade, matriz_distancias, deposito)
    for i in range(len(rotas)):
        rotas[i] = two_opt(rotas[i], matriz_distancias, deposito)
    return rotas, demandas

def salvar_solucao(
    nome_arquivo,
    rotas,
    matriz_distancias,
    tempo_referencia_execucao,
    tempo_referencia_solucao,
    deposito=0,
):
    custo_total_solucao = 0
    total_rotas = len(rotas)
    linhas_rotas = []

    for idx_rota, rota in enumerate(rotas, start=1):
        servicos_unicos = {}
        demanda_rota = 0
        custo_servico_rota = 0
        custo_transporte_rota = 0

        destinos = []

        for serv in rota:
            id_s = serv["id_servico"]
            if id_s in servicos_unicos:
                continue
            servicos_unicos[id_s] = serv
            demanda_rota += serv["demanda"]
            custo_servico_rota += serv["custo_servico"]
            destinos.append(serv["destino"])

        if destinos:
            custo_transporte_rota += matriz_distancias[deposito][destinos[0]]
            for i in range(len(destinos) - 1):
                custo_transporte_rota += matriz_distancias[destinos[i]][destinos[i + 1]]
            custo_transporte_rota += matriz_distancias[destinos[-1]][deposito]

        custo_rota = custo_servico_rota + custo_transporte_rota
        custo_total_solucao += custo_rota

        total_visitas = 2 + len(servicos_unicos)

        linha = f"0 1 {idx_rota} {demanda_rota} {custo_rota} {total_visitas} (D {deposito},1,1)"

        servicos_impressos = set()
        for serv in rota:
            id_s = serv["id_servico"]
            if id_s in servicos_impressos:
                continue
            servicos_impressos.add(id_s)
            linha += f" (S {id_s},{serv['origem']},{serv['destino']})"

        linha += f" (D {deposito},1,1)"
        linhas_rotas.append(linha)

    with open(nome_arquivo, "w", encoding="utf-8") as f:
        f.write(f"{custo_total_solucao}\n")
        f.write(f"{total_rotas}\n")
        f.write(f"{tempo_referencia_execucao}\n")
        f.write(f"{tempo_referencia_solucao}\n")
        for linha in linhas_rotas:
            f.write(linha + "\n")

    print(f"Solução salva em '{nome_arquivo}' com {total_rotas} rotas e custo total {custo_total_solucao}.")