import pandas as pd
import json
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# CARGAR Y PREPARAR DATOS
# Cargar GeoJSON (generado localmente con prepare_geojson.py)
with open("MUNICIPIOS.geojson", "r", encoding="utf-8") as f:
    geojson_data = json.load(f)

# Cargar Excel (esto depende de openpyxl)
df = pd.read_excel("CLIMA PRUEBAS 2020.xlsx")

# Lista de años disponibles
years = sorted(df['AÑO'].unique())

# VARIABLE FIJA A MAPEAR
VARIABLE = "TEMPERATURA"   # <-- cámbiala aquí si quieres otra

# CONFIGURAR DASH APP
app = Dash(__name__)
server = app.server  # necesario para gunicorn / hosting

# Permitir que la app sea embebida en un iframe (Wix)
@server.after_request
def allow_iframe(response):
    response.headers['X-Frame-Options'] = 'ALLOWALL'
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response

app.title = "Mapa Climático Interactivo"

app.layout = html.Div([
    html.H2("Mapa Climático por Municipio y Año", style={'textAlign': 'center'}),

    html.Div([
        html.Label("Selecciona un año:"),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(int(y)), 'value': int(y)} for y in years],
            value=min(years),
            clearable=False,
            style={'width': '200px', 'margin': '0 auto'}
        )
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        dcc.Graph(id='mapa-climatico', style={'height': '80vh'})
    ]),
])

# CALLBACK
@app.callback(
    Output('mapa-climatico', 'figure'),
    Input('year-dropdown', 'value')
)
def update_map(year):

    # Filtrar datos por año
    df_year = df[df['AÑO'] == year]

    # Asegurar que la columna MUNICIPIO exista y coincida con las propiedades del geojson
    # (en tu Excel la columna debe llamarse 'MUNICIPIO')
    if 'MUNICIPIO' not in df_year.columns:
        raise ValueError("La columna 'MUNICIPIO' no existe en tu Excel. Renómbrala para que coincida con el GeoJSON.")

    fig = px.choropleth_mapbox(
        df_year,
        geojson=geojson_data,
        locations='MUNICIPIO',
        featureidkey="properties.MUNICIPIO",
        color=VARIABLE,
        color_continuous_scale='RdYlBu_r' if 'TEMP' in VARIABLE else 'YlGnBu',
        mapbox_style="carto-positron",
        center={"lat": -16.29, "lon": -63.58},
        zoom=5,
        opacity=0.8,
        hover_name="MUNICIPIO",
        custom_data=[
            df_year["MUNICIPIO"],
            df_year["AÑO"],
            df_year.get("TEMPERATURA"),
            df_year.get("TEMP_MIN"),
            df_year.get("TEMP_MAX"),
            df_year.get("PRECIPITACIONES"),
        ]
    )

    fig.update_traces(
        hovertemplate=
            "<b>%{customdata[0]}</b><br>" +
            "Año: %{customdata[1]:.0f}<br>" +
            "Temperatura: %{customdata[2]:.2f}°C<br>" +
            "Temp Mín: %{customdata[3]:.2f}°C<br>" +
            "Temp Máx: %{customdata[4]:.2f}°C<br>" +
            "Precipitación: %{customdata[5]:.2f} mm<br>" +
            "<extra></extra>"
    )

    fig.update_layout(
        margin={"r":0,"t":0,"l":0,"b":0},
        coloraxis_colorbar=dict(title=VARIABLE),
        title=f"{VARIABLE} en el año {year}"
    )

    return fig

# NO llamar app.run en producción; Render usa gunicorn (Procfile).
# Mantener la cláusula para desarrollo local si quieres:
if __name__ == '__main__':
    app.run_server(debug=True)