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

def clarke_wright_grasp(servicos, deposito, matriz_distancias, capacidade, k=3):
    """
    Variante GRASP do Clarke & Wright:
    - Em cada iteração, escolhe aleatoriamente entre os top-k savings disponíveis para tentar a fusão de rotas.
    - Mantém todas as restrições do Clarke & Wright clássico (capacidade, demanda, etc.).
    - Não perde nenhum serviço obrigatório.
    - Retorna rotas e demandas prontas para VND ou outras etapas.

    Parâmetros:
        servicos: lista de serviços obrigatórios
        deposito: índice do depósito
        matriz_distancias: matriz de distâncias do grafo
        capacidade: capacidade máxima do veículo
        k: número de savings do topo a considerar em cada passo (top-k)

    Retorna:
        rotas, demandas
    """

    # Inicializa cada serviço em uma rota separada
    rotas, demandas = construir_rotas_iniciais(servicos, deposito, matriz_distancias, capacidade)

    # Calcula e ordena savings (maior para menor) apenas uma vez
    savings = calcular_savings(servicos, deposito, matriz_distancias)

    # Mantém um conjunto de savings ainda disponíveis para fusão
    savings_disponiveis = savings[:]

    while savings_disponiveis:
        # Seleciona os top-k savings disponíveis (ou menos, se restarem poucos)
        top_k = savings_disponiveis[:k]
        saving_escolhido = random.choice(top_k)
        _, i, j = saving_escolhido

        # Encontra as rotas onde estão os serviços i e j
        idx_i = idx_j = None
        for idx, rota in enumerate(rotas):
            if rota and rota[0]['id_servico'] == servicos[i]['id_servico']:
                idx_i = idx
            if rota and rota[-1]['id_servico'] == servicos[j]['id_servico']:
                idx_j = idx

        # Só tenta fundir se as rotas são diferentes e a fusão respeita a capacidade
        if (
            idx_i is not None and idx_j is not None and idx_i != idx_j
            and demandas[idx_i] + demandas[idx_j] <= capacidade
        ):
            # Funde as rotas
            rotas[idx_i] = rotas[idx_i] + rotas[idx_j]
            demandas[idx_i] += demandas[idx_j]
            rotas[idx_j] = []
            demandas[idx_j] = 0

        # Remove o saving escolhido da lista (não tenta mais esse par)
        savings_disponiveis.remove(saving_escolhido)

    # Remove rotas vazias e sincroniza demandas
    rotas = [r for r in rotas if r]
    demandas = [d for r, d in zip(rotas, demandas) if r]

    # Validação final: todos os serviços obrigatórios devem estar presentes
    ids_esperados = set(s['id_servico'] for s in servicos)
    ids_nas_rotas = set(serv['id_servico'] for rota in rotas for serv in rota)
    if ids_esperados != ids_nas_rotas:
        raise Exception("Erro: serviços obrigatórios perdidos na construção GRASP!")

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


def multi_start_pipeline(
    servicos,
    deposito,
    matriz_distancias,
    capacidade,
    servicos_obrigatorios,
    k_grasp=3,
    num_tentativas=5
):
    """
    Multi-start controlado para o pipeline CARP:
    - Executa todo o pipeline (Clarke & Wright GRASP + VND + segment_relocate) múltiplas vezes,
      cada vez com uma seed diferente para a randomização do GRASP.
    - Em cada tentativa, gera uma solução completa (rotas finais e custo total).
    - Ao final, seleciona e retorna apenas a melhor solução (menor custo total, ou menos rotas em caso de empate).

    Parâmetros:
        servicos: lista de serviços obrigatórios
        deposito: índice do depósito
        matriz_distancias: matriz de distâncias do grafo
        capacidade: capacidade máxima do veículo
        servicos_obrigatorios: lista de todos os serviços obrigatórios (para validação)
        k_grasp: parâmetro top-k para o GRASP (default=3)
        num_tentativas: número de tentativas multi-start (default=5)

    Retorna:
        melhor_rotas, melhor_demandas
    """
    melhor_custo = float('inf')
    melhor_num_rotas = float('inf')
    melhor_rotas = None
    melhor_demandas = None

    for tentativa in range(num_tentativas):
        # Define uma seed diferente para cada tentativa para garantir diversidade
        random.seed(12345 + tentativa)

        # 1. Construção inicial com Clarke & Wright GRASP (com randomização controlada)
        rotas, demandas = clarke_wright_grasp(
            servicos, deposito, matriz_distancias, capacidade, k=k_grasp
        )

        # 2. Otimização local com VND (relocate + 2-opt)
        rotas_otimizadas, demandas_otimizadas = vnd(
            rotas, demandas, capacidade, matriz_distancias, deposito
        )

        # 3. Pós-processamento com realocação de segmentos (segment relocate)
        rotas_final, demandas_final = segment_relocate(
            rotas_otimizadas, demandas_otimizadas, capacidade, matriz_distancias, deposito, servicos_obrigatorios
        )

        # 4. Calcula custo total e número de rotas
        custo_total = sum(rota_custo(rota, matriz_distancias, deposito) for rota in rotas_final)
        num_rotas = len(rotas_final)

        # 5. Validação: todos os serviços obrigatórios devem estar presentes e sem duplicatas
        ids_esperados = set(s['id_servico'] for s in servicos_obrigatorios)
        ids_nas_rotas = [serv['id_servico'] for rota in rotas_final for serv in rota]
        if set(ids_nas_rotas) != ids_esperados or len(ids_nas_rotas) != len(set(ids_nas_rotas)):
            print(f"[Tentativa {tentativa+1}] Solução inválida: serviços perdidos ou duplicados!")
            continue

        # 6. Atualiza melhor solução se necessário (menor custo, depois menos rotas)
        if (custo_total < melhor_custo) or (custo_total == melhor_custo and num_rotas < melhor_num_rotas):
            melhor_custo = custo_total
            melhor_num_rotas = num_rotas
            melhor_rotas = [list(r) for r in rotas_final]
            melhor_demandas = list(demandas_final)
            print(f"[Tentativa {tentativa+1}] Nova melhor solução: custo {custo_total}, rotas {num_rotas}")

    # Mostra resultado final
    if melhor_rotas is not None:
        print(f"\nMelhor solução multi-start: custo {melhor_custo}, rotas {melhor_num_rotas}")
    else:
        print("Nenhuma solução válida encontrada!")

    return melhor_rotas, melhor_demandas

