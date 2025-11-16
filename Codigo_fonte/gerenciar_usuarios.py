import pandas as pd
import os
import random
from . import busca_filme 
import time
import numpy as np


USUARIOS_CSV_PATH_GER = os.path.join("Data", "usuarios.csv")
FILMES_CSV_PATH_GER = os.path.join("Data", "filmes.csv") 
USUARIOS_DF_GER = None
FILMES_DF_GER = None

def _carregar_dados_gerenciamento():
    """Carrega o DataFrame de usuários e filmes globalmente."""
    global USUARIOS_DF_GER, FILMES_DF_GER
    
    print("Iniciando carregamento de dados para gerenciamento de usuários...")
    
    try:
        # Carrega filmes (necessário para listar filmes ao adicionar avaliações)
        FILMES_DF_GER = pd.read_csv(FILMES_CSV_PATH_GER)
        
        # Carrega ou cria USUARIOS_DF_GER
        if os.path.exists(USUARIOS_CSV_PATH_GER) and os.path.getsize(USUARIOS_CSV_PATH_GER) > 0:
            USUARIOS_DF_GER = pd.read_csv(USUARIOS_CSV_PATH_GER)
            USUARIOS_DF_GER['userId'] = USUARIOS_DF_GER['userId'].astype(int)
            print("Arquivo 'usuarios.csv' carregado com sucesso.")
        else:
            # Cria um DataFrame vazio com as colunas esperadas se o arquivo não existir/estiver vazio
            USUARIOS_DF_GER = pd.DataFrame(columns=['userId', 'movieId', 'rating', 'timestamp'])
            USUARIOS_DF_GER.to_csv(USUARIOS_CSV_PATH_GER, index=False)
            print("Arquivo 'usuarios.csv' criado como vazio.")
            
        return True
    except FileNotFoundError as e:
        print(f"ERRO CRÍTICO ao carregar arquivo de dados para gerenciamento: {e}")
        return False
    except Exception as e:
        print(f"ERRO INESPERADO ao carregar dados para gerenciamento: {e}")
        return False

# Carrega os dados na inicialização do módulo
_carregar_dados_gerenciamento()

def _salvar_usuarios_df():
    """Salva o DataFrame de usuários no arquivo CSV."""
    global USUARIOS_DF_GER
    if USUARIOS_DF_GER is not None:
        USUARIOS_DF_GER.to_csv(USUARIOS_CSV_PATH_GER, index=False)
        print("Dados de usuários salvos em 'usuarios.csv'.")

def obter_proximo_userid():
    """Retorna o próximo userId disponível."""
    if USUARIOS_DF_GER is None or USUARIOS_DF_GER.empty or 'userId' not in USUARIOS_DF_GER.columns:
        return 1
    return USUARIOS_DF_GER['userId'].max() + 1

def _adicionar_novo_usuario():
    """Adiciona um novo usuário ao sistema."""
    global USUARIOS_DF_GER
    new_user_id = obter_proximo_userid()
    
    print(f"\nAdicionando novo usuário com ID: {new_user_id}")
    adicionar_avaliacoes(new_user_id) # Chama a função para adicionar avaliações

    print(f"Usuário {new_user_id} adicionado com sucesso (com avaliações).")
    return new_user_id

def _listar_usuarios():
    """Lista todos os userIds existentes no sistema."""
    global USUARIOS_DF_GER
    if USUARIOS_DF_GER is None or USUARIOS_DF_GER.empty:
        print("\nNão há usuários registrados ainda.")
        return False 

    if 'userId' not in USUARIOS_DF_GER.columns:
        print("\nAVISO: Coluna 'userId' não encontrada no DataFrame.")
        return False
        
    user_ids = USUARIOS_DF_GER['userId'].unique()

    if user_ids.size == 0:
        print("\nNão há usuários registrados ainda.")
        return False
        
    print("\n--- Usuários Registrados ---")
    for uid in user_ids:
        print(f" - ID: {uid}")
    print("--------------------------")
    return True

