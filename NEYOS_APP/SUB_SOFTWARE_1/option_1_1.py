import streamlit as st
import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots


# Fonction pour charger les données CSV par morceaux
@st.cache_data
def load_data_in_chunks(file_path):
    chunk_size = 100000  # Nombre de lignes à lire par morceau
    data_chunks = []
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        data_chunks.append(chunk)
        if len(data_chunks) * chunk_size > 2000000:  # Limite arbitraire pour éviter de charger trop de données en mémoire
            break
    data = pd.concat(data_chunks, axis=0)
    return data


# Fonction pour créer les graphiques interactifs avec Plotly
def plot_data(df):
    # Inverser l'ordre des données
    df = df.iloc[::-1].reset_index(drop=True)

    fig = make_subplots(rows=4, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                        subplot_titles=('+1V8 vs Time', 'VSYS vs Time', 'BAT+ vs Time', '+3V3 vs Time'))

    fig.add_trace(go.Scatter(x=df['Time [s]'], y=df['+1V8'], mode='lines', name='+1V8'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df['Time [s]'], y=df['VSYS'], mode='lines', name='VSYS'), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['Time [s]'], y=df['BAT+'], mode='lines', name='BAT+'), row=3, col=1)
    fig.add_trace(go.Scatter(x=df['Time [s]'], y=df['+3V3'], mode='lines', name='+3V3'), row=4, col=1)

    fig.update_layout(
        title='Visualisation des données CSV',
        height=800
    )

    st.plotly_chart(fig)


# Titre de l'application
st.title('Visualisation des données CSV')

# Remplacez par le chemin du fichier CSV local
file_path = 'C:/Users/kevin/Documents/DOCUMENTS/analog.csv'

if st.button('Charger les données et afficher les graphiques'):
    data = load_data_in_chunks(file_path)
    st.write(data.head())  # Afficher les premières lignes du dataframe
    plot_data(data)