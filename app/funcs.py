import os
import re
import tweepy
import pymongo

from nltk.sentiment.vader import SentimentIntensityAnalyzer
from nltk.corpus import stopwords
from nltk.tag import pos_tag
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from funcy import project

def increment_coin(coin):
    client = pymongo.MongoClient(os.environ.get("MONGO_URL"))
    db = client['cryptofection']
    document = db['monitor']
    
    data = document.find_one({},{"_id":False})
    
    document.update_one({},{ "$inc" if coin in data.keys() else "$set" : { coin: 1 } })

    return document.find_one({},{"_id":False})

def search(keyword, resultType, nb):
    consumer_token = os.environ.get("CONSUMER_TOKEN")
    consumer_secret = os.environ.get("CONSUMER_SECRET")
    access_token = os.environ.get("ACCESS_TOKEN")
    access_token_secret = os.environ.get("ACCESS_TOKEN_SECRET")
    auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth, wait_on_rate_limit=True)

    tweets = []
    for tweet in api.search(q=keyword, lang="en", result_type=resultType, count=nb):
        tweets.append(
            {
                "id": tweet.id_str,
                "tweet": tweet.text,
                "name": tweet.user.name,
                "location": tweet.user.location,
                "hashtags": [x["text"] for x in tweet._json["entities"]["hashtags"]],
                "created_at": tweet._json["created_at"],
                "avatar": tweet._json["user"]["profile_image_url"],
                "username": tweet._json["user"]["screen_name"],
            }
        )

    return tweets


def get_sentiments(tweets):
    pos, neg, com, neu, nb_pos, nb_neg, nb_neu = 0, 0, 0, 0, 0, 0, 0

    vader = SentimentIntensityAnalyzer()

    for row in tweets:
        text = row
        text = re.sub(r"http\S+", "", text)
        text = re.sub(r"\$", "", text)
        text = re.sub(r"\@", "", text)
        text = re.sub(r"\#", "", text)
        text = re.sub(r"\&", "", text)
        text = re.sub(r"\-", " ", text)
        text = re.sub(r"\_", " ", text)

        result = vader.polarity_scores(text)

        pos += result["neg"]
        neu += result["neu"]
        neg += result["pos"]
        com += result["compound"]

        if result["compound"] > 0.05:
            nb_pos += 1
        elif result["compound"] < -0.05:
            nb_neg += 1
        else:
            nb_neu += 1

    pos = pos / len(tweets)
    neg = neg / len(tweets)
    com = com / len(tweets)
    neu = neu / len(tweets)

    return {
        "pos": round(pos, 2),
        "neu": round(neu, 2),
        "neg": round(neg, 2),
        "com": round(com, 2),
        "nb_pos": nb_pos,
        "nb_neu": nb_neu,
        "nb_neg": nb_neg,
    }


def get_tokenized_text(text):
    text = text = re.sub(r"\$|\£|\%|\:|\…|\@|\-|\_|\“|\”|\'|rt", "", text)
    text = re.compile(
        "["
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
        "]+",
        flags=re.UNICODE,
    ).sub(r" ", text)

    token = word_tokenize(text)
    tokens_clean = []

    for i in token:
        if i not in stopwords.words("english"):
            tokens_clean.append(i.lower())

    lemmatizer = WordNetLemmatizer()
    lemmatized_sentence = []
    for word, tag in pos_tag(tokens_clean):
        if tag.startswith("NN"):
            pos = "n"
        elif tag.startswith("VB"):
            pos = "v"
        else:
            pos = "a"
        lemmatized_sentence.append(lemmatizer.lemmatize(word, pos))

    words = [word for word in lemmatized_sentence if word.isalpha()]

    return words


def get_wordCloud(tweets):
    twt = []
    for i in tweets:
        twt += get_tokenized_text(i)
    return " ".join(twt)


buy_terms = ["positive", "positif", "buy", "bull", "boost", "moon", "rise", "pump"]

hodl_terms = ["hold", "stay", "hodl"]

sell_terms = [
    "negative",
    "positif",
    "loss",
    "drop",
    "plummet",
    "sell",
    "fundraising",
    "dump",
]


def word_count(words):
    counts = dict()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return counts


def get_decision(twt):
    wordCount = word_count(twt)

    buy_terms_list = []
    sell_terms_list = []
    hold_terms_list = []

    for i in buy_terms:
        for j in wordCount.keys():
            if i in j:
                buy_terms_list.append(j)

    for i in sell_terms:
        for j in wordCount.keys():
            if i in j:
                sell_terms_list.append(j)

    for i in hodl_terms:
        for j in wordCount.keys():
            if i in j:
                hold_terms_list.append(j)

    small_1 = project(word_count(twt), [x for x in buy_terms_list])
    small_2 = project(word_count(twt), [x for x in hold_terms_list])
    small_3 = project(word_count(twt), [x for x in sell_terms_list])

    result = {
        "buy_terms_in": [small_1, sum(small_1.values()) + 1],
        "sell_terms_in": [small_2, sum(small_2.values()) + 1],
        "hold_terms_in": [small_3, sum(small_3.values()) + 1],
    }

    return result


def buy_decision(result):
    return {
        "buy": result["buy_terms_in"][1],
        "sell": result["sell_terms_in"][1],
        "hold": result["hold_terms_in"][1]
    }


def hashtag_input(hashtags):
    text = word_count(re.findall(r"#[a-zA-Z0-9]+", " ".join(hashtags)))
    res = sorted(text.items(), key=lambda x: x[1], reverse=True)
    return res[:5]
