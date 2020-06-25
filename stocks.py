import yfinance as yf
import requests
import json
from twx.botapi import TelegramBot, InputFileInfo, InputFile
from random import choice
import matplotlib.pyplot as plt
from emoji import emojize
import credentials

############################################################
#						TELEGRAM STUFF
############################################################

BOT_TOKEN = credentials.bot_token

s = requests.Session()

response = s.get('https://api.telegram.org/bot{}/getUpdates'.format(BOT_TOKEN))
res = json.loads(response.text)
ids = [11033299]
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

############################################################
#						STOCKS STUFF
############################################################


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

# Plot the diagram
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

# Send message
evolution = round((bb['y'][-1]-sma['y'][-1])/(2*rstd['y'][-1])*100)
is_up_trend = bb['y'][-1]/bb['y'][-2] > 1
date = str(bb.index[-1]).split()[0]
message = emojize(":date:", use_aliases=True) + ' ' + date + '\n\n'
message += is_up_trend*emojize(":small_red_triangle:", use_aliases=True) + (not is_up_trend)*emojize(":small_red_triangle_down:", use_aliases=True) + ' Market cap is {}$, {}% away from the rolling mean\n\n'.format(bb['y'][-1], evolution)


if bb['y'][-1] <= bb['lower'][-1]:
    message += emojize(":chart_with_downwards_trend:", use_aliases=True) + choice(['Market is down. Buy!', 'Buy!!', 'Going doown. Buy!', 'Good time to buy!', 'Reaching lows today. Buy!'])
    send_image('bollinger.png', message)
elif bb['y'][-1] >= bb['upper'][-1]:
    message += emojize(":chart_with_upwards_trend:", use_aliases=True) + ' ' + choice(['Sell!', 'The market is up. Good time to sell.', 'Going up. Sell'])
    send_image('bollinger.png', message)
elif abs(bb['y'][-1]/bb['y'][-2] - 1) > 0.05:
    send_image('bollinger.png', message)
else:
    send_broadcast(message)