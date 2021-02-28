from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from funcy import project


import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure

import seaborn as sns
import io
import base64
from wordcloud import WordCloud
import plotly.graph_objects as go

import os
import re
import pandas as pd

import tweepy


#///////////////////////////// FUNCTIONS \\\\\\\\\\\\\\\\\\\\\\\\\\\

# Search_All :
#=============
    
def search(keyword, resultType,nb):
    
    consumer_token=os.environ.get("CONSUMER_TOKEN")
    consumer_secret=os.environ.get("CONSUMER_SECRET")
    access_token=os.environ.get("ACCESS_TOKEN")
    access_token_secret=os.environ.get("ACCESS_TOKEN_SECRET")
    auth = tweepy.OAuthHandler(consumer_token,consumer_secret)
    auth.set_access_token(access_token,access_token_secret)
    api= tweepy.API(auth,wait_on_rate_limit=True)
    
    tweets = []
    
    for tweet in api.search(q=keyword, lang="en", result_type=resultType,count=nb):
       tweetId = tweet.id
       tweetText = tweet.text
       tweetUsername = tweet.user.name
       tweetUserLocation = tweet.user.location
       hashtags=tweet._json['entities']['hashtags']
       hashtags=[x['text'] for x in hashtags]
       created_at=tweet._json['created_at']
       prof=tweet._json['user']['profile_image_url']
       nickname=tweet._json['user']['screen_name']
       
       tweets.append({
            "Tweet_Id": tweetId,
            "Tweet":tweetText,
            "Tweet_User": tweetUsername,
            "Tweet_Location": tweetUserLocation,
            "Hashtags":hashtags,
            "created_at":created_at,
            "image_profile":prof,
            "username":nickname
        })
    return tweets


# Get_sentiments :
# ================
def get_sentiments(tweets):
    
    pos, neg, com, neu, nb_pos, nb_neg, nb_neu=0,0,0,0,0,0,0
    
    vader = SentimentIntensityAnalyzer()
    
    for row in tweets:
        text=row
        text =re.sub(r"http\S+", "", text)
        text = re.sub(r"\$", "", text)
        text = re.sub(r"\@", "", text)
        text = re.sub(r"\#", "", text)
        text = re.sub(r"\&", "", text)
        text = re.sub(r"\-", " ", text)
        text = re.sub(r"\_", " ", text)
        
        result=vader.polarity_scores(text)

        pos+=result['neg']
        neu+=result['neu']
        neg+=result['pos']
        com+=result['compound']
        
        if result['compound'] > 0.05:
            nb_pos+=1
        elif result['compound'] < -0.05:
            nb_neg+=1
        else:
            nb_neu+=1
            
    pos=pos/len(tweets)
    neg=neg/len(tweets)
    com=com/len(tweets)
    neu=neu/len(tweets)
    
    return {"pos":round(pos,2),"neu":round(neu,2),"neg":round(neg,2),"com":round(com,2),"nb_pos":nb_pos,"nb_neu":nb_neu,"nb_neg":nb_neg}

# Get_tokenized_from_row :
# ========================
def get_tokenized_text(text):
    text = text = re.sub(r"\$|\£|\%|\:|\…|\@|\-|\_|\“|\”|\'|rt", "", text)
    text = re.compile("["
                                   u"\U0001F600-\U0001F64F"  # emoticons
                                   u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                                   u"\U0001F680-\U0001F6FF"  # transport & map symbols
                                   u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                                   u"\U00002500-\U00002BEF"  # chinese char
                                   u"\U00002702-\U000027B0"
                                   u"\U00002702-\U000027B0"
                                   u"\U000024C2-\U0001F251"
                                   u"\U0001f926-\U0001f937"
                                   u"\U00010000-\U0010ffff"
                                   u"\u2640-\u2642"
                                   u"\u2600-\u2B55"
                                   u"\u200d"
                                   u"\u23cf"
                                   u"\u23e9"
                                   u"\u231a"
                                   u"\ufe0f"  # dingbats
                                   u"\u3030"
                                   "]+", flags=re.UNICODE).sub(r' ',text)
    
    token = word_tokenize(text)
    tokens_clean=[]

    for i in token:
        if i not in stopwords.words('english'):
            tokens_clean.append(i.lower())
    
    
    
    lemmatizer = WordNetLemmatizer()
    lemmatized_sentence = []
    for word, tag in pos_tag(tokens_clean):
        if tag.startswith('NN'):
            pos = 'n'
        elif tag.startswith('VB'):
            pos = 'v'
        else:
            pos = 'a'
        lemmatized_sentence.append(lemmatizer.lemmatize(word, pos))
    
    words = [word for word in lemmatized_sentence if word.isalpha()]
    
    return words
