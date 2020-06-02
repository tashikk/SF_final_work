from flask import Flask, request, jsonify
import pickle
import numpy as np
from statistics import mean
import re
import pandas as pd
from application import regression as reg 

app = Flask(__name__)

@app.route('/hello')
def hello():
    return 'Hello!'

@app.route('/predict', methods=['POST'])
def predict():
    #подгружаем списки, необходимые для преобразования входных данных
    with open('mean_target.txt', 'rb') as f:
        mean_target = pickle.load(f)

    with open('states_list.txt', 'rb') as f:
        states_list = pickle.load(f)
    #подгружаем модель
    with open('model.pkl', 'rb') as f:
       model = pickle.load(f)

    stroka = pd.Series(request.json)
    X_pred = reg.make_data_4_predict(stroka, states_list,mean_target)
    y_pred = model.predict(X_pred)
    return f'Ориентировочная стоимость дома: ${str(y_pred[0])} '
    #return f'{stroka}'

if __name__ == '__main__':
    app.run('localhost', 5000)

