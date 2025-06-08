import plotly.graph_objects as go
from datetime import datetime
import os

def draw_price_chart(depart_data, return_data):
    def parse(data):
        dates = [datetime.strptime(d['date'], '%Y-%m-%d') for d in data if d["price"] > 0]
        prices = [d['price'] for d in data if d["price"] > 0]
        return dates, prices

    depart_dates, depart_prices = parse(depart_data)
    return_dates, return_prices = parse(return_data)

    fig = go.Figure()

    if depart_dates:
        fig.add_trace(go.Scatter(
            x=depart_dates,
            y=depart_prices,
            mode='lines+markers',
            name='출국 항공권',
            marker=dict(symbol='circle')
        ))

    if return_dates:
        fig.add_trace(go.Scatter(
            x=return_dates,
            y=return_prices,
            mode='lines+markers',
            name='귀국 항공권',
            marker=dict(symbol='square')
        ))

    fig.update_layout(
        title='📈 항공권 가격 추이 (KRW)',
        xaxis_title='날짜',
        yaxis_title='가격 (₩)',
        hovermode='x unified',
        template='plotly_white'
    )

    os.makedirs("static", exist_ok=True)
    fig.write_html("static/price_chart.html", include_plotlyjs='cdn')
