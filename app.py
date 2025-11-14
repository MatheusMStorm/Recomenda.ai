import streamlit as st
import pandas as pd
import time
import os
import sys

# --- ID DE DEMONSTRAÇÃO (O "TRUQUE") ---
# Use um ID de usuário que VOCÊ SABE que tem muitas avaliações no seu usuarios.csv
# Quase sempre é o ID 1.
USER_ID_PARA_DEMONSTRACAO = 1 
# -----------------------------------

# --- Configuração do Projeto ---
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(current_script_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- NOSSOS MÓDULOS ---
import auth_simple # O auth simples com senha em texto puro

try:
    from Codigo_fonte import recomendar 
    from Codigo_fonte import busca_filme 
    print("Módulos 'recomendar' e 'busca_filme' importados com sucesso.")
except ImportError as e:
    st.error(f"Erro de Importação: {e}")
    st.error("Verifique se 'app.py' está na pasta raiz e 'recomendar.py' está em 'Codigo_fonte'.")
    st.stop()
except Exception as e:
    st.error(f"Erro inesperado ao carregar módulos: {e}")
    st.stop()

# --- CAMINHOS DOS ARQUIVOS ---
AUTH_CSV = "user_credentials.csv" # Onde os logins/senhas (TEXTO PURO) são salvos
RATINGS_CSV = os.path.join("Data", "usuarios.csv") # Onde as avaliações do usuário estão

# --- Configuração da Página ---
st.set_page_config(page_title="Recomenda Ai Chat", layout="centered")

# --- Inicialização da Memória (Session State) ---
if "username" not in st.session_state:
    st.session_state.username = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "chat_state" not in st.session_state:
    st.session_state.chat_state = "IDLE" 
if "temp_data" not in st.session_state:
    st.session_state.temp_data = {}

# --- LÓGICA DE LOGIN/CADASTRO (Uma só página com abas) ---
if st.session_state.username is None:
    st.title("🤖 Recomenda Ai")
    
    tab_login, tab_cadastro = st.tabs(["Login", "Cadastro"])

    with tab_login:
        st.header("Login")
        with st.form("login_form"):
            username = st.text_input("Nome de Usuário")
            password = st.text_input("Senha", type="password")
            submitted = st.form_submit_button("Entrar")

            if submitted:
                user_id = auth_simple.login_user(username, password, AUTH_CSV)
                if user_id is not None:
                    st.session_state.username = username # Salva o NOME do usuário
                    
                    welcome_message = (f"Olá {username.capitalize()}! "
                                     "Você pode dizer **'recomendar'** para eu te ajudar a encontrar filmes ou **'buscar'** para procurar um título específico.")

                    st.session_state.messages = [{"role": "assistant", "content": welcome_message}]
                    st.session_state.chat_state = "IDLE"
                    st.session_state.temp_data = {}
                    st.rerun()
                else:
                    st.error("Usuário ou senha inválidos.")

    with tab_cadastro:
        st.header("Cadastro")
        st.write("Crie sua conta para acessar o chat.")
        with st.form("cadastro_form"):
            new_username = st.text_input("Escolha um Nome de Usuário")
            new_password = st.text_input("Escolha uma Senha", type="password")
            confirm_password = st.text_input("Confirme a Senha", type="password")
            submitted = st.form_submit_button("Cadastrar")

            if submitted:
                if not new_username or not new_password:
                    st.error("Por favor, preencha todos os campos.")
                elif new_password != confirm_password:
                    st.error("As senhas não coincidem.")
                else:
                    new_user_id = auth_simple.register_user(new_username, new_password, AUTH_CSV, RATINGS_CSV)
                    if new_user_id == "EXISTS":
                        st.error("Esse nome de usuário já existe. Tente outro.")
                    elif new_user_id is not None:
                        st.success(f"Usuário {new_username} cadastrado com sucesso! Fazendo login...")
                        st.session_state.username = new_username # Salva o NOME
                        st.session_state.messages = [{"role": "assistant", "content": (
                            f"Bem-vindo, {new_username.capitalize()}! "
                            "Você pode dizer **'recomendar'** para eu te ajudar a encontrar filmes ou **'buscar'** para procurar um título específico.")}]
                        st.session_state.chat_state = "IDLE"
                        st.session_state.temp_data = {}
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Ocorreu um erro ao cadastrar.")

# --- LÓGICA DO CHATBOT (Usuário Logado) ---
else:
    username_logado = st.session_state.username
    st.title(f"🤖 Chat (Usuário: {username_logado})")

    # Botão de Sair
    if st.sidebar.button("Sair (Logout)"):
        st.session_state.username = None
        st.session_state.messages = []
        st.rerun()

    # Exibe o histórico do chat
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Input do chat
    if prompt := st.chat_input("Diga 'recomendar' ou 'buscar'..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        
        state = st.session_state.chat_state
        
        try:
            # --- ESTADO 1: ESPERANDO COMANDO ---
            if state == "IDLE":
                if "recomendar" in prompt.lower():
                    st.session_state.chat_state = "AWAITING_TIME"
                    bot_response = "Ótimo! Vamos recomendar. Quanto tempo você tem disponível (em minutos)?"
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                elif "buscar" in prompt.lower():
                    st.session_state.chat_state = "AWAITING_SEARCH_TITLE"
                    bot_response = "Claro. Qual o nome do filme que você quer buscar?"
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                
                else:
                    bot_response = "Desculpe, não entendi. Você pode dizer **'recomendar'** ou **'buscar'**."
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})

            # --- ESTADO 2: ESPERANDO O TEMPO ---
            elif state == "AWAITING_TIME":
                tempo = int(prompt.strip())
                st.session_state.temp_data = {"tempo": tempo}
                st.session_state.chat_state = "AWAITING_TOP_N"
                bot_response = f"Perfeito, {tempo} minutos. Quantas recomendações você gostaria de ver (ex: 5, 10)?"
                st.session_state.messages.append({"role": "assistant", "content": bot_response})

            # --- ESTADO 3: ESPERANDO O TOP_N (E EXECUTANDO) ---
            elif state == "AWAITING_TOP_N":
                top_n = int(prompt.strip())
                tempo = st.session_state.temp_data.get("tempo")
                if not tempo: raise Exception("Estado perdido")

                with st.spinner(f"Buscando {top_n} filmes de até {tempo} min... (Usando perfil de demo ID: {USER_ID_PARA_DEMONSTRACAO})"):
                    
                    # --- O "TRUQUE" ESTÁ AQUI ---
                    # Usamos o ID de DEMO (ex: 1) em vez do ID real do usuário logado.
                    recomendacoes_df = recomendar.gerar_recomendacoes_hibridas(
                        USER_ID_PARA_DEMONSTRACAO, 
                        tempo, 
                        top_n
                    )
                
                if recomendacoes_df is not None and not recomendacoes_df.empty:
                    bot_response = "Aqui estão suas recomendações:\n"
                    for i, row in recomendacoes_df.iterrows():
                        bot_response += f"\n- **{row['titulo']}** (Score: {row['prioridade_fuzzy']:.2f} | Duração: {row['duracao_min']} min)"
                    st.session_state.messages.append({"role": "assistant", "content": bot_response})
                else:
                    st.session_state.messages.append({"role": "assistant", "content": "Não encontrei nenhuma recomendação com esses filtros. Tente um tempo maior."})
                
                st.session_state.chat_state = "IDLE"
                st.session_state.temp_data = {}

            # --- ESTADO 4: ESPERANDO TÍTULO DA BUSCA (E EXECUTANDO) ---
            elif state == "AWAITING_SEARCH_TITLE":
                titulo_busca = prompt.strip()
                
                with st.spinner(f"Buscando por '{titulo_busca}'..."):
                    movie_id_encontrado = busca_filme.encontrar_movieid_por_titulo(titulo_busca)
                    
                    if movie_id_encontrado:
                        titulo_real = busca_filme.TITULOS_MAP.get(movie_id_encontrado, "Desconhecido")
                        bot_response = f"Encontrei: **{titulo_real}**. Buscando filmes similares...\n"
                        
                        similares_ids = busca_filme.recomendar_por_similaridade(movie_id_encontrado, top_n=5)
                        
                        if similares_ids:
                            for sim_id in similares_ids:
                                titulo_similar = busca_filme.TITULOS_MAP.get(sim_id, f"ID {sim_id}")
                                bot_response += f"\n- {titulo_similar}"
                        else:
                            bot_response += "\nNão encontrei filmes similares."
                        st.session_state.messages.append({"role": "assistant", "content": bot_response})
                    else:
                        st.session_state.messages.append({"role": "assistant", "content": "Não encontrei nenhum filme com esse título."})
                
                st.session_state.chat_state = "IDLE"
                st.session_state.temp_data = {}

        except ValueError:
            st.session_state.messages.append({"role": "assistant", "content": "Por favor, digite um número válido (ex: 120, 5)."})
        except Exception as e:
            print(f"ERRO NO CHAT: {e}")
            st.session_state.chat_state = "IDLE"
            st.session_state.temp_data = {}
            st.session_state.messages.append({"role": "assistant", "content": "Ops, algo deu errado. Vamos tentar de novo. Diga 'recomendar' ou 'buscar'."})

        st.rerun()