import pandas as pd
import pickle
import os
import numpy as np
# MUDANÇA: 'from .' foi alterado para 'from Codigo_fonte'
from Codigo_fonte import busca_filme 
from skfuzzy import control as ctrl
from surprise import SVD, Dataset, Reader

print("Carregando módulo 'recomendar.py'...")

FILMES_CSV = os.path.join("Data", "filmes.csv")
USUARIOS_CSV = os.path.join("Data", "usuarios.csv") 
CF_MODEL_FILE = os.path.join("Modelos", "modelo_colaborativo.pkl")
FUZZY_MODEL_FILE = os.path.join("Modelos", "fuzzy_control_system.pkl")

# --- Passo 2: Carregamento GLOBAL de Modelos e Dados ---
FILMES_DF_GLOBAL = None
USUARIOS_RATINGS_DF_GLOBAL = None
MODELO_CF_GLOBAL = None
FUZZY_SISTEMA_GLOBAL = None

def _carregar_recursos_para_recomendacao():
    """
    Função interna para carregar todos os modelos (CF, Fuzzy) e dados (Usuários/Ratings, Filmes).
    Esta função é chamada uma única vez na inicialização do módulo.
    """
    global FILMES_DF_GLOBAL, USUARIOS_RATINGS_DF_GLOBAL, MODELO_CF_GLOBAL, FUZZY_SISTEMA_GLOBAL
    
    print("Iniciando carregamento GLOBAL de modelos (CF, Fuzzy) e dados (Usuários/Ratings, Filmes)...")
    
    try:
        # Carrega filmes_df e define movieId como índice para acesso rápido com .loc
        FILMES_DF_GLOBAL = pd.read_csv(FILMES_CSV, index_col='movieId')
        USUARIOS_RATINGS_DF_GLOBAL = pd.read_csv(USUARIOS_CSV)
        
        with open(CF_MODEL_FILE, 'rb') as f:
            MODELO_CF_GLOBAL = pickle.load(f)
            
        with open(FUZZY_MODEL_FILE, 'rb') as f:
            FUZZY_SISTEMA_GLOBAL = pickle.load(f)
            
        print("Modelos CF, Fuzzy e dados carregados GLOBALMENTE com sucesso.")
        return True # Indica sucesso
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO ao carregar o arquivo: {e}")
        print("Verifique se os arquivos .csv e .pkl existem e estão nas pastas corretas.")
        print("Certifique-se de executar 'coleta_api.py', 'machine.py' e 'fuzzy_modulo.py' (nessa ordem) antes.")
        return False # Indica falha
    except Exception as e:
        print(f"ERRO INESPERADO ao carregar recursos de recomendação: {e}")
        return False

# Chama a função de carregamento imediatamente quando o módulo é importado
_carregar_recursos_para_recomendacao()

# --- Passo 3: Funções de Geração de Candidatos ---

def _get_lista_a_cf(modelo_cf, user_id, unseen_movie_ids):
    """
    (Gera a "Lista A": Candidatos da Filtragem Colaborativa)
    """
    print(f"Calculando {len(unseen_movie_ids)} previsões (CF) para o usuário {user_id}...")
    
    predictions = {}
    for movie_id in unseen_movie_ids:
        # Verifica se o movie_id está no índice GLOBAL de filmes antes de tentar prever
        if FILMES_DF_GLOBAL is not None and movie_id in FILMES_DF_GLOBAL.index:
            try:
                pred = modelo_cf.predict(uid=user_id, iid=movie_id)
                predictions[movie_id] = pred.est 
            except Exception:
                pass
            
    print("Cálculo de previsões CF concluído.")
    return predictions

def _get_lista_b_pnl(favorite_movie_ids, num_recs_per_movie=25):
    """
    (Gera a "Lista B": Candidatos do Conteúdo/PNL)
    """
    print(f"Buscando filmes similares (PNL) para {len(favorite_movie_ids)} filmes favoritos...")
    
    all_pnl_candidates = set()
    
    for seed_id in favorite_movie_ids:
        # Assegura que o seed_id exista no FILMES_DF_GLOBAL antes de buscar similaridade
        if FILMES_DF_GLOBAL is None or seed_id not in FILMES_DF_GLOBAL.index: 
            # print(f"AVISO: Filme favorito ID {seed_id} não encontrado no catálogo global. Pulando PNL para ele.")
            continue

        try:
            similars_result = busca_filme.recomendar_por_similaridade(
                movieId_base=seed_id,
                top_n=num_recs_per_movie
            )
            
            if isinstance(similars_result, (list, set)):
                if similars_result: # Se a lista/set não for vazia
                    all_pnl_candidates.update(similars_result)
            elif isinstance(similars_result, pd.DataFrame):
                if not similars_result.empty and 'movieId' in similars_result.columns:
                    all_pnl_candidates.update(similars_result['movieId'].tolist())
            elif isinstance(similars_result, pd.Series):
                if not similars_result.empty:
                    all_pnl_candidates.update(similars_result.tolist())
            elif similars_result is not None:
                try: 
                    all_pnl_candidates.update(list(similars_result))
                except TypeError:
                    # print(f"AVISO: Retorno inesperado de busca_filme.recomendar_por_similaridade para {seed_id}: {type(similars_result)}")
                    pass # Ignora tipos não iteráveis ou inválidos

        except Exception as e:
            print(f"ERRO ao buscar similares para o filme ID {seed_id}: {e}")
            pass # Continua para o próximo filme favorito mesmo se houver erro
        
    print(f"Encontrados {len(all_pnl_candidates)} candidatos únicos via PNL.")
    return all_pnl_candidates

