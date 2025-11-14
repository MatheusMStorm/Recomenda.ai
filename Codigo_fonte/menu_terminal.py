import pandas as pd
import os
# MUDANÇA: 'from .' foi alterado para 'from Codigo_fonte'
from Codigo_fonte import recomendar 
from Codigo_fonte import busca_filme 

print("Iniciando o Menu Interativo (menu_terminal.py)...")

# --- 1. Carregamento de Dados Auxiliares ---
FILMES_CSV_PATH = os.path.join("Data", "filmes.csv")
USUARIOS_CSV_PATH = os.path.join("Data", "usuarios.csv") # Este é o que contém os ratings dos usuários

FILMES_DF_MENU = None
USUARIOS_RATINGS_DF_MENU = None 

try:
    FILMES_DF_MENU = pd.read_csv(FILMES_CSV_PATH)
    
    # Tenta carregar usuarios.csv, verificando se não está vazio
    if os.path.exists(USUARIOS_CSV_PATH) and os.path.getsize(USUARIOS_CSV_PATH) > 0:
        USUARIOS_RATINGS_DF_MENU = pd.read_csv(USUARIOS_CSV_PATH)
    else:
        print(f"AVISO: '{USUARIOS_CSV_PATH}' está vazio ou não existe. O gerenciamento de usuários o criará/preencherá.")
        USUARIOS_RATINGS_DF_MENU = pd.DataFrame(columns=['userId', 'movieId', 'rating', 'timestamp']) # DataFrame vazio com colunas esperadas
        
    print("Dados de filmes e usuários carregados para o menu terminal.")
except FileNotFoundError:
    print("\nERRO: Arquivos de dados (filmes.csv ou usuarios.csv) não encontrados.")
    input("Pressione Enter para sair...")
    exit(1)
except Exception as e:
    print(f"\nERRO inesperado ao carregar dados no menu terminal: {e}")

def exibir_recomendacoes(user_id, tempo_disponivel_min, top_n_recomendacoes):
    """
    Chama o módulo de recomendação e exibe os resultados no terminal.
    """
    print(f"\n--- Gerando Recomendações para Usuário {user_id} (Tempo: {tempo_disponivel_min} min, Top {top_n_recomendacoes}) ---")
    print("Isso pode levar um momento...")
    
    recomendacoes_df = recomendar.gerar_recomendacoes_hibridas(
        user_id=user_id, 
        tempo_disponivel_min=tempo_disponivel_min, 
        top_n=top_n_recomendacoes
    )
    
    if recomendacoes_df is not None and not recomendacoes_df.empty: # Checagem explícita (.empty)
        print(f"\nTop {len(recomendacoes_df)} Recomendações:")
        for i, rec in recomendacoes_df.iterrows(): # Itera sobre as linhas do DataFrame
            print(f"\n{i+1}. Título: {rec['titulo']}")
            print(f"   Prioridade Fuzzy: {rec['prioridade_fuzzy']:.2f}")
            print(f"   Nota Prevista CF: {rec['nota_prevista_cf']:.2f}")
            
            # Busca detalhes adicionais do filme
            if FILMES_DF_MENU is not None and not FILMES_DF_MENU.empty:
                detalhes_filme_row = FILMES_DF_MENU[FILMES_DF_MENU['movieId'] == rec['movieId']]
                if not detalhes_filme_row.empty:
                    detalhes_filme = detalhes_filme_row.iloc[0]
                    print(f"   Gêneros: {detalhes_filme.get('generos', 'N/A')}") 
                    print(f"   Duração: {detalhes_filme.get('duracao', 'N/A')} min")
                else:
                    print(f"   Detalhes do filme ID {rec['movieId']} não encontrados no CSV.")
            print("------------------------------------------")
    else:
        print("Nenhuma recomendação encontrada ou houve um problema na geração.")

