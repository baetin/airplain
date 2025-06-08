# pip install flask selenium matplotlib requests  터미널에서 실행
from flask import Flask, render_template, request
import os, json, time, requests
from concurrent.futures import ThreadPoolExecutor
from crawler.kayak_driver import run_single_flight_check
from utils.date_utils import generate_date_range
from visualize.chart import draw_price_chart

app = Flask(__name__)
executor = ThreadPoolExecutor(max_workers=5)

# 1. 실시간 환율 가져오는 함수
def get_usd_to_krw_rate():
    try:
        res = requests.get("https://api.exchangerate.host/latest?base=USD&symbols=KRW", timeout=5)
        res.raise_for_status()
        return res.json()["rates"]["KRW"]
    except Exception as e:
        print("⚠️ 환율 API 실패:", e)
        return 1350  # 기본 환율

# 2. 가격 필터 (Jinja 템플릿에서 ₩ 표시)
@app.template_filter('won')
def won_format(value):
    try:
        return f"₩{int(float(value)):,}"
    except:
        return value

# 3. 가격 크롤링 후 KRW 환산 처리
def crawl_wrapper(args):
    start, end, date, exchange_rate = args
    print(f"📅 {start} → {end} / {date} 크롤링 중...")
    data = run_single_flight_check(start, end, date)

    usd_price = data["price"]
    krw_price = int(usd_price * exchange_rate)

    return {
        "date": date.strftime("%Y-%m-%d"),
        "price": krw_price,
        "airline": data["airline"]
    }

# 4. 메인 페이지
@app.route('/')
def index():
    return render_template('index.html')

# 5. 결과 페이지
@app.route('/result', methods=['POST'])
def result():
    start_time = time.time()

    start_area = request.form['start']
    end_area = request.form['end']
    depart_base = request.form['depart_date']
    return_base = request.form['return_date']

    depart_dates = generate_date_range(depart_base, days=7)
    return_dates = generate_date_range(return_base, days=7)

    exchange_rate = get_usd_to_krw_rate()

    depart_args = [(start_area, end_area, d, exchange_rate) for d in depart_dates]
    return_args = [(end_area, start_area, d, exchange_rate) for d in return_dates]

    results_depart = list(executor.map(crawl_wrapper, depart_args))
    results_return = list(executor.map(crawl_wrapper, return_args))

    os.makedirs("data", exist_ok=True)
    with open("data/flight_depart.json", "w", encoding="utf-8") as f:
        json.dump(results_depart, f, ensure_ascii=False, indent=2)
    with open("data/flight_return.json", "w", encoding="utf-8") as f:
        json.dump(results_return, f, ensure_ascii=False, indent=2)

    draw_price_chart(results_depart, results_return)

    elapsed_time = round(time.time() - start_time, 2)

    valid_depart = [r for r in results_depart if r["price"] > 0]
    valid_return = [r for r in results_return if r["price"] > 0]

    best_price = 0
    best_date = "-"
    average_price = 0
    best_return_price = 0
    best_return_date = "-"
    average_return_price = 0

    # 출국
    if valid_depart:
        best_depart = min(valid_depart, key=lambda x: x["price"])
        best_price = best_depart["price"]
        best_date = best_depart["date"]

    # 귀국
    if valid_return:
        best_return = min(valid_return, key=lambda x: x["price"])
        best_return_price = best_return["price"]
        best_return_date = best_return["date"]

    # 평균
    if valid_depart or valid_return:
        depart_prices = [r["price"] for r in valid_depart]
        return_prices = [r["price"] for r in valid_return]

        if depart_prices:
            average_price = round(sum(depart_prices) / len(depart_prices))
        if return_prices:
            average_return_price = round(sum(return_prices) / len(return_prices))

    return render_template(
        "result.html",
        results_depart=results_depart,
        results_return=results_return,
        best_price=best_price,
        best_date=best_date,
        average_price=average_price,
        best_return_price=best_return_price,
        best_return_date=best_return_date,
        average_return_price=average_return_price,
        elapsed_time=elapsed_time,
        start=start_area,
        end=end_area
    )

@app.route('/price-chart-preview')
def chart_preview():
    with open("data/flight_depart.json", encoding="utf-8") as f:
        depart_data = json.load(f)
    with open("data/flight_return.json", encoding="utf-8") as f:
        return_data = json.load(f)

    return render_template("price_chart.html", depart_data=depart_data, return_data=return_data)

if __name__ == '__main__':
    app.run(debug=True)
