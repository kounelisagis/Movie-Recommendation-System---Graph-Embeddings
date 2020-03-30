import os
import re
import spacy
from collections import Counter
from fuzzywuzzy import process
from spacy import displacy
import networkx as nx
import matplotlib.pyplot as plt
from karateclub import Graph2Vec

nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser"])

read_path = "3.metadata"
write_path = "4.embeddings"

weight_step = 1


def create_graph(movie):
    read_path2 = "3.metadata\\" + movie
    with open(read_path2, encoding="utf8") as opened_file:
        read_data = opened_file.read()
    opened_file.closed

    characters = re.split('\n', read_data)[:-1] # ignore empty last line
    appearances = [0 for character in characters]

    read_path2 = "2.scripts\\" + movie
    with open(read_path2, encoding="utf8") as opened_file:
        read_data = opened_file.read()
    opened_file.closed

    scenes = re.split('INT|EXT', read_data)

    expected_characters_per_scene = []

    for scene in scenes:
        scene = scene.replace("'s", "")
        scene = scene.title()
        scene = " ".join(scene.split())
        doc = nlp(scene)
        scene_characters = [ee.text for ee in doc.ents if ee.label_ == 'PERSON']
        for character in characters:
            if character in scene:
                scene_characters.append(character)
        
        expected_characters_per_scene.append(scene_characters)

    # Add Graph's Vertices
    G = nx.Graph()
    for i in range(len(characters)):
        G.add_node(i, pos=(i,i))

    for expected_characters_in_scene in expected_characters_per_scene:
        shown_in_scene = []
        for expected_character in expected_characters_in_scene:
            result = process.extractOne(expected_character, characters, score_cutoff = 80)
            if result is not None:
                index = characters.index(result[0])
                if index not in shown_in_scene:
                    shown_in_scene.append(index)

        for index1 in shown_in_scene:
            for index2 in shown_in_scene:
                if index1 != index2:
                    if G.has_edge(index1,index2):
                        G[index1][index2]["weight"] += weight_step
                    else:
                        G.add_edge(index1, index2, weight= weight_step)

    # Remove vertices with degree = 0

    weights_sum = G.size(weight="weight")

    contributions = []

    for (n, val) in G.degree(weight="weight"):
        label = round(val/weights_sum, 1)
        G.nodes[n]["feature"] = label
        contributions.append(label)

    G.remove_nodes_from(list(nx.isolates(G)))

    return G, [characters[i] + ": " + str(contributions[i]) for i in range(len(characters))]

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

def extract_embeddings():
    movies = []
    graphs = []
    counter = 0
    fails = []
    
    for r, d, f in os.walk(read_path):
        for movie in f:
            counter += 1
            if counter == 20:
                break
            print(str(counter) + " - " + movie )

            try:
                G, _ = create_graph(movie)
                graphs.append(G)
                movies.append(movie)
            except Exception as e:
                print(e)
                print(movie)
                fails.append(movie)


    # wl = 1, check for vertex label and the neighbours similarity
    # min = 2, count even the one similarity
    model = Graph2Vec(attributed=True, wl_iterations=1, min_count=2)
    model.fit(graphs)
    X = model.get_embedding()


    for i in range(len(movies)):
        try:
            with open(os.path.join(write_path, movies[i]), 'w', encoding="utf-8") as outfile:
                for number in X[i]:
                    outfile.write(str(number) + " ")
            outfile.close()
        except Exception as e:
            print(e)
    
    print(fails)


# Main Program

# extract_embeddings()

G, labels = create_graph("Interstellar.txt")
draw_graph(G, labels)
