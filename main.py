import os
import time
import psutil
from leitor_grafo import leitor_arquivo, criar_matriz_distancias, extrair_servicos
from algoritmo_construtivo import salvar_solucao,multi_start_pipeline

def main():
    pasta_entrada = "dados"
    pasta_saida = "solucoes"

    if not os.path.exists(pasta_entrada):
        print(f"Pasta de entrada '{pasta_entrada}' não existe.")
        return

    os.makedirs(pasta_saida, exist_ok=True)

    arquivos = [f for f in os.listdir(pasta_entrada) if f.endswith(".dat")]
    arquivos.sort()

    if not arquivos:
        print(f"Nenhum arquivo .dat encontrado na pasta '{pasta_entrada}'.")
        return

    freq_mhz = psutil.cpu_freq().current
    freq_hz = freq_mhz * 1_000_000

    for arquivo in arquivos:
        print(f"Processando {arquivo}...")
        caminho = os.path.join(pasta_entrada, arquivo)
        dados = leitor_arquivo(caminho)
        matriz_distancias = criar_matriz_distancias(dados["vertices"], dados["arestas"], dados["arcos"])
        capacidade = int(dados["header"]["Capacity"])
        deposito = int(dados["header"].get("Depot Node", 0))
        servicos = extrair_servicos(dados)

        # Medição do tempo total de execução (em ciclos de CPU estimados)
        clock_inicio_total = time.perf_counter_ns()

        rotas_otimizadas, demandas = multi_start_pipeline(
            servicos,
            deposito,
            matriz_distancias,
            capacidade,
            servicos,         # lista completa de serviços obrigatórios
            k_grasp=3,        # ou outro valor desejado para top-k do GRASP
            num_tentativas=5  # ajuste conforme desejado
        )
        clock_fim_total = time.perf_counter_ns()
        clock_total = clock_fim_total - clock_inicio_total

        ciclos_estimados_total = int(clock_total * (freq_hz / 1_000_000_000))

        nome_saida = os.path.join(pasta_saida, f"sol-{arquivo}")
        salvar_solucao(
            nome_saida,
            rotas_otimizadas,
            matriz_distancias,
            deposito=deposito,
            tempo_referencia_execucao=ciclos_estimados_total,
            tempo_referencia_solucao=ciclos_estimados_total
        )

if __name__ == "__main__":
    main()