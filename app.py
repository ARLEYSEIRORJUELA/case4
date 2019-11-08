import os
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import dash_table

my_passwd = os.environ.get('DB_USER_PASSWORD')import pandas as pd

from sqlalchemy import create_engine

engine = create_engine('postgresql://strategy_user:my_passwd@nps-demo-instance.c5tqrqfogffp.us-east-2.rds.amazonaws.com/strategy')
df = pd.read_sql("SELECT * from trades", engine.connect(), parse_dates=['Entrytime'])

df['YearMonth']= df['Entrytime'].dt.year.astype(str) + '-' + df['Entrytime'].dt.month.astype(str)

grafico2 = df[(df['Tradetype'] == 'Short')]
grafico3 = df[(df['Tradetype'] == 'Long')]

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/uditagarwal/pen/oNvwKNP.css', 'https://codepen.io/uditagarwal/pen/YzKbqyV.css'])

def filter_df(dff,exchange, margin, start_date, end_date):
    mask1 = (dff['Exchange'] == exchange)
    mask2 = (dff['Margin'] == int(margin))
    mask3 = ((dff['Entrytime'] > start_date) & (dff['Entrytime'] <= end_date))
    # print(dff[(mask1 & mask2 & mask3)])
    return dff[(mask1 & mask2 & mask3)]


def filter_short(dff):
    mask4 = ((dff['Tradetype'] == 'Short'))
    # print(dff[(mask1 & mask2 & mask3)])
    return dff[(mask4)]


def filter_long(dff):
    mask5 = ((dff['Tradetype'] == 'Long'))
    # print(dff[(mask1 & mask2 & mask3)])
    return dff[(mask5)]

def calc_returns_over_month(dff):
    out = []
    dff['YearMonth']= dff['Entrytime'].dt.year.astype(str) + '-' + dff['Entrytime'].dt.month.astype(str)
    for name, group in dff.groupby('YearMonth'):
        exit_balance = group.head(1)['Exitbalance'].values[0]
        entry_balance = group.tail(1)['Entrybalance'].values[0]
        monthly_return = (exit_balance*100 / entry_balance)-100
        out.append({
            'month': name,
            'entry': entry_balance,
            'exit': exit_balance,
            'monthly_return': monthly_return
        })
    return out


def calc_btc_returns(dff):
    btc_start_value = dff.tail(1)['BTCPrice'].values[0]
    btc_end_value = dff.head(1)['BTCPrice'].values[0]
    btc_returns = (btc_end_value * 100/ btc_start_value)-100
    return btc_returns

def calc_strat_returns(dff):
    start_value = dff.tail(1)['Exitbalance'].values[0]
    end_value = dff.head(1)['Entrybalance'].values[0]
    returns = (end_value * 100/ start_value)-100
    return returns


def load_bar_trades_plot(df_short, df_long):
       
    data = []
	
    data.append[
		go.Bar(name='Short', x=df_short['YearMonth'], y=df_short['Pnl']),
		go.Bar(name='Long', x=df_long['YearMonth'], y=df_long['Pnl'])
    ]
    return data


app.layout = html.Div(children=[
    html.Div(
            children=[
                html.H2(children="Arley Seir - Bitcoin Leveraged Trading Backtest Analysis", className='h2-title'),
            ],
            className='study-browser-banner row'
    ),
    html.Div(
        className="row app-body",
        children=[
            html.Div(
                className="twelve columns card",
                children=[
                    html.Div(
                        className="padding row",
                        children=[
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Exchange",),
                                    dcc.RadioItems(
                                        id="exchange-select",
                                        options=[
                                            {'label': label, 'value': label} for label in df['Exchange'].unique()
                                        ],
                                        value='Bitmex',
                                        labelStyle={'display': 'inline-block'}
                                    )
                                ]
                            ),
                            # Leverage Selector
                            html.Div(
                                className="two columns card",
                                children=[
                                    html.H6("Select Leverage"),
                                    dcc.RadioItems(
                                        id="leverage-select",
                                        options=[
                                            {'label': str(label), 'value': int(label)} for label in df['Margin'].unique()
                                        ],
                                        value=1,
                                        labelStyle={'display': 'inline-block'}
                                    ),
                                ]
                            ),
                            html.Div(
                                className="three columns card",
                                children=[
                                    html.H6("Select a Date Range"),
                                    dcc.DatePickerRange(
                                        id="date-range",
                                        display_format="MMM YY",
                                        start_date=df['Entrytime'].min(),
                                        end_date=df['Entrytime'].max()
                                    ),
                                ]
                            ),
                            html.Div(
                                id="strat-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-returns", className="indicator_value"),
                                    html.P('Strategy Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="market-returns-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="market-returns", className="indicator_value"),
                                    html.P('Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                            html.Div(
                                id="strat-vs-market-div",
                                className="two columns indicator pretty_container",
                                children=[
                                    html.P(id="strat-vs-market", className="indicator_value"),
                                    html.P('Strategy vs. Market Returns', className="twelve columns indicator_text"),
                                ]
                            ),
                        ]
                )
        ]),
        html.Div(
            className="twelve columns card",
            children=[
                dcc.Graph(
                    id="monthly-chart",
                    figure={
                        'data': []
                    }
                )
            ]
        ), 
        
        html.Div(
                className="padding row",
                children=[
                    html.Div(
                        className="six columns card",
                        children=[
                            dash_table.DataTable(
                                id='table',
                                columns=[
                                    {'name': 'Number', 'id': 'Number'},
                                    {'name': 'Tradetype', 'id': 'Tradetype'},
                                    {'name': 'Exposure', 'id': 'Exposure'},
                                    {'name': 'Entrybalance', 'id': 'Entrybalance'},
                                    {'name': 'Exitbalance', 'id': 'Exitbalance'},
                                    {'name': 'Pnl', 'id': 'Pnl'},
                                ],
                                style_cell={'width': '50px'},
                                style_table={
                                    'maxHeight': '450px',
                                    'overflowY': 'scroll'
                                },
                            )
                        ]
                    ),
                    dcc.Graph(
                        id="pnl-types",
                        className="six columns card",
                        figure={}
                    )
                    
                ]
            ),html.Div(
                className="padding row",
                children=[
                    dcc.Graph(
                        id="daily-btc",
                        className="six columns card",
                        figure={}
                    ),
                    dcc.Graph(
                        id="balance",
                        className="six columns card",
                        figure={}
                    )
                ]
            )
        ]
    )        
])

