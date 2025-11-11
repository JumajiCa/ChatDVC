
from flask import Flask 
from numpy import random as npr

# Really Sketchy Flask code
app = Flask(__name__)

@app.route("/") 
def hello(): 
    return "<h1>Hello World!</h1>"

@app.route("/rand") 
def basic_rand(): 
    random_num_lst  = npr.rand(30)
    text = ""
    for num in random_num_lst: 
        text += f"<h1>{str(num)}</h1>"
    return text

if __name__ == "__main__": 
    app.run(debug=True)