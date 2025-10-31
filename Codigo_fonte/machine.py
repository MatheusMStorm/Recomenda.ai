import pandas as pd
import pickle
import os
from surprise import Dataset, Reader
from surprise.model_selection import train_test_split
from surprise import SVD, accuracy 


#Criar o segundo motor de IA: Filtragem Colaborativa. Este script treinará um modelo que entende o comportamento do usuário quais filmes eles avaliaram bem.
#Definição dos caminhos, criar funções, criar e iniciar o bloco