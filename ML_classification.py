import pymysql
import warnings
import keras
from keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
from keras.models import load_model
import jieba
import pickle
import json
import numpy as np
import re
from env_paras import *

def load_models():
    tokenizer_maincat = pickle.load(open(MODEL_MAIN_TOKEN, 'rb'))
    cnn_maincat = load_model(MODEL_MAIN, compile=False)
    tokenizer_cat = pickle.load(open(MODEL_SUB_TOKEN, 'rb'))
    cnn_cat = load_model(MODEL_SUB, compile=False)
    jieba.load_userdict(MODEL_DICC)

    cnn_maincat.predict(pad_sequences([[0]], maxlen=37))
    cnn_cat.predict(pad_sequences([[0]], maxlen=55))

    return (tokenizer_maincat, cnn_maincat, tokenizer_cat, cnn_cat)

tokenizer_maincat, cnn_maincat, tokenizer_cat, cnn_cat = load_models()


def remove_puncs(x, puncs):
    for s in puncs:
        x = x.replace(s, ' ')
    return x

def remove_units(x, units):
    for u in units:
        if u in x:
            x.remove(u)
    return x

def preclean(df, col_name):
    if col_name not in list(df.columns):
        puncs = PUNCS
        df[col_name] = df['goods_name'].apply(lambda x: re.sub(r'\d+', ' ', str(x)))
        df[col_name] = df[col_name].apply(lambda x: remove_puncs(x, puncs))

    return df

def predict_maincat(df, maxlen, col_name, tokenizer, cnn):
    units = UNITS.split('|')
    df[col_name] = df[col_name].astype('str')
    df['segmentation'] = df[col_name].apply(
        lambda x: list(' '.join([' '.join(jieba.cut(seg)) for seg in x.split()]).split()))
    df['segmentation'] = df['segmentation'].apply(lambda x: remove_units(x, units))

    x = df['segmentation']
    x = tokenizer.texts_to_sequences(x)
    x = pad_sequences(x, maxlen=maxlen)
    predict = cnn.predict_classes(x)
    df['CNN_cat1'] = predict
    labelmap = {CLASS_NAME_LIST[0]: 0, CLASS_NAME_LIST[1]: 1, CLASS_NAME_LIST[2]: 2, CLASS_NAME_LIST[3]: 3, CLASS_NAME_LIST[4]: 4}
    df['CNN_cat1'] = df['CNN_cat1'].map(dict(zip(labelmap.values(), labelmap.keys())))

    return df

def predict_category(df, maxlen, col_name, prob_threshold, tokenizer_cat, cnn_cat):
    # 读取模型
    with open(MODEL_LABEL_JSON, 'r', encoding='utf8')as f:
        label_cat_dicc = json.load(f)
        label_cat_dicc = dict(zip(map(int, label_cat_dicc.keys()), label_cat_dicc.values()))

    with open(MODEL_NAME_JSON, 'r', encoding='utf8')as f:
        cat_name_dicc = json.load(f)

    pred_category = []

    for idx, row in df.iterrows():
        if row['CNN_cat1'] == CLASS_NAME_LIST[1] or row['CNN_cat1'] == CLASS_NAME_LIST[2]:
            seqs = pad_sequences(tokenizer_cat.texts_to_sequences([row['segmentation']]), maxlen)
            pred = cnn_cat.predict_proba(seqs)[0]
            max_idx = np.argmax(pred)
            if np.max(pred) >= prob_threshold:
                pred_category.append(cat_name_dicc[label_cat_dicc[max_idx]])
            else:
                pred_category.append(row['CNN_cat1'])
        else:
            pred_category.append(row['CNN_cat1'])
    df['CNN_cat2'] = pred_category

    return df.drop([col_name, 'CNN_cat1', 'segmentation'], axis=1)