def buscar_filme_e_similares():
    """
    Permite ao usuário buscar um filme por título e ver seus similares.
    """
    print("\n--- Buscar um Filme Específico ---")
    titulo_busca = input("Digite o nome do filme (mesmo com erro de digitação, ou 'voltar'): ")
    
    if titulo_busca.lower() == 'voltar':
        return

    if titulo_busca and FILMES_DF_MENU is not None and not FILMES_DF_MENU.empty: 
        movie_id_encontrado = busca_filme.encontrar_movieid_por_titulo(titulo_busca)
        
        if movie_id_encontrado:
            filme_encontrado_row = FILMES_DF_MENU[FILMES_DF_MENU['movieId'] == movie_id_encontrado]
            if not filme_encontrado_row.empty: 
                filme_encontrado = filme_encontrado_row.iloc[0]
                titulo_filme = filme_encontrado.get('titulo', 'N/A')
                print(f"\nFilme encontrado: {titulo_filme} (ID: {movie_id_encontrado})") 
                
                ver_similares = input("Deseja ver filmes similares a este (s/n)? ").lower()
                if ver_similares == 's':
                    print(f"Buscando filmes similares a '{titulo_filme}'...")
                    similares_ids = busca_filme.recomendar_por_similaridade(movie_id_encontrado, top_n=5)
                    
                    if similares_ids: # Checagem de lista/set não é ambígua
                        print(f"\nFilmes com 'DNA' similar a '{titulo_filme}':")
                        for i, mid_sim in enumerate(similares_ids):
                            filme_sim_row = FILMES_DF_MENU[FILMES_DF_MENU['movieId'] == mid_sim]
                            if not filme_sim_row.empty: 
                                filme_sim = filme_sim_row.iloc[0]
                                print(f"  {i+1}. {filme_sim.get('titulo', 'N/A')} (ID: {mid_sim})") 
                            else:
                                print(f"  {i+1}. Filme com ID {mid_sim} não encontrado nos detalhes.")
                    else:
                        print("Nenhum filme similar encontrado.")
            else:
                print(f"Detalhes do filme ID {movie_id_encontrado} não encontrados em {FILMES_CSV_PATH}.")
        else:
            print(f"Nenhum filme encontrado para a busca '{titulo_busca}'.")
    elif FILMES_DF_MENU is None or FILMES_DF_MENU.empty:
        print("Dados de filmes não carregados, não é possível buscar.")

def menu_interativo(initial_user_id=None): 
    # Recarrega USUARIOS_RATINGS_DF_MENU caso ele não tenha sido carregado na inicialização
    # ou caso novos usuários tenham sido adicionados em 'gerenciar_usuarios'.
    global USUARIOS_RATINGS_DF_MENU
    try:
        if os.path.exists(USUARIOS_CSV_PATH) and os.path.getsize(USUARIOS_CSV_PATH) > 0:
            USUARIOS_RATINGS_DF_MENU = pd.read_csv(USUARIOS_CSV_PATH)
        else:
            USUARIOS_RATINGS_DF_MENU = pd.DataFrame(columns=['userId', 'movieId', 'rating', 'timestamp'])
    except Exception as e:
        print(f"\nERRO ao recarregar usuários para o menu: {e}")
        USUARIOS_RATINGS_DF_MENU = pd.DataFrame(columns=['userId', 'movieId', 'rating', 'timestamp'])

    # Checagem explícita para obter IDs de usuários únicos
    if USUARIOS_RATINGS_DF_MENU.empty or 'userId' not in USUARIOS_RATINGS_DF_MENU.columns:
        print("\nATENÇÃO: Nenhum usuário com avaliações encontrado. Por favor, adicione usuários e avaliações primeiro.")
        input("Pressione Enter para voltar ao Menu Principal...")
        return 
        
    user_ids_disponiveis = sorted(USUARIOS_RATINGS_DF_MENU['userId'].unique().tolist())
    
    if not user_ids_disponiveis: # Checagem se a lista de IDs está vazia
        print("\nATENÇÃO: Não há IDs de usuários disponíveis com avaliações. Por favor, adicione usuários primeiro.")
        input("Pressione Enter para voltar ao Menu Principal...")
        return
        
    user_id = initial_user_id 
    
    if user_id is None or user_id not in user_ids_disponiveis: 
        user_id = None 
        while user_id not in user_ids_disponiveis:
            try:
                user_id_input = input(f"Selecione seu ID de Usuário (Disponíveis: {', '.join(map(str, user_ids_disponiveis))}): ")
                user_id = int(user_id_input.strip())
                if user_id not in user_ids_disponiveis:
                    print("ID de usuário inválido. Tente novamente.")
            except ValueError:
                print("Entrada inválida. Digite um número.")

    while True:
        print(f"\n--- Bem-vindo, Usuário {user_id}! ---")
        print("1. Gerar Recomendações Personalizadas")
        print("2. Buscar Filme por Título e Ver Similares")
        print("3. Voltar ao Menu Principal")
        
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            while True: 
                try:
                    tempo_str = input("Quanto tempo você tem disponível (minutos, ex: 120)? ")
                    tempo = int(tempo_str.strip())
                    if tempo <= 0:
                        print("Por favor, digite um tempo positivo.")
                        continue
                    break
                except ValueError:
                    print("Entrada inválida. Por favor, digite um número inteiro para o tempo.")

            while True: 
                try:
                    num_recs_str = input("Quantos filmes você quer ver (ex: 10)? ")
                    num_recs = int(num_recs_str.strip())
                    if num_recs <= 0:
                        print("Por favor, digite um número positivo de recomendações.")
                        continue
                    break
                except ValueError:
                    print("Entrada inválida. Por favor, digite um número inteiro para a quantidade de filmes.")
            
            exibir_recomendacoes(user_id, tempo, num_recs)
        elif escolha == '2':
            buscar_filme_e_similares()
        elif escolha == '3':
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    print("\n" + "="*50)
    print("EXECUTANDO 'menu_terminal.py' DIRETAMENTE PARA TESTE...")
    print("="*50)
    menu_interativo()