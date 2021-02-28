import os
import requests
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify,request
from flask_cors import CORS
from .funcs import *




load_dotenv(find_dotenv())

app = Flask(__name__) 
CORS(app)

@app.route('/info', methods=['GET'])
def get_info():
    result={}

    data=request.get_json()
    key=data['coin']
    # top tweets [ 10 ] => name,@username,avatar,created_at,idOfTweet
    topTweets= search(key,"popular",10)
    result['topTweets']=list(map(lambda x :{key: x[key] for key in x if key not in ["Hashtags","Tweet","Tweet_Location"]},topTweets)) #clean
    # sentiments => compound
    result_all=search("cardano","recent",10)
    tweets=[x['Tweet']for x in result_all]
    
    sentiments=get_sentiments(tweets) #clean
    result['compound']=sentiments['com']
    result['posNeuNeg']=[sentiments['nb_pos'],sentiments['nb_neu'],sentiments['nb_neg']]
    
    result['hash_top_freq_data']=hashtag_input(tweets) 
    # buy hold sell :
    all_terms=[]
    for i in tweets:
        all_terms+=get_tokenized_text(i)
 
    result['buy_hold_sell_data']=circle_graph_input(get_decision(all_terms))
    # visualisations => wordcloud + bar_plots
    result['wordcloud_data']=get_wordCloud(tweets)
    result['bar_pays_data']=bar_graph_input(result_all)
    return jsonify(result)


@app.route("/coins", methods=['GET']) 
def coins():
    headers = {'X-CMC_PRO_API_KEY': os.environ.get("CMC_API_KEY")}
    response = requests.get(f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/map?aux&sort=cmc_rank', headers=headers)
    return jsonify(response.json()["data"])

@app.route("/coins/<string:id>", methods=['GET']) 
def coin(id: str): 
    headers = {'X-CMC_PRO_API_KEY': os.environ.get("CMC_API_KEY")}
    response = requests.get(f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/info?id={id}', headers=headers)
    return jsonify(response.json()["data"][id])

@app.route("/quotes/<string:id>", methods=['GET']) 
def quote(id: str): 
    headers = {'X-CMC_PRO_API_KEY': os.environ.get("CMC_API_KEY")}
    response = requests.get(f'https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest?id={id}', headers=headers)
    return jsonify(response.json()["data"][id])
