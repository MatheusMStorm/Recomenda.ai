import pandas as pd
import pickle
import os
from sklearn.metrics.pairwise import cosine_similarity
from fuzzywuzzy import process


#Carregar Dados, criar as funções,Fornecer funções de utilidade para pesquisar filmes e encontrar similares baseado no PNL