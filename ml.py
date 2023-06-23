import pandas as pd
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.neighbors import NearestNeighbors
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt
import seaborn as sns
import sys

#Reading the dataframe
df = pd.read_csv("C:/Web_Dev/minor/reddit_data.csv")
df.drop(['utc'], inplace=True, axis=1)

#Finding number of usernames and subreddits
users = df.username.unique().tolist()
subs = df.subreddit.unique().tolist()

dftot = df.groupby(['username','subreddit']).size().reset_index(name="tot_comments")

#Finding each user's max number of comments for all subreddits
dfmax = dftot.groupby(['username'])['tot_comments'].max().reset_index(name="max_comments")

#Merging total and max comments onto new dataframe
dfnew = pd.merge(dftot, dfmax, on='username', how='left')

#Calculate a user's subreddit rating based on total and max comments
dfnew['rating'] = dfnew['tot_comments']/dfnew['max_comments']*10

dfusers = df.drop_duplicates(subset='username')
#Drop subs
dfusers.drop(['subreddit'], inplace=True, axis=1)
#Sort by users
dfusers = dfusers.sort_values(['username'], ascending=True)
#Reset index
dfusers.reset_index(drop=True, inplace=True)
#Create user id from index
dfusers['user_id'] = dfusers.index+1

#Create new dataframe and drop duplicate subs
dfsubs = df.drop_duplicates(subset='subreddit')
#Drop users
dfsubs.drop(['username'], inplace=True, axis=1)
#Sort by subs
dfsubs = dfsubs.sort_values(['subreddit'], ascending=True)
#Reset index
dfsubs.reset_index(drop=True, inplace=True)
#Create user id from index
dfsubs['sub_id'] = dfsubs.index+1

#Merging user id onto dataframe, moving position
dfnew = pd.merge(dfnew, dfusers, on='username', how='left')
move_pos = dfnew.pop('user_id')
dfnew.insert(1, 'user_id', move_pos)
#Merging sub id onto dataframe, moving position
dfnew = pd.merge(dfnew, dfsubs, on='subreddit', how='left')
move_pos = dfnew.pop('sub_id')
dfnew.insert(3, 'sub_id', move_pos)

dfcounts = dfnew['subreddit'].value_counts().rename_axis('subreddit').reset_index(name='tot_users').head(10)
dfsum = dfnew.groupby(['subreddit']).sum()
dfsum = dfsum[['tot_comments']].sort_values(by='tot_comments', ascending=False).head(10)
dfcounts = dfnew['username'].value_counts().rename_axis('username').reset_index(name='tot_subs').head(10)
dfsum = dfnew.groupby(['username']).sum()
dfsum = dfsum[['tot_comments']].sort_values(by='tot_comments', ascending=False).head(10)
dftop = dfnew[dfnew.username.str.contains('OriginalPostSearcher')]
dftop = dftop.sort_values(by='tot_comments', ascending=False).head(10)
dfnum = dfnew

#Drop non-numerical columns
dfnew.drop(['username','subreddit','tot_comments','max_comments'], inplace=True, axis=1)

#Pivot dataframe into a matrix of total ratings for users and subs
dfrat = dfnum.pivot(index='sub_id', columns='user_id', values='rating')

#Replace all null values with 0
dfrat.fillna(0,inplace=True)

num_users = dfnum.groupby('sub_id')['rating'].agg('count')

#Calculating number of subs per user
num_subs = dfnum.groupby('user_id')['rating'].agg('count')
dflast = dfrat.loc[num_users[num_users > 100].index,:]

#Limiting dataframe to only users following 10 or more subs
dflast = dflast.loc[:,num_subs[num_subs > 10].index]

#Removing sparsity from the ratings dataset
csr_data = csr_matrix(dflast.values)
dflast.reset_index(inplace=True)
knn = NearestNeighbors(metric='cosine', algorithm='brute', n_neighbors=20, n_jobs=-1)
knn.fit(csr_data)
uname = sys.argv[1]
num_subs_to_reccomend = sys.argv[2]
def subreddit_recommender(username):
    sub_list = dfsubs[dfsubs['subreddit'].str.contains(username)]  
    if len(sub_list):
        sub_idx = sub_list.iloc[0]['sub_id']
        if sub_idx in dflast['sub_id'].values:
            sub_idx = dflast[dflast['sub_id'] == sub_idx].index[0]
            distances , indices = knn.kneighbors(csr_data[sub_idx],n_neighbors=int(num_subs_to_reccomend)+1)    
            rec_sub_indices = sorted(list(zip(indices.squeeze().tolist(),distances.squeeze().tolist())),key=lambda x: x[1])[:0:-1]
            recommend_frame = []
            for val in rec_sub_indices:
                sub_idx = dflast.iloc[val[0]]['sub_id']
                idx = dfsubs[dfsubs['sub_id'] == sub_idx].index
                recommend_frame.append(dfsubs.iloc[idx]['subreddit'].values[0])
                
            return recommend_frame
    else:
        return "No matching subreddit found in data."
    
result = subreddit_recommender(uname)
print(result)
