from dash import Dash, html, dcc, callback, Output, Input
import numpy as np
import plotly.express as px
import pandas as pd

def check_if_notice_after_submit(df:pd.DataFrame):
    valids = []
    for s, n in zip(df["Date of Submit"], df["Date of Notice"]):
        if not pd.isna(s):
            valid = n > s
        else:
            valid = True
        valids.append(valid)
    return np.array(valids)
    
def load_csv():
    df = pd.read_csv('https://docs.google.com/spreadsheets/d/1dPY1LQAMbR60w246kQV6Iwi4UqmZKgIa4iAlP3wppXo/export?format=csv&gid=995531617')
    df = df.rename(columns={
        "What is your order number?": "order_number_str",
        "What is the Model you got?": "model",
        "4G Included?": "4G",
        "CM4 Included?": "CM4",
        "What is the color?": "color",
        "When the shipment notice was sent?":"_notice",
        "When you submit your order?": "_submit",
    })

    df = df.dropna(subset=["_notice"])
    # df["_notice"] = [x[:-4] + "20"+x[-2:] for x in df["_notice"]]
    df["Date of Submit"] = pd.to_datetime(df["_submit"], format='%m/%d/%Y',errors="coerce")

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

    for name, _df in df.groupby("Order Detail"):
        _df.sort_values("Order Number")
        

    df = df[[
        "Order Number",
        "Date of Submit",
        "Date of Notice",
        "Order Detail",
    ]]
    return df

df = load_csv()
valids = check_if_notice_after_submit(df)
if np.sum(~valids) > 0:
    df["Order Detail"] = [x if valid else "_maybe error_" for x, valid in zip(df["Order Detail"], valids)]
df = df.sort_values("Order Detail")

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
    fig = px.scatter(df, x="Date of Notice", y="Order Number", color="Order Detail",
                     hover_name="Order Number", hover_data=["Date of Submit", "Date of Notice", "Order Detail"])
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
    print("start")
    app.run(debug=True)