def segment_relocate(rotas, demandas, capacidade, matriz_distancias, deposito, servicos_obrigatorios):
    """
    Pós-processamento: realocação de segmentos (blocos contínuos) entre pares de rotas.
    - Para cada par de rotas, tenta mover blocos de 1 até n-1 serviços de uma rota para outra.
    - Só faz a realocação se não ultrapassar a capacidade e o custo total das duas rotas diminuir.
    - Repete até não haver mais melhorias.
    - Garante que nenhum serviço obrigatório é perdido ou duplicado.

    Parâmetros:
        rotas: lista de rotas (cada rota é uma lista de serviços)
        demandas: lista de demandas de cada rota
        capacidade: capacidade máxima do veículo
        matriz_distancias: matriz de distâncias do grafo
        deposito: índice do depósito
        servicos_obrigatorios: lista de todos os serviços obrigatórios (para validação)

    Retorna:
        rotas_finais, demandas_finais
    """
    melhorou = True
    while melhorou:
        melhorou = False
        # Percorre todos os pares de rotas distintas
        for i in range(len(rotas)):
            for j in range(len(rotas)):
                if i == j or not rotas[i] or not rotas[j]:
                    continue
                rota_origem = rotas[i]
                rota_destino = rotas[j]
                demanda_origem = demandas[i]
                demanda_destino = demandas[j]
                n = len(rota_origem)
                # Tenta todos os blocos possíveis (segmentos contínuos) de 1 até n-1 serviços
                for start in range(n):
                    for end in range(start + 1, n + 1):
                        bloco = rota_origem[start:end]
                        if not bloco or len(bloco) == n:
                            continue  # Não move rota inteira
                        demanda_bloco = sum(serv['demanda'] for serv in bloco)
                        if demanda_destino + demanda_bloco > capacidade:
                            continue
                        nova_rota_origem = rota_origem[:start] + rota_origem[end:]
                        nova_rota_destino = rota_destino + bloco
                        if not nova_rota_origem:
                            continue  # Não deixa rota vazia
                        # Calcula custos antes e depois
                        custo_antigo = rota_custo(rota_origem, matriz_distancias, deposito) + rota_custo(rota_destino, matriz_distancias, deposito)
                        custo_novo = rota_custo(nova_rota_origem, matriz_distancias, deposito) + rota_custo(nova_rota_destino, matriz_distancias, deposito)
                        if custo_novo < custo_antigo:
                            # Aplica movimento
                            rotas[i] = nova_rota_origem
                            rotas[j] = nova_rota_destino
                            demandas[i] = sum(serv['demanda'] for serv in nova_rota_origem)
                            demandas[j] = sum(serv['demanda'] for serv in nova_rota_destino)
                            melhorou = True
                            break  # Recomeça busca após melhoria
                    if melhorou:
                        break
                if melhorou:
                    break
            if melhorou:
                break
        # Remove rotas vazias e sincroniza demandas
        novas_rotas = []
        novas_demandas = []
        for r, d in zip(rotas, demandas):
            if r:
                novas_rotas.append(r)
                novas_demandas.append(d)
        rotas = novas_rotas
        demandas = novas_demandas

    # Validação final: todos os serviços obrigatórios devem estar presentes e sem duplicatas
    ids_esperados = set(s['id_servico'] for s in servicos_obrigatorios)
    ids_nas_rotas = [serv['id_servico'] for rota in rotas for serv in rota]
    if set(ids_nas_rotas) != ids_esperados or len(ids_nas_rotas) != len(set(ids_nas_rotas)):
        raise Exception("Erro: serviços obrigatórios perdidos ou duplicados após segment relocate!")

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