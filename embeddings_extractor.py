import pandas as pd
from karateclub import Graph2Vec
import json
import networkx as nx

class EmbeddingsExtractor:
    data = {}

    def __init__(self, dimensions=6, wl_iterations=2, min_count=1):
        self.dimensions = dimensions
        self.wl_iterations = wl_iterations
        self.min_count = min_count


    def extract_embeddings(self):
        model = Graph2Vec(attributed=True, dimensions=self.dimensions, wl_iterations=self.wl_iterations, min_count=self.min_count)
        
        try:
            model.fit([value["graph"] for _, value in self.data.items()])
        except BaseException as e:
            print(e)
            print("hjf66666666666666666666666")

        for (key, _), embedding in zip(self.data.items(), model.get_embedding()):
            self.data[key]["embedding"] = embedding

        return self.data


    @classmethod
    def read_data(cls, df_in, GRAPHS_DIR = "data\\graphs"):
        def read_json_file(filename):
            with open(filename) as f:
                js_graph = json.load(f)
                G = nx.readwrite.json_graph.node_link_graph(js_graph)
                G = nx.convert_node_labels_to_integers(G)
                return G

        df_in.set_index("movieId", drop=True, inplace=True)
        dictionary = df_in.to_dict(orient="index")

        for key, value in dictionary.items():
            try:
                graph = read_json_file(GRAPHS_DIR + "\\" + value["fileName"] + ".json")
                dictionary[key]["graph"] = graph
            except:
                pass
        
        cls.data = dictionary

