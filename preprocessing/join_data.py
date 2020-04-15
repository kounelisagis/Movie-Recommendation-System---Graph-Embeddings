import pandas as pd

df1 = pd.read_csv("data\\data3.csv")
df2 = pd.read_csv("data\\ml-25m\\links.csv")

df3 = pd.merge(df1, df2[['movieId','tmdbId']], on = ["tmdbId"])

df3.to_csv("data\\final.csv", index=False)