#==================================
# WORDCLOUD :
#=================    
def get_wordCloud(tweets):
    twt=[]
    for i in tweets:
        twt+=get_tokenized_text(i)
    return ' '.join(twt)
#=================================
# Buy Hold Sell :
#=================

positif_terms=['positive','positif', 'buy','bull','boost','moon','rise',"pump"]

neu_terms=['hold','stay','hodl']

negatif_terms=['negative','positif', 'loss', 'drop', 'plummet', 'sell', 'fundraising',"dump"]

def word_count(words):
    
    counts = dict()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return counts

def get_decision(twt):
    
    wordCount=word_count(twt)

    posTerms=[]
    negTerms=[]
    neuTerms=[]

    for i in positif_terms:
        for j in wordCount.keys():
            if i in j:
                posTerms.append(j)

    for i in negatif_terms:
        for j in wordCount.keys():
            if i in j:
                negTerms.append(j)

    for i in neu_terms:
        for j in wordCount.keys():
            if i in j:
                neuTerms.append(j)

    
    small_1 = project(word_count(twt), [x for x in posTerms])
    small_2 = project(word_count(twt), [x for x in neuTerms])
    small_3 = project(word_count(twt), [x for x in negTerms])

    result={
        "pos_terms_in":[small_1,sum(small_1.values())+1],
        "neg_terms_in":[small_2,sum(small_2.values())+1],
        "neu_terms_in":[small_3,sum(small_3.values())+1]
    }
    return result

#===================================
# plots :
#===================================
    # BARPLOTS :
    def bar_graph(tweets):
        data=pd.DataFrame(data={"pays":[i['Tweet_Location']  for i in tweets if i['Tweet_Location']!=""]})
        ax = sns.countplot(x="pays", data=data, order=data.pays.value_counts().iloc[:5].index)
        return graph_to_base64(ax.get_figure(), "Top 5 Interaction Country", "This is a graph of top5 of the most high interaction country based about the coin searched")

def graph_to_base64(fig, title, description):
    pic_IObytes = io.BytesIO()
    fig.savefig(pic_IObytes,  format='png', transparent=True)
    pic_IObytes.seek(0)
    pic_hash = base64.b64encode(pic_IObytes.read())
    return {"title":title, "description": description, "base64": pic_hash}


     # WORDCLOUD :
     #============
def plot_cloud_input(text):
    return text    
#===================================
    # CIRCLE :
    #============
def circle_graph_input(result):  
    col = (['Buy','Sell','Hold'],[result['pos_terms_in'][1],result['neg_terms_in'][1],result['neu_terms_in'][1]])
    return col
#=====================================
    # hashtags
    #============
def hashtag_input(hashtags):
    text =word_count(re.findall(r'#[a-zA-Z0-9]+',' '.join(hashtags)))
    res=list(reversed([(k,v) for k, v in sorted(text.items(), key=lambda item: item[1])]))
    if len(res)<5:
        return res
    else :
        return res[0:5]
    # GET_PAYS :
    #===========
def bar_graph_input(tweets):
        text =word_count([i['Tweet_Location']  for i in tweets if i['Tweet_Location']!=""])
        res=list(reversed([(k,v) for k, v in sorted(text.items(), key=lambda item: item[1])]))
        if len(res)<5:
            return res
        else :
            return res[0:5]