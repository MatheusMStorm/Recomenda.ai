import pandas as pd
import re #  buscar ou extrair padrões"""
import nltk # biblioteca PNL"""
from nltk.corpus import stopwords # reduz os ruidos das frases"""
from nltk.stem import RSLPStemmer # reduz palavras para o entendimento"""
from sklearn.feature_extraction.text import TfidfVectorizer # transforma os textos em vetor"""
from sklearn.metrics.pairwise import cosine_similarity # Para calcular a similaridade
from sklearn.decomposition import TruncatedSVD #reduz a dimensão dos dados
import pickle # Para salvar o modelo
import os # Para lidar com caminhos de arquivo
import string #  manipulação dos textos"""
import numpy as np #  manipução numerica"""



DATA_FILE = os.path.join("Data", "filmes.csv") #Modelo
MODEL_FILE = os.path.join("Modelos", "pnl_similarity_model.pkl")

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    print("Baixando pacote 'stopwords' do NLTK...")
    nltk.download('stopwords')

STOPWORDS_PT = set(stopwords.words('portuguese'))

def carregar_dados():    #Carrega a pasta Data.
    try:
        df = pd.read_csv(DATA_FILE)
        print(f"Arquivo '{DATA_FILE}' carregado com {len(df)} filmes.")
        return df
    except FileNotFoundError:
        print(f"Erro: Arquivo '{DATA_FILE}' não encontrado.")
        # print("Certifique-se de executar o script 'coleta_api.py' primeiro.")
        return None

def limpar_texto(texto): #Limpa e pré-processa uma string de texto.
    if not isinstance(texto, str):
        return
    texto = texto.lower()
    texto = re.sub(r'[^a-z\s]', '', texto)
    palavras = [palavra for palavra in texto.split() if palavra not in STOPWORDS_PT]
    return " ".join(palavras)

def criar_features_de_texto(df): #Combina colunas de texto (sinopse, generos, etc.) em uma única "super-feature" para o modelo PNL.
    print("Criando features de texto combinadas...")

    df['sinopse'] = df['sinopse'].fillna('') # Preenche valores vazios com strings vazias
    df['generos'] = df['generos'].fillna('')
    df['diretor'] = df['diretor'].fillna('')
    df['atores'] = df['atores'].fillna('')
    df['sinopse_limpa'] = df['sinopse'].apply(limpar_texto) # Limpa e formata cada coluna de texto e são unidos por '|'. Trocamos por espaço.
    df['generos_limpo'] = df['generos'].apply(lambda x: " ".join(x.split('|')))
    df['diretor_limpo'] = df['diretor'].apply(lambda x: " ".join(x.split('|')))
    df['atores_limpo'] = df['atores'].apply(lambda x: " ".join(x.split('|')))
    df['feature_pnl'] = (
        df['sinopse_limpa'] * 3 + " " +  # Sinopse tem maior peso
        df['generos_limpo'] * 2 + " " + # Gêneros tem peso médio
        df['diretor_limpo'] + " " +     # Diretor tem peso normal
        df['atores_limpo']              # Atores tem peso normal
    )
    
    print("Features de texto criadas com sucesso.")
    return df

def treinar_e_salvar_modelo():
       # Função OTIMIZADA: Carrega, processa, aplica TF-IDF e
  #  USA REDUÇÃO DE DIMENSIONALIDADE (SVD) para salvar uma matriz leve.
    
    filmes_df = carregar_dados() 
    if filmes_df is None:
        return
        
    filmes_df = criar_features_de_texto(filmes_df) # Combina sinopse, gênero, etc., em 'feature_pnl'
    
    print("Iniciando vetorização TF-IDF...")
    
    # Cria o vetorizador. limita o "dicionário" às 5000 palavras mais importantes
    tfidf_vectorizer = TfidfVectorizer(max_features=5000)
    
    # Treina o TF-IDF e transforma os textos em uma matriz numérica
    tfidf_matrix = tfidf_vectorizer.fit_transform(filmes_df['feature_pnl'])
    print(f"Matriz TF-IDF criada. Shape: {tfidf_matrix.shape}")
    print("Iniciando Redução de Dimensionalidade (TruncatedSVD)...")
    n_components = 100 
    svd = TruncatedSVD(n_components=n_components, random_state=42)
    
    # Treina o SVD e transforma a matriz TF-IDF (9622x5000)
    # em uma Matriz Latente (9622x100)
    latent_matrix = svd.fit_transform(tfidf_matrix)
    
    print(f"Matriz Latente criada. Shape: {latent_matrix.shape}")
    
    # Define o mapeamento do 'movieId' para o índice da matriz (0, 1, 2...)
    movie_indices = pd.Series(filmes_df.index, index=filmes_df['movieId']).drop_duplicates()
    
    os.makedirs("Modelos", exist_ok=True) 
    
    # Cria o dicionário que será salvo.
    modelo_pnl_data = {
        'latent_matrix': latent_matrix, # A matriz (9622 x 100)
        'movie_indices': movie_indices
    }
    
    # Abre o arquivo de modelo em modo 'write binary' (wb)
    with open(MODEL_FILE, 'wb') as f:
        # Usa o pickle para "despejar" (dump) o dicionário no arquivo
        pickle.dump(modelo_pnl_data, f)
        
    print(f"Modelo PNL salvo com sucesso em '{MODEL_FILE}'!")

if __name__ == "__main__":
    print("Iniciando script de treinamento do 'pnl_modulo'...")
    treinar_e_salvar_modelo()