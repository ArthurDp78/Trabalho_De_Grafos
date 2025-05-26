import os
import time
import psutil
from leitor_grafo import leitor_arquivo, criar_matriz_distancias, extrair_servicos
from grasp import grasp 
from algoritmo_construtivo import salvar_solucao, algoritmo_clarke_wright
from otimizacao import swap_entre_rotas  

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

        # Algoritmo construtivo como referência (opcional, se quiser medir separadamente)
        rotas_construtivo = algoritmo_clarke_wright(
            servicos,
            deposito=deposito,
            matriz_distancias=matriz_distancias,
            capacidade=capacidade
        )

        # Medição apenas da solução (GRASP + otimização)
        clock_ini_sol = time.perf_counter_ns()
        rotas_final = grasp(
            servicos,
            deposito=deposito,
            matriz_distancias=matriz_distancias,
            capacidade=capacidade,
            max_iter=30, 
            alpha=0.3    
        )
        rotas_final = swap_entre_rotas(rotas_final, matriz_distancias, capacidade, deposito)
        clock_fim_sol = time.perf_counter_ns()
        clock_sol = clock_fim_sol - clock_ini_sol

        clock_fim_total = time.perf_counter_ns()
        clock_total = clock_fim_total - clock_inicio_total

        ciclos_estimados_total = int(clock_total * (freq_hz / 1_000_000_000))
        ciclos_estimados_melhor_sol = int(clock_sol * (freq_hz / 1_000_000_000))

        nome_saida = os.path.join(pasta_saida, f"sol-{arquivo}")
        salvar_solucao(
            nome_saida,
            rotas_final,
            matriz_distancias,
            deposito=deposito,
            tempo_referencia_execucao=ciclos_estimados_total,
            tempo_referencia_solucao=ciclos_estimados_melhor_sol
        )

if __name__ == "__main__":
    main()
