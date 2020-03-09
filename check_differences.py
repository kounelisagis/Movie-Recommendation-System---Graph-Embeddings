import os
from urllib import request
import json
import re
from bs4 import BeautifulSoup
from tmdbv3api import TMDb, Movie

tmdb = TMDb()
tmdb.api_key = 'API-KEY'
movie = Movie()

read_path = '2.scripts'
write_path = '3.metadata'

files2 = []
for r, d, f in os.walk(read_path):
    for file in f:
        files2.append(file)

files3 = []
for r, d, f in os.walk(write_path):
    for file in f:
        files3.append(file)

temp = [x for x in files2 if x not in files3]

print(temp)
print(len(temp))
