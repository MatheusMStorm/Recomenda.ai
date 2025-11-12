import http
import requests
import pandas as pd
import time
from dotenv import load_dotenv
import os
import json 
import numpy as np 

load_dotenv()

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
API_KEY = os.getenv("API_KEY") # Mantido caso precise para outros endpoints, mas o BEARER_TOKEN é preferencial
BASE_URL = "https://api.themoviedb.org/3"

DATA_FOLDER = "Data"
MOVIELENS_LINKS_FILE = os.path.join(DATA_FOLDER, "links.csv")
OUTPUT_FILE = os.path.join(DATA_FOLDER, "filmes.csv") 

# Variáveis globais para controle de filmes já processados
PROCESSED_MOVIE_IDS = set()
FAILED_MOVIE_IDS = set()

def _load_existing_filmes_df():
    """Carrega o DataFrame de filmes existente ou retorna um novo com colunas."""
    initial_columns = ['movieId', 'titulo', 'sinopse', 'generos', 'diretor', 'atores', 'tmdbId', 
                       'duracao', 'data_lancamento', 'media_votos', 'total_votos', 'popularidade']
    
    if os.path.exists(OUTPUT_FILE):
        df = pd.read_csv(OUTPUT_FILE)
        print(f"Arquivo '{OUTPUT_FILE}' carregado com {len(df)} registros existentes.")
        
        # Garante que todas as colunas esperadas existam, preenchendo com NaN se faltar
        for col in initial_columns:
            if col not in df.columns:
                df[col] = np.nan
        
        # Converte 'duracao' e 'tmdbId' para numérico, com 'coerce' para NaN em erros
        df['duracao'] = pd.to_numeric(df['duracao'], errors='coerce')
        df['tmdbId'] = pd.to_numeric(df['tmdbId'], errors='coerce').astype('Int64')

        # Preenche os sets de controle
        PROCESSED_MOVIE_IDS.update(df['movieId'].unique())
        return df[initial_columns] # Retorna com as colunas na ordem desejada
    else:
        print(f"Arquivo '{OUTPUT_FILE}' não encontrado. Criando novo DataFrame vazio.")
        return pd.DataFrame(columns=initial_columns)

def buscar_detalhes_filme(movie_id_movielens, tmdb_id):
    """Busca detalhes de um filme na API do TMDB, incluindo duração e outros campos."""
    if not BEARER_TOKEN:
        print("ERRO: BEARER_TOKEN do TMDB não configurado. Por favor, adicione sua chave .env.")
        return None

    endpoint = f"{BASE_URL}/movie/{tmdb_id}?language=pt-BR&append_to_response=credits"
    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}",
        "accept": "application/json",
    }
    
    try: 
        response = requests.get(endpoint, headers=headers)
        response.raise_for_status() 
        data = response.json()
        
        # Extração de dados (campos já existentes)
        sinopse = data.get('overview', '')
        generos = [g['name'] for g in data.get('genres', [])]
        generos_str = "|".join(generos)
        cast = [c['name'] for c in data.get('credits', {}).get('cast', [])[:5]]
        atores_str = "|".join(cast)
        diretor = ""
        for member in data.get('credits', {}).get('crew', []):
            if member['job'] == 'Director':
                diretor = member['name']
                break
        titulo = data.get('title', '')
        duracao = data.get('runtime', np.nan) # Em minutos
        data_lancamento = data.get('release_date', '')
        media_votos = data.get('vote_average', np.nan)
        total_votos = data.get('vote_count', np.nan)
        popularidade = data.get('popularity', np.nan)

        return {
            'movieId': movie_id_movielens,
            'titulo': titulo,
            'sinopse': sinopse,
            'generos': generos_str,
            'duracao': duracao,
            'diretor': diretor,
            'atores': atores_str,
            'tmdbId': tmdb_id,
            'duracao': duracao,
            'data_lancamento': data_lancamento,
            'media_votos': media_votos,
            'total_votos': total_votos,
            'popularidade': popularidade,
        }
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            # print(f"Alerta: Filme TMDB ID {tmdb_id} não encontrado (404).")
            return None
        else:
            print(f"Alerta: Erro HTTP {e.response.status_code} ao buscar tmdb_id {tmdb_id}: {e}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Erro de conexão ao buscar tmdb_id {tmdb_id}: {e}")
        return None
    except json.JSONDecodeError:
        print(f"Erro ao decodificar JSON para tmdb_id {tmdb_id}. Resposta: {response.text[:200]}...")
        return None
    except Exception as e:
        print(f"Erro inesperado ao buscar detalhes de tmdb_id {tmdb_id}: {e}")
        return None
    finally:
        time.sleep(0.25) # Controle de Rate Limit

