import os
import re
import spacy
from fuzzywuzzy import process
import networkx as nx
import matplotlib.pyplot as plt
from karateclub import Graph2Vec
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import pandas as pd


nlp = spacy.load("en_core_web_lg", disable=["tagger", "parser"])

WEIGHT_STEP = 1
SCRIPTS_DIR = 'data\\screenplays'
CSV_IN = "data\\data2.csv"
CSV_OUT = "data\\data3.csv"


def create_graph(data):
    try:
        filename = data[1]

        characters = re.split(';', data[3])

        with open(SCRIPTS_DIR + "\\" + filename, encoding="utf8") as opened_file:
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

        return (G, [characters[i] + ": " + str(contributions[i]) for i in range(len(characters))], data)

    except Exception as e:
        print(e)
        print(filename)
        return None


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


def extract_embeddings(data):

    with Pool(8) as p:
        results = p.map(create_graph, data)

    results = [x for x in results if x is not None]

    graphs = [result[0] for result in results]

    print("end of graph extraction")

    # wl = 1, check for vertex label and the neighbours similarity
    # min = 1, don't drop any labels
    model = Graph2Vec(attributed=True, wl_iterations=1, min_count=1)
    model.fit(graphs)

    X = [[str(y) for y in x] for x in model.get_embedding()]

    data_out = [results[i][2] + (';'.join(X[i]),) for i in range(len(results))]

    df_out = pd.DataFrame(data_out, columns = ['movie_name', 'filename', 'tmdb_id', 'characters', 'vector'])

    df_out.to_csv(CSV_OUT, encoding='utf-8', index=False)


if __name__ == "__main__":

    df_in = pd.read_csv(CSV_IN)
    data = list(df_in.itertuples(index=False))

    # extract_embeddings(data)

    target_movie_name = "Interstellar"

    for movie in data:
        if movie[0] == target_movie_name:
            result = create_graph(movie)
            draw_graph(result[0], result[1])
