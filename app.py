import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

# Caricamento dati
# Usa il percorso relativo per funzionare anche su Render
import os
data_path = os.path.join(os.path.dirname(__file__), 'domande_fisio.csv')
df = pd.read_csv(data_path, sep=';')

# Prepara i dati
summary = df.groupby(['Macro-Area', 'Argomento Principale']).size().reset_index(name='Conteggio')
totali_per_area = summary.groupby('Macro-Area')['Conteggio'].sum().sort_values(ascending=False)
ordine_macro_aree = totali_per_area.index.tolist()

# Crea l'app Dash
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Layout dell'app
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("Distribuzione Domande d'Esame", className="text-center mb-4"),
            html.P("Clicca su una sezione della barra per vedere le domande", 
                   className="text-center text-muted")
        ])
    ]),
    
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='bar-chart', style={'height': '600px'})
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div(id='selected-info', className="mt-3 p-3 bg-light rounded")
        ], width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.Div(id='questions-list', className="mt-3")
        ], width=12)
    ])
], fluid=True)

# Callback per creare il grafico iniziale
@callback(
    Output('bar-chart', 'figure'),
    Input('bar-chart', 'id')
)
def create_chart(_):
    # Aggiungi customdata al summary per passare l'argomento
    summary_with_custom = summary.copy()
    summary_with_custom['custom_argomento'] = summary_with_custom['Argomento Principale']
    
    fig = px.bar(
        summary_with_custom, 
        x='Conteggio', 
        y='Macro-Area', 
        color='Argomento Principale',
        pattern_shape='Argomento Principale',
        orientation='h',
        category_orders={'Macro-Area': ordine_macro_aree},
        height=600,
        text_auto=True,
        custom_data=['custom_argomento']  # Passa l'argomento come customdata
    )
    
    fig.update_layout(
        xaxis_title="Numero di Domande (Frequenza Assoluta)",
        yaxis_title="Macro-Area",
        legend_title_text='Sottoargomenti',
        font=dict(size=12),
        bargap=0.2,
        hovermode='closest'
    )
    
    fig.update_traces(
        marker_line_color='black', 
        marker_line_width=1,
        hovertemplate='<b>%{y}</b><br>%{fullData.name}<br>Domande: %{x}<br><i>Clicca per dettagli</i><extra></extra>'
    )
    
    return fig

# Callback per gestire il click e mostrare le domande
@callback(
    [Output('selected-info', 'children'),
     Output('questions-list', 'children')],
    Input('bar-chart', 'clickData')
)
def display_questions(clickData):
    if clickData is None:
        return (
            html.P("Nessuna selezione. Clicca su una barra per vedere le domande.", 
                   className="text-muted"),
            html.Div()
        )
    
    # Estrai informazioni dal click
    point = clickData['points'][0]
    macro_area = point['y']
    
    # Estrai l'argomento dal legendgroup o customdata
    if 'legendgroup' in point:
        argomento = point['legendgroup']
    elif 'customdata' in point and point['customdata']:
        argomento = point['customdata'][0]
    else:
        # Fallback: cerca il trace name nella curveNumber
        trace_index = point['curveNumber']
        argomento = clickData['points'][0].get('label', 'Sconosciuto')
    
    conteggio = point['x']
    
    # Filtra le domande
    domande_filtrate = df[
        (df['Macro-Area'] == macro_area) & 
        (df['Argomento Principale'] == argomento)
    ]
    
    # Info selezione
    info = dbc.Alert([
        html.H5(f"📚 {argomento}", className="alert-heading"),
        html.Hr(),
        html.P([
            html.Strong("Macro-Area: "), macro_area, html.Br(),
            html.Strong("Numero domande: "), str(conteggio)
        ])
    ], color="info")
    
    # Lista domande
    domande_cards = []
    for idx, row in domande_filtrate.iterrows():
        card = dbc.Card([
            dbc.CardBody([
                html.P(row['Domanda Specifica'], className="mb-0")
            ])
        ], className="mb-2")
        domande_cards.append(card)
    
    questions_div = html.Div([
        html.H4(f"Elenco Domande ({len(domande_filtrate)}):", className="mb-3"),
        html.Div(domande_cards)
    ])
    
    return info, questions_div

# Avvia l'app
if __name__ == '__main__':
    # Per sviluppo locale
    app.run(debug=True)

# Per Render.com
server = app.server