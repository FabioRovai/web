# -*- coding: utf-8 -*-
"""Welcome_to_Colaboratory.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/18-HuPeFKeMfUGslaaj7neVCyq6754w9c
"""

!wget https://raw.githubusercontent.com/FabioRovai/web/main/pT.py

!pip install flask-ngrok --q

!wget https://github.com/FabioRovai/web/blob/main/temp.zip?raw=true -O foo.zip
!unzip '/content/foo.zip'

!wget  https://raw.githubusercontent.com/FabioRovai/test7/main/PDB.txt -O PDB.txt

import flask
from flask import Flask, render_template, request
import pickle
import numpy as np
from flask_ngrok import run_with_ngrok
import itertools
import IPython
import IPython.display as ipd
import matplotlib.pyplot as plt
import os 
import pandas as pd
import random
import re
import requests 
import seaborn as sns
import shutil 
import soundfile as sf
import sys
import warnings
import zipfile
from contextlib import suppress
from __future__ import generators
from IPython.display import clear_output 
from mpl_toolkits.mplot3d import Axes3D
from scipy.spatial import ConvexHull
from scipy.io import wavfile

warnings.filterwarnings("ignore")

from pT import data
wavfile.write('twelve-tone_comb_wave.wav', 44100, data.astype(np.int16))
IPython.display.Audio("twelve-tone_comb_wave.wav")

#https://medium.datadriveninvestor.com/machine-learning-model-deployment-using-flask-in-google-colab-1f718693a3c0


app = Flask(__name__)
run_with_ngrok(app)

#model = pickle.load(open('model.pkl', 'rb'))

@app.route('/', methods=['GET'])
def home():
  return render_template('index.html')

@app.route('/', methods=['GET', "POST"])
def predict():
  input_values = [float(x) for x in request.form.values()]
  inp_features = [input_values]
  prediction = model.predict(inp_features)
  if prediction==1:
    return render_template('index.html', prediction_text='Death event took Place. Person is no more')
  else:
    return render_template('ID', prediction_text='data')
  

app.run()