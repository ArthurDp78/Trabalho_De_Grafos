import heapq
import random
import time
import math  # para teto divisão
from copy import deepcopy

def preparar_clientes(vertices_req, arestas_req, arcos_req):
    clientes = []
    id_servico = 1
    for v, (demanda, custo_servico) in vertices_req:
        clientes.append({'tipo': 'n', 'id': id_servico, 'origem': v, 'destino': v, 'demanda': demanda, 'custo': custo_servico})
        id_servico += 1
    for (u, v), (custo_transporte, demanda, custo_servico) in arestas_req:
        clientes.append({'tipo': 'e', 'id': id_servico, 'origem': u, 'destino': v, 'demanda': demanda, 'custo': custo_servico})
        id_servico += 1
    for (u, v), (custo_transporte, demanda, custo_servico) in arcos_req:
        clientes.append({'tipo': 'a', 'id': id_servico, 'origem': u, 'destino': v, 'demanda': demanda, 'custo': custo_servico})
        id_servico += 1
    return clientes

def inicializar_rotas(clientes, deposito, distancias):
    rotas = []
    for cliente in clientes:
        rota = {
            'clientes': [cliente],
            'demanda_total': cliente['demanda'],
            'servicos': {(cliente['tipo'], cliente['id'])},
            'sequencia': [deposito, cliente['origem'], cliente['destino'], deposito]
        }
        rotas.append(rota)
    return rotas

def calcular_savings_inicial(rotas, distancias, deposito, capacidade):
    savings = []
    n = len(rotas)
    for i in range(n):
        for j in range(i+1, n):
            if rotas[i]['demanda_total'] + rotas[j]['demanda_total'] > capacidade:
                continue
            fim_i = rotas[i]['sequencia'][-2]
            ini_j = rotas[j]['sequencia'][1]
            saving = distancias[fim_i][deposito] + distancias[deposito][ini_j] - distancias[fim_i][ini_j]
            heapq.heappush(savings, (-saving, i, j))
    return savings

def juntar_rotas_com_heap(rotas, distancias, deposito, capacidade, ganho_minimo=0.1, max_clientes_rota=20):
    savings = calcular_savings_inicial(rotas, distancias, deposito, capacidade)
    rotas_ativas = {i for i in range(len(rotas))}
    mapa_rota = {i: rotas[i] for i in rotas_ativas}

    demanda_total = sum(r['demanda_total'] for r in rotas)
    minimo_rotas = math.ceil(demanda_total / capacidade)

    while savings and len(rotas_ativas) > minimo_rotas:
        neg_saving, i, j = heapq.heappop(savings)
        if i not in rotas_ativas or j not in rotas_ativas:
            continue

        rota_i = mapa_rota[i]
        rota_j = mapa_rota[j]

        if rota_i['demanda_total'] + rota_j['demanda_total'] > capacidade:
            continue
        if rota_i['servicos'] & rota_j['servicos']:
            continue
        if len(rota_i['clientes']) + len(rota_j['clientes']) > max_clientes_rota:
            continue

        seqs_candidatas = [
            rota_i['sequencia'][:-1] + rota_j['sequencia'][1:],
            rota_i['sequencia'][:-1] + rota_j['sequencia'][-2:0:-1] + [deposito],
            [deposito] + rota_i['sequencia'][-2:0:-1] + rota_j['sequencia'][1:],
            [deposito] + rota_i['sequencia'][-2:0:-1] + rota_j['sequencia'][-2:0:-1] + [deposito]
        ]
        custo_servico = sum(c['custo'] for c in rota_i['clientes'] + rota_j['clientes'])

        melhor_seq = None
        melhor_ganho = float('-inf')
        for seq in seqs_candidatas:
            if seq[0] != deposito or seq[-1] != deposito:
                continue
            custo_transporte = sum(distancias[seq[k]][seq[k+1]] for k in range(len(seq)-1))
            custo_total_novo = custo_transporte + custo_servico

            custo_transporte_antigo = (
                sum(distancias[rota_i['sequencia'][k]][rota_i['sequencia'][k+1]] for k in range(len(rota_i['sequencia'])-1)) +
                sum(distancias[rota_j['sequencia'][k]][rota_j['sequencia'][k+1]] for k in range(len(rota_j['sequencia'])-1))
            )
            custo_total_antigo = custo_transporte_antigo + custo_servico

            ganho = custo_total_antigo - custo_total_novo
            if ganho > melhor_ganho:
                melhor_ganho = ganho
                melhor_seq = seq

        if melhor_ganho < ganho_minimo or melhor_seq is None:
            continue

        nova_rota = {
            'clientes': rota_i['clientes'] + rota_j['clientes'],
            'demanda_total': rota_i['demanda_total'] + rota_j['demanda_total'],
            'servicos': rota_i['servicos'] | rota_j['servicos'],
            'sequencia': melhor_seq
        }
        nova_id = max(mapa_rota.keys()) + 1
        rotas_ativas.remove(i)
        rotas_ativas.remove(j)
        rotas_ativas.add(nova_id)
        mapa_rota[nova_id] = nova_rota

        for k in rotas_ativas:
            if k == nova_id:
                continue
            fim_nova = nova_rota['sequencia'][-2]
            ini_k = mapa_rota[k]['sequencia'][1]
            saving1 = distancias[fim_nova][deposito] + distancias[deposito][ini_k] - distancias[fim_nova][ini_k]
            fim_k = mapa_rota[k]['sequencia'][-2]
            ini_nova = nova_rota['sequencia'][1]
            saving2 = distancias[fim_k][deposito] + distancias[deposito][ini_nova] - distancias[fim_k][ini_nova]
            heapq.heappush(savings, (-saving1, nova_id, k))
            heapq.heappush(savings, (-saving2, k, nova_id))

    rotas_finais = [mapa_rota[i] for i in rotas_ativas]
    for rota in rotas_finais:
        if len(rota['sequencia']) <= 20:
            rota['sequencia'], _ = two_opt(rota['sequencia'], distancias, max_iter=10)
    return rotas_finais

