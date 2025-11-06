import pandas as pd
import pickle
import os
import numpy as np
from surprise import Dataset, Reader
from surprise.model_selection import GridSearchCV
from surprise import SVD

DATA_FILE = os.path.join("Data", "usuarios.csv")
MODEL_FILE = os.path.join ("Modelos", "modelo_colaborativo.pkl")

print("iniciando o script machine.py...")
         
def otimizar_e_treinar_modelo_colaborativo():
    """
    Carrega os dados de avaliação, otimiza os hiperparâmetros do modelo SVD usando GridSearchCV,
    treina o modelo SVD final com os melhores parâmetros e o salva.
    """

    try: 
        df_usuarios = pd.read_csv(DATA_FILE)
        print(f"Arquivo '{DATA_FILE}' carregado com {len(df_usuarios)} avaliações.")

    except FileNotFoundError:
        print(f"Erro: Arquivo '{DATA_FILE}' não encontrado.") 
        return None

    reader = Reader(rating_scale = (0.5, 5.0))
    data = Dataset.load_from_df(df_usuarios[['userId', 'movieId', 'rating']], reader)

        

    param_grid = {                              #definção de parâmetros a serem testados
        'n_factors': [50, 100, 150],
        'n_epochs': [10, 20, 30],
        'lr_all': [0.005, 0.01],
        'reg_all': [0.02, 0.05],
        'random_state': [42]
    }

    print("\nExecutando GridSearchCV para encontrar os melhores hiperparâmetros...")
    gs = GridSearchCV (SVD, param_grid, measures=['rmse'], cv=3, n_jobs=-1)

    gs.fit(data)  # . fit Executa e treina o 'data'

    print("\n--- Resultados do Grid Search ---")
    print("Melhor RMSE:", gs.best_score['rmse'])
    print("Melhores parâmetros:", gs.best_params['rmse'])
    print("\nTreinando o modelo final SVD com os melhores parâmetros encontrados...")

    trainset = data.build_full_trainset() #construção o trainset completo
    teste_final = SVD(**gs.best_params['rmse'])
    teste_final.fit(trainset)
    print("Treinamento concluido!")

    os.makedirs("Modelos", exist_ok=True) #Salva o modelo treinado
        #Salva o sistema de controle no arquivo
    with open(MODEL_FILE, 'wb') as f:
        pickle.dump(teste_final, f)
        
    print(f"Sistema de Otimização e Treinamento salvo em '{MODEL_FILE}'!")
        
    return teste_final

if __name__ == "__main__":
    print("Exibindo 'machine.py' com resultados otimizados.")
    modelo_final = otimizar_e_treinar_modelo_colaborativo()
    # print("\n--- Executando Testes de Simulação ---")

    if modelo_final: 
        print("\n--- Exemplo de Previsão com o Modelo Otimizado ---")
        usuario_teste = 1
        filme_teste = 783
        previsao = modelo_final.predict(uid = usuario_teste, iid = filme_teste)

        print(f"Usuário: {previsao.uid}")
        print(f"Filme (ID): {previsao.iid}")
        print(f"Nota prevista: {previsao.est:.3f} / 5.0")
    else:
        print("Não foi possível gerar previsões porque o modelo não foi treinado.")







#Criar o segundo motor de IA: Filtragem Colaborativa. Este script treinará um modelo que entende o comportamento do usuário quais filmes eles avaliaram bem.
#Definição dos caminhos, criar funções, criar e iniciar o bloco