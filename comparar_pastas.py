import os

def ler_solucao(arquivo):
    with open(arquivo, encoding="utf-8") as f:
        linhas = f.readlines()
    custo_total = float(linhas[0].strip())
    n_rotas = int(linhas[1].strip())
    # (Opcional) Extrai serviços, se quiser detalhar
    servicos = set()
    for linha in linhas[4:]:
        tokens = linha.split()
        for token in tokens:
            if token.startswith("(S"):
                id_servico = token.split(",")[0][3:]
                servicos.add(id_servico)
    return custo_total, n_rotas, servicos

def comparar_pastas(pasta_user, pasta_otimo):
    arquivos = sorted([f for f in os.listdir(pasta_user) if f.endswith(".dat")])
    print(f"{'Instância':<16} {'Rotas User':<10} {'Rotas Ótima':<12} {'Custo User':<15} {'Custo Ótima':<15} {'Dif Rotas':<10} {'Dif Custo':<10}")
    print('-'*80)
    for arq in arquivos:
        path_user = os.path.join(pasta_user, arq)
        path_otimo = os.path.join(pasta_otimo, arq)
        if not os.path.exists(path_otimo):
            print(f"{arq:<16} Arquivo ótimo não encontrado.")
            continue
        try:
            custo_user, n_rotas_user, serv_user = ler_solucao(path_user)
            custo_otimo, n_rotas_otimo, serv_otimo = ler_solucao(path_otimo)
        except Exception as e:
            print(f"{arq:<16} Erro ao ler: {e}")
            continue
        print(f"{arq:<16} {n_rotas_user:<10} {n_rotas_otimo:<12} {custo_user:<15.2f} {custo_otimo:<15.2f} {n_rotas_user-n_rotas_otimo:<10} {custo_user-custo_otimo:<10.2f}")

if __name__ == "__main__":
    comparar_pastas("solucoes", "G0")
