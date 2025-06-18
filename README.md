
# **Algoritmos de Roteamento com Grafos**

**Autores:** Arthur Soares Marques, Matheus Gomes Monteiro  
**Curso:** Ciência da Computação - Universidade Federal de Lavras (UFLA)  

## 📌 **Descrição**

Este projeto tem como objetivo aplicar algoritmos de roteamento em grafos utilizando a **heurística Clarke & Wright** para o **Problema de Roteamento Capacitado** (CAP). A primeira etapa consiste na **leitura e análise de grafos** a partir de arquivos `.dat`, **cálculo de métricas** e **geração de soluções de roteamento** de forma eficiente, utilizando técnicas de otimização como **2-opt** e **GRASP**.

## ⚙️ **Funcionalidades Implementadas**

- 📥 **Leitura e validação do grafo** a partir de arquivos `.dat`, incluindo a leitura das seções:
  - `ReN.`: Vértices requeridos
  - `ReE.`: Arestas requeridas
  - `EDGE`: Arestas gerais
  - `ReA.`: Arcos requeridos
  - `ARC`: Arcos gerais
- ✅ **Verificação de integridade** do grafo para garantir a consistência das conexões.
- 📊 **Cálculo das métricas do grafo**:
  - **Graus** (total, entrada, saída)
  - **Densidade do grafo**
  - **Diâmetro** e **caminho médio**
  - **Intermediação** (betweenness) por vértice
- 🧠 **Implementação do algoritmo Clarke & Wright** para construção inicial das rotas, seguido de **2-opt** e **GRASP** para otimização.
- 🚚 **Relocação e fusão de rotas** com base na demanda e capacidade dos veículos.
- 📝 **Geração da solução final** com formato específico e detalhamento de custos.

## 📂 **Estrutura do Arquivo `.dat`**

O arquivo de entrada deve estar estruturado da seguinte forma:
- `ReN.` – Vértices requeridos com demanda e custo.
- `ReE.` – Arestas requeridas entre vértices, com custo de transporte, demanda e custo do serviço.
- `EDGE` – Arestas gerais do grafo.
- `ReA.` – Arcos requeridos com as mesmas informações das arestas.
- `ARC` – Arcos gerais do grafo.

Exemplo:
```text
ReN.	DEMAND	S. COST
N54	13	13
N23	49	49
...
```

## 💡 **Algoritmos e Heurísticas**

- **Clarke & Wright**: Algoritmo utilizado para calcular a solução inicial, gerando as rotas baseadas no cálculo de savings (economia de custo).
- **2-opt**: Aplicado para **melhorar as rotas**, minimizando o custo de transporte ao reordenar segmentos de rotas.
- **GRASP**: Heurística de busca local para refinar a solução e alcançar um resultado mais otimizado, com múltiplas tentativas e melhorias sucessivas.
- **Relocação**: Ajuste de serviços entre rotas para melhorar a utilização da capacidade e reduzir o número de rotas.

## 🚀 **Como Executar**

1. **Pré-requisitos**:  
   - Python 3.x
   - Instalar as dependências (caso necessário) com:
     ```bash
     pip install -r requirements.txt
     ```

2. **Execução**:  
   No terminal, execute o código com:
   ```bash
   python main.py
   ```

3. **Entrada de dados**:  
   O programa solicitará o caminho para o arquivo `.dat` com os dados do grafo. Exemplo:
   ```text
   Informe o caminho do arquivo .dat para leitura do grafo: exemplos/grafo.dat
   ```

4. **Saída**:  
   O programa gerará uma solução otimizada para o problema de roteamento e salvará o arquivo de saída na pasta `solucoes`.

---

## 📊 **Exemplo de Saída**

```text
Solução salva em 'solucoes/sol-grafo.dat'
Custo Total: 2534.42
Total de Rotas: 15
Tempo de Execução: 12.34 segundos
```

### Detalhamento das rotas geradas:

```text
0 1 1 302 1491 13 (D 1,1,1) (S 60,15,18) (S 38,72,72) (S 37,70,70) ... (D 1,1,1)
0 1 2 305 1116 10 (D 1,1,1) (S 126,60,62) (S 136,68,66) (S 28,55,55) ...
```

---

## 🛠️ **Tecnologias Utilizadas**

- Python 3
- Biblioteca **`psutil`** para medições de CPU
- Algoritmos de grafos clássicos:
  - **Floyd-Warshall** para cálculo de distâncias mínimas
  - **Clarke & Wright** para solução inicial
  - **2-opt** e **GRASP** para otimização
