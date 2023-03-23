from flask import Flask, jsonify
import ccxt
import os
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()


app = Flask(__name__)
binance = ccxt.binance({
    'apiKey': os.environ.get('apiKey'),
    'secret': os.environ.get('secret'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future'
    }
})

def create_order():
    # 마진 20배로 BTCUSDT 선물 매수 주문
    order = binance.create_order(
        symbol='BTC/USDT',
        type='market',
        side='buy',
        amount=0.001,
        leverage=20
    )

    # take-profit 주문
    take_profit_order = binance.create_order(
        symbol='BTC/USDT',
        type='take_profit',
        side='sell',
        amount=0.001,
        price=60000,
        params={
            'stopPrice': 59000
        }
    )

    # stop-loss 주문
    stop_loss_order = binance.create_order(
        symbol='BTC/USDT',
        type='stop_loss',
        side='sell',
        amount=0.001,
        price=57000,
        params={
            'stopPrice': 57000
        }
    )

@app.route('/price', methods=['GET'])
def get_price():
    # 현재가 조회
    ticker = binance.fetch_ticker('BTCUSDT')
    price = ticker['last']
    return jsonify(price)

@app.route('/balance', methods=['GET'])
def get_balance():
    # 계좌 잔고 조회
    balance = binance.fetch_balance()
    # 잔액이 0이 아닌 자산만 출력
    for asset in balance['total']:
        if balance['total'][asset] != 0:
            print(f"{asset}: {balance['total'][asset]}")

    return jsonify(balance)

if __name__ == '__main__':
    app.run()
