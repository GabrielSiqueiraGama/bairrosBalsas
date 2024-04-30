import pandas as pd
import numpy as np
from sklearn.metrics import DistanceMetric
import plotly.graph_objs as go
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

# Leia os dados do arquivo CSV contendo todos os estados dos EUA e converta-os em um dataframe pandas
states = pd.read_csv("https://raw.githubusercontent.com/GabrielSiqueiraGama/bairrosBalsas/main/enderecos.csv?token=GHSAT0AAAAAACPBPLDDEAI2MKNS7IIA4UXOZQZYYPA")

# Remova os pontos de separação de milhares e converta as colunas Latitude e Longitude para o tipo numérico
states['Latitude'] = states['Latitude'].str.replace('.', '').astype(float)
states['Longitude'] = states['Longitude'].str.replace('.', '').astype(float)
print(states)
# Criando um dataset de veículos
data = {'Name': ['Vehicle 0', 'Vehicle 1', 'Vehicle 2', 'Vehicle 3', 'Vehicle 4', 'Vehicle 5'],
        'Plate': ['MIY208', 'UH1BCD', '7GDE215', '6543MS', '8DFG468', 'D48541T']
        }

# Criando um dataframe
vehicles = pd.DataFrame(data, columns=['Name', 'Plate'])

# Utiliza uma amostra dos dados de estado como localização dos nossos veículos
sample = states.sample(n=6, random_state=1)

# Remove a amostra dos dados de estado
states.drop(sample.index, inplace=True)

# Junte ambos
vehicles = vehicles.join(sample.reset_index(drop=True))

# Função para pré-processamento do VRP
# Função para pré-processamento do VRP
def PreProcessVRP(vehicles, places):
    # Mapeia todas as coordenadas de lugares
    visits = places[['Latitude','Longitude']].astype(float)

    # Mapeia todos os pontos de partida
    starts = vehicles[['Latitude','Longitude']].astype(float)

    # Mapeia todos os depósitos de agentes
    depots = vehicles[['Latitude','Longitude']].astype(float)

    # Concatena todas as coordenadas
    data = pd.concat([starts, depots, visits]).reset_index(drop=True)

    # Normaliza as coordenadas
    sources = data.apply(np.deg2rad)

    return {"starts": starts, "depots": depots, "places": visits, "coordinates": sources}

# Pre Processamento
dataset = PreProcessVRP(vehicles, states)

# Imprimir as coordenadas normalizadas
print("Coordenadas normalizadas:")
print(dataset['coordinates'])
# Método para criar nosso modelo de processamento
def BuildModel(matrix, dataset, vehicles: int):
    
    start_indexes = (list(map(int,dataset.get("starts").index.values)))

    depot_indexes = [index + len(start_indexes) for index, element in enumerate(dataset.get("depots").index.values)]

    return dict(distance_matrix=matrix, num_vehicles=vehicles, starts=start_indexes, ends=depot_indexes)

# Método para criar uma matriz de distância
def CreateDistanceMatrix(distances):
    dist = DistanceMetric.get_metric('haversine')
    return dist.pairwise(distances) * 6373



# Criação da matriz de distância
distance_matrix = CreateDistanceMatrix(dataset['coordinates'])

# Construção do modelo
model = BuildModel(distance_matrix, dataset, len(vehicles))
# Create the distance matrix
distance_matrix = CreateDistanceMatrix(dataset.get("coordinates").values)
 
# Build problem data
data = BuildModel(distance_matrix, dataset, len(vehicles))

# Method that will calculate the result of clustering the routes for each of the vehicles

def ProcessVRP(data: object, maxTravelDistance: int): 
    # Create the routing index manager.
    manager = pywrapcp.RoutingIndexManager(
        len(data['distance_matrix']),
        data['num_vehicles'],
        data['starts'],
        data['ends'])  
    
    # Create Routing Model.
    routing = pywrapcp.RoutingModel(manager)

    # Create and register a transit callback.
    def distance_callback(from_index, to_index):
        print()
        """Returns the distance between the two nodes."""
        # Convert from routing variable Index to distance matrix NodeIndex.
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return data['distance_matrix'][from_node][to_node]

    transit_callback_index = routing.RegisterTransitCallback(distance_callback)

    # Define cost of each arc.
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

    # Add Distance constraint.
    dimension_name = 'Distance'
    routing.AddDimension(transit_callback_index, 0, maxTravelDistance, True, dimension_name)

    distance_dimension = routing.GetDimensionOrDie(dimension_name)
    distance_dimension.SetGlobalSpanCostCoefficient(100)

    # Setting first solution heuristic.
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    
    # Time to solv the problem
    search_parameters.time_limit.seconds = 120
    
    # Active logs
    search_parameters.log_search = True

    # Solve the problem.
    solution = routing.SolveWithParameters(search_parameters)

    return dict(data=data, manager=manager, routing=routing, solution=solution)