def gerar_recomendacoes_hibridas(user_id, tempo_disponivel_min, top_n=10):
    """
    Esta é a função principal que orquestra todo o processo de recomendação.
    Retorna: Um DataFrame Pandas com o Top N, ordenado pela prioridade.
    """
    global FILMES_DF_GLOBAL, USUARIOS_RATINGS_DF_GLOBAL, MODELO_CF_GLOBAL, FUZZY_SISTEMA_GLOBAL

    if FILMES_DF_GLOBAL is None or FILMES_DF_GLOBAL.empty:
        print("ERRO: FILMES_DF_GLOBAL não carregado ou está vazio.")
        return pd.DataFrame()
    if USUARIOS_RATINGS_DF_GLOBAL is None or USUARIOS_RATINGS_DF_GLOBAL.empty:
        print("ERRO: USUARIOS_RATINGS_DF_GLOBAL não carregado ou está vazio.")
        return pd.DataFrame()
    if MODELO_CF_GLOBAL is None:
        print("ERRO: MODELO_CF_GLOBAL não carregado.")
        return pd.DataFrame()
    if FUZZY_SISTEMA_GLOBAL is None:
        print("ERRO: FUZZY_SISTEMA_GLOBAL não carregado.")
        return pd.DataFrame()

    print("\nIniciando processo de recomendação híbrida...")
    try:
        if 'userId' not in USUARIOS_RATINGS_DF_GLOBAL.columns:
            print(f"ERRO: Coluna 'userId' não encontrada em '{USUARIOS_CSV}'.")
            return pd.DataFrame()

        user_ratings = USUARIOS_RATINGS_DF_GLOBAL[USUARIOS_RATINGS_DF_GLOBAL['userId'] == user_id]
        if user_ratings.empty:
            print(f"Erro: Usuário {user_id} não encontrado ou não possui avaliações em '{USUARIOS_CSV}'.")
            return pd.DataFrame()

        seen_movie_ids = set(user_ratings['movieId'])
        favoritos_filtered = user_ratings[user_ratings['rating'] >= 4.5]
        if favoritos_filtered.empty:
            favorite_movie_ids = set()
        else:
            favorite_movie_ids = set(favoritos_filtered['movieId'].tolist())
        
        all_movie_ids = set(FILMES_DF_GLOBAL.index)
        unseen_movie_ids = list(all_movie_ids - seen_movie_ids)
        
        if not favorite_movie_ids:
            print(f"Aviso: Usuário {user_id} não tem filmes 'favoritos' (>= 4.5). A Lista B (PNL) será vazia ou limitada.")
            
    except Exception as e:
        print(f"Erro ao processar dados do usuário {user_id} na fase inicial: {e}")
        return pd.DataFrame() 

    cf_scores_map = _get_lista_a_cf(MODELO_CF_GLOBAL, user_id, unseen_movie_ids)
    
    pnl_candidates_set = _get_lista_b_pnl(favorite_movie_ids)

    cf_candidates_set = set(cf_scores_map.keys())
    candidate_ids = cf_candidates_set.union(pnl_candidates_set)
    candidate_ids = candidate_ids - seen_movie_ids # Remove filmes já vistos novamente
    
    print(f"Listas combinadas. Total de {len(candidate_ids)} candidatos únicos para ranquear.")

    if FUZZY_SISTEMA_GLOBAL is None:
        print("ERRO: Sistema Fuzzy não carregado.")
        return pd.DataFrame()
        
    simulacao_fuzzy = ctrl.ControlSystemSimulation(FUZZY_SISTEMA_GLOBAL) # Usa o sistema fuzzy GLOBAL
    recomendacoes = []
    
    # --- CONTADORES DE DEBUG ---
    cont_sucesso = 0
    cont_falha_key = 0
    cont_falha_type = 0
    cont_falha_tempo = 0

    print("Iniciando filtragem por tempo e ranqueamento Fuzzy...")
    for movie_id in candidate_ids:
        
        if FILMES_DF_GLOBAL is None or movie_id not in FILMES_DF_GLOBAL.index:
            cont_falha_key += 1
            continue 
        movie_data_series = FILMES_DF_GLOBAL.loc[movie_id] 

        try:
            duracao_raw = movie_data_series.get('duracao')
            
            if duracao_raw is None: 
                cont_falha_key += 1
                continue

            duracao = int(duracao_raw)
            
            # 2. VERIFICA O TEMPO
            if duracao > tempo_disponivel_min:
                cont_falha_tempo += 1
                continue 
            
        except (ValueError, TypeError): 
            cont_falha_type += 1
            continue
        except Exception: 
            cont_falha_type += 1
            continue

        # --- REFINAMENTO (CF + FUZZY) ---
        nota_prevista = cf_scores_map.get(movie_id)
        if nota_prevista is None:
            continue 
            
        min_nota = 1
        max_nota = 5
        min_tempo = 0
        max_tempo = 200

        if not (min_nota <= nota_prevista <= max_nota):
            continue 
        if not (min_tempo <= tempo_disponivel_min <= max_tempo):
            continue 

        simulacao_fuzzy.input['nota_prevista'] = nota_prevista
        simulacao_fuzzy.input['tempo_disponivel'] = tempo_disponivel_min
        
        try:
            simulacao_fuzzy.compute()
            prioridade = simulacao_fuzzy.output['prioridade_final']
        except ValueError as fuzzy_e: 
            prioridade = 0 
        except Exception as e:
            prioridade = 0 

        recomendacoes.append({
            'movieId': movie_id,
            'titulo': movie_data_series.get('titulo', f"Filme ID {movie_id}"), 
            'prioridade_fuzzy': prioridade,
            'nota_prevista_cf': nota_prevista,
            'duracao_min': duracao
        })
        cont_sucesso += 1 

    print("\n--- RELATÓRIO DE DIAGNÓSTICO ---")
    print(f"Filmes que passaram nos filtros: {cont_sucesso}")
    print(f"Filmes filtrados por Tempo.....: {cont_falha_tempo}")
    print(f"Filmes filtrados por KeyError..: {cont_falha_key}")
    print(f"Filmes filtrados por TypeError.: {cont_falha_type}")
    print("---------------------------------")
    
    if not recomendacoes:
        print("Nenhuma recomendação encontrada após aplicar todos os filtros.")
        return pd.DataFrame()
        
    df_recs = pd.DataFrame(recomendacoes)
    df_recs = df_recs.sort_values(by='prioridade_fuzzy', ascending=False)
    
    return df_recs.head(top_n) 

