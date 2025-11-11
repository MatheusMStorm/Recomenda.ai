import streamlit as st

# Configuração da página
st.set_page_config(page_title="Recomenda Ai", layout="centered")

# --- Inicialização da Memória (Session State) ---
# Isso é fundamental para o Streamlit "lembrar" das coisas

# 1. Guarda os dados do usuário após o cadastro
if "user" not in st.session_state:
    st.session_state.user = None

# 2. Guarda o histórico do chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- Abas de Navegação ---
tab_chat, tab_cadastro = st.tabs(["💬 Chat", "👤 Cadastro"])

# --- Aba de Cadastro ---
with tab_cadastro:
    st.header("Cadastro de Usuário")
    
    # Se o usuário já estiver cadastrado, mostre os dados
    if st.session_state.user:
        st.success(f"Usuário já cadastrado: {st.session_state.user['nome']}")
        st.write(f"Email: {st.session_state.user['email']}")
    else:
        # Formulário de cadastro
        with st.form("cadastro_form"):
            nome = st.text_input("Nome")
            email = st.text_input("Email")
            submitted = st.form_submit_button("Cadastrar")
            
            if submitted and nome and email:
                # Salva o usuário na "memória" da sessão
                st.session_state.user = {"nome": nome, "email": email}
                st.success(f"Usuário {nome} cadastrado com sucesso!")
            elif submitted:
                st.error("Por favor, preencha nome e email.")

# --- Aba de Chat ---
with tab_chat:
    st.header("Chatbot Básico")

    # Verifica se o usuário está cadastrado
    if st.session_state.user is None:
        st.warning("👋 Por favor, cadastre-se na aba 'Cadastro' para usar o chat.")
    else:
        st.write(f"Bem-vindo, {st.session_state.user['nome']}!")

        # Exibe o histórico de mensagens
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Input do chat
        if prompt := st.chat_input("Digite sua mensagem..."):
            # Adiciona a mensagem do usuário ao histórico
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # --- Lógica do Chatbot (Aqui é um simples "eco") ---
            # TODO: Substitua esta lógica por uma IA real (OpenAI, Gemini, etc.)
            response = f"O chatbot recebeu: '{prompt}'"
            # ----------------------------------------------------

            # Adiciona a resposta do bot ao histórico
            st.session_state.messages.append({"role": "assistant", "content": response})
            with st.chat_message("assistant"):
                st.markdown(response)