def refusao_pos_otimizacao(rotas, capacidade, distancias, deposito, ganho_minimo=0.1):
    rotas = deepcopy(rotas)
    mudou = True
    while mudou:
        mudou = False
        n = len(rotas)
        melhor_ganho = 0
        melhor_par = None
        melhor_seq = None

        for i in range(n):
            for j in range(i+1, n):
                r1, r2 = rotas[i], rotas[j]
                if r1["demanda_total"] + r2["demanda_total"] > capacidade:
                    continue
                if r1["servicos"] & r2["servicos"]:
                    continue
                seqs = [
                    r1['sequencia'][:-1] + r2['sequencia'][1:],
                    r1['sequencia'][:-1] + r2['sequencia'][-2:0:-1] + [deposito],
                    [deposito] + r1['sequencia'][-2:0:-1] + r2['sequencia'][1:],
                    [deposito] + r1['sequencia'][-2:0:-1] + r2['sequencia'][-2:0:-1] + [deposito],
                ]
                custo_servico = sum(c['custo'] for c in r1['clientes'] + r2['clientes'])
                custo_antigo = (
                    sum(distancias[r1['sequencia'][k]][r1['sequencia'][k+1]] for k in range(len(r1['sequencia'])-1)) +
                    sum(distancias[r2['sequencia'][k]][r2['sequencia'][k+1]] for k in range(len(r2['sequencia'])-1)) +
                    custo_servico
                )
                for seq in seqs:
                    if seq[0] != deposito or seq[-1] != deposito:
                        continue
                    custo_novo = sum(distancias[seq[k]][seq[k+1]] for k in range(len(seq)-1)) + custo_servico
                    ganho = custo_antigo - custo_novo
                    if ganho > melhor_ganho and ganho > ganho_minimo:
                        melhor_ganho = ganho
                        melhor_par = (i, j)
                        melhor_seq = seq

        if melhor_par:
            i, j = melhor_par
            nova_rota = {
                'clientes': rotas[i]['clientes'] + rotas[j]['clientes'],
                'demanda_total': rotas[i]['demanda_total'] + rotas[j]['demanda_total'],
                'servicos': rotas[i]['servicos'] | rotas[j]['servicos'],
                'sequencia': melhor_seq
            }
            rotas = [r for idx, r in enumerate(rotas) if idx not in (i, j)]
            rotas.append(nova_rota)
            mudou = True
    return rotas

