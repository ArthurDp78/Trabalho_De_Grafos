import random
import copy
import time
def construir_rotas_iniciais(servicos, deposito, matriz_distancias, capacidade):
    """
    1. Objetivo:
       Cria uma solução inicial trivial para o problema de roteamento, onde cada serviço obrigatório é atendido por uma rota separada.

    2. Entradas:
       - servicos: lista de dicionários, cada um representando um serviço obrigatório.
       - deposito: índice do depósito (nó de partida/chegada).
       - matriz_distancias: matriz de distâncias entre os nós do grafo.
       - capacidade: capacidade máxima do veículo.

    3. Lógica:
       Para cada serviço, cria uma rota contendo apenas esse serviço e registra sua demanda.

    4. Contribuição:
       Serve como ponto de partida para algoritmos construtivos e heurísticas de fusão de rotas.
    """
    rotas = []
    demandas = []
    for serv in servicos:
        demanda = serv['demanda']
        rotas.append([serv])
        demandas.append(demanda)
    return rotas, demandas

def rota_custo(rota, matriz_distancias, deposito):
    """
    1. Objetivo:
       Calcula o custo total de uma rota, considerando custos de serviço e transporte.

    2. Entradas:
       - rota: lista de serviços (na ordem de atendimento).
       - matriz_distancias: matriz de distâncias entre nós.
       - deposito: índice do depósito.

    3. Lógica:
       Soma o custo de serviço de cada serviço na rota.
       Soma o custo de transporte: do depósito ao primeiro serviço, entre serviços consecutivos, e do último serviço de volta ao depósito.

    4. Contribuição:
       Permite avaliar e comparar rotas, sendo fundamental para heurísticas de melhoria e validação de soluções.
    """
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
    """
    1. Objetivo:
       Calcula a matriz de 'savings' (economias) para todos os pares de serviços, segundo o método de Clarke & Wright.

    2. Entradas:
       - servicos: lista de serviços obrigatórios.
       - deposito: índice do depósito.
       - matriz_distancias: matriz de distâncias.

    3. Lógica:
       Para cada par de serviços (i, j), calcula o quanto se economiza ao atendê-los juntos em vez de separadamente.
       Ordena os savings do maior para o menor.

    4. Contribuição:
       Fundamenta o algoritmo de fusão de rotas do Clarke & Wright e suas variantes.
    """
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
    1. Objetivo:
       Gera uma solução inicial para o CARP usando o algoritmo Clarke & Wright com randomização GRASP (escolha aleatória entre os top-k savings).

    2. Entradas:
       - servicos: lista de serviços obrigatórios.
       - deposito: índice do depósito.
       - matriz_distancias: matriz de distâncias.
       - capacidade: capacidade máxima do veículo.
       - k: número de savings do topo a considerar em cada passo (top-k).

    3. Lógica:
       Inicializa cada serviço em uma rota separada.
       Calcula os savings e, em cada iteração, escolhe aleatoriamente um dos top-k savings disponíveis para tentar fundir rotas, respeitando a capacidade.
       Remove savings já tentados e repete até não haver mais savings disponíveis.
       Remove rotas vazias e valida que todos os serviços obrigatórios estão presentes.

    4. Contribuição:
       Cria soluções iniciais diversificadas e potencialmente melhores para serem refinadas por heurísticas locais.
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
    """
    1. Objetivo:
       Melhora a solução atual movendo serviços de uma rota para outra, se isso reduzir o custo total e respeitar a capacidade.

    2. Entradas:
       - rotas: lista de rotas (cada rota é uma lista de serviços).
       - demandas: lista de demandas de cada rota.
       - capacidade: capacidade máxima do veículo.
       - matriz_distancias: matriz de distâncias.
       - deposito: índice do depósito.

    3. Lógica:
       Para cada serviço em cada rota, tenta movê-lo para outra rota se isso não violar a capacidade e reduzir o custo total.
       Repete até não haver mais melhorias.

    4. Contribuição:
       Refina a solução inicial, reduzindo o custo total e melhorando a distribuição dos serviços entre as rotas.
    """
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
    """
    1. Objetivo:
       Otimiza a ordem dos serviços em uma única rota, tentando todas as inversões possíveis de segmentos (2-opt), buscando reduzir o custo.

    2. Entradas:
       - rota: lista de serviços (na ordem atual).
       - matriz_distancias: matriz de distâncias.
       - deposito: índice do depósito.

    3. Lógica:
       Para cada par de posições, inverte o segmento intermediário e aceita a inversão se reduzir o custo da rota.
       Repete até não haver mais melhorias.

    4. Contribuição:
       Reduz o custo de cada rota individualmente, melhorando a eficiência do trajeto do veículo.
    """
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
    """
    1. Objetivo:
       Aplica a metaheurística VND (Variable Neighborhood Descent) para refinar a solução, combinando relocate e 2-opt.

    2. Entradas:
       - rotas: lista de rotas.
       - demandas: lista de demandas.
       - capacidade: capacidade máxima do veículo.
       - matriz_distancias: matriz de distâncias.
       - deposito: índice do depósito.

    3. Lógica:
       Primeiro aplica relocate para mover serviços entre rotas, depois aplica 2-opt para otimizar a ordem dos serviços em cada rota.

    4. Contribuição:
       Refina significativamente a solução inicial, explorando diferentes vizinhanças para encontrar soluções de menor custo.
    """
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
    num_tentativas=3,
    freq_hz=None
):
    """
    1. Objetivo:
       Executa o pipeline completo de construção e otimização de rotas múltiplas vezes (multi-start), cada vez com uma randomização diferente, e retorna a melhor solução encontrada.

    2. Entradas:
       - servicos: lista de serviços obrigatórios.
       - deposito: índice do depósito.
       - matriz_distancias: matriz de distâncias.
       - capacidade: capacidade máxima do veículo.
       - servicos_obrigatorios: lista de todos os serviços obrigatórios (para validação).
       - k_grasp: parâmetro top-k para o GRASP.
       - num_tentativas: número de tentativas (multi-start).
       - freq_hz: frequência do processador para medir tempo em ciclos (opcional).

    3. Lógica:
       Para cada tentativa:
         - Executa o construtivo GRASP.
         - Refina com VND e segment_relocate.
         - Valida a solução.
         - Guarda a melhor solução encontrada (menor custo, ou menos rotas em caso de empate).
       Mede o tempo total e o tempo até encontrar a melhor solução.

    4. Contribuição:
       Aumenta a robustez e qualidade das soluções, explorando diferentes pontos de partida e refinando cada um.
    """
    melhor_custo = float('inf')
    melhor_num_rotas = float('inf')
    melhor_rotas = None
    melhor_demandas = None
    melhor_clock_encontrado = None

    clock_inicio = time.perf_counter_ns()
    for tentativa in range(num_tentativas):
        # Marca o clock do início da tentativa
        clock_tentativa = time.perf_counter_ns()
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
            melhor_clock_encontrado = clock_tentativa  # registra o clock quando achou a melhor

            print(f"[Tentativa {tentativa+1}] Nova melhor solução: custo {custo_total}, rotas {num_rotas}")

    clock_fim = time.perf_counter_ns()

    # Converte para ciclos se freq_hz foi fornecida (senão retorna em nanosegundos)
    if freq_hz:
        clock_total_ciclos = int((clock_fim - clock_inicio) * (freq_hz / 1_000_000_000))
        melhor_clock_encontrado_ciclos = int((melhor_clock_encontrado - clock_inicio) * (freq_hz / 1_000_000_000)) if melhor_clock_encontrado else -1
    else:
        clock_total_ciclos = clock_fim - clock_inicio
        melhor_clock_encontrado_ciclos = (melhor_clock_encontrado - clock_inicio) if melhor_clock_encontrado else -1

    if melhor_rotas is not None:
        print(f"\nMelhor solução multi-start: custo {melhor_custo}, rotas {melhor_num_rotas}")
    else:
        print("Nenhuma solução válida encontrada!")

    return melhor_rotas, melhor_demandas, clock_total_ciclos, melhor_clock_encontrado_ciclos



