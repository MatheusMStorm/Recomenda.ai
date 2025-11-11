import pandas as pd
import os
import random

print("Carregando módulo 'gerenciar_usuarios.py'...")

# --- Definição de Caminhos ---
USUARIOS_CSV_PATH_GER = os.path.join("Data", "usuarios.csv")
FILMES_CSV_PATH_GER = os.path.join("Data", "filmes.csv")

# --- Variáveis Globais de Dados ---
USUARIOS_DF_GER = None
FILMES_DF_GER = None

def _carregar_dados_gerenciamento():
    """
    Carrega o DataFrame de usuários e filmes globalmente para o módulo.
    Cria o arquivo 'usuarios.csv' se não existir ou estiver vazio.
    """
    global USUARIOS_DF_GER, FILMES_DF_GER
    
    print("Iniciando carregamento de dados para gerenciamento de usuários...")
    
    try:
        # Carrega filmes (necessário para listar filmes ao adicionar avaliações)
        FILMES_DF_GER = pd.read_csv(FILMES_CSV_PATH_GER)
        
        # Carrega ou cria USUARIOS_DF_GER
        if os.path.exists(USUARIOS_CSV_PATH_GER) and os.path.getsize(USUARIOS_CSV_PATH_GER) > 0:
            USUARIOS_DF_GER = pd.read_csv(USUARIOS_CSV_PATH_GER)
            # Garante que userId seja int para consistência
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
        print(f"Verifique se '{FILMES_CSV_PATH_GER}' existe.")
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

def _get_next_user_id():
    """Retorna o próximo userId disponível."""
    if USUARIOS_DF_GER is None or USUARIOS_DF_GER.empty or 'userId' not in USUARIOS_DF_GER.columns:
        return 1
    # Pega o maior userId existente e adiciona 1
    return USUARIOS_DF_GER['userId'].max() + 1

def _adicionar_novo_usuario():
    """Adiciona um novo usuário ao sistema."""
    global USUARIOS_DF_GER
    new_user_id = _get_next_user_id()
    
    # Para adicionar um usuário, ele precisa ter pelo menos 1 rating para aparecer no menu de recomendação
    print(f"\nAdicionando novo usuário com ID: {new_user_id}")
    adicionar_avaliacoes(new_user_id) # Chama a função para adicionar avaliações

    print(f"Usuário {new_user_id} adicionado com sucesso (com avaliações).")
    return new_user_id

def _listar_usuarios():
    """Lista todos os usuários existentes."""
    global USUARIOS_DF_GER
    if USUARIOS_DF_GER is None or USUARIOS_DF_GER.empty:
        print("\nNão há usuários registrados ainda.")
        return False
    
    print("\n--- Usuários Registrados ---")
    # Pega apenas os IDs únicos dos usuários
    user_ids = USUARIOS_DF_GER['userId'].unique()
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

    _listar_usuarios()
    try:
        user_id_del = int(input("Digite o ID do usuário a ser deletado: "))
        
        # Checagem explícita para o userId
        if user_id_del not in USUARIOS_DF_GER['userId'].unique():
            print("ID de usuário não encontrado.")
            return

        # Filtra o DataFrame para remover as linhas do usuário
        USUARIOS_DF_GER = USUARIOS_DF_GER[USUARIOS_DF_GER['userId'] != user_id_del]
        _salvar_usuarios_df()
        print(f"Usuário {user_id_del} e todas as suas avaliações foram deletados.")
    except ValueError:
        print("Entrada inválida. Por favor, digite um número inteiro.")

