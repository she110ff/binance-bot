from flask import Flask, jsonify, request, abort
import ccxt
import os
import smtplib
import pprint
from builtins import int
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

# .env 파일에서 환경 변수를 로드합니다.
load_dotenv()
mode = os.environ.get('mode')
userKey = os.environ.get('userKey')
pprint.pprint(mode)

app = Flask(__name__)
exchange = ccxt.binanceusdm({
    'apiKey': os.environ.get('apiKey') if mode == 'prod' else os.environ.get('testApiKey'),
    'secret': os.environ.get('secret') if mode == 'prod' else os.environ.get('testSecret'),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'future',
    }
})
if mode != 'prod':
    exchange.set_sandbox_mode(True)

_symbol = 'BTC/USDT'


# 미들웨어 함수 작성
@app.before_request
def before_request():
    # 인증된 사용자인지 확인하기
    if 'user_id' in request.view_args:
        user_id = request.view_args['user_id']
        if user_id != userKey:  # 인증된 사용자의 user_id
            abort(403, 'Forbidden')
    else:
        abort(403, 'Forbidden')

def _get_position():
    # 포지션 조회
    balance = exchange.fetch_balance()
    positions = balance['info']['positions']

    for position in positions:
        if position["symbol"] == _symbol:
            pprint.pprint(position)
    return position


def _get_balance():
    # 계좌 잔고 조회
    balance = exchange.fetch_balance()
    return balance


def _create_order():
    # 마진 20배로 BTCUSDT 선물 매수 주문
    symbol = _symbol
    side = 'buy'
    inverted_side = 'sell' if side == 'buy' else 'buy'
    amount = 1
    price = None
    ticker = exchange.fetch_ticker(_symbol)
    cprice = ticker['last']
    stopLossPrice = int(cprice - (cprice * 0.01))
    takeProfitPrice = int(cprice + (cprice * 0.1))

    message = f"order> symbol: {symbol}, side:{side}, amount:{amount}, \
    cprice:{cprice}, stopLossPrice:{stopLossPrice}, takeProfitPrice:{takeProfitPrice}"
    pprint.pprint(message)
    params = {} if mode == 'prod' else {'test': True}
    order = exchange.create_order(symbol, 'MARKET', side, amount, params)
    pprint.pprint(order)

    stopLossParams = {'stopPrice': stopLossPrice}
    stopLossOrder = exchange.create_order(symbol, 'STOP_MARKET', inverted_side, amount, price, stopLossParams)
    pprint.pprint(stopLossOrder)

    takeProfitParams = {'stopPrice': takeProfitPrice}
    takeProfitOrder = exchange.create_order(symbol, 'TAKE_PROFIT_MARKET', inverted_side, amount, price, takeProfitParams)
    pprint.pprint(takeProfitOrder)
    return 'order'



@app.route('/tradingView/v1/<user_id>', methods=['POST'])
def handle_webhook(user_id):
    if request.method == 'POST':
        # TradingView에서 보낸 JSON 데이터를 파싱합니다.
        data = request.get_json()
        pprint.pprint(data)
        # 파싱된 데이터에서 필요한 정보를 추출합니다.
        symbol = data['symbol']
        strategy = data['strategy']
        signal = data['signal']

        # 추출한 정보를 사용하여 필요한 작업을 수행합니다.
        message = f"New signal from {symbol} ({strategy}): {signal}"
        pprint.pprint(message)

        _create_order()
        # TradingView 알림(alert)을 Gmail로 보내기
        send_email('New signal from TradingView', message, 'youngsoo.j@gmail.com')
        return '{"ret":"success"}'


@app.route('/price/<user_id>', methods=['GET'])
def get_price(user_id):
    # 현재가 조회
    ticker = exchange.fetch_ticker(_symbol)
    price = ticker['last']

    # TradingView 알림(alert)을 Gmail로 보내기
    send_email('New signal from TradingView', 'New signal detected!', 'youngsoo.j@gmail.com')
    return jsonify(price)


@app.route('/position/<user_id>', methods=['GET'])
def get_position(user_id):
    position = _get_position()
    return jsonify(position)


@app.route('/balance/<user_id>', methods=['GET'])
def get_balance(user_id):
    # 계좌 잔고 조회
    balance = _get_balance()
    # 잔액이 0이 아닌 자산만 출력
    for asset in balance['total']:
        if balance['total'][asset] != 0:
            pprint.pprint(f"{asset}: {balance['total'][asset]}")

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
