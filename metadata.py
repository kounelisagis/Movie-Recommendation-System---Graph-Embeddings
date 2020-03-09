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

files = []
for r, d, f in os.walk(read_path):
    for file in f:
        try:
            file = file.replace(".txt", "")
            file = file.replace("-", " ")

            movies_list = movie.search(file)
            movies_list.sort(key=lambda x: x.popularity, reverse=True)

            cast_list = (movie.credits(movies_list[0].id)).cast

            topActors = min(10, len(cast_list))

            write_file = open(write_path+"\\"+file+".txt", "w", encoding="utf-8")

            for actor in cast_list[:topActors]:
                write_file.write(actor["character"]+"\n")
            
            write_file.close() 

        except Exception as e:
            print(file)
            print(e)
            print("-----------------------")
