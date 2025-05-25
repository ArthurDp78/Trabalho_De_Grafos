import os
from leitor_grafo import leitor_arquivo, criar_matriz_distancias, extrair_servicos
from algoritmo_construtivo import algoritmo_clarke_wright, salvar_solucao

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

    for arquivo in arquivos:
        print(f"Processando {arquivo}...")
        caminho = os.path.join(pasta_entrada, arquivo)
        dados = leitor_arquivo(caminho)
        matriz_distancias = criar_matriz_distancias(dados["vertices"], dados["arestas"], dados["arcos"])
        capacidade = int(dados["header"]["Capacity"])

        deposito = int(dados["header"].get("Depot Node", 0))

        servicos = extrair_servicos(dados)

        rotas_final = algoritmo_clarke_wright(
            servicos,
            deposito=deposito,
            matriz_distancias=matriz_distancias,
            capacidade=capacidade
        )

        nome_saida = os.path.join(pasta_saida, f"sol-{arquivo}")
        salvar_solucao(nome_saida, rotas_final, matriz_distancias, deposito=deposito)

if __name__ == "__main__":
    main()