#The first parameter is our model, the second is the maximum distance that each vehicle will travel
vrp = ProcessVRP(data,10000)
# Convert the result to structured data

def MapResult(agents, places, vrp):
    routing = vrp["routing"]
    solution = vrp["solution"]
    manager = vrp["manager"]
    vehicles = len(agents)

    itineraries = []

    max_route_distance = 0
    for vehicle_id in range(vehicles):

        # Default route distance
        route_distance: int = 0
        # Start current vehicle
        index = routing.Start(vehicle_id)

        waypoints = []

        plan_output = 'Route for vehicle {}:\n'.format(vehicle_id)
        while not routing.IsEnd(index):
            plan_output += ' {} -> '.format(manager.IndexToNode(index))          
            
            previous_index = index
    
            index = solution.Value(routing.NextVar(index))
        
            if routing.IsEnd(index) == False and routing.IsStart(index) == False:
                
                p_index = index - (len(vrp["data"]["starts"]) + len(vrp["data"]["ends"]))

                # Create a new itinerary place object
                waypoint = places.iloc[p_index]

                # Add it to waypoints
                waypoints.append(waypoint)     
        
            route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
              
            
        plan_output += '{}\n'.format(manager.IndexToNode(index))
        plan_output += 'Distance of the route: {}km\n'.format(route_distance)
        print(plan_output)

        max_route_distance = max(route_distance, max_route_distance)

        # Create a dataframe for the current vehicle
        item = CreateRouteDataframe(vehicle_id,agents,waypoints,route_distance)
        
        # Add new itinerary
        itineraries.append(item)

    print('Maximum of the route distances: {}km'.format(max_route_distance))
    
    return itineraries

def CreateRouteDataframe(vehicle_id, agents, waypoints, route_distance):

    vehicle = agents.iloc[vehicle_id]

    # Criar um dataframe
    item = pd.DataFrame(waypoints, columns=['Latitude', 'Longitude', 'City', 'State'])

    # Adicionar o ponto de partida
    item.loc[-1] = [vehicle["Latitude"], vehicle["Longitude"], vehicle["City"], vehicle["State"]]  
    item.index = item.index + 1
    item.sort_index(inplace=True)

    # Adicionar o ponto final
    item = pd.concat([item, item.head(1)], ignore_index=True, axis=0)

    # Atualizar outros valores
    item["VehicleId"] = vehicle_id
    item["Plate"] = vehicle["Plate"]
    item["Distance"] = ConvertToKm(route_distance)

    return item


# Convert miles to KM
def ConvertToKm(miles):
    return miles * 1.6


# If the solution to the problem was found show the results
if vrp["solution"] is None:
    print("No solution found.")
else:
    response = MapResult(vehicles,states,vrp)
    
# Concatenate the dataframe of all vehicles to get the complete route
routes = pd.concat(response,ignore_index=True)

# Here's the vehicle routing problem solved :), now let's get to the fun part, showing it on the map!
routes    

# Put your mapbox token here
mapbox_token = "pk.eyJ1IjoiemhhbnR0IiwiYSI6ImNsdjFqbXFiMzA1aXcybmxkcHd1Ym5zajYifQ.Hcys5Sf519pfI_BauT5iVA"

# Method to plot our vehicle routing problem solved on the map
def ShowGraph(response):
    
    fig = go.Figure(go.Scattermapbox())
    
    fig.data = []

    for route in response:
        fig.add_trace(go.Scattermapbox(
            lat=route["Latitude"],
            lon=route["Longitude"],
            mode='markers+text+lines',
            marker=go.scattermapbox.Marker(
                size=20
            ),
            text=route.index.tolist(),
            name=route["Plate"].iloc[0]
        ))

    fig.update_layout(
            autosize=True,
            hovermode='closest',
            mapbox=dict(
                accesstoken=mapbox_token,
                bearing=0,
                center=dict(
                    lat=38,
                    lon=-94
                ),
                pitch=0,
                zoom=3,
                style='dark'
            ),
             title=dict(
                text="Rotas",
                font=dict(
                    size=20
                )
            ),
        )

    fig.show()
# And here's the magic
ShowGraph(response)

