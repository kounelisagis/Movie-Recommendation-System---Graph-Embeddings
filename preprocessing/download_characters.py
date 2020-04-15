import os
from urllib import request
import json
import re
from bs4 import BeautifulSoup
from tmdbv3api import TMDb, Movie
from multiprocessing.dummy import Pool
from multiprocessing import cpu_count
import pandas as pd
import config


tmdb = TMDb()
tmdb.api_key = config.tmdb_key
movie = Movie()

CSV_IN = "data\\data1.csv"
CSV_OUT = "data\\data2.csv"


def process_task(row):
    movieName = row[0]
    filename = row[1]

    try:
        movies_list = movie.search(movieName)
        if len(movies_list) == 0:
            temp_movieName = re.sub(r'\(.+?\)\s*', '', movieName)
            movies_list = movie.search(temp_movieName)

        tmdbId = movies_list[0].id

        cast_list = (movie.credits(tmdbId)).cast
        cast_list = [character for character in cast_list if character['character'] != ""]

        if len(cast_list) == 0:
            return None

        topCharacters = min(10, len(cast_list))

        return (movieName, filename, tmdbId, [actor["character"] for actor in cast_list[:topCharacters]])

    except Exception as e:
        print(movieName)
        print(e)
        return None


if __name__ == "__main__":

    df_in = pd.read_csv(CSV_IN, encoding='utf-8')
    data = list(df_in.itertuples(index=False))

    with Pool(10) as p:
        results = p.map(process_task, data)

    results = [x[:-1] + (";".join(x[-1]),) for x in results if x is not None]

    df_out = pd.DataFrame(results, columns = ['movieName', 'fileΝame', 'tmdbId', 'characters'])
    df_out = df_out.drop_duplicates(subset=['tmdbId'], keep='first')

    df_out.to_csv(CSV_OUT, encoding='utf-8', index=False)

