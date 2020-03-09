import re
import spacy
from collections import Counter
from fuzzywuzzy import process
from spacy import displacy
import networkx as nx
import matplotlib.pyplot as plt

nlp = spacy.load("en_core_web_sm", disable=["tagger", "parser"])


movie = "Titanic"

read_path = "3.metadata\\" + movie + ".txt"
with open(read_path, encoding="utf8") as opened_file:
    read_data = opened_file.read()
opened_file.closed

characters = re.split('\n', read_data)[:-1] # ignore empty last line
appearances = [0 for character in characters]

read_path = "2.scripts\\" + movie + ".txt"
with open(read_path, encoding="utf8") as opened_file:
    read_data = opened_file.read()
opened_file.closed

scenes = re.split('INT|EXT', read_data)

scene_characters = []

for scene in scenes:
    doc = nlp(scene)
    scene_characters.append([ee for ee in doc.ents if ee.label_ == 'PERSON'])

# Graph
G=nx.Graph()
for i in range(len(characters)):
    G.add_node(characters[i], pos=(i,i))
# ---

for i in characters:
    for j in characters:
        if i != j:
            G.add_edge(i, j, weight=0)


for expected_characters in scene_characters:
    shown_in_scene = []
    for expected_character in expected_characters:
        result = process.extractOne(expected_character.text, characters)
        index = characters.index(result[0])
        shown_in_scene.append(index)
    
    for index1 in shown_in_scene:
        for index2 in shown_in_scene:
            if index1 != index2:
                G[characters[index1]][characters[index2]]['weight'] += 0.01


# Plotting
weights = [G[u][v]['weight'] for u, v in G.edges() if u != v]

pos = nx.spring_layout(G)

nx.draw_networkx_nodes(G, pos, cmap=plt.get_cmap('jet'), node_size=500)
nx.draw_networkx_labels(G, pos, font_color='red')
nx.draw_networkx_edges(G, pos, alpha=0.7, width=weights)

plt.show()
