import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import plotly.graph_objs as go

# Função para calcular a distância entre dois pontos usando a fórmula de Haversine
def calcular_distancia(coord1, coord2):
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    R = 6371.0  # raio da Terra em km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    distance = R * c
    return distance

# Carregando os dados dos estados
states = pd.read_csv("https://raw.githubusercontent.com/GabrielSiqueiraGama/bairrosBalsas/main/enderecos.csv?token=GHSAT0AAAAAACPBPLDDEAI2MKNS7IIA4UXOZQZYYPA")

# Solicitar ao usuário o índice do ponto de entrada
partida_index = int(input("Digite o índice do ponto de entrada: "))
print(f"Índice do ponto de entrada: {partida_index}")

# Solicitar ao usuário o índice do ponto de saída
destino_index = int(input("Digite o índice do ponto de saída: "))
print(f"Índice do ponto de saída: {destino_index}")

# Lista de nós intermediários que a rota deve passar
nos_intermediarios = [9]  # Exemplo de nós intermediários
print("Nós intermediários: ", nos_intermediarios)

# Inicializando a rota ótima
optimal_path = [partida_index]

# Calculando a distância total percorrida
total_distance = 0

# Adicionando os nós intermediários à rota ótima
for node in nos_intermediarios:
    distance = calcular_distancia((states.loc[optimal_path[-1], 'Latitude'], states.loc[optimal_path[-1], 'Longitude']),
                                  (states.loc[node, 'Latitude'], states.loc[node, 'Longitude']))
    total_distance += distance
    optimal_path.append(node)

# Adicionando o ponto de saída à rota ótima
distance = calcular_distancia((states.loc[optimal_path[-1], 'Latitude'], states.loc[optimal_path[-1], 'Longitude']),
                              (states.loc[destino_index, 'Latitude'], states.loc[destino_index, 'Longitude']))
total_distance += distance
optimal_path.append(destino_index)

print("Distância total percorrida:", total_distance, "km")

# Plotagem do mapa com a rota ótima
mapbox_token = "pk.eyJ1IjoiemhhbnR0IiwiYSI6ImNsdjFqbXFiMzA1aXcybmxkcHd1Ym5zajYifQ.Hcys5Sf519pfI_BauT5iVA"

trace1 = go.Scattermapbox(
    lat=states['Latitude'],
    lon=states['Longitude'],
    mode='markers+lines',
    marker=dict(
        size=9,
        color='blue',  # Azul para o ponto de entrada
        opacity=0.7
    ),
    text=states['City'] + ', ' + states['State']
)

trace2 = go.Scattermapbox(
    lat=[states.loc[i, 'Latitude'] for i in optimal_path],
    lon=[states.loc[i, 'Longitude'] for i in optimal_path],
    mode='lines',
    line=dict(
        color='red',  # Vermelho para a rota ótima
        width=2
    ),
    text=[f"{states.loc[i, 'City']}, {states.loc[i, 'State']}" for i in optimal_path]
)

layout = go.Layout(
    title='Rota Ótima do Ponto de Entrada para o Destino',
    width=800,  # Defina a largura desejada em pixels
    height=800,  # Defina a altura desejada em pixels
    hovermode='closest',
    showlegend=False,
    mapbox=dict(
        accesstoken=mapbox_token,
        bearing=0,
        center=dict(
            lat=-7.5242,
            lon=-46.0322
        ),
        pitch=0,
        zoom=11,
        style='dark'
    ),
)

# Criando a figura do mapa
fig = go.Figure(data=[trace1, trace2], layout=layout)

# Exibindo o mapa
print("Exibindo o mapa...")
fig.show()
print("Mapa exibido com sucesso.")