def adicionar_avaliacoes(user_id):
    """Permite adicionar avaliações para um usuário específico."""
    global USUARIOS_DF_GER, FILMES_DF_GER
    
    if FILMES_DF_GER is None or FILMES_DF_GER.empty:
        print("Não foi possível carregar o catálogo de filmes. Não é possível adicionar avaliações.")
        return

    print(f"\n--- Adicionando Avaliações para Usuário {user_id} ---")
    print("Digite 'fim' para parar de adicionar avaliações.")

    while True:
        titulo_busca = input("Digite parte do título do filme para buscar (ou 'fim'): ").strip()
        if titulo_busca.lower() == 'fim':
            break

        # Busca filmes usando fuzzy matching para encontrar o movieId
        # busca_filme.encontrar_movieid_por_titulo pode retornar um movieId ou None
        # Assumindo que essa função retorna o movieId se top_n=1
        
        # Retorna uma lista de movieIds ou None. Usamos o primeiro se houver.
        found_movie_ids = busca_filme.encontrar_movieid_por_titulo(titulo_busca, top_n=5) 

        if found_movie_ids:
            # Garante que found_movie_ids é uma lista (mesmo que seja de um único elemento)
            if not isinstance(found_movie_ids, list):
                found_movie_ids = [found_movie_ids]
                
            print("\nFilmes encontrados:")
            filmes_encontrados_info = []
            for i, mid in enumerate(found_movie_ids):
                # Usamos .isin() para checagem segura
                filme_row = FILMES_DF_GER[FILMES_DF_GER['movieId'].isin([mid])]
                if not filme_row.empty:
                    f = filme_row.iloc[0]
                    filmes_encontrados_info.append({'idx': i+1, 'movieId': f['movieId'], 'titulo': f['titulo']})
                    print(f"{i+1}. Título: {f['titulo']} (ID: {f['movieId']})")
            
            if not filmes_encontrados_info:
                print("Nenhum detalhe de filme encontrado no catálogo para os IDs retornados.")
                continue

            try:
                escolha_idx = int(input("Escolha o número do filme para avaliar (ou 0 para cancelar): "))
                if escolha_idx == 0:
                    continue
                
                filme_escolhido = next((item for item in filmes_encontrados_info if item['idx'] == escolha_idx), None)

                if filme_escolhido is None:
                    print("Escolha inválida.")
                    continue

                movie_id = filme_escolhido['movieId']
                titulo_filme = filme_escolhido['titulo']

                while True:
                    try:
                        rating = float(input(f"Avalie '{titulo_filme}' (1.0 a 5.0): "))
                        if 1.0 <= rating <= 5.0:
                            break
                        else:
                            print("Avaliação inválida. Digite um número entre 1.0 e 5.0.")
                    except ValueError:
                        print("Entrada inválida. Digite um número.")

                # Cria um novo registro de avaliação
                new_rating_data = pd.DataFrame([{
                    'userId': user_id,
                    'movieId': movie_id,
                    'rating': rating,
                    'timestamp': int(pd.Timestamp.now().timestamp())
                }])

                # Concatena o novo registro ao DataFrame global
                # Utiliza concat para uma operação segura
                USUARIOS_DF_GER = pd.concat([USUARIOS_DF_GER, new_rating_data], ignore_index=True)
                _salvar_usuarios_df()
                print(f"Avaliação para '{titulo_filme}' adicionada com sucesso.")

            except ValueError:
                print("Entrada inválida. Tente novamente.")
            except Exception as e:
                print(f"Ocorreu um erro ao processar a avaliação: {e}")
        else:
            print(f"Nenhum filme encontrado para '{titulo_busca}'.")

def gerenciar_usuarios_menu():
    """
    Menu para gerenciar usuários (adicionar, listar, deletar, adicionar avaliações).
    Retorna o novo user_id se um for adicionado e o usuário quiser ir para recomendação.
    """
    global USUARIOS_DF_GER
    
    # Recarrega os dados antes de exibir o menu para garantir que está atualizado
    _carregar_dados_gerenciamento()

    new_user_id_added = None

    while True:
        print("\n--- Gerenciar Usuários ---")
        print("1. Adicionar Novo Usuário")
        print("2. Listar Usuários")
        print("3. Deletar Usuário")
        print("4. Adicionar Avaliações a Usuário Existente")
        print("5. Voltar ao Menu Principal")
        
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            new_user_id_added = _adicionar_novo_usuario()
            escolha_recomendar = input(f"Deseja iniciar recomendações para o novo usuário {new_user_id_added} (s/n)? ").lower()
            if escolha_recomendar == 's':
                return new_user_id_added # Retorna o ID para o main.py
            new_user_id_added = None # Reseta se não for para recomendação
        elif escolha == '2':
            _listar_usuarios()
        elif escolha == '3':
            _deletar_usuario()
        elif escolha == '4':
            if _listar_usuarios(): # Lista usuários e verifica se existem
                try:
                    user_id_avaliar = int(input("Digite o ID do usuário para adicionar avaliações: "))
                    if user_id_avaliar in USUARIOS_DF_GER['userId'].unique():
                        adicionar_avaliacoes(user_id_avaliar)
                    else:
                        print("ID de usuário não encontrado.")
                except ValueError:
                    print("Entrada inválida. Digite um número inteiro.")
            else:
                print("Não há usuários para avaliar.")
        elif escolha == '5':
            return None # Retorna None para o main.py (não redireciona)
        else:
            print("Opção inválida. Tente novamente.")

# Bloco de execução para testar o módulo diretamente
if __name__ == "__main__":
    print("\n" + "="*50)
    print("EXECUTANDO 'gerenciar_usuarios.py' DIRETAMENTE PARA TESTE...")
    print("="*50)
    gerenciar_usuarios_menu()