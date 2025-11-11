import os
import sys

# --- Configuração do sys.path para encontrar módulos ---
# Garante que a raiz do projeto seja adicionada ao sys.path.
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(current_script_dir) 
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Importa os módulos usando o nome completo do pacote
import Codigo_fonte.gerenciar_usuarios 
import Codigo_fonte.menu_terminal 

print("Iniciando o sistema de recomendação...")

def iniciar_menu_terminal_recomendacao(user_id=None):
    """
    Função wrapper para iniciar o menu interativo de recomendações.
    """
    print("\nIniciando o menu de interação com o sistema de recomendação...")
    try:
        Codigo_fonte.menu_terminal.menu_interativo(initial_user_id=user_id)
        print("Saindo do menu de recomendações.")
    except Exception as e:
        print(f"Ocorreu um erro ao iniciar o menu de recomendações: {e}")

def main_menu():
    """
    Menu principal do sistema.
    """
    while True:
        print("\n--- Menu Principal do Sistema de Recomendação ---")
        print("1. Iniciar Recomendações (Terminal Interativo)")
        print("2. Gerenciar Usuários (Terminal)")
        print("3. Sair")
        
        escolha = input("Escolha uma opção: ")

        if escolha == '1':
            iniciar_menu_terminal_recomendacao() 
        elif escolha == '2':
            new_user_id = Codigo_fonte.gerenciar_usuarios.gerenciar_usuarios_menu()
            if new_user_id is not None:
                print(f"\nRedirecionando para o menu de recomendações com o novo usuário {new_user_id}...")
                iniciar_menu_terminal_recomendacao(user_id=new_user_id)
        elif escolha == '3':
            print("Saindo do sistema. Até mais!")
            break
        else:
            print("Opção inválida. Tente novamente.")

if __name__ == "__main__":
    main_menu()