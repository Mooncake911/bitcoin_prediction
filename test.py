from stockstats import StockDataFrame
import requests
import json
import pandas as pd

pd.options.display.expand_frame_repr = False

columns = ['time', 'high', 'low', 'open', 'volumefrom', 'volumeto', 'close', 'conversionType', 'conversionSymbol']
df = pd.DataFrame(columns=columns)

# Вставьте свой API ключ
API_KEY = "ecea075dff079a0f94479f7c7a0c554495873b48923e33363aa4aca513367370"
params = {'fsym': 'BTC', 'tsym': 'USD', 'limit': 2000, 'api_key': API_KEY}

# Сформируйте URL для запроса
url = 'https://min-api.cryptocompare.com/data/v2/histohour'
# Выполните запрос к API и получите ответ
response = requests.get(url, params=params)

# Обработайте ответ и извлеките значения скользящих средних
data = json.loads(response.text)
for quote in data['Data']['Data']:
    df = df._append(quote, ignore_index=True)

# Пре-подготовка дат-асета
df = df.drop(['conversionType', 'conversionSymbol', 'volumefrom'], axis=1)
df = df.rename(columns={'volumeto': 'volume'})

df = StockDataFrame.retype(df)

# https://github.com/jealous/stockstats/tree/master
df['macd'] = df.get('macd')  # calculate MACD
df['rsi_5'] = df.get('rsi_5')  # RSI - Relative Strength Index
df['stochrsi_5'] = df.get('stochrsi_5')  # Stochastic RSI
df['wt1'] = df.get('wt1')  # WT - Wave Trend
df['vr'] = df.get('vr')  # Volume Variation Index
df['wr'] = df.get('wr')  # Williams Overbought/Oversold index
df['trix'] = df.get('trix')  # TRIX - Triple Exponential Average
df['tema'] = df.get('tema')  # TEMA - Another Triple Exponential Average
df['cci'] = df.get('cci')  # CCI - Commodity Channel Index
df['kdjk'] = df.get('kdjk')  # Уровни поддержки

df.to_csv('bitcoin.csv', index=False)
