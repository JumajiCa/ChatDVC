from flask import jsonify, request, render_template
from flask_cors import CORS
from app import app 
from sys import version_info
from numpy import random as npr

@app.route('/')
def hello(): 
    user = {"username": "Pog"}
    return render_template("index.html", user=user)
@app.route('/rand')
def basic_rand(): 
    random_num_lst  = npr.rand(30)
    txt_lst = [str(num) for num in random_num_lst]
    return render_template("rand.html", num_lst=txt_lst)