@app.callback(
    [
        dash.dependencies.Output('date-range', 'start_date'),
        dash.dependencies.Output('date-range', 'end_date'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
    )
)
def update_dates_due_to_exchange_select(value):
    df_aux = df[df['Exchange']==value]
    #print(df_aux['Entrytime'].min(),df_aux['Entrytime'].max())
    return df_aux['Entrytime'].min(),df_aux['Entrytime'].max()


@app.callback(
    dash.dependencies.Output('monthly-chart', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),

    )
)
def update_monthly(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return {
        'data': [
            go.Candlestick(
                open=[each['entry'] for each in data],
                close=[each['exit'] for each in data],
                x=[each['month'] for each in data],
                low=[each['entry'] for each in data],
                high=[each['exit'] for each in data]
            )
        ],
        'layout': {
            'title': 'Overview of Monthly performance'
        }
    }


@app.callback(
    [
        dash.dependencies.Output('market-returns', 'children'),
        dash.dependencies.Output('strat-returns', 'children'),
        dash.dependencies.Output('strat-vs-market', 'children'),
    ],
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),

    )
)
def update_indicators(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    data = calc_returns_over_month(dff)
    btc_returns = calc_btc_returns(dff)
    strat_returns = calc_strat_returns(dff)
    strat_vs_market = strat_returns - btc_returns

    return f'{btc_returns:0.2f}%', f'{strat_returns:0.2f}%', f'{strat_vs_market:0.2f}%'


@app.callback(
    dash.dependencies.Output('table', 'data'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_table(exchange, leverage, start_date, end_date):
    dff = filter_df(df, exchange, leverage, start_date, end_date)
    return dff.to_dict('records')
    
@app.callback(
    dash.dependencies.Output('pnl-types', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_bar(exchange, leverage, start_date, end_date):
	dff = filter_df(df, exchange, leverage, start_date, end_date)
	dff2 = filter_short(dff)
	dff3 = filter_long(dff)
	
	return {
			'data': [
				go.Bar(name='Short', x=dff2['YearMonth'], y=dff2['Pnl']),
				go.Bar(name='Long', x=dff3['YearMonth'], y=dff3['Pnl'])
			],
			'layout': {
				'barmode': 'group',
				'title': 'PnL vs Trade type',
				'plot_bgcolor' : 'rgba(0,0,0,0)',
				'height': 500
				
			}
	}


@app.callback(
    dash.dependencies.Output('daily-btc', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_btc(exchange, leverage, start_date, end_date):
	dff = filter_df(df, exchange, leverage, start_date, end_date)
	
	return {
			'data': [
				go.Scatter(x=dff['YearMonth'], y=dff['BTCPrice'])
			],
			'layout': {
				'title': 'Daily BTC Price',
				'height': 500
				
			}
	}      

@app.callback(
    dash.dependencies.Output('balance', 'figure'),
    (
        dash.dependencies.Input('exchange-select', 'value'),
        dash.dependencies.Input('leverage-select', 'value'),
        dash.dependencies.Input('date-range', 'start_date'),
        dash.dependencies.Input('date-range', 'end_date'),
    )
)
def update_portfolio(exchange, leverage, start_date, end_date):
	dff = filter_df(df, exchange, leverage, start_date, end_date)
	
	return {
			'data': [
				go.Scatter(x=dff['YearMonth'], y=(dff['Exitbalance'] + ((dff['Exitbalance']*dff['Pnl'])/100)))
			],
			'layout': {
				'title': 'Balance Over Time',
				'height': 500
				
			}
	}      
    
    

if __name__ == "__main__":
    app.run_server(debug=True)
