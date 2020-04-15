import os
import re
import spacy
from fuzzywuzzy import process
import networkx as nx
from networkx.readwrite import json_graph
import matplotlib.pyplot as plt
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import pandas as pd
import json


nlp = spacy.load("en_core_web_lg", disable=["tagger", "parser"])

WEIGHT_STEP = 1
SCRIPTS_DIR = "data\\screenplays"
CSV_IN = "data\\data2.csv"
CSV_OUT = "data\\data3.csv"


def create_graph(data):
    try:
        filename = data[1]

        characters = re.split(';', data[3])

        with open(SCRIPTS_DIR + "\\" + filename + ".txt", encoding="utf8") as opened_file:
            read_data = opened_file.read()
        opened_file.close()

        scenes = re.split('INT|EXT', read_data)

        expected_characters_per_scene = []

        for scene in scenes:
            # making nlp's life easier
            scene = scene.replace("'s", "")
            scene = scene.title()

            # merge multiple whitespaces
            scene = " ".join(scene.split())
            doc = nlp(scene)
            found_persons = [ee.text for ee in doc.ents if ee.label_ == 'PERSON']

            # get explicit characters
            for character in characters:
                if character in scene:
                    found_persons.append(character)
            
            expected_characters_per_scene.append(found_persons)


        # Add Graph's Vertices
        G = nx.Graph()
        for i in range(len(characters)):
            G.add_node(i, pos=(i,i))

        for expected_characters_in_scene in expected_characters_per_scene:
            shown_in_scene = []
            for expected_character in expected_characters_in_scene:
                if expected_character:
                    result = process.extractOne(expected_character, characters, score_cutoff = 80)
                    if result:
                        index = characters.index(result[0])
                        if index not in shown_in_scene:
                            shown_in_scene.append(index)

            for index1 in shown_in_scene:
                for index2 in shown_in_scene:
                    if index1 != index2:
                        if G.has_edge(index1,index2):
                            G[index1][index2]["weight"] += WEIGHT_STEP
                        else:
                            G.add_edge(index1, index2, weight= WEIGHT_STEP)

        # Remove vertices with degree = 0

        weights_sum = G.size(weight="weight")
        if weights_sum == 0:
            return None

        contributions = []

        for (n, val) in G.degree(weight="weight"):
            label = round(val/weights_sum, 1)
            G.nodes[n]["feature"] = label
            contributions.append(label)

        G.remove_nodes_from(list(nx.isolates(G)))

        if len(G) == 0 or (not nx.is_connected(G)):
            return None

        labels = [characters[i] + ": " + str(contributions[i]) for i in range(len(characters))]

        return (G, labels, data)

    except Exception as e:
        print(e)
        print(filename)
        return None


def save_graphs(graphs):
    for graph in graphs:
        filename_out = graph[2][1]
        with open("data\\graphs\\" + filename_out + ".json", 'w', encoding='utf-8') as f:
            json.dump(json_graph.node_link_data(graph[0]), f)


def draw_graph(G, labels):
    # Get the Graph weights
    width_multiplier = 50/G.size(weight="weight")

    weights = [G[u][v]["weight"]*width_multiplier for u, v in G.edges() if u != v]

    # Position nodes using Fruchterman-Reingold force-directed algorithm
    pos = nx.spring_layout(G)

    nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size=500)
    nx.draw_networkx_labels(G, pos, font_color='red', labels={node:labels[node] for node in G.nodes()})
    nx.draw_networkx_edges(G, pos, alpha=0.7, width=weights)

    plt.show()


if __name__ == "__main__":

    df_in = pd.read_csv(CSV_IN, encoding='utf-8')
    data_in = list(df_in.itertuples(index=False))

    with Pool(18) as p:
        results = p.map(create_graph, data_in)

    graphs = [x for x in results if x is not None]

    save_graphs(graphs)

    data_out = [graph[2] for graph in graphs]

    df_out = pd.DataFrame(data_out, columns=['movieName', 'fileName', 'tmdbId', 'characters'])

    df_out.to_csv(CSV_OUT, encoding='utf-8', index=False)