def iniciar_coleta():
    print("--- 1. Carregando Mapeamento de Filmes ---")
    try:
        movie_map_df = pd.read_csv(MOVIELENS_LINKS_FILE)
        movie_map_df.rename(columns={'tmdbId': 'tmdbId'}, inplace=True) 
        # Garante que tmdbId seja Int64 para evitar problemas com NaN
        movie_map_df['tmdbId'] = pd.to_numeric(movie_map_df['tmdbId'], errors='coerce').astype('Int64')
        print(f"Arquivo '{MOVIELENS_LINKS_FILE}' carregado. Total de {len(movie_map_df)} filmes para mapear.")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{MOVIELENS_LINKS_FILE}' (links.csv) não encontrado.")
        print("Certifique-se de que o arquivo 'links.csv' está na pasta 'Data'.")
        return

    # Carrega (ou inicializa) o DataFrame de filmes existente
    df_filmes_existente = _load_existing_filmes_df()
    
    # Cria um dicionário para acesso rápido aos filmes existentes pelo movieId
    filmes_existentes_dict = df_filmes_existente.set_index('movieId').to_dict('index')

    lista_de_filmes_atualizada = []
    total_de_filmes_a_processar = len(movie_map_df)

    print("\n--- 2. Iniciando Coleta/Atualização da API do TMDB ---")

    for index, row in movie_map_df.iterrows():
        movie_id_movielens = row['movieId']
        tmdb_id = row['tmdbId']
        
        # Pula se o tmdb_id for inválido
        if pd.isna(tmdb_id) or tmdb_id == 0:
            # print(f"Pulando movieId {movie_id_movielens} (sem tmdbId mapeado ou inválido)")
            continue

        # Verifica se o filme já existe E tem a duração preenchida
        filme_ja_completo = False
        if movie_id_movielens in filmes_existentes_dict:
            existing_movie = filmes_existentes_dict[movie_id_movielens]
            if not pd.isna(existing_movie.get('duracao')): # Se a duração já existe, não precisa buscar
                lista_de_filmes_atualizada.append(existing_movie) # Adiciona o filme existente
                filme_ja_completo = True

        if not filme_ja_completo: # Se o filme não está completo, busca da API
            detalhes = buscar_detalhes_filme(movie_id_movielens, tmdb_id)
            
            if detalhes:
                lista_de_filmes_atualizada.append(detalhes)
                # Atualiza o dicionário com os detalhes recém-buscados
                filmes_existentes_dict[movie_id_movielens] = detalhes 
            else:
                # Se falhou, mas já existia um registro, mantemos o existente (mesmo incompleto)
                if movie_id_movielens in filmes_existentes_dict:
                    lista_de_filmes_atualizada.append(filmes_existentes_dict[movie_id_movielens])
                FAILED_MOVIE_IDS.add(movie_id_movielens)

        # Imprime o progresso
        if (index + 1) % 100 == 0:
            print(f"[{index + 1}/{total_de_filmes_a_processar}] Processado: {movie_id_movielens}")

    print(f"\nColeta/Atualização finalizada. Total de {len(lista_de_filmes_atualizada)} filmes com detalhes obtidos ou atualizados.")

    if lista_de_filmes_atualizada: 
        # Converte para DataFrame e garante que não há duplicatas de movieId
        df_filmes_final = pd.DataFrame(lista_de_filmes_atualizada).drop_duplicates(subset=['movieId'], keep='first')

        # Garante a ordem das colunas
        colunas_ordenadas = ['movieId', 'titulo', 'sinopse', 'generos', 'diretor', 'atores', 'tmdbId', 
                             'duracao', 'data_lancamento', 'media_votos', 'total_votos', 'popularidade']
        
        # Filtra e reordena colunas, adicionando as que podem ter sido criadas como NaN
        for col in colunas_ordenadas:
            if col not in df_filmes_final.columns:
                df_filmes_final[col] = np.nan

        df_filmes_final = df_filmes_final[colunas_ordenadas]

        df_filmes_final.to_csv(OUTPUT_FILE, index=False, encoding='utf-8')

        print(f"Arquivo '{OUTPUT_FILE}' (filmes.csv) salvo com sucesso!")
    else:
        print("Nenhum filme foi coletado ou atualizado. O arquivo 'filmes.csv' não foi alterado.")

if __name__ == "__main__":
    iniciar_coleta()