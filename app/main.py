import os
import requests
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from .funcs import *


load_dotenv(find_dotenv())

app = Flask(__name__)
CORS(app)


@app.route("/info", methods=["POST"])
def get_info():
    result = {}

    data = request.get_json()
    key = data["coin"]

    # search history
    result["search_history"] = increment_coin(key)

    # top 10 tweets
    topTweets = search(key, "popular", 10)
    result["topTweets"] = list(
        map(
            lambda x: {
                key: x[key] for key in x if key not in ["hashtags", "tweet", "location"]
            },
            topTweets,
        )
    )

    # sentiments => compound
    result_all = search(key, "recent", 25)
    tweets = [x["tweet"] for x in result_all]

    sentiments = get_sentiments(tweets)
    result["score"] = {
        "positive": sentiments["nb_pos"],
        "negative": sentiments["nb_neg"],
        "neutral": sentiments["nb_neu"],
    }

    result["hashtags"] = hashtag_input(tweets)

    # buy hold sell
    all_terms = []
    for i in tweets:
        all_terms += get_tokenized_text(i)
    result["buyDecision"] = buy_decision(get_decision(all_terms))

    # visualisations => wordcloud
    result["wordcloud"] = get_wordCloud(tweets)

    return jsonify(result)


@app.route("/coins", methods=["GET"])
def coins():
    headers = {"X-CMC_PRO_API_KEY": os.environ.get("CMC_API_KEY")}
    response = requests.get(
        f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/map?aux&sort=cmc_rank",
        headers=headers,
    )
    return jsonify(response.json()["data"])


@app.route("/coins/<string:id>", methods=["GET"])
def coin(id: str):
    headers = {"X-CMC_PRO_API_KEY": os.environ.get("CMC_API_KEY")}
    response = requests.get(
        f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id={id}",
        headers=headers,
    )
    return jsonify(response.json()["data"][id])


@app.route("/quotes/<string:id>", methods=["GET"])
def quote(id: str):
    headers = {"X-CMC_PRO_API_KEY": os.environ.get("CMC_API_KEY")}
    response = requests.get(
        f"https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?id={id}",
        headers=headers,
    )
    return jsonify(response.json()["data"][id])