def _deletar_usuario():
    """Deleta um usuário existente e suas avaliações."""
    global USUARIOS_DF_GER
    if USUARIOS_DF_GER is None or USUARIOS_DF_GER.empty:
        print("Não há usuários para deletar.")
        return

    try:
        user_id_del = int(input("Digite o ID do usuário a ser deletado: ").strip())
        if user_id_del in USUARIOS_DF_GER['userId'].unique():
            USUARIOS_DF_GER = USUARIOS_DF_GER[USUARIOS_DF_GER['userId'] != user_id_del]
            _salvar_usuarios_df()
            print(f"Usuário {user_id_del} e suas avaliações deletados com sucesso.")
        else:
            print("ID de usuário não encontrado.")
    except ValueError:
        print("Entrada inválida. Por favor, digite um número inteiro.")

def selecionar_usuario_existente():
    """Permite ao usuário selecionar um ID de usuário existente."""
    global USUARIOS_DF_GER
    if _listar_usuarios():
        try:
            user_id_sel = int(input("Digite o ID do usuário que deseja selecionar: ").strip())
            if user_id_sel in USUARIOS_DF_GER['userId'].unique():
                print(f"Usuário {user_id_sel} selecionado.")
                return user_id_sel
            else:
                print("ID de usuário não encontrado.")
                return None
        except ValueError:
            print("Entrada inválida. Digite um número inteiro.")
            return None
    return None

def adicionar_avaliacoes(user_id, num_avaliacoes_aleatorias=10):
    """
    Permite ao usuário adicionar avaliações (ou atribui avaliações aleatórias se o catálogo for pequeno).
    """
    global USUARIOS_DF_GER, FILMES_DF_GER
    
    if FILMES_DF_GER is None or FILMES_DF_GER.empty:
        print("Não foi possível carregar o catálogo de filmes. Não é possível adicionar avaliações.")
        return

    print(f"\n--- Adicionando Avaliações para Usuário {user_id} ---")
    print("Digite 'fim' para parar de adicionar avaliações.")

    # 1. Atribuição de Avaliações Aleatórias (Para garantir que o novo usuário tenha dados)
    if user_id not in USUARIOS_DF_GER['userId'].unique():
        print("Atribuindo avaliações iniciais aleatórias (para fins de teste)...")
        filmes_para_amostra = FILMES_DF_GER[FILMES_DF_GER['movieId'].notna()]
        if len(filmes_para_amostra) >= num_avaliacoes_aleatorias:
            filmes_selecionados = filmes_para_amostra['movieId'].sample(num_avaliacoes_aleatorias, random_state=int(time.time()))
        else:
            filmes_selecionados = filmes_para_amostra['movieId'].sample(len(filmes_para_amostra), random_state=int(time.time()))
        
        novas_avaliacoes = []
        for movie_id in filmes_selecionados:
            rating = np.random.choice([4.0, 4.5, 5.0])
            novas_avaliacoes.append({'userId': user_id, 'movieId': movie_id, 'rating': rating, 'timestamp': int(time.time())})
        
        if novas_avaliacoes:
            USUARIOS_DF_GER = pd.concat([USUARIOS_DF_GER, pd.DataFrame(novas_avaliacoes)], ignore_index=True)
            _salvar_usuarios_df()
            print(f"Atribuição de {len(novas_avaliacoes)} avaliações aleatórias concluída.")

    # 2. Loop para Entrada Manual
    print("\nVocê pode adicionar mais avaliações manualmente agora.")
    while True:
        titulo_busca = input("Digite parte do título do filme para buscar (ou 'fim'): ").strip()
        if titulo_busca.lower() == 'fim':
            break # Sai do loop de entrada manual

        # A função busca_filme.encontrar_movieid_por_titulo retorna uma LISTA DE IDs (inteiros)
        found_movie_ids = busca_filme.encontrar_movieid_por_titulo(titulo_busca, top_n=5) 
        
        if found_movie_ids:
            # Filtra o DataFrame de filmes com base nos IDs encontrados
            filmes_encontrados_df = FILMES_DF_GER[FILMES_DF_GER['movieId'].isin(found_movie_ids)]
            
            if filmes_encontrados_df.empty:
                print("Nenhum detalhe de filme encontrado no catálogo para os IDs retornados.")
                continue

            print("\nFilmes encontrados:")
            filmes_encontrados_info = []
            for i, row in filmes_encontrados_df.iterrows():
                # Note: 'titulo' e 'movieId' são acessados diretamente do DataFrame
                filmes_encontrados_info.append({'idx': i+1, 'movieId': row['movieId'], 'titulo': row['titulo']})
                print(f"{i+1}. Título: {row['titulo']} (ID: {row['movieId']})")

            filme_selecionado = None 
            while True:
                try:
                    escolha_idx_str = input("Escolha o número do filme para avaliar (ou '0' para cancelar): ").strip()
                    
                    if escolha_idx_str == '0':
                        break # Volta para o loop de busca por título
                    
                    escolha_idx = int(escolha_idx_str)
                    
                    # Usa next() para encontrar o filme escolhido no dicionário de informações
                    filme_selecionado = next((item for item in filmes_encontrados_info if item['idx'] == escolha_idx), None)

                    if filme_selecionado is None:
                        print("Escolha inválida. O número não corresponde a nenhum filme da lista.")
                        continue
                    break

                except ValueError:
                    print("Entrada inválida. Digite um número inteiro ou '0'.")
                    continue

            # --- LÓGICA DE AVALIAÇÃO (SÓ EXECUTA SE HOUVE UM FILME SELECIONADO) ---
            if filme_selecionado is None:
                continue # Volta para o loop de busca por título (se o usuário cancelou ou a escolha falhou)
            
            movie_id = filme_selecionado['movieId']
            titulo_filme = filme_selecionado['titulo']

            while True:
                try:
                    rating = float(input(f"Avalie '{titulo_filme}' (1.0 a 5.0): ").strip())
                    if 1.0 <= rating <= 5.0:
                        break
                    else:
                        print("Avaliação inválida. Digite um número entre 1.0 e 5.0.")
                except ValueError:
                    print("Entrada inválida. Digite um número.")

            new_rating_data = pd.DataFrame([{
                'userId': user_id,
                'movieId': movie_id,
                'rating': rating,
                'timestamp': int(pd.Timestamp.now().timestamp())
            }])

            USUARIOS_DF_GER = pd.concat([USUARIOS_DF_GER, new_rating_data], ignore_index=True)
            _salvar_usuarios_df()
            print(f"Avaliação para '{titulo_filme}' adicionada com sucesso.")
            
        else:
            print(f"Nenhum filme encontrado para '{titulo_busca}'.")


