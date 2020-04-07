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
from surprise.model_selection import KFold
from sklearn.metrics import ndcg_score


dataset_df = pd.read_csv("data\\final.csv")
movies_id_list = dataset_df["movieId"].tolist()

ratings_df = pd.read_csv("data\\ml-25m\\ratings.csv", nrows=100000)
ratings_df = ratings_df.loc[ratings_df['movieId'].isin(movies_id_list)]



class MyOwnAlgorithm(AlgoBase):

    def __init__(self, sim_options={}, bsl_options={}):

        AlgoBase.__init__(self, sim_options=sim_options, bsl_options=bsl_options)

    def fit(self, trainset):

        AlgoBase.fit(self, trainset)

        mean_vectors = {}

        weights_sum = 0.0

        for u in trainset.ur:
            user_scores = [score for _, score in trainset.ur[u]]

            user_movies = [trainset.to_raw_iid(movieId) for movieId, _ in trainset.ur[u]]
            user_df = dataset_df[dataset_df.movieId.isin(user_movies)]
            movies_vectors = [[float(vector_str) for vector_str in vectors_str.split(";")] for vectors_str in user_df['vector'].tolist()]


            sum_vector = [0.0 for _ in range(len(movies_vectors[0]))]
            for (movie_vector, score) in zip(movies_vectors, user_scores):
                sum_vector = [x + y*score for x, y in zip(sum_vector, movie_vector)]
                weights_sum += score
            
            mean_vector = [x/weights_sum for x in sum_vector]

            mean_vectors[u] = mean_vector

        self.mean_vectors = mean_vectors

        return self



    def estimate(self, u, i):
        if not (self.trainset.knows_user(u) and self.trainset.knows_item(i)):
            raise PredictionImpossible('User and/or item is unkown.')

        # convertion to real ids
        # print("user: " + str(self.trainset.to_raw_uid(u)))
        # print("item: " + str(self.trainset.to_raw_iid(i)))

        movie_df = dataset_df[dataset_df['movieId'] == int(self.trainset.to_raw_iid(i))]
        movie_vector = [float(x) for x in movie_df.iloc[0]["vector"].split(";")]

        result = 1 - spatial.distance.cosine(self.mean_vectors[u], movie_vector)
        result = 2.25*result + 2.75 # from [-1, 1] to [0.5, 5]

        return round(result*2)/2 # round to the nearest .5



def get_top_n(predictions, n=10):

    # First map the predictions to each user.
    top_n = defaultdict(list)
    for uid, iid, true_r, est, _ in predictions:
        top_n[uid].append((iid, est))

    # Then sort the predictions for each user and retrieve the k highest ones.
    for uid, user_ratings in top_n.items():
        user_ratings.sort(key=lambda x: x[1], reverse=True)
        top_n[uid] = user_ratings[:n]

    return top_n



if __name__ == "__main__":
    reader = Reader(line_format='user item rating', sep=',', skip_lines=1, rating_scale=(0, 5))
    data = Dataset.load_from_df(ratings_df[['userId', 'movieId', 'rating']], reader)


    kf = KFold(n_splits=5)
    my_algo = MyOwnAlgorithm(sim_options={'user_based': True})

    knn_algo = KNNBasic(sim_options={'user_based': True})


    for trainset, testset in kf.split(data):
        my_algo.fit(trainset)
        predictions = my_algo.test(testset)
        accuracy.rmse(predictions, verbose=True)

        top_n = get_top_n(predictions, n=10)

        # Print the recommended items for each user
        for uid, user_ratings in top_n.items():
            print(uid, [iid for (iid, _) in user_ratings])
        

        knn_algo.fit(trainset)
        predictions = knn_algo.test(testset)
        accuracy.rmse(predictions, verbose=True)
