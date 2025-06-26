import os
import time
import psutil
from leitor_grafo import leitor_arquivo, criar_matriz_distancias, extrair_servicos
from algoritmo_construtivo import salvar_solucao,clarke_wright_grasp,relocate,vnd,segment_relocate,multi_start_pipeline


def eh_grafo_grande(dados):
    """
    Retorna True se o grafo for considerado grande,
    usando como critério: mais de 150 vértices OU mais de 500 serviços obrigatórios.
    """
    n_vertices = len(dados["vertices"])
    n_servicos = (
        len(dados["vertices_requeridos"])
        + len(dados["arestas_requeridas"])
        + len(dados["arcos_requeridos"])
    )
    return n_vertices > 150 or n_servicos > 500


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

        rotas_otimizadas, demandas, clock_total_ciclos, melhor_clock_encontrado_ciclos = multi_start_pipeline(
        servicos,
        deposito,
        matriz_distancias,
        capacidade,
        servicos,
        k_grasp=7,
        num_tentativas=10,
        freq_hz=freq_hz
        )

        nome_saida = os.path.join(pasta_saida, f"sol-{arquivo}")
        salvar_solucao(
            nome_saida,
            rotas_otimizadas,
            matriz_distancias,
            deposito=deposito,
            tempo_referencia_execucao=clock_total_ciclos,
            tempo_referencia_solucao=melhor_clock_encontrado_ciclos
        )

if __name__ == "__main__":
    main()