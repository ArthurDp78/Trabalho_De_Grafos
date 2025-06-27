def leitor_arquivo(path):
    """
    1. Objetivo:
       Ler e interpretar um arquivo de instância do problema CARP (Capacitated Arc Routing Problem), extraindo todas as informações relevantes do grafo e dos serviços obrigatórios.

    2. Entradas:
       - path: caminho do arquivo de entrada (.dat) contendo a descrição do grafo e dos serviços.

    3. Lógica interna:
       - Inicializa estruturas para armazenar cabeçalho, vértices, arestas, arcos e seus subconjuntos obrigatórios.
       - Lê o arquivo linha a linha, identificando seções (vértices, arestas, arcos, obrigatórios ou não).
       - Para cada linha relevante, extrai os dados (origem, destino, custos, demandas, etc.) e armazena nas estruturas apropriadas.
       - Ignora comentários, linhas vazias e metadados irrelevantes.
       - Trata erros de leitura e formatação, exibindo avisos quando necessário.

    4. Contribuição:
       Fornece toda a base de dados estruturada para o pipeline de otimização, permitindo que as próximas funções acessem o grafo, os serviços obrigatórios e os parâmetros do problema.
    """
    header = {}
    vertices = set()
    arestas = set()
    arcos = set()
    vertices_requeridos = set()
    arestas_requeridas = set()
    arcos_requeridos = set()

    secao_atual = None

    try:
        with open(path, "r", encoding="utf-8") as arquivo:
            linhas = arquivo.readlines()
    except FileNotFoundError:
        print(f"Erro: Arquivo '{path}' não encontrado.")
        exit()
    except Exception as e:
        print(f"Erro ao ler o arquivo: {e}")
        exit()

    for linha in linhas:
        linha = linha.strip()

        # Identifica e armazena informações do cabeçalho (parâmetros globais)
        if linha.startswith(("Optimal value:", "Capacity:", "Depot Node:", "#Nodes:", "#Edges:", "#Arcs:",
                             "#Required N:", "#Required E:", "#Required A:")):
            chave, valor = linha.split(":", 1)
            header[chave.strip()] = valor.strip()
            continue

        # Ignora comentários, linhas vazias e metadados não relevantes
        if not linha or linha.startswith("//") or linha.startswith("Name:") or "based on the" in linha.lower():
            continue

        # Identifica início de cada seção do arquivo
        if linha.startswith("ReN."):
            secao_atual = "ReN"
            continue
        elif linha.startswith("ReE."):
            secao_atual = "ReE"
            continue
        elif linha.startswith("EDGE"):
            secao_atual = "EDGE"
            continue
        elif linha.startswith("ReA."):
            secao_atual = "ReA"
            continue
        elif linha.startswith("ARC"):
            secao_atual = "ARC"
            continue

        # Processa linhas de dados conforme a seção atual
        if linha and secao_atual:
            partes = linha.split()
            try:
                if secao_atual == "ReN":
                    # Vértices obrigatórios: (N, demanda, custo_servico)
                    vertice = int(partes[0].replace("N", ""))
                    demanda = int(partes[1])
                    custo_servico = int(partes[2])
                    vertices_requeridos.add((vertice, (demanda, custo_servico)))
                    vertices.add(vertice)
                elif secao_atual in ["ReE", "EDGE"]:
                    # Arestas (com ou sem obrigatoriedade)
                    origem, destino = int(partes[1]), int(partes[2])
                    aresta = (min(origem, destino), max(origem, destino))
                    custo_transporte = int(partes[3])
                    arestas.add((aresta, custo_transporte))
                    vertices.update([origem, destino])
                    if secao_atual == "ReE":
                        # Aresta obrigatória: inclui demanda e custo de serviço
                        demanda = int(partes[4])
                        custo_servico = int(partes[5])
                        arestas_requeridas.add((aresta, (custo_transporte, demanda, custo_servico)))
                elif secao_atual in ["ReA", "ARC"]:
                    # Arcos (com ou sem obrigatoriedade)
                    origem, destino = int(partes[1]), int(partes[2])
                    arco = (origem, destino)
                    custo_transporte = int(partes[3])
                    arcos.add((arco, custo_transporte))
                    vertices.update([origem, destino])
                    if secao_atual == "ReA":
                        # Arco obrigatório: inclui demanda e custo de serviço
                        demanda = int(partes[4])
                        custo_servico = int(partes[5])
                        arcos_requeridos.add((arco, (custo_transporte, demanda, custo_servico)))
            except ValueError:
                print(f"[Aviso] Linha ignorada por erro: {linha}")
                continue

    return {
        "header": header,
        "vertices": vertices,
        "arestas": arestas,
        "arcos": arcos,
        "vertices_requeridos": vertices_requeridos,
        "arestas_requeridas": arestas_requeridas,
        "arcos_requeridos": arcos_requeridos
    }

