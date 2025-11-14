import pandas as pd
import numpy as np
import pickle
import os
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process

print("Carregando módulo 'busca_filme.py'...")

FILMES_CSV_PATH_BUSCA = os.path.join('Data', 'filmes.csv')
PNL_MODEL_PATH = os.path.join('Modelos', 'pnl_similarity_model.pkl')

# --- Variáveis Globais para Busca ---
FILMES_DF_BUSCA = None
MATRIZ_LATENTE = None
INDICES_MAP = None
TITULOS_MAP = None

def carregar_info_busca_pnl():
    """
    Carrega a matriz latente (modelo PNL otimizado), mapa de índices e títulos de filmes.
    Retorna (matriz_latente, indices_map, titulos_map) ou (None, None, None) em caso de erro.
    """
    global FILMES_DF_BUSCA, MATRIZ_LATENTE, INDICES_MAP, TITULOS_MAP
    
    try:
        # 1. Carregar o Modelo PNL (Matriz Latente e Índices)
        with open(PNL_MODEL_PATH, 'rb') as f:
            PNL_DATA = pickle.load(f)
        
        MATRIZ_LATENTE = PNL_DATA['latent_matrix']
        INDICES_MAP = PNL_DATA['movie_indices']
        
        # 2. Carregar o DataFrame de Filmes
        FILMES_DF_BUSCA = pd.read_csv(FILMES_CSV_PATH_BUSCA)
        
        # 3. Criar o Mapa de Títulos para Fuzzy Matching
        TITULOS_MAP = FILMES_DF_BUSCA.set_index('movieId')['titulo'].drop_duplicates()
        print("Modelos PNL e dados de filmes carregados para busca.")
        return MATRIZ_LATENTE, INDICES_MAP, TITULOS_MAP
        
    except FileNotFoundError as e:
        print(f'Erro no busca_filme.py. Arquivo não encontrado: {e}')
        return None, None, None
    except Exception as e:
        print(f'Erro inesperado ao carregar PNL/Dados: {e}')
        return None, None, None

# Carrega os recursos na inicialização do módulo
carregar_info_busca_pnl()

# --- Função 1: Recomendação por Similaridade de Conteúdo (PNL) ---
def recomendar_por_similaridade(movieId_base, top_n=10):
    """
    Calcula a similaridade de conteúdo 'ao vivo' usando a matriz latente otimizada.
    Retorna uma lista de movieIds.
    """
    if MATRIZ_LATENTE is None or INDICES_MAP is None:
        return []
    
    try:
        # Pega o índice interno do movieId_base
        if movieId_base not in INDICES_MAP.index:
            # print(f"AVISO: movieId_base {movieId_base} não encontrado em INDICES_MAP para similaridade.")
            return []

        indice_base = INDICES_MAP.loc[movieId_base]
        
        # Pega o "DNA PNL" do filme base
        dna_pnl = MATRIZ_LATENTE[indice_base].reshape(1, -1)
        
        # Calcula a similaridade de cosseno (comparando o vetor base com toda a matriz)
        similaridades = cosine_similarity(dna_pnl, MATRIZ_LATENTE)
        similaridades = similaridades[0] 
        
        # Ordena os resultados e pega os índices dos top N
        enumerar_dados = list(enumerate(similaridades))
        ordenar_dados = sorted(enumerar_dados, key=lambda x : x[1], reverse=True)
        
        # Converte os índices internos de volta para movieIds originais
        indice_top = [i[0] for i in ordenar_dados[1:top_n + 1]]
        
        # Garante que os índices retornados estão presentes no INDICES_MAP antes de acessá-los
        filmes_recomendados = []
        for idx in indice_top:
            if idx in INDICES_MAP.values: # Verifica se o índice interno existe
                # Encontra o movieId correspondente ao índice interno
                corresponding_movieId = INDICES_MAP[INDICES_MAP == idx].index[0]
                filmes_recomendados.append(corresponding_movieId)
        
        return filmes_recomendados
        
    except KeyError:
        # Erro se o movieId não existir no INDICES_MAP
        # print(f"Não foi encontrado o movieID {movieId_base} no índice PNL.")
        return []
    except Exception as e:
        # print(f"Erro inesperado no PNL para movieId {movieId_base}: {e}")
        return []

def encontrar_movieid_por_titulo(titulo_query, top_n=1):
    if TITULOS_MAP is None:
        print("Erro! O mapa de títulos não foi carregado.")
        return None
    
    resultados = process.extract(titulo_query, TITULOS_MAP.to_dict(), limit=top_n)

    if not resultados:
        return None if top_n == 1 else []

    if top_n == 1:
        # Retorna o movieId (o terceiro item da tupla)
        return resultados[0][2] 
    else:
        # Retorna uma lista de movieIds
        return [r[2] for r in resultados]

# Bloco de execução para testar o módulo diretamente
if __name__ == "__main__":
    print("\n" + "="*50)
    print("EXECUTANDO 'busca_filme.py' DIRETAMENTE PARA TESTE...")
    print("="*50)

    if MATRIZ_LATENTE is not None and TITULOS_MAP is not None:
        # Teste encontrar_movieid_por_titulo
        print("\n--- Testando Busca de Título (Fuzzy) ---")
        query_errada = "Avatara"
        id_encontrado = encontrar_movieid_por_titulo(query_errada)

        if id_encontrado:
            # Usa .get() para acesso seguro ao dicionário TITULOS_MAP
            titulo_real = TITULOS_MAP[id_encontrado] if id_encontrado in TITULOS_MAP else f"ID {id_encontrado} (Título não encontrado)"
            print(f"Consulta: '{query_errada}' -> Encontrado: '{titulo_real}' (ID: {id_encontrado})")
        
            # Teste recomendar_por_similaridade
            print("\n--- Testando Similaridade ---")
            similares = recomendar_por_similaridade(id_encontrado, top_n=5)
            
            if similares:
                print(f"Top 5 filmes similares ao ID {id_encontrado}:")
                for mid in similares:
                    titulo = TITULOS_MAP.get(mid, f"ID {mid} (Título não encontrado)")
                    print(f"  - {titulo} (ID: {mid})")
            else:
                print(f"Nenhum filme similar encontrado para o ID {id_encontrado}.")

        else:
            print("Não foi possível encontrar o ID para 'Avatara'. Verifique o arquivo filmes.csv.")
    else:
        print("\n--- TESTE FALHOU ---")
        print("Modelos PNL NÃO PUDERAM SER CARREGADOS. Verifique os arquivos na pasta 'Modelos'.")