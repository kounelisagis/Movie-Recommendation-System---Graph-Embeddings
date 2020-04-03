import os
from urllib import request
import json
import re
from bs4 import BeautifulSoup
from tmdbv3api import TMDb, Movie
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import pandas as pd


tmdb = TMDb()
tmdb.api_key = 'API-KEY'
movie = Movie()

CSV_IN = "data\\data.csv"
CSV_OUT = "data\\data2.csv"


def process_task(row):
    movie_name = row[0]
    filename = row[1]

    try:
        movies_list = movie.search(movie_name)
        if len(movies_list) == 0:
            temp_movie_name = re.sub(r'\(.+?\)\s*', '', movie_name)
            movies_list = movie.search(temp_movie_name)

        movies_list.sort(key=lambda x: x.popularity, reverse=True)

        tmdb_id = movies_list[0].id

        cast_list = (movie.credits(tmdb_id)).cast

        topCharacters = min(10, len(cast_list))

        # write_file = open(CHARACTERS_DIR + "\\" + filename, "w", encoding="utf-8")

        # for actor in cast_list[:topCharacters]:
        #     if actor:
        #         write_file.write(actor["character"]+"\n")
        
        # write_file.close() 
        return (movie_name, filename, tmdb_id, [actor["character"] for actor in cast_list[:topCharacters]])

    except Exception as e:
        print(movie_name)
        print(e)
        return None


if __name__ == "__main__":

    df_in = pd.read_csv(CSV_IN)
    data = list(df_in.itertuples(index=False))

    with Pool(10) as p:
        results = p.map(process_task, data)

    results = [x[:-1] + (";".join(x[-1]),) for x in results if x is not None]

    df_out = pd.DataFrame(results, columns = ['movie_name', 'filename', 'tmdb_id', 'characters'])

    df_out.to_csv(CSV_OUT, encoding='utf-8', index=False)