if __name__ == "__main__":
    
    print("\n" + "="*50)
    print("EXECUTANDO 'recomendar.py' DIRETAMENTE PARA TESTE...")
    print("="*50)

    # Note: O carregamento de recursos agora acontece na importação do módulo.
    # Esta verificação é para garantir que o carregamento global foi bem-sucedido.
    if FILMES_DF_GLOBAL is not None and MODELO_CF_GLOBAL is not None:
            
        USER_ID_TESTE = 1      
        TEMPO_DISPONIVEL_TESTE = 90
        TOP_N_TESTE = 5
        
        print("\n" + "="*50)
        print(f"GERANDO RECOMENDAÇÕES HÍBRIDAS PARA (TESTE):")
        print(f"  Usuário ID: {USER_ID_TESTE}")
        print(f"  Tempo Disponível: {TEMPO_DISPONIVEL_TESTE} minutos")
        print(f"  Top N: {TOP_N_TESTE}")
        print("="*50)

        recomendacoes_finais = gerar_recomendacoes_hibridas(
            user_id=USER_ID_TESTE,
            tempo_disponivel_min=TEMPO_DISPONIVEL_TESTE,
            top_n=TOP_N_TESTE
        )
        
        if not recomendacoes_finais.empty:
            print("\n--- TESTE BEM-SUCEDIDO: RECOMENDAÇÕES FINAIS ---")
            pd.set_option('display.float_format', '{:.2f}'.format)
            print(recomendacoes_finais) # Imprime o DataFrame completo
        else:
            print("\n--- TESTE CONCLUÍDO (SEM RESULTADOS) ---")
            print("O sistema funcionou, mas nenhum filme correspondeu a todos os critérios ou ao usuário.")
    else:
        print("\n--- TESTE FALHOU ---")
        print("Não foi possível carregar os modelos e dados.")