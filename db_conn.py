import pymysql
import pandas as pd
import datetime
from ML_classification import *
from env_paras import *

class DB_conn:
    db_name = None
    username = None
    password = None
    host = DB_HOST
    conn = None
    port = DB_PORT

    def __init__(self, db_name, username=None, password=None):
        if username == None:
            username = self.username
            password = self.password

        self.db_name = db_name

    def connect(self):
        self.conn = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username, passwd=self.password,
                db=self.db_name, charset='gbk', use_unicode=True)

    def close(self):
        self.conn.close()

    def find_user_info(self, user_id):
        sql = sql_user_query(user_id)
        try:
            df_user = pd.read_sql(sql, con=self.conn)
        except:
            self.connect()
            df_user = pd.read_sql(sql, con=self.conn)
        if df_user.shape[0] == 0:
            return df_user
        else:
            return df_user.iloc[0]

    def find_trip_img(self, upload_id):
        sql = sql_trip_image_query(upload_id)
        try:
            df_trip_img = pd.read_sql(sql, con=self.conn)
        except:
            self.connect()
            df_trip_img = pd.read_sql(sql, con=self.conn)
        return df_trip_img

    def find_trip_info(self, upload_id):
        sql = sql_trip_info_query(upload_id)
        try:
            df_trips = pd.read_sql(sql, con=self.conn)
        except:
            self.connect()
            df_trips = pd.read_sql(sql, con=self.conn)
        trip_info = {}
        for col in list(df_trips.columns):
            trip_info[col] = None
        if df_trips.shape[0] == 1:
            trip_info = dict(df_trips.reset_index().iloc[0])
        # 获取小票状态
        sql = sql_trip_status_query(upload_id)
        df_trip_state = pd.read_sql(sql, con=self.conn)
        for col in list(df_trip_state.columns):
            try:
                trip_info[col] = df_trip_state.reset_index().iloc[0][col]
            except:
                trip_info[col] = None

        return trip_info

    def find_trip_details(self, upload_id):
        sql = sql_trip_details_query(upload_id)
        try:
            df_trip_items = pd.read_sql(sql, con=self.conn)
        except:
            self.connect()
            df_trip_items = pd.read_sql(sql, con=self.conn)
        trip_items = []
        df_trip_items = df_trip_items.reset_index()

        #导入模型进行类别预测
        # tokenizer_maincat, cnn_maincat, tokenizer_cat, cnn_cat = load_models()
        df_trip_items = preclean(df_trip_items, col_name=ATTRI_NAME_LIST[0])
        df_trip_items = predict_maincat(df_trip_items, maxlen=MODEL_MAXLEN, col_name=ATTRI_NAME_LIST[0], tokenizer=tokenizer_maincat,
                                        cnn=cnn_maincat)
        df_trip_items = predict_category(df_trip_items, maxlen=MODEL_SUB_MAXLEN, col_name=ATTRI_NAME_LIST[0], tokenizer_cat=tokenizer_cat,
                                         cnn_cat=cnn_cat, prob_threshold=0.6)

        for idx in range(df_trip_items.shape[0]):
            trip_items.append(dict(df_trip_items.iloc[idx]))
        return trip_items

    def find_trips_to_user(self, user_id):
        sql = sql_trip_user_query(user_id)
        try:
            df_trips = pd.read_sql(sql, con=self.conn)
        except:
            self.connect()
            df_trips = pd.read_sql(sql, con=self.conn)
        df_trips[ATTRI_NAME_LIST[1]] =df_trips[ATTRI_NAME_LIST[1]].apply(lambda x: x.strftime('%Y-%m-%d'))
        df_trips[ATTRI_NAME_LIST[2]] = df_trips[ATTRI_NAME_LIST[1]].apply(lambda x: x[: 4])
        df_trips[ATTRI_NAME_LIST[3]] = df_trips[ATTRI_NAME_LIST[1]].apply(lambda x: x[: 7])
        df_trips[ATTRI_NAME_LIST[4]] = df_trips[ATTRI_NAME_LIST[1]].apply(lambda x: x[: 10])
        trip_hierarchy = {}
        for col in [ATTRI_NAME_LIST[2], ATTRI_NAME_LIST[3], ATTRI_NAME_LIST[4]]:
            temp_stat = df_trips.groupby([col])[ATTRI_NAME_LIST[5]].count().reset_index()
            temp_stat[col+'_rename'] = temp_stat.apply(lambda row: row[col] + ' : ' + str(row[ATTRI_NAME_LIST[5]]) + ' trips', axis=1)
            df_trips = pd.merge(left=df_trips, right=temp_stat[[col, col+'_rename']], on=col, how='left')
        for idx, row in df_trips.iterrows():
            year = row[ATTRI_NAME_LIST[2] + '_rename']
            month = row[ATTRI_NAME_LIST[3] + '_rename']
            day = row[ATTRI_NAME_LIST[4] + '_rename']
            if year not in trip_hierarchy:
                trip_hierarchy[year] = {}
            if month not in trip_hierarchy[year]:
                trip_hierarchy[year][month] = {}
            if day not in trip_hierarchy[year][month]:
                trip_hierarchy[year][month][day] = df_trips[df_trips[ATTRI_NAME_LIST[4] + '_rename'] == day][ATTRI_NAME_LIST[5]].tolist()

        # 判断状况，分trip_type
        type_trips = {}
        days_28 = datetime.datetime.now() - datetime.timedelta(days=28)
        df_trips[ATTRI_NAME_LIST[1]] = df_trips[ATTRI_NAME_LIST[1]].apply(lambda x: datetime.datetime.strptime(x[: 10], '%Y-%m-%d'))
        type_stats = df_trips[df_trips[ATTRI_NAME_LIST[1]] >= days_28].groupby([ATTRI_NAME_LIST[6]])[ATTRI_NAME_LIST[5]].count().reset_index()
        type_stats = dict(zip(type_stats.trip_type, type_stats.upload_id))
        for t in ['et', 'nt', 'ct', 'ft']:
            if t not in type_stats:
                type_trips[t] = 0
            else:
                type_trips[t] = type_stats[t]

        if sum(list(type_trips.values())) < 10:
            type_trips[ATTRI_NAME_LIST[7]] = '是'
        else:
            type_trips[ATTRI_NAME_LIST[7]] = '否'

        for t in ['et', 'nt', 'ct', 'ft']:
            if type_trips[t] > 200:
                type_trips[ATTRI_NAME_LIST[7]] = '是'
                break
            else:
                type_trips[ATTRI_NAME_LIST[8]] = '否'

        return (trip_hierarchy, type_trips)


