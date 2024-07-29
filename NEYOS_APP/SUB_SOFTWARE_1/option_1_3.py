import streamlit as st
import pandas as pd
from io import BytesIO
import datetime
import plotly.express as px


def process_csv(file):
    # Lire le contenu du fichier CSV en tant que texte
    file_content = file.getvalue().decode('utf-8')
    lines = file_content.splitlines()

    # Préparer des listes pour les temps et les courants
    times = []
    currents = []
    normalized_times = []

    for index, line in enumerate(lines):
        if index >= 5:  # Ignorer les cinq premières valeurs (index 0 à 4)
            parts = line.split(',')
            if len(parts) >= 4:
                time = f"{parts[0]}.{parts[1]}"  # Remplacer la virgule par un point pour la conversion en float
                current = f"{parts[2]}.{','.join(parts[3:])}"
            elif len(parts) == 2:
                time = parts[0]
                current = parts[1]
            else:
                st.error(f"Ligne mal formatée : {line}")
                continue

            try:
                time_value = float(time)
                current_value = float(current)
                times.append(time_value)
                currents.append(current_value)

                # Convertir le temps en heures, minutes, secondes
                normalized_time = str(datetime.timedelta(seconds=time_value))
                normalized_times.append(normalized_time)
            except ValueError as e:
                st.error(f"Erreur de conversion en float: {e}")
                st.error(f"Valeur de temps: {time}, Valeur de courant: {current}")

    # Créer une nouvelle DataFrame avec le temps, le courant et le temps normalisé
    new_df = pd.DataFrame({
        'Temps normalisé': normalized_times,
        'Temps (s)': times,
        'Courant (A)': currents
    })

    return new_df


def add_chart(writer, df):
    workbook = writer.book
    worksheet = writer.sheets['Modifie']

    # Créer un graphique
    chart = workbook.add_chart({'type': 'line'})

    # Configurer le graphique avec les données de la DataFrame
    chart.add_series({
        'name': 'Courant (A)',
        'categories': ['Modifie', 1, 1, len(df), 1],  # x-values (temps)
        'values': ['Modifie', 1, 2, len(df), 2],  # y-values (courant)
    })

    # Ajouter le graphique à la feuille de calcul
    worksheet.insert_chart('E2', chart)


# Interface Streamlit
st.title('Modification de CSV')

uploaded_file = st.file_uploader("Choisissez un fichier CSV", type="csv")

if uploaded_file is not None:
    # Traiter le fichier CSV
    new_df = process_csv(uploaded_file)

    # Afficher la DataFrame modifiée
    st.write("Voici les données modifiées :")
    st.dataframe(new_df)

    # Afficher le graphique interactif avec Plotly
    fig = px.line(new_df, x='Temps (s)', y='Courant (A)', title='Courant en fonction du Temps')
    st.plotly_chart(fig)

    # Convertir la DataFrame modifiée en CSV
    csv_buffer = BytesIO()
    with pd.ExcelWriter(csv_buffer, engine='xlsxwriter') as writer:
        new_df.to_excel(writer, sheet_name='Modifie', index=False)
        add_chart(writer, new_df)

    # Déplacer le curseur au début du buffer
    csv_buffer.seek(0)

    # Générer le nom du fichier avec la date et l'heure actuelles et le nom du fichier original
    original_file_name = uploaded_file.name.rsplit('.', 1)[0]
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    file_name = f"{original_file_name}_{current_time}.xlsx"

    # Télécharger le fichier CSV modifié
    st.download_button(
        label="Télécharger le fichier CSV modifié",
        data=csv_buffer,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
