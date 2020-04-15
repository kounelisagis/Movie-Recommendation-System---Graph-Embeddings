import os
import pandas as pd
import numpy as np
from collections import defaultdict
from scipy import spatial
from surprise import Dataset
from surprise import Reader
from surprise import AlgoBase
from surprise import Dataset, PredictionImpossible
from surprise import KNNBasic
from surprise import accuracy
from surprise.model_selection import ShuffleSplit
from sklearn.metrics import dcg_score, ndcg_score

from embeddings_extractor import EmbeddingsExtractor


class MyOwnAlgorithm(AlgoBase):

    def __init__(self, sim_options={}, bsl_options={}):

        AlgoBase.__init__(self, sim_options=sim_options, bsl_options=bsl_options)

    def fit(self, trainset, movies):

        AlgoBase.fit(self, trainset)

        self.movies = movies
        mean_user_vectors = {}

        for u in trainset.ur:
            weights_sum = 0.0

            user_movies = {}
            
            for movieId, score in trainset.ur[u]:
                movieRawId = trainset.to_raw_iid(movieId)
                if movieRawId in self.movies:
                    user_movies[movieRawId] = self.movies[movieRawId]
                    user_movies[movieRawId]["score"] = score

            sum_vector = [0.0 for _ in user_movies[list(user_movies)[0]]["embedding"]]
            for _, movie in user_movies.items():
                sum_vector = [x + y*movie["score"] for x, y in zip(sum_vector, movie["embedding"])]
                weights_sum += score
            
            mean_vector = [x/weights_sum for x in sum_vector]

            mean_user_vectors[u] = mean_vector

        self.mean_user_vectors = mean_user_vectors

        return self


    def estimate(self, u, i):
        if not (self.trainset.knows_user(u) and self.trainset.knows_item(i)):
            raise PredictionImpossible('User and/or item is unkown.')

        # convertion to real ids
        # print("user: " + str(self.trainset.to_raw_uid(u)))
        # print("item: " + str(self.trainset.to_raw_iid(i)))

        movieRawId = trainset.to_raw_iid(i)
        movie_vector = self.movies[movieRawId]["embedding"]

        result = 1 - spatial.distance.cosine(self.mean_user_vectors[u], movie_vector)
        result = 2.25*result + 2.75 # from [-1, 1] to [0.5, 5]

        return result


def get_average_ndcg(predictions, n=10):

    top_true = defaultdict(list)
    top_predicted = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_true[uid].append((iid, est, true_r))
        top_predicted[uid].append((iid, est, true_r))

    for uid, user_ratings in top_true.items():
        user_ratings.sort(key=lambda x: x[2], reverse=True)
        top_true[uid] = user_ratings#[:n]

    for uid, user_ratings in top_predicted.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_predicted[uid] = user_ratings#[:n]

    ndcg_scores = []

    for uid, _ in top_predicted.items():
        true = np.asarray([[x[2] for x in top_true[uid]]])
        predicted = np.asarray([[x[2] for x in top_predicted[uid]]])

        if len(true[0]) > 1:
            ndcg_scores.append(ndcg_score(true, predicted))
        # else:
        #     ndcg_scores.append(1.0)


    return np.mean(ndcg_scores)


if __name__ == "__main__":

    data_df = pd.read_csv("data\\final.csv")
    movies_id_list = data_df["movieId"].tolist()

    ratings_df = pd.read_csv("data\\ml-25m\\ratings.csv", nrows=100000)
    ratings_df = ratings_df.loc[ratings_df['movieId'].isin(movies_id_list)]

    del movies_id_list[:]
    del movies_id_list

    reader = Reader(line_format='user item rating', sep=',', skip_lines=1, rating_scale=(0, 5))
    data = Dataset.load_from_df(ratings_df[['userId', 'movieId', 'rating']], reader)


    my_algo = MyOwnAlgorithm(sim_options={'user_based': True})


    ex = EmbeddingsExtractor()
    ex.read_data(data_df)


    rs = ShuffleSplit(n_splits=5, test_size=.2)

    for d in list(range(3, 15)) + [20,35,50,80,110,140]:
        for w in range(1, 5):
            for m in range(1, 5):
                ex = EmbeddingsExtractor(dimensions=d, wl_iterations=w, min_count=m)
                movies = ex.extract_embeddings()

                for trainset, testset in rs.split(data):
                    my_algo.fit(trainset, movies)
                    predictions = my_algo.test(testset)

                    rmse = accuracy.rmse(predictions, verbose=False)
                    print(rmse)

                    ndcg_average = get_average_ndcg(predictions)
                    print(ndcg_average)
