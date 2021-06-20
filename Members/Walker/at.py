import time
import datetime
from datetime import timedelta
import ccxt 
import pandas as pd
import requests

binance = ccxt.binance(config={'apiKey': api_key, 'secret': secret,
                        'enableRateLimit': True,'options': {'defaultType': 'future'}})

benefit = 0.01
leverage = 15
k = 0.5
amount = 27000
loss_limit = -0.2

buy_price = 0
cnt = 0
res = 1

def post_message(token, channel, text):
    response = requests.post("https://slack.com/api/chat.postMessage",
        headers={"Authorization": "Bearer "+token},
        data={"channel": channel,"text": text}
    )

def init():
    today =datetime.datetime.now()
    yesterday = today - datetime.timedelta(1)
    print()
    post_message(myToken,"#gg", "[" + str(yesterday.strftime("%Y-%m-%d")) + "] 누적 수익률 : " 
                    + str(round(res*100,1)) + "%, 거래 횟수 : " + str(cnt))
    post_message(myToken,"#gg", "=============================================================")

print("ready..")
post_message(myToken,"#gg", "ready..")
while True :
    if datetime.datetime.now().second == 1 :
        print("start!!")
        post_message(myToken,"#gg", "start!!")
        break
    time.sleep(1)

while True :

    print("while 시작!!")
    btc = binance.fetch_ticker("BTT/USDT")
    current_price = float(btc['last'])

    if buy_price == 0 :
        print("buy_price == 0")

        btt = binance.fetch_ohlcv(symbol="BTT/USDT", timeframe='1m', since=None, limit=2)
        df = pd.DataFrame(btt, columns=['datetime', 'open', 'high', 'low', 'close', 'volume'])
        df['datetime'] = pd.to_datetime(df['datetime'], unit='ms') + timedelta(hours=9)
        target_price = float(df.iloc[0]['close'] + (df.iloc[0]['high'] - df.iloc[0]['low']) * k) 

        print("target_price : " + str(target_price))
        print("current_price : " + str(current_price))

        if target_price < current_price:
            print("포지션 진입 준비")
            order = binance.create_market_buy_order(symbol="BTT/USDT", amount=amount,)
            
            buy_price = 0
            balance = binance.fetch_balance()
            positions = balance['info']['positions']
            for position in positions:
                if position["symbol"] == "BTTUSDT":
                    buy_price = float(position["entryPrice"])
            
            if buy_price != 0 :
                print("포지션 진입 성공")
                post_message(myToken,"#gg", "[BTT/USDT][롱] " + str(buy_price) + " 진입")
    
    else :
        
        ror = (current_price - buy_price) / buy_price * leverage
           
        if ror <= loss_limit :
            print("warnning!!")
            order = binance.create_market_sell_order(symbol="BTT/USDT", amount=amount,)
            
            while(True) :
                chk_posion = 0
                balance = binance.fetch_balance()
                positions = balance['info']['positions']
                for position in positions:
                    if position["symbol"] == "BTTUSDT":
                        chk_posion = float(position["entryPrice"])
                
                if chk_posion == 0:
                    break

                print("포지션 정리 실패")
                order = binance.create_market_sell_order(symbol="BTT/USDT", amount=amount,)
                time.sleep(1)
            
            print("Warnning 정리 완료")
            post_message(myToken,"#gg", "[Warnning][BTT/USDT][롱] " + str(current_price) + " 정리 (실현 이익 : " 
                                + str(round(ror*100,1)) + "%, 누적 이익 : " + str(round(res*100, 1)) + "%)")

        else:
            if  ror >= benefit :
                
                order = binance.create_market_sell_order(symbol="BTT/USDT", amount=amount,)
                while(True) :
                    chk_posion = 0
                    balance = binance.fetch_balance()
                    positions = balance['info']['positions']
                    for position in positions:
                        if position["symbol"] == "BTTUSDT":
                            chk_posion = float(position["entryPrice"])
                    
                    if chk_posion == 0:
                        break

                    print("포지션 정리 실패")
                    order = binance.create_market_sell_order(symbol="BTT/USDT", amount=amount,)
                    time.sleep(1)
                print("포지션 정리 완료")

                cnt = cnt + 1
                res = res + ror
                buy_price = 0           
                
                post_message(myToken,"#gg", "[BTT/USDT][롱] " + str(current_price) + " 정리 (실현 이익 : " 
                                    + str(round(ror*100,1)) + "%, 누적 이익 : " + str(round(res*100, 1)) + "%)")
    
    print("1minute wait..")
    while True :
        if datetime.datetime.now().second == 1 :
            break
        time.sleep(1)
    
    if datetime.datetime.now().hour == 7 :
        print("init")
        init()
        res = 1
        cnt = 0
    