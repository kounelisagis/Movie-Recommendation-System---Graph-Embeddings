import os
import re

read_path = "4.embeddings"
movies = []

def files_to_list():
    to_return = []
    for r, d, f in os.walk(read_path):
        for file in f:
            with open(read_path + "\\" + file, encoding="utf8") as opened_file:
                read_data = opened_file.read()
            opened_file.closed
            movies.append(file)
            vec = re.split(' ', read_data)[:-1] # ignore empty last
            num_vec = [float(i) for i in vec]
            to_return.append(num_vec)
    return to_return


vectors = files_to_list()

movie = "Interstellar.txt"

with open(read_path + "\\" + movie, encoding="utf8") as opened_file:
    read_data = opened_file.read()
opened_file.closed
vec = re.split(' ', read_data)[:-1] # ignore empty last
num_vec = [float(i) for i in vec]


from scipy import spatial
results = []
for i in range(len(vectors)):
    result = 1 - spatial.distance.cosine(num_vec, vectors[i])
    if movies[i] != movie:
        results.append((movies[i], result))

results.sort(key=lambda tup: tup[1], reverse=True)

print(results[:10])
