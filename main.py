from dash import Dash, html, dcc, callback, Output, Input
import plotly.express as px
import pandas as pd

def load_csv():
    df = pd.read_csv('https://docs.google.com/spreadsheets/d/1dPY1LQAMbR60w246kQV6Iwi4UqmZKgIa4iAlP3wppXo/export?format=csv&gid=995531617')
    df = df.rename(columns={
        "What is your order number?": "order_number_str",
        "What is the Model you got?": "model",
        "4G Included?": "4G",
        "CM4 Included?": "CM4",
        "What is the color?": "color",
        "When the shipment notice was sent?":"_notice"
    })

    df = df.dropna(subset=["_notice"])
    # df["_notice"] = [x[:-4] + "20"+x[-2:] for x in df["_notice"]]
    df["Date of Notice"] = pd.to_datetime(df["_notice"], format='%m/%d/%Y',errors="coerce")
    df = df.dropna(subset=["Date of Notice"])

    def to_order_number(order_number_str:str):
        order_number_str = order_number_str.replace("x","0")
        order_number_str = order_number_str.replace("X","0")
        if order_number_str.isdecimal():
            return int(order_number_str)
        else:
            return pd.NA
        
    def to_order_pattern(model, inc_4G, inc_CM4, color):
        detail = model
        if inc_4G or inc_CM4:
            a = []
            if inc_4G:
                a += ["4G"]
            if inc_CM4:
                a += ["CM4"]
            detail = f"{detail}({','.join(a)})"
        return detail+","+color
    df["Order Detail"] = [to_order_pattern(x, y, z, w) for x, y, z, w in zip(df["model"], df["4G"]=="Yes", df["CM4"]=="Yes", df["color"])]
    df["Order Number"] = [to_order_number(x) for x in df["order_number_str"]]
    df = df.dropna(subset=["Order Number"])
    df = df[[
        "Order Number",
        "Date of Notice",
        "Order Detail",
    ]]

    df = df.sort_values("Order Detail")
    return df

app = Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1(children='uConsole Order Progress', style={'textAlign':'center'}),
    html.H3(
        children=html.A("Link to Source forum", href='https://forum.clockworkpi.com/t/highest-order-number-that-received-the-shipment-notice/10478', target="_blank"),
        style={'textAlign':'center'}
    ),
    dcc.Interval(
        id='interval-component',
        interval=3600*1000, # in milliseconds
        n_intervals=0
    ),
    dcc.Graph(id='graph-content')
])

@callback(
    Output('graph-content', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_graph(
    n,
):
    df = load_csv()
    fig = px.scatter(df, x="Date of Notice", y="Order Number", color="Order Detail")
    fig.update_traces(
        marker=dict(
            size=12,
            line=dict(width=2,
            color='DarkSlateGrey')
        ),
        selector=dict(mode='markers')
    )
    return fig

if __name__ == '__main__':
    app.run(debug=True)
