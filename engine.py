from math import sqrt
from numpy import concatenate
from matplotlib import pyplot
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LSTM
import numpy as np
import datetime
from pytz import timezone
import time
import queue
est = timezone('US/Eastern')


data = pd.read_csv("merged_data.csv")

datag = data[['Price', 'Sentiment']].groupby(data['Time']).mean()

values = datag['Price'].values.reshape(-1, 1)
sentiment = datag['Sentiment'].values.reshape(-1, 1)
values = values.astype('float32')
sentiment = sentiment.astype('float32')
scaler = MinMaxScaler(feature_range=(0, 1))
scaled = scaler.fit_transform(values)

train_size = int(len(scaled) * 0.7)
test_size = len(scaled) - train_size
train, test = scaled[0:train_size, :], scaled[train_size:len(scaled), :]
print(len(train), len(test))
split = train_size


def create_dataset(dataset, look_back, sentiment, sent=False):
    dataX, dataY = [], []
    for i in range(len(dataset) - look_back):
        if i >= look_back:
            a = dataset[i - look_back:i + 1, 0]
            a = a.tolist()
            if sent == True:
                a.append(sentiment[i].tolist()[0])
            dataX.append(a)
            dataY.append(dataset[i + look_back, 0])
    # print(len(dataY))
    return np.array(dataX), np.array(dataY)


look_back = 2
trainX, trainY = create_dataset(train, look_back, sentiment[0:train_size], sent=True)
testX, testY = create_dataset(test, look_back, sentiment[train_size:len(scaled)], sent=True)

trainX = np.reshape(trainX, (trainX.shape[0], 1, trainX.shape[1]))
testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))

model = Sequential()
model.add(LSTM(100, input_shape=(trainX.shape[1], trainX.shape[2]), return_sequences=True))
model.add(LSTM(100))
model.add(Dense(1))
model.compile(loss='mae', optimizer='adam')
history = model.fit(trainX, trainY, epochs=300, batch_size=100, validation_data=(testX, testY), verbose=0,
                    shuffle=False)

yhat = model.predict(testX)

yhat_inverse_sent = scaler.inverse_transform(yhat.reshape(-1, 1))
testY_inverse_sent = scaler.inverse_transform(testY.reshape(-1, 1))

rmse_sent = sqrt(mean_squared_error(testY_inverse_sent, yhat_inverse_sent))
print('Test RMSE: %.3f' % rmse_sent)

true_q = queue.Queue()
pred_q = queue.Queue()


def process_data(in_data):
    out_data = []
    for line in in_data:
        out_data.append(float(line.split(',')[0]))
    return np.array(out_data).reshape(-1, 1)


prev = 15000
threshold = 0.05
while True:
    btc = open('live_bitcoin.csv', 'r')
    sent = open('live_tweet.csv', 'r')
    bit_data = btc.readlines()
    sent_data = sent.readlines()
    bit_data = process_data(bit_data[len(bit_data) - 5:])
    sent_data = process_data(sent_data[len(sent_data) - 5:])
    live = scaler.transform(bit_data)
    testX, testY = create_dataset(live, 2, sent_data, sent=True)
    testX = np.reshape(testX, (testX.shape[0], 1, testX.shape[1]))
    yhat = model.predict(testX)
    yhat_inverse = scaler.inverse_transform(yhat.reshape(-1, 1))
    true_q.put(bit_data[4])
    pred_q.put(yhat_inverse[0])
    val = 100 * ((yhat_inverse[0][0] - prev) / prev)
    if val > threshold:
        decision = 'Buy!!!'
    elif val < -threshold:
        decision = 'Sell!!!'
    else:
        decision = ''
    print(decision)
    prev = yhat_inverse[0][0]

    time.sleep(60)
