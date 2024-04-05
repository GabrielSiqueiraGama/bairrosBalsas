import pandas as pd
import numpy as np
from sklearn.neighbors import DistanceMetric
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

import plotly.express as px
import plotly.graph_objects as go

# Ler todos os estados(bairros) dentro do arquivo csv contendo a latitude e longitude
states=pd.read_csv("https://raw.githubusercontent.com/GabrielSiqueiraGama/bairrosBalsas/main/enderecos%20-%20enderecos.csv.csv?token=GHSAT0AAAAAACPBPLDDS6HXBN36VK3DP37QZQJ6GYA")

# Cria um dataset dos veiculos
data = {'Name': ['Vehicle 0','Vehicle 1','Vehicle 2','Vehicle 3','Vehicle 4','Vehicle 5'],
        'Plate': ['MIY208','UH1BCD','7GDE215','6543MS','8DFG468','D48541T']
       }

# Cria um dataframe
vehicles = pd.DataFrame(data, columns = ['Name','Plate'])

# Usando um numero aleatorio para associar com o veiculo
sample = states.sample(n=6,random_state=1)

# Unsamples state data
states.drop(sample.index,inplace=True)

# Join both
vehicles = vehicles.join(sample.reset_index(drop=True))
