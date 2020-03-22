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
const = 0.3

graphs = []
movies = []

counter = 0

def create_graph(movie):

    movies.append(movie)

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
            result = process.extractOne(expected_character, characters)
            if result is not None and result[1] > 80:
                index = characters.index(result[0])
                if index not in shown_in_scene:
                    shown_in_scene.append(index)

        for index1 in shown_in_scene:
            for index2 in shown_in_scene:
                if index1 != index2:
                    if G.has_edge(index1,index2):
                        G[index1][index2]['weight'] += const
                    else:
                        G.add_edge(index1, index2, weight=const)

    # Remove vertices with degree = 0
    G.remove_nodes_from(list(nx.isolates(G)))

    # Get the Graph weights
    weights = [G[u][v]['weight'] for u, v in G.edges() if u != v]

    # Position nodes using Fruchterman-Reingold force-directed algorithm
    pos = nx.spring_layout(G)


    nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size=500)
    nx.draw_networkx_labels(G, pos, font_color='red', labels={node:characters[node] for node in G.nodes()})
    nx.draw_networkx_edges(G, pos, alpha=0.7, width=weights)

    plt.show()

    return G


def extract_embeddings():
    for r, d, f in os.walk(read_path):
        for movie in f:
            counter += 1
            print(counter)

            graphs.append(create_graph(movie))


    model = Graph2Vec()
    model.fit(graphs)
    X = model.get_embedding()


    write_path = "4.embeddings"

    for i in range(len(movies)):
        try:
            with open(os.path.join(write_path, movies[i]), 'w', encoding="utf-8") as outfile:
                for number in X[i]:
                    outfile.write(str(number) + " ")
            outfile.close()
        except Exception as e:
            print(e)


# Main Program

create_graph("Purple-Rain.txt")
