import os
import requests
from dotenv import load_dotenv, find_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

load_dotenv(find_dotenv())

app = Flask(__name__) 
CORS(app)

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