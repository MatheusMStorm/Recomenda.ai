import pandas as pd
import pickle
import os
import numpy as np
import busca_filme
from skfuzzy import control as ctrl
from surprise import SVD, Dataset, Reader


# --- Passo 1: Definição dos Caminhos ---

# Define constantes globais (variáveis) que apontam para os arquivos
# de dados e os OUTROS DOIS modelos que este script precisa carregar.
FILMES = os.path.join("Data", "filmes.csv")
USUARIOS_FILE = os.path.join("Data", "usuarios.csv")
CF_MODEL_FILE = os.path.join("Modelos", "modelo_colaborativo.pkl")
FUZZY_MODEL_FILE = os.path.join("Modelos", "fuzzy_control_system.pkl")

# --- Passo 2: Função de Carregamento Principal ---

def carregar_modelos_e_dados_principais():
    """
    Propósito: Carregar todos os "ingredientes" necessários para a recomendação,
    EXCETO o modelo PNL (que 'busca_filme' já carregou).
    
    Esta função será chamada pela aplicação principal (GUI ou main.py)
    no início para preparar o sistema.
    """
    print("Carregando modelos (CF, Fuzzy) e dados (Usuários, Filmes)...")
    
    try:
        # 1. Carrega os dados brutos
        filmes_df = pd.read_csv(FILMES, index_col='movieId')
        df_usuarios = pd.read_csv(USUARIOS_FILE)
        
        # 2. Carrega o modelo de Machine Learning (Filtragem Colaborativa)
        # Este modelo foi treinado pelo 'machine.py'
        with open(CF_MODEL_FILE, 'rb') as f:
            modelo_cf = pickle.load(f)
            
        # 3. Carrega o Sistema de Controle Fuzzy
        # Este modelo foi definido pelo 'fuzzy_modulo.py'
        with open(FUZZY_MODEL_FILE, 'rb') as f:
            fuzzy_sistema = pickle.load(f)
            
        print("Modelos CF, Fuzzy e dados carregados com sucesso.")
        
        # Retorna todos os objetos carregados para a aplicação principal
        return filmes_df, df_usuarios, modelo_cf, fuzzy_sistema

    except FileNotFoundError as e:
        print(f"Erro ao carregar o arquivo: {e}")
        print("Verifique se os arquivos .csv e .pkl (CF, Fuzzy) existem.")
        return None

# --- Passo 3: Funções de Geração de Candidatos (Listas A e B) ---

def get_lista_a_cf(modelo_cf, user_id, unseen_movie_ids):
    """
    (Gera a "Lista A": Candidatos da Filtragem Colaborativa)
    
    Propósito: Usar o modelo CF (SVD) para prever a nota que o 'user_id'
    daria para CADA filme que ele ainda não viu ('unseen_movie_ids').
    
    Retorna: Um grande dicionário (mapa) no formato {movieId: nota_prevista}
    """
    print(f"Calculando {len(unseen_movie_ids)} previsões (CF) para o usuário {user_id}...")
    
    predictions = {}
    # Itera sobre milhares de IDs de filmes (todos os não vistos)
    for movie_id in unseen_movie_ids:
        # Usa o modelo 'surprise' para prever a nota
        pred = modelo_cf.predict(uid=user_id, iid=movie_id)
        # Armazena a nota estimada (ex: 4.21) no dicionário
        predictions[movie_id] = pred.est 
        
    print("Cálculo de previsões CF concluído.")
    return predictions

def get_lista_b_pnl(favorite_movie_ids, num_recs_per_movie=25):
    """
    (Gera a "Lista B": Candidatos do Conteúdo/PNL)
    
    Propósito: Encontrar filmes SIMILARES (baseado em sinopse, gênero, etc.)
    aos filmes que o usuário já "favoritou" (nota alta).
    
    Retorna: Um 'set' (conjunto) de movieIds únicos.
    """
    print(f"Buscando filmes similares (PNL) para {len(favorite_movie_ids)} filmes favoritos...")
    
    all_pnl_candidates = set()
    
    # Itera sobre cada filme que o usuário deu nota 4.5 ou 5.0
    for seed_id in favorite_movie_ids:
        
        # --- INTEGRAÇÃO CHAVE ---
        # Aqui, ele chama a função do módulo 'busca_filme'
        # Esta função usa o modelo PNL (MATRIZ_LATENTE) para
        # encontrar os 'top_n' filmes mais parecidos com o 'seed_id'.
        similars = busca_filme.recomendar_por_similaridade(
            movieId_base=seed_id,
            top_n=num_recs_per_movie
        )
        # --- FIM DA INTEGRAÇÃO ---
        
        # Adiciona os resultados ao conjunto (set)
        # O 'set' automaticamente remove duplicatas
        all_pnl_candidates.update(similars)
        
    print(f"Encontrados {len(all_pnl_candidates)} candidatos únicos via PNL.")
    return all_pnl_candidates