def criar_matriz_distancias(vertices, arestas, arcos):
    """
    1. Objetivo:
       Construir a matriz de distâncias entre todos os pares de vértices do grafo, considerando arestas e arcos, e computando o caminho mais curto entre todos os pares (Floyd-Warshall).

    2. Entradas:
       - vertices: conjunto de vértices do grafo.
       - arestas: conjunto de arestas (bidirecionais) com custos.
       - arcos: conjunto de arcos (direcionais) com custos.

    3. Lógica interna:
       - Inicializa a matriz de distâncias com infinito para todos os pares, exceto zero na diagonal.
       - Preenche as distâncias diretas a partir das arestas (bidirecional) e arcos (direcional).
       - Aplica o algoritmo de Floyd-Warshall para garantir que a matriz contenha o menor custo entre todos os pares de vértices.

    4. Contribuição:
       Permite calcular rapidamente o custo de deslocamento entre quaisquer dois pontos do grafo, fundamental para avaliar e construir rotas no pipeline de otimização.
    """
    distancias = {v: {u: float('inf') for u in vertices} for v in vertices}
    for v in vertices:
        distancias[v][v] = 0
    # Preenche distâncias diretas de arestas (bidirecionais)
    for (u, v), custo in arestas:
        distancias[u][v] = custo
        distancias[v][u] = custo
    # Preenche distâncias diretas de arcos (direcionais)
    for (u, v), custo in arcos:
        distancias[u][v] = custo

    # Algoritmo de Floyd-Warshall para caminhos mínimos entre todos os pares
    for k in vertices:
        for i in vertices:
            for j in vertices:
                if distancias[i][j] > distancias[i][k] + distancias[k][j]:
                    distancias[i][j] = distancias[i][k] + distancias[k][j]
    return distancias

def extrair_servicos(dados_leitura):
    """
    1. Objetivo:
       Extrair e organizar todos os serviços obrigatórios do grafo (vértices, arestas e arcos obrigatórios) em uma lista padronizada para uso nos algoritmos de roteamento.

    2. Entradas:
       - dados_leitura: dicionário retornado por leitor_arquivo, contendo os conjuntos de serviços obrigatórios.

    3. Lógica interna:
       - Para cada vértice obrigatório, cria um dicionário de serviço com tipo 'vertice'.
       - Para cada aresta obrigatória, cria um dicionário de serviço com tipo 'aresta'.
       - Para cada arco obrigatório, cria um dicionário de serviço com tipo 'arco'.
       - Cada serviço recebe um id_servico único, origem, destino, demanda e custo de serviço.

    4. Contribuição:
       Gera a lista de serviços obrigatórios no formato esperado pelos algoritmos construtivos e heurísticas de otimização, garantindo padronização e facilidade de manipulação.
    """
    servicos = []
    id_atual = 1

    # Adiciona vértices obrigatórios como serviços
    for (vertice, (demanda, custo_servico)) in sorted(dados_leitura["vertices_requeridos"], key=lambda x: x[0]):
        servicos.append({
            "id_servico": id_atual,
            "tipo": "vertice",
            "origem": vertice,
            "destino": vertice,
            "demanda": demanda,
            "custo_servico": custo_servico
        })
        id_atual += 1

    # Adiciona arestas obrigatórias como serviços
    for (aresta, (custo_transporte, demanda, custo_servico)) in sorted(dados_leitura["arestas_requeridas"], key=lambda x: x[0]):
        origem, destino = aresta
        servicos.append({
            "id_servico": id_atual,
            "tipo": "aresta",
            "origem": origem,
            "destino": destino,
            "demanda": demanda,
            "custo_servico": custo_servico
        })
        id_atual += 1

    # Adiciona arcos obrigatórios como serviços
    for (arco, (custo_transporte, demanda, custo_servico)) in sorted(dados_leitura["arcos_requeridos"], key=lambda x: x[0]):
        origem, destino = arco
        servicos.append({
            "id_servico": id_atual,
            "tipo": "arco",
            "origem": origem,
            "destino": destino,
            "demanda": demanda,
            "custo_servico": custo_servico
        })
        id_atual += 1

    return servicos