def remover_rotas_inuteis(rotas):
    rotas_filtradas = []
    for rota in rotas:
        if not rota['clientes']:
            continue
        rotas_filtradas.append(rota)
    return rotas_filtradas

def two_opt(seq, distancias, max_iter=10, verbose=False):
    melhor_seq = seq
    melhor_custo = sum(distancias[seq[i]][seq[i+1]] for i in range(len(seq)-1))
    iter_count = 0
    melhorou = True

    while melhorou and iter_count < max_iter:
        melhorou = False
        iter_count += 1

        for i in range(1, len(seq) - 2):
            for j in range(i+1, len(seq) -1):
                if j - i == 1:
                    continue
                nova_seq = seq[:i] + seq[i:j][::-1] + seq[j:]
                novo_custo = sum(distancias[nova_seq[k]][nova_seq[k+1]] for k in range(len(nova_seq)-1))
                if novo_custo < melhor_custo:
                    melhor_seq = nova_seq
                    melhor_custo = novo_custo
                    melhorou = True
        seq = melhor_seq

        if verbose and iter_count % 100 == 0:
            print(f"2-opt iteração {iter_count}: custo atual {melhor_custo}")

    if verbose:
        print(f"2-opt finalizou após {iter_count} iterações com custo {melhor_custo}")

    return melhor_seq, melhor_custo

def aplicar_2opt_em_todas_rotas(rotas, distancias, max_iter=10, verbose=False):
    for idx, rota in enumerate(rotas, 1):
        if len(rota['sequencia']) <= 20:
            seq_atual = rota['sequencia']
            seq_melhor, _ = two_opt(seq_atual, distancias, max_iter=max_iter, verbose=verbose)
            rota['sequencia'] = seq_melhor
            if verbose:
                print(f"2-opt aplicada na rota {idx} (tamanho {len(seq_atual)})")
        elif verbose:
            print(f"PULANDO 2-opt na rota {idx} (tamanho {len(rota['sequencia'])})")
    return rotas

def salvar_solucao(rotas, nome_arquivo, deposito, matriz_dist):
    with open(nome_arquivo, "w", encoding="utf-8") as f:
        custo_total_global = 0
        for rota in rotas:
            seq = rota["sequencia"]
            custo_transporte = sum(matriz_dist[seq[k]][seq[k + 1]] for k in range(len(seq) - 1))
            custo_servico = sum(c['custo'] for c in rota["clientes"])
            custo_total_global += custo_transporte + custo_servico

        f.write(f"{custo_total_global}\n")
        f.write(f"{len(rotas)}\n")
        f.write(f"{int(time.time())}\n")

        for i, rota in enumerate(rotas, start=1):
            seq = rota["sequencia"]
            visitas = []
            custo_transporte = 0
            custo_servico = 0
            visitados = set()

            for k in range(len(seq) - 1):
                u = seq[k]
                v = seq[k + 1]
                custo_transporte += matriz_dist[u][v]
                for cliente in rota["clientes"]:
                    chave = (cliente["tipo"], cliente["id"])
                    if chave in visitados:
                        continue
                    if (cliente["tipo"] == 'a' and cliente["origem"] == u and cliente["destino"] == v) or \
                       (cliente["tipo"] == 'e' and ((min(u,v), max(u,v)) == (min(cliente["origem"], cliente["destino"]), max(cliente["origem"], cliente["destino"])))) or \
                       (cliente["tipo"] == 'n' and cliente["origem"] == u and cliente["destino"] == v):
                        visitas.append(f"(S {cliente['id']},{u},{v})")
                        visitados.add(chave)
                        custo_servico += cliente['custo']

            total_visitas = len(visitas) + 2
            demanda_total = rota['demanda_total']
            linha = f" 0 1 {i} {demanda_total} {int(custo_transporte + custo_servico)}  {total_visitas} (D 0,1,1) "
            linha += " ".join(visitas) + " (D 0,1,1)\n"
            f.write(linha)