# --- Passo 4: Função "Cérebro" de Orquestração ---

def recomendar_filmes(user_id, tempo_disponivel, filmes_df, df_usuarios, modelo_cf, fuzzy_sistema):
    """
    Esta é a função principal que orquestra todo o processo de recomendação.
    Ela segue a arquitetura híbrida de "blend" (mistura).
    
    Retorna: Um DataFrame Pandas com o Top 10, ordenado pela prioridade.
    """
    
    # --- Passo 4.1: Setup do Usuário ---
    print("\nIniciando processo de recomendação...")
    try:
        user_data = df_usuarios[df_usuarios['userId'] == user_id]
        seen_movie_ids = set(user_data['movieId'])
        favorite_movie_ids = set(user_data[user_data['rating'] >= 4.5]['movieId'])
        all_movie_ids = set(filmes_df.index)
        unseen_movie_ids = all_movie_ids - seen_movie_ids
        
        if not favorite_movie_ids:
            print(f"Aviso: Usuário {user_id} não tem filmes 'favoritos' (>= 4.5). A Lista B (PNL) ficará vazia.")
            
    except Exception as e:
        print(f"Erro ao processar dados do usuário {user_id}: {e}")
        return pd.DataFrame() 

    # --- Passo 4.2: Gerar Lista A (CF) ---
    cf_scores_map = get_lista_a_cf(modelo_cf, user_id, unseen_movie_ids)
    
    # --- Passo 4.3: Gerar Lista B (PNL) ---
    pnl_candidates_set = get_lista_b_pnl(favorite_movie_ids, num_recs_per_movie=25)

    # --- Passo 4.4: Hibridização (Blend) ---
    cf_candidates_set = set(cf_scores_map.keys())
    candidate_ids = cf_candidates_set.union(pnl_candidates_set)
    candidate_ids = candidate_ids - seen_movie_ids
    
    print(f"Listas combinadas. Total de {len(candidate_ids)} candidatos únicos para ranquear.")

    # --- Passo 4.5: Filtro (Tempo) e Refinamento (Fuzzy) ---
    simulacao_fuzzy = ctrl.ControlSystemSimulation(fuzzy_sistema)
    recomendacoes = []
    
    # --- CONTADORES DE DEBUG ---
    cont_sucesso = 0
    cont_falha_key = 0
    cont_falha_type = 0
    cont_falha_tempo = 0

    print("Iniciando filtragem por tempo e ranqueamento Fuzzy (MODO DEBUG)...")
    for movie_id in candidate_ids:
        
        try:
            movie_data = filmes_df.loc[movie_id]
            
            # 1. TENTA LER A DURAÇÃO
            #   Se o nome da coluna (ex: 'runtime') estiver errado,
            #   ele vai pular para 'except KeyError'.
            duracao = movie_data['runtime'] 
            
            # 2. VERIFICA O TEMPO
            #   Se o tempo for maior, ele pula.
            if duracao > tempo_disponivel:
                cont_falha_tempo += 1
                continue 
            
            # 3. Se chegou aqui, o filme passou no filtro de tempo E a coluna 'runtime' existe
            
        except KeyError:
            # Esta exceção pega:
            # 1. 'movie_id' não encontrado em filmes_df (raro)
            # 2. A COLUNA 'runtime' não foi encontrada (MUITO PROVÁVEL)
            cont_falha_key += 1
            continue 
        except (TypeError, ValueError):
            # Esta exceção pega:
            # 1. Dados inválidos (NaN, '120 min', None) na coluna 'runtime' (MUITO PROVÁVEL)
            cont_falha_type += 1
            continue

        # --- REFINAMENTO (CF + FUZZY) ---
        # Se o filme passou por todos os 'try/except', ele é pontuado.
        
        nota_prevista = cf_scores_map.get(movie_id)
        if nota_prevista is None:
            continue 
            
        simulacao_fuzzy.input['nota_prevista'] = nota_prevista
        simulacao_fuzzy.input['tempo_disponivel'] = tempo_disponivel
        
        try:
            simulacao_fuzzy.compute()
            prioridade = simulacao_fuzzy.output['prioridade_final']
        except ValueError:
            prioridade = 0 

        recomendacoes.append({
            'movieId': movie_id,
            'titulo': movie_data['title'],
            'prioridade_fuzzy': prioridade,
            'nota_prevista_cf': nota_prevista,
            'duracao_min': duracao
        })
        cont_sucesso += 1 # Conta como um sucesso

    # --- Passo 4.6: Classificar e Retornar ---
    
    # --- IMPRIME O RELATÓRIO DE DEBUG ---
    print("\n--- RELATÓRIO DE DIAGNÓSTICO ---")
    print(f"Filmes que passaram nos filtros: {cont_sucesso}")
    print(f"Filmes filtrados por Tempo.....: {cont_falha_tempo}")
    print(f"Filmes filtrados por KeyError..: {cont_falha_key} (Verifique o NOME da coluna 'runtime')")
    print(f"Filmes filtrados por TypeError.: {cont_falha_type} (Verifique DADOS INVÁLIDOS (NaN) na coluna 'runtime')")
    print("---------------------------------")
    
    if not recomendacoes:
        print("Nenhuma recomendação encontrada após aplicar todos os filtros.")
        return pd.DataFrame()
        
    df_recs = pd.DataFrame(recomendacoes)
    df_recs = df_recs.sort_values(by='prioridade_fuzzy', ascending=False)
    
    return df_recs