def segment_relocate(rotas, demandas, capacidade, matriz_distancias, deposito, servicos_obrigatorios):
    """
    1. Objetivo:
       Refina a solução movendo blocos contínuos de serviços (segmentos) entre rotas, se isso reduzir o custo total e respeitar a capacidade.

    2. Entradas:
       - rotas: lista de rotas (cada rota é uma lista de serviços).
       - demandas: lista de demandas de cada rota.
       - capacidade: capacidade máxima do veículo.
       - matriz_distancias: matriz de distâncias.
       - deposito: índice do depósito.
       - servicos_obrigatorios: lista de todos os serviços obrigatórios (para validação).

    3. Lógica:
       Para cada par de rotas, tenta mover todos os blocos possíveis de uma para outra, desde que não deixe rota vazia e não exceda a capacidade.
       Aceita o movimento se reduzir o custo total das duas rotas.
       Repete até não haver mais melhorias.
       Remove rotas vazias e valida a solução.

    4. Contribuição:
       Permite grandes saltos na vizinhança da solução, potencialmente reduzindo o número de rotas e o custo total.
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
    """
    1. Objetivo:
       Salva a solução final em um arquivo, no formato esperado pelo avaliador do problema.

    2. Entradas:
       - nome_arquivo: caminho do arquivo de saída.
       - rotas: lista de rotas (cada rota é uma lista de serviços).
       - matriz_distancias: matriz de distâncias.
       - tempo_referencia_execucao: tempo total de execução (em ciclos ou ns).
       - tempo_referencia_solucao: tempo até encontrar a melhor solução (em ciclos ou ns).
       - deposito: índice do depósito.

    3. Lógica:
       Para cada rota, calcula o custo, demanda e monta a linha de saída no formato especificado.
       Garante que cada serviço é impresso apenas uma vez por rota.
       Escreve o custo total, número de rotas, tempos e as rotas no arquivo.

    4. Contribuição:
       Permite avaliar e comparar as soluções geradas pelo algoritmo, além de servir como saída oficial para submissão.
    """
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