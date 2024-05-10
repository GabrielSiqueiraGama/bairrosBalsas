import pandas as pd
from sklearn.metrics.pairwise import haversine_distances
from math import radians
import plotly.graph_objs as go
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Função para calcular a distância haversine entre dois pontos
def calcular_distancia(coord1, coord2):
    # Convertendo coordenadas de graus para radianos
    coord1_rad = [radians(_) for _ in coord1]
    coord2_rad = [radians(_) for _ in coord2]

    # Calculando a distância haversine
    dist = haversine_distances([coord1_rad, coord2_rad])
    distancia_km = dist[0][1] * 6371  # Multiplicando pelo raio da Terra em km
    return distancia_km

# Carregando os dados dos estados
states = pd.read_csv("https://raw.githubusercontent.com/GabrielSiqueiraGama/bairrosBalsas/main/enderecos.csv?token=GHSAT0AAAAAACPBPLDDEAI2MKNS7IIA4UXOZQZYYPA")

# Selecionando as coordenadas do ponto de partida (exemplo)
coordenadas_partida = (states.loc[0, 'Latitude'], states.loc[0, 'Longitude'])

# Calculando a distância entre o ponto de partida e todos os outros pontos
distancias = []
for i in range(len(states)):
    coordenadas_destino = (states.loc[i, 'Latitude'], states.loc[i, 'Longitude'])
    distancia = calcular_distancia(coordenadas_partida, coordenadas_destino)
    distancias.append(distancia)

# Adicionando a coluna de distância ao DataFrame
states['Distancia'] = distancias

# Criação da matriz de distância
distance_matrix = []
for i in range(len(states)):
    dist_row = []
    for j in range(len(states)):
        coordenadas_i = (states.loc[i, 'Latitude'], states.loc[i, 'Longitude'])
        coordenadas_j = (states.loc[j, 'Latitude'], states.loc[j, 'Longitude'])
        distancia_ij = calcular_distancia(coordenadas_i, coordenadas_j)
        dist_row.append(distancia_ij)
    distance_matrix.append(dist_row)

# Função para resolver o VRP
def resolver_vrp(distance_matrix):
    # Cria o gerenciador de índices
    manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, [0], [0])

    # Cria o modelo de roteamento
    routing = pywrapcp.RoutingModel(manager)

    # Define a função de custo
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return distance_matrix[from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define a função de custo
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Define o parâmetro de pesquisa
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)

    # Resolve o problema VRP
    solution = routing.SolveWithParameters(search_parameters)

    # Retorna a rota encontrada
    rota = []
    if solution:
        index = routing.Start(0)
        while not routing.IsEnd(index):
            rota.append(manager.IndexToNode(index))
            index = solution.Value(routing.NextVar(index))
    return rota

# Resolve o VRP
rota_vrp = resolver_vrp(distance_matrix)

# Atualiza o DataFrame com a ordem da rota encontrada
states = states.iloc[rota_vrp]

# Mapa
mapbox_token = "pk.eyJ1IjoiemhhbnR0IiwiYSI6ImNsdjFqbXFiMzA1aXcybmxkcHd1Ym5zajYifQ.Hcys5Sf519pfI_BauT5iVA"

# Plotagem do mapa
trace1 = go.Scattermapbox(
    lat=states['Latitude'],
    lon=states['Longitude'],
    mode='markers+lines',
    marker=dict(
        size=9,
        color=['blue' if i == 0 else 'red' for i in range(len(states))],  # Azul para o ponto de partida, vermelho para os outros pontos
        opacity=0.7
    ),
    text=states['City'] + ', ' + states['State'] + '<br>' + 'Distância até o ponto de partida: ' + states['Distancia'].round(2).astype(str) + ' km'
)

layout = go.Layout(
    title='Rota Ótima do Veículo',
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
fig = go.Figure(data=[trace1], layout=layout)
fig.show()
