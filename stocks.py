import yfinance as yf
import requests
import json
from twx.botapi import TelegramBot, InputFileInfo, InputFile
import pandas as pd
import numpy as np
from datetime import datetime
from random import choice
import matplotlib.pyplot as plt
from emoji import emojize

##################
#   TELEGRAM STUFF #
##################

BOT_TOKEN = [YOUR_TOKEN]

s = requests.Session()

response = s.get('https://api.telegram.org/bot{}/getUpdates'.format(BOT_TOKEN))
res = json.loads(response.text)
ids = [] # Enter your keys here
for update in res['result']:
    ids.append(update['message']['chat']['id'])

ids = list(set(ids))


def send_broadcast(message):
    bot = TelegramBot(BOT_TOKEN)
    for chat_id in ids:
        bot.send_message(chat_id, message, parse_mode='Markdown')

import time     
def send_image(filename, message):
  bot = TelegramBot(BOT_TOKEN)
  for chat_id in ids:
    fp = open(filename, 'rb')
    file_info = InputFileInfo(filename, fp, 'image/png')
    photo = InputFile('photo', file_info)
    print(chat_id)
    bot.send_photo(chat_id=chat_id, photo=photo, caption=message)
    fp.close()

################
#   STOCKS STUFF #
################


equity = yf.Ticker("VHGEX")

df = equity.history(period='2mo')[['Close']]
df.reset_index(level=0, inplace=True)
df.columns = ['ds', 'y']
df = df.set_index('ds')

# calculate Simple Moving Average with 20 days window
sma = df.rolling(window=20).mean()
exp = df.y.ewm(span=20, adjust=False).mean()

# calculate the standar deviation
rstd = df.rolling(window=20).std()

upper_band = sma + 2 * rstd
upper_band = upper_band.rename(columns={'y': 'upper'})
lower_band = sma - 2 * rstd
lower_band = lower_band.rename(columns={'y': 'lower'})

# Making of plot
bb = df.join(upper_band).join(lower_band)
bb = bb.dropna()
plt.style.use('dark_background')
plt.figure(figsize=(10,10))
plt.plot(bb['upper'], color='#ADCCFF', alpha=0.2, label='Bollinger Bands')
plt.plot(bb['lower'], color='#ADCCFF', alpha=0.2)
plt.plot(bb['y'], label='VHGEX')
plt.plot(sma, linestyle='--', alpha=0.7, label='Simple Moving Average')
plt.title('VHGEX Price and BB')
plt.legend(loc='best')
plt.fill_between(bb.index, bb['lower'], bb['upper'], color='#ADCCFF', alpha=0.2)

ax = plt.gca()
fig = plt.gcf()
fig.autofmt_xdate()

plt.ylabel('SMA and BB')
plt.grid()
plt.savefig('bollinger')

# Calculate evolution
evolution = round((bb['y'][-1]-sma['y'][-1])/(2*rstd['y'][-1])*100)

today = bb['y'][-1]
yesterday = bb['y'][-2]

percentage_increase = 100 * (today - yesterday) / yesterday
date = str(bb.index[-1]).split()[0]

# Message generation

# General stats
message = emojize(":date:", use_aliases=True) + ' ' + date + '\n'
message += (percentage_increase > 0)*emojize(":small_red_triangle:", use_aliases=True) + (percentage_increase < 0)*emojize(":small_red_triangle_down:", use_aliases=True)
message += '{}% | {}$\n\n'.format(round(percentage_increase,2), round(today, 2))

if evolution > 0:
  message += '{}% recommended *SELL* for added rentability'.format(evolution)
else:
  message += '{}% recommended *BUY* for added rentability'.format(-evolution)


# emojize(":chart_with_downwards_trend:", use_aliases=True)

if abs(percentage_increase) >= 0.5 or evolution >= 50:
    send_image('bollinger.png', message)
else:
    send_broadcast(message)
