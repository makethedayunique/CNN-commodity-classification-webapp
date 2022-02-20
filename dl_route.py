import time
from io import TextIOWrapper
import xlrd
import csv
import pandas as pd
from flask import Flask, render_template, request, send_file
from flask import Blueprint, jsonify
from ML_classification import *
from env_paras import *

dl_route = Blueprint("dl_route", __name__)

files = [] # 用户上传的文件
text_df = None  # 用户输入框内写入的数据df
files_names = [] # 用户上传的文件名
processed_dfs = [] # 处理用户上传文件后的df列表
lines = [] # 输入框内的数据行
goods_names = [] # 处理后的商品列表 限100条
categorys = [] # 处理后的商品分类 限100条
output_paths = [] # 输出文件的目录

# 控制上传文件类型为这三种
ALLOWED_EXTENSIONS = set(['txt', 'csv', 'xlsx'])
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

def write_file(df, i=None):
    prefix_path = 'static/temp_file/'
    if i==None:
        output_file = 'user_input_DL.csv'
    else:
        output_file = ''.join(files_names[i].split('.')[: -1]) + '_DL.csv'

    output_paths.append(output_file)

    with open(prefix_path + output_file, 'w', newline='', encoding='utf-8') as f:
        f_csv = csv.writer(f)
        f_csv.writerow(df.columns.tolist())
        f_csv.writerows(df.values.tolist())


def process_file(i):
    """
    :param i: input Filestorage object index
    :return: pd.dataframe containing goods_name and category
    """
    #判断类型
    file = files[i]
    file_name = files_names[i]
    if file_name.split(".")[-1] == "xlsx":
        excel_file = xlrd.open_workbook(file_contents=file)
        table = excel_file.sheets()[0]
        header = [col.value for col in table.row(0)]
        if "goods_name" in header:
            name_index = header.index('goods_name')
            names = [str(cell.value) for cell in table.col(name_index)[1:]]
            df = pd.DataFrame({'goods_name': names})
            df = preclean(df, col_name='goods_cn')
            df = predict_maincat(df, maxlen=MODEL_MAXLEN, col_name='goods_cn', tokenizer=tokenizer_maincat,
                                 cnn=cnn_maincat)
            df = predict_category(df, maxlen=MODEL_SUB_MAXLEN, col_name='goods_cn', tokenizer_cat=tokenizer_cat,
                                  cnn_cat=cnn_cat, prob_threshold=0.6)
            return df
        else:
            return None
    else:
        lines = []
        csv_file = csv.reader(file.decode('utf-8').split('\n'))
        for line in csv_file:
            lines.append(line)
        header = lines[0]
        if "goods_name" in header:
        # if "goods_name" in file.columns.tolist():
            name_index = header.index("goods_name")
            names = []
            for line in lines[1:]:
                try:
                    names.append(str(line[name_index]))
                except:
                    continue
            df = pd.DataFrame({'goods_name': names})
            # df = file
            df = preclean(df, col_name='goods_cn')
            df = predict_maincat(df, maxlen=MODEL_MAXLEN, col_name='goods_cn', tokenizer=tokenizer_maincat,
                                 cnn=cnn_maincat)
            df = predict_category(df, maxlen=MODEL_SUB_MAXLEN, col_name='goods_cn', tokenizer_cat=tokenizer_cat,
                                  cnn_cat=cnn_cat, prob_threshold=0.6)
            return df
        else:
            return None

@dl_route.route("/upload", methods=['POST'])
def receive_upload():
    if request.method == "POST":
        # 上传文件的键名是 file，判断是否有file
        if "file" not in request.files:
            return jsonify({'code': -1, 'filename': '', 'msg': 'No file information'})

        upload_files = request.files.getlist('file')
        if len(upload_files) == 0:
            return jsonify({'code': -1, 'filename': '', 'msg': 'No selected file'})
        for file in upload_files:
            if file and allowed_file(file.filename):
                files_names.append(file.filename)
                if file.filename[-4:] == 'xlsx':
                    files.append(file.read())
                else:
                    files.append(file.read())
        return jsonify({'code': 0, 'filename': '', 'msg': 'Upload successfully'})
    else:
        return jsonify({'code': -1, 'filename': '', 'msg': 'Method not allowed'})

@dl_route.route("/dl", methods=['POST', 'GET'])
def return_files():
    global lines
    global goods_names
    global categorys
    global processed_dfs
    global files
    global text_df
    # return render_template("classification-page-inner1.html", filenames = [file.filename for file in files])

    if request.method == "POST":
        data = request.form.get("item_text")
        if data != '':
            lines = data.split('\n')

            text_df = pd.DataFrame({'goods_name': [line.strip() for line in lines]})

            text_file = preclean(text_df, col_name='goods_cn')
            text_df = predict_maincat(text_df, maxlen=MODEL_MAXLEN, col_name='goods_cn', tokenizer=tokenizer_maincat,
                                 cnn=cnn_maincat)
            text_df = predict_category(text_df, maxlen=MODEL_SUB_MAXLEN, col_name='goods_cn', tokenizer_cat=tokenizer_cat,
                                  cnn_cat=cnn_cat, prob_threshold=0.6)
            #仅供预览，提供100条数据
            goods_names = text_df.iloc[:100, :]['goods_name'].tolist()
            categorys = text_df.iloc[:100, :]['CNN_cat2'].tolist()

            write_file(text_df)


        for i in range(len(files)):
            # 计算还需几条数据用于预览
            number_left_for_preview = 100 - len(goods_names)
            df = process_file(i)
            if df is not None:
                processed_dfs.append(df)

                write_file(df, i)

                if number_left_for_preview > 0:
                    goods_names += df['goods_name'].tolist()
                    categorys += df['CNN_cat2'].tolist()
                    goods_names = goods_names[: 100]
                    categorys = categorys[: 100]
            else:
                pass


        if (len(files) == 0) and (len(lines) == 0):
            return jsonify({"code": -1, "msg": "No file uploaded"})
        elif len(lines) != 0 and len(files) == 0:
            return jsonify({'goods_names': goods_names, 'categorys': categorys, 'output_paths': output_paths})
        else:
            return jsonify({'goods_names': goods_names, 'categorys': categorys, 'output_paths': output_paths})
    else:
        return jsonify({'code': -1, 'msg':'Method not allowed'})

