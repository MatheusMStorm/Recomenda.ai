import pandas as pd
import pickle
import os
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process

FILMES = os.path.join('Data', 'filmes.csv')
PNL_MODEL = os.path.join('Modelos', 'pnl_similarity_model.pkl')

def carregar_info_busca_pnl():
    print("Carregando informações de busca da PNL.")
    
    try:
        PNL_DATA = pickle.load(open(PNL_MODEL, 'rb'))
        matriz_latente = PNL_DATA['latent_matrix']

        indices_map = PNL_DATA['movie_indices']
        filmes_db = pd.read_csv(FILMES)
    
        titulos_map = filmes_db.set_index('movieId')['titulo']

        return matriz_latente, indices_map, titulos_map
    except FileNotFoundError as e:
        print(f'Erro no busca_filme.py. Arquivo não encontrado. {e}')
        return None

MATRIZ_LATENTE, INDICES_MAP, TITULOS_MAP = carregar_info_busca_pnl()

def recomendar_por_similaridade(movieId_base, top_n=10):
    if MATRIZ_LATENTE is None:
        print("Erro! Matriz PNL não carregada.")
        return []
    
    try:
        indice_base = INDICES_MAP[movieId_base]
        dna_pnl = MATRIZ_LATENTE[indice_base].reshape(1, -1)
        salvar_dados_recomendacao = cosine_similarity(dna_pnl, MATRIZ_LATENTE)
        salvar_dados_recomendacao = salvar_dados_recomendacao[0]
        enumerar_dados = list(enumerate(salvar_dados_recomendacao))
        ordenar_dados = sorted(enumerar_dados, key=lambda x : x[1], reverse=True)
        indice_top = [i[0] for i in ordenar_dados[1:top_n + 1]]
        filmes_recomendados = INDICES_MAP.iloc[indice_top].index.tolist()
        return filmes_recomendados
    except KeyError:
        print(f"Não foi encontrado o movieID {movieId_base}")
        return []
    except Exception as e:
        print(f"Erro inesperado: {e}")
        return []

def encontrar_movieId_por_titulo(titulo_query, top_n=1):
    if TITULOS_MAP is None:
        print("Erro! O mapa de títulos não foi carregado.")
        return None
    
    resultados = process.extract(titulo_query, TITULOS_MAP.to_dict(), limit=top_n)

    if not resultados:
        return None

    if top_n == 1:
        return resultados[0][2]
    else:
        return [r[2] for r in resultados]

if __name__ == "__main__":
    print("Testando busca de filmes!")

    if MATRIZ_LATENTE is not None:
        query_errada = "Pocahantas"
        id_errado = encontrar_movieId_por_titulo(query_errada)

        if id_errado:
            print(f"Consulta: '{query_errada}', foi encontrado {TITULOS_MAP[id_errado]} (id: {id_errado})")
    
    print("Teste de similaridade")

    if id_errado:
        similares = recomendar_por_similaridade(id_errado, 5)
        print(f"Filmes similares a '{TITULOS_MAP[id_errado]}'")

        for mid in similares:
            print(f"{TITULOS_MAP[mid]} (id: {mid})")
    else:
        print("Testes não executados pois modelo não foi carregado.") 

#Carregar Dados, criar as funções,Fornecer funções de utilidade para pesquisar filmes e encontrar similares baseado no PNL