import pandas as pd
import plotly.express as px
import duckdb

def obtener_perfil_armas(con):
    
    query = """
    SELECT 
        arma_medio, 
        COUNT(*) as total_casos,
        ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 2) as porcentaje
    FROM hechos
    GROUP BY arma_medio
    ORDER BY total_casos DESC
    LIMIT 10
    """
    return con.execute(query).df()

def plot_perfil_armas(df):
    """
    Genera un gráfico de barras horizontal.
    """
    fig = px.bar(
        df, 
        x='total_casos', 
        y='arma_medio',
        orientation='h',
        title='Top 10 Medios/Armas Utilizados en Delitos',
        labels={'total_casos': 'Número de Casos', 'arma_medio': 'Arma o Medio'},
        text='porcentaje'
    )
    fig.update_traces(texttemplate='%{text}%', textposition='outside')
    fig.update_layout(yaxis={'categoryorder':'total ascending'})
    return fig