# binance-bot


```
curl -X POST -H "Content-Type: application/json" -d '{"price": 123.45, "symbol": "AAPL", "strategy": "Moving Average Crossover", "signal": "buy"}' http://127.0.0.1/tradingView/v1

```


# cctx 

### example
https://github.com/ccxt/ccxt/tree/master/examples/py


# screen

### 세션 생성하기
screen -S [session name]

### 세션 나가기
Ctrl + a, d (컨트롤 누른채로 a와 d를 순서대로 누르면 됨)

### 세션 리스트 확인
screen -ls

### 세션 다시 연결하기
screen -r [session name]

#### 세션이 하나만 있는 경우
screen -r

### 세션 없애기 (세션 자체를 제거)
screen -X -S [session name] quit

