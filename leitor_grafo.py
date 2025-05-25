def leitor_arquivo(path):
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

        if linha.startswith(("Optimal value:", "Capacity:", "Depot Node:", "#Nodes:", "#Edges:", "#Arcs:",
                             "#Required N:", "#Required E:", "#Required A:")):
            chave, valor = linha.split(":", 1)
            header[chave.strip()] = valor.strip()
            continue

        if not linha or linha.startswith("//") or linha.startswith("Name:") or "based on the" in linha.lower():
            continue

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

        if linha and secao_atual:
            partes = linha.split()
            try:
                if secao_atual == "ReN":
                    vertice = int(partes[0].replace("N", ""))
                    demanda = int(partes[1])
                    custo_servico = int(partes[2])
                    vertices_requeridos.add((vertice, (demanda, custo_servico)))
                    vertices.add(vertice)
                elif secao_atual in ["ReE", "EDGE"]:
                    origem, destino = int(partes[1]), int(partes[2])
                    aresta = (min(origem, destino), max(origem, destino))
                    custo_transporte = int(partes[3])
                    arestas.add((aresta, custo_transporte))
                    vertices.update([origem, destino])
                    if secao_atual == "ReE":
                        demanda = int(partes[4])
                        custo_servico = int(partes[5])
                        arestas_requeridas.add((aresta, (custo_transporte, demanda, custo_servico)))
                elif secao_atual in ["ReA", "ARC"]:
                    origem, destino = int(partes[1]), int(partes[2])
                    arco = (origem, destino)
                    custo_transporte = int(partes[3])
                    arcos.add((arco, custo_transporte))
                    vertices.update([origem, destino])
                    if secao_atual == "ReA":
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
    distancias = {v: {u: float('inf') for u in vertices} for v in vertices}
    for v in vertices:
        distancias[v][v] = 0
    for (u, v), custo in arestas:
        distancias[u][v] = custo
        distancias[v][u] = custo
    for (u, v), custo in arcos:
        distancias[u][v] = custo

    for k in vertices:
        for i in vertices:
            for j in vertices:
                if distancias[i][j] > distancias[i][k] + distancias[k][j]:
                    distancias[i][j] = distancias[i][k] + distancias[k][j]
    return distancias

def extrair_servicos(dados_leitura):
    servicos = []
    id_atual = 1

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
