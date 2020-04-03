import os
import re
import pandas as pd
from scipy import spatial


# read_path = "4.embeddings"
movies = []

CSV_IN = "data\\data3.csv"

movies = pd.read_csv(CSV_IN, index_col=0).T.to_dict()
# print(movies)

for key, _ in movies.items():
    # print(key)
    movies[key]["vector"] = movies[key]["vector"].split(';')
    movies[key]["vector"] = [float(x) for x in movies[key]["vector"]]


target_movie_name = "Interstellar"
target_vector = movies[target_movie_name]["vector"]


results = []
for key, _ in movies.items():
    if key != target_movie_name:
        result = 1 - spatial.distance.cosine(target_vector, movies[key]["vector"])
        results.append((key, result))


results.sort(key=lambda tup: tup[1], reverse=True)

print(results[:10])
