import streamlit as st
import pandas as pd
from math import radians, sin, cos, sqrt, atan2
import plotly.graph_objs as go
import heapq
from itertools import permutations

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

# Função A*
def astar(start_index, goal_index, states):
    class Node:
        def __init__(self, index, parent=None, g=0, h=0):
            self.index = index  # Índice do nó
            self.parent = parent  # Nó pai
            self.g = g  # Custo atual do nó até o ponto de partida
            self.h = h  # Heurística (distância estimada do nó até o ponto de destino)
        
        def f(self):
            return self.g + self.h
        
        def __lt__(self, other):
            return self.f() < other.f()
    
    start_node = Node(start_index)
    goal_node = Node(goal_index)
    
    open_set = []  # Conjunto de nós a serem explorados
    heapq.heappush(open_set, start_node)
    closed_set = set()  # Conjunto de nós já explorados
    
    while open_set:
        current_node = heapq.heappop(open_set)
        
        if current_node.index == goal_node.index:
            # Reconstruir o caminho a partir do nó objetivo
            path = []
            while current_node:
                path.append(current_node.index)
                current_node = current_node.parent
            return path[::-1]  # Inverter o caminho
            
        closed_set.add(current_node.index)
        
        for neighbor_index in states.loc[current_node.index, 'Neighbors'].split(','):
            neighbor_index = int(neighbor_index)
            if neighbor_index in closed_set:
                continue
            
            neighbor_node = Node(neighbor_index)
            neighbor_node.parent = current_node
            neighbor_node.g = current_node.g + calcular_distancia(
                (states.loc[current_node.index, 'Latitude'], states.loc[current_node.index, 'Longitude']),
                (states.loc[neighbor_index, 'Latitude'], states.loc[neighbor_index, 'Longitude'])
            )
            neighbor_node.h = calcular_distancia(
                (states.loc[neighbor_index, 'Latitude'], states.loc[neighbor_index, 'Longitude']),
                (states.loc[goal_index, 'Latitude'], states.loc[goal_index, 'Longitude'])
            )
            
            if not any(node.index == neighbor_node.index for node in open_set):
                heapq.heappush(open_set, neighbor_node)
    
    return None  # Caminho não encontrado

# Função para calcular o custo total de um caminho
def calcular_custo_total(path, states):
    total_cost = 0
    for i in range(len(path) - 1):
        total_cost += calcular_distancia(
            (states.loc[path[i], 'Latitude'], states.loc[path[i], 'Longitude']),
            (states.loc[path[i + 1], 'Latitude'], states.loc[path[i + 1], 'Longitude'])
        )
    return total_cost

# Função para encontrar o melhor caminho passando por pontos intermediários
def encontrar_melhor_caminho(partida_index, destino_index, intermediarios, states):
    melhor_caminho = None
    menor_custo = float('inf')
    
    for perm in permutations(intermediarios):
        caminho_atual = [partida_index] + list(perm) + [destino_index]
        custo_atual = calcular_custo_total(caminho_atual, states)
        
        if custo_atual < menor_custo:
            menor_custo = custo_atual
            melhor_caminho = caminho_atual
    
    return melhor_caminho

# Streamlit interface
st.title("Roteamento Ótimo com Streamlit")

# Carregar os dados dos estados
states = pd.read_csv("https://raw.githubusercontent.com/GabrielSiqueiraGama/bairrosBalsas/main/estados_com_vizinhos.csv")

# Exibir a lista de bairros com seus números em uma única linha
bairros_lista = ", ".join([f"{i}: {row['City']}" for i, row in states.iterrows()])
st.write("Lista de bairros com seus índices:")
st.text(bairros_lista)

# Entrada do usuário
partida_index = st.number_input("Digite o índice do ponto de entrada", min_value=0, max_value=len(states)-1, step=1)
destino_index = st.number_input("Digite o índice do ponto de saída", min_value=0, max_value=len(states)-1, step=1)
intermediarios_input = st.text_input("Digite os índices dos pontos intermediários separados por vírgula (ou deixe em branco se não houver)")

intermediarios = [int(x) for x in intermediarios_input.split(',')] if intermediarios_input else []

# Encontrar o melhor caminho usando permutações dos pontos intermediários
if st.button("Encontrar Melhor Caminho"):
    melhor_caminho = encontrar_melhor_caminho(partida_index, destino_index, intermediarios, states)

    if melhor_caminho:
        st.write("Melhor rota encontrada:", melhor_caminho)
    else:
        st.write("Não foi possível encontrar uma rota.")

    # Plotagem do mapa com a melhor rota
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
        lat=[states.loc[i, 'Latitude'] for i in melhor_caminho],
        lon=[states.loc[i, 'Longitude'] for i in melhor_caminho],
        mode='lines',
        line=dict(
            color='red',  # Vermelho para a melhor rota
            width=2
        ),
        text=[f"{states.loc[i, 'City']}, {states.loc[i, 'State']}" for i in melhor_caminho]
    )

    layout = go.Layout(
        title='Melhor Rota do Ponto de Entrada para o Destino',
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
    st.plotly_chart(fig)
