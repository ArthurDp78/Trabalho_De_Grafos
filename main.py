import os
import time
import psutil
import concurrent.futures
from leitor_grafo import leitor_arquivo, criar_matriz_distancias, extrair_servicos
from algoritmo_construtivo import salvar_solucao, clarke_wright_grasp, relocate, vnd, segment_relocate, multi_start_pipeline


def processar_arquivo(arquivo, pasta_entrada, pasta_saida):
    """
    1. Objetivo:
       Processa uma instância do problema de roteamento de veículos (um arquivo .dat), executando todo o pipeline de construção e otimização de rotas, e salva a melhor solução encontrada.

    2. Entradas:
       - arquivo: nome do arquivo de entrada (instância do problema).
       - pasta_entrada: diretório onde estão os arquivos de entrada.
       - pasta_saida: diretório onde as soluções serão salvas.

    3. Lógica interna:
       - Lê e interpreta os dados do arquivo de entrada (grafo, demandas, etc.).
       - Cria a matriz de distâncias e extrai os serviços obrigatórios.
       - Obtém a capacidade do veículo e o depósito.
       - Mede a frequência do processador para referência temporal.
       - Executa o pipeline multi-start (multi_start_pipeline), que constrói e refina soluções múltiplas vezes (com GRASP, VND, segment_relocate, etc.), retornando a melhor solução encontrada.
       - Salva a solução otimizada no formato esperado.

    4. Contribuição:
       É a função central de processamento de cada instância, integrando leitura, construção, otimização e salvamento da solução.
    """
    print(f"Processando {arquivo}...")

    caminho = os.path.join(pasta_entrada, arquivo)
    dados = leitor_arquivo(caminho)
    matriz_distancias = criar_matriz_distancias(dados["vertices"], dados["arestas"], dados["arcos"])
    capacidade = int(dados["header"]["Capacity"])
    deposito = int(dados["header"].get("Depot Node", 0))
    servicos = extrair_servicos(dados)

    freq_mhz = psutil.cpu_freq().current
    freq_hz = freq_mhz * 1_000_000

    # Executa o pipeline multi-start, que tenta várias soluções iniciais e refina cada uma,
    # retornando a melhor solução encontrada (menor custo/rotas).
    rotas_otimizadas, demandas, clock_total_ciclos, melhor_clock_encontrado_ciclos = multi_start_pipeline(
        servicos,
        deposito,
        matriz_distancias,
        capacidade,
        servicos,
        k_grasp=10,
        num_tentativas=5,
        freq_hz=freq_hz
    )
    

    nome_saida = os.path.join(pasta_saida, f"sol-{arquivo}")
    # Salva a solução final no formato esperado pelo avaliador do problema.
    salvar_solucao(
        nome_saida,
        rotas_otimizadas,
        matriz_distancias,
        deposito=deposito,
        tempo_referencia_execucao=clock_total_ciclos,
        tempo_referencia_solucao=melhor_clock_encontrado_ciclos
    )

def main():
    """
    1. Objetivo:
       Gerencia o fluxo principal do programa: prepara diretórios, identifica arquivos de entrada e distribui o processamento das instâncias.

    2. Entradas:
       Nenhuma direta (usa variáveis internas para diretórios).

    3. Lógica interna:
       - Verifica se a pasta de entrada existe.
       - Cria a pasta de saída, se necessário.
       - Lista e ordena todos os arquivos .dat (instâncias do problema) na pasta de entrada.
       - Se não houver arquivos, exibe mensagem e encerra.
       - Usa ThreadPoolExecutor para processar múltiplos arquivos em paralelo, chamando processar_arquivo para cada um.

    4. Contribuição:
       Organiza o processamento em lote das instâncias, aproveitando múltiplos núcleos da máquina para acelerar a execução.
    """
    pasta_entrada = "dados"
    pasta_saida = "solucoes"
    num_threads = os.cpu_count()
    if not os.path.exists(pasta_entrada):
        print(f"Pasta de entrada '{pasta_entrada}' não existe.")
        return

    os.makedirs(pasta_saida, exist_ok=True)

    arquivos = [f for f in os.listdir(pasta_entrada) if f.endswith(".dat")]
    arquivos.sort()

    if not arquivos:
        print(f"Nenhum arquivo .dat encontrado na pasta '{pasta_entrada}'.")
        return

    # Utiliza processamento paralelo para acelerar o processamento de múltiplas instâncias.
    with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
      executor.map(processar_arquivo, arquivos, [pasta_entrada] * len(arquivos), [pasta_saida] * len(arquivos))

if __name__ == "__main__":
    """
    1. Objetivo:
       Ponto de entrada do programa. Garante que o main só será executado se o script for chamado diretamente.

    2. Entradas:
       Nenhuma.

    3. Lógica interna:
       Chama a função main().

    4. Contribuição:
       Permite que o script seja usado como módulo ou executável, seguindo boas práticas em Python.
    """
    main()