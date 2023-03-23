from flask import Flask, jsonify
import ccxt
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
@app.route('/tradingView/v1', methods=['POST'])
def handle_webhook():
    if request.method == 'POST':
        # TradingView에서 보낸 JSON 데이터를 파싱합니다.
        data = request.get_json()

        # 파싱된 데이터에서 필요한 정보를 추출합니다.
        symbol = data['symbol']
        strategy = data['strategy']
        signal = data['signal']

        # 추출한 정보를 사용하여 필요한 작업을 수행합니다.
        message = f"New signal from {symbol} ({strategy}): {signal}"
        print(message)
        # TradingView 알림(alert)을 Gmail로 보내기
        send_email('New signal from TradingView', message, 'youngsoo.j@gmail.com')

@app.route('/price', methods=['GET'])
def get_price():
    # 현재가 조회
    ticker = binance.fetch_ticker('BTCUSDT')
    price = ticker['last']

    # TradingView 알림(alert)을 Gmail로 보내기
    send_email('New signal from TradingView', 'New signal detected!', 'youngsoo.j@gmail.com')
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


def send_email(subject, body, to):
    # 이메일 설정
    email = os.environ.get('mail')  # 발신자 Gmail 계정 이메일 주소
    password = os.environ.get('mail_pwd')  # 발신자 Gmail 계정 비밀번호

    # 이메일 서버 설정
    smtp_server = 'smtp.gmail.com'  # Gmail SMTP 서버
    smtp_port = 587  # Gmail SMTP 서버 포트 번호

    # 이메일 생성
    msg = MIMEMultipart()
    msg['From'] = email
    msg['To'] = to
    msg['Subject'] = subject
    msg.attach(MIMEText(body, 'plain'))

    # 이메일 보내기
    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.ehlo()
        server.starttls()
        server.login(email, password)
        server.sendmail(email, to, msg.as_string())



if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
