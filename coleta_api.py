import http
import requests
import pandas as pd
import time
from dotenv import load_dotenv
import os

load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
API_KEY = os.getenv("API_KEY")
BASE_URL = "https://api.themoviedb.org/3"

DATA_FOLDER = "Data"
MOVIELENS_LINKS_FILE = os.path.join(DATA_FOLDER, "links.csv")
OUTPUT_FILE = os.path.join(DATA_FOLDER, "filmes.csv")

def buscar_detalhes_filme(movie_id_movielens, tmdb_id): #Busca na chave
    # endpoint = f"{BASE_URL}/movie/{tmdb_id}?api_key={API_KEY}&language=pt-BR&append_to_response=credits"
    endpoint = f"{BASE_URL}/movie/{tmdb_id}?language=pt-BR&append_to_response=credits"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "accept": "application/json",
    }
    try: 
        response = requests.get(endpoint, headers=headers)

        if response.status_code != 200: #informa erro existente
                if response.status_code != 404:
                    print(f"Alerta: Erro inesperado ao buscar tmdb_id {tmdb_id}: Status {response.status_code}")
                return None
    
        data = response.json()#inicia a extração
        sinopse = data.get('overview', '')

        generos = [g['name'] for g in data.get('genres', [])]
        generos_str = "|".join(generos)
        
        duracao = data.get('runtime', 0)
        if duracao is None:
            duracao = 0

        cast = [c['name'] for c in data.get('credits', {}).get('cast', [])[:5]]
        atores_str = "|".join(cast)

        diretor = ""
        for member in data.get('credits', {}).get('crew', []):
            if member['job'] == 'Director':
                diretor = member['name']
                break

        titulo = data.get('title', '')   

        return {
            'movieId': movie_id_movielens, # O ID do MovieLens que conecta com usuarios.csv
            'titulo': titulo,
            'sinopse': sinopse,
            'generos': generos_str,
            'duracao': duracao,
            'diretor': diretor,
            'atores': atores_str,
            'tmdbId': tmdb_id
        }
    
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao buscar tmdb_id {tmdb_id}: {e}")
        return None

def iniciar_coleta():
    print("--- 1. Carregando Mapeamento de Filmes ---")
    try:
        movie_map_df = pd.read_csv(MOVIELENS_LINKS_FILE)
        movie_map_df.rename(columns={'tmdbId': 'tmdbId'}, inplace=True) 
        movie_map_df['tmdbId'] = pd.to_numeric(movie_map_df['tmdbId'], errors='coerce').astype('Int64')
        print(f"Arquivo '{MOVIELENS_LINKS_FILE}' carregado. Total de {len(movie_map_df)} filmes para mapear.")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{MOVIELENS_LINKS_FILE}' (links.csv) não encontrado.")
        return # Sai da função se o arquivo não for encontrado

    lista_de_filmes_final = []
    total_de_filmes = len(movie_map_df)

    print("\n--- 2. Iniciando Coleta da API do TMDB ---")

    for index, row in movie_map_df.iterrows():
        movie_id_movielens = row['movieId']
        tmdb_id = row['tmdbId']
    
        if pd.isna(tmdb_id) or tmdb_id == 0: #pula se for nulo
                # print(f"Pulando movieId {movie_id_movielens} (sem tmdbId mapeado)")
                continue

        detalhes = buscar_detalhes_filme(movie_id_movielens, tmdb_id)
        
        if detalhes:
            lista_de_filmes_final.append(detalhes)
            # Imprime o progresso
            if (index + 1) % 100 == 0: # Imprime a cada 100 filmes
                print(f"[{index + 1}/{total_de_filmes}] Coletado: {detalhes['titulo']}")

        time.sleep(0.25) # Controle de Rate Limit

    print(f"\nColeta finalizada. Total de {len(lista_de_filmes_final)} filmes com detalhes obtidos.")

    if lista_de_filmes_final: 
        df_filmes = pd.DataFrame(lista_de_filmes_final)

        colunas_ordenadas = ['movieId', 'titulo', 'sinopse', 'generos', 'duracao', 'diretor', 'atores', 'tmdbId']
        df_filmes = df_filmes[colunas_ordenadas]

        df_filmes.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

        print(f"Arquivo '{OUTPUT_FILE}' (filmes.csv) salvo com sucesso!")
    else:
        print("Nenhum filme foi coletado. O arquivo 'filmes.csv' não foi criado.")

if __name__ == "__main__":
    iniciar_coleta()