def gerenciar_usuarios_menu():
    """
    Menu principal para gerenciamento de usuários.
    Retorna o userId selecionado/criado para ser usado no menu de recomendações.
    """
    new_user_id_return = None
    while True:
        print("\n--- Menu de Gerenciamento de Usuários ---")
        print("1. Adicionar Novo Usuário")
        print("2. Selecionar Usuário Existente")
        print("3. Deletar Usuário")
        print("4. Adicionar Avaliações a Usuário Existente")
        print("5. Voltar ao Menu Principal")

        escolha = input("Escolha uma opção: ").strip()

        if escolha == '1':
            new_user_id_added = _adicionar_novo_usuario()
            if new_user_id_added is not None:
                escolha_recomendar = input(f"Deseja iniciar recomendações para o novo usuário {new_user_id_added} (s/n)? ").lower()
                if escolha_recomendar == 's':
                    return new_user_id_added
            new_user_id_return = None
        elif escolha == '2':
            new_user_id_added = selecionar_usuario_existente() 
            if new_user_id_added is not None:
                return new_user_id_added
        elif escolha == '3':
            if _listar_usuarios():
                _deletar_usuario()
            else:
                print("Não há usuários para deletar.")
        elif escolha == '4':
            if _listar_usuarios():
                try:
                    user_id_avaliar = int(input("Digite o ID do usuário para adicionar avaliações: ").strip())
                    if user_id_avaliar in USUARIOS_DF_GER['userId'].unique():
                        adicionar_avaliacoes(user_id_avaliar)
                    else:
                        print("ID de usuário não encontrado.")
                except ValueError:
                    print("Entrada inválida. Digite um número inteiro.")
            else:
                print("Não há usuários para avaliar.")
        elif escolha == '5':
            return new_user_id_return
        else:
            print("Opção inválida. Tente novamente.")
            time.sleep(1)
    return new_user_id_return


if __name__ == "__main__":
    print("\n" + "="*50)
    print("EXECUTANDO 'gerenciar_usuarios.py' DIRETAMENTE PARA TESTE...")
    print("="*50)
    gerenciar_usuarios_menu()