# --- (Cole isto substituindo seu bloco if __name__ == "__main__") ---

if __name__ == "__main__":
    
    print("\n" + "="*50)
    print("EXECUTANDO 'recomendar.py' DIRETAMENTE PARA TESTE...")
    print("="*50)

    if busca_filme.MATRIZ_LATENTE is None:
        print("TESTE FALHOU: O modelo PNL (de 'busca_filme') não foi carregado.")
    else:
        print("Iniciando carregamento de modelos (CF, Fuzzy) e dados...")
        dados_carregados = carregar_modelos_e_dados_principais()
        
        if dados_carregados:
            filmes_df, df_usuarios, modelo_cf, fuzzy_sistema = dados_carregados
            
            # --- PARÂMETROS DE TESTE ---
            USER_ID_TESTE = 1         
            # Define um tempo GIGANTE para desativar o filtro de tempo
            TEMPO_DISPONIVEL_TESTE = 999 
            
            print("\n" + "="*50)
            print(f"GERANDO RECOMENDAÇÕES HÍBRIDAS PARA (TESTE):")
            print(f"  Usuário ID: {USER_ID_TESTE}")
            print(f"  Tempo Disponível: {TEMPO_DISPONIVEL_TESTE} minutos (TESTE)")
            print("="*50)

            recomendacoes_finais = recomendar_filmes(
                user_id=USER_ID_TESTE,
                tempo_disponivel=TEMPO_DISPONIVEL_TESTE,
                filmes_df=filmes_df,
                df_usuarios=df_usuarios,
                modelo_cf=modelo_cf,
                fuzzy_sistema=fuzzy_sistema
            )
            
            if not recomendacoes_finais.empty:
                print("\n--- TESTE BEM-SUCEDIDO: RECOMENDAÇÕES FINAIS ---")
                pd.set_option('display.float_format', '{:.2f}'.format)
                print(recomendacoes_finais.head(10)) 
            else:
                print("\n--- TESTE CONCLUÍDO (SEM RESULTADOS) ---")
                print("O sistema funcionou, mas nenhum filme correspondeu a todos os critérios.")
        
        else:
            print("\n--- TESTE FALHOU ---")
            print("Não foi possível carregar os modelos e dados (CF/Fuzzy/CSVs).")
    

#combinar os resultados dos três modelos (PNL, ML, Fuzzy) para gerar a recomendação 
#Carregar os modelos, criar as funções, fazer refinamento