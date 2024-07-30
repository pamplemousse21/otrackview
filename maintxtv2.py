import streamlit as st
import folium
import plotly.express as px
import plotly.graph_objects as go
import gpxpy
import gpxpy.gpx
from datetime import datetime, timedelta
from streamlit.components.v1 import html
import paramiko
from streamlit_autorefresh import st_autorefresh

# Définir les valeurs par défaut pour la date et l'heure de filtrage
default_start_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
default_end_date = datetime.now() + timedelta(hours=2)  # Date et heure actuelles

# Informations de connexion SFTP
hostname = '51.83.73.60'
port = 55001
username = 'kevin'
password = 'KevinKevinCitron44!!'


# Fonction pour récupérer la liste des fichiers .txt via SFTP
def get_txt_files_sftp():
    file_list = []
    transport = paramiko.Transport((hostname, port))
    try:
        # Connexion au serveur SFTP
        transport.connect(username=username, password=password)

        # Créer une instance SFTP
        sftp = paramiko.SFTPClient.from_transport(transport)

        # Changer de répertoire vers 'data'
        sftp.chdir('data')

        # Lister les fichiers dans le répertoire 'data'
        file_list = [filename for filename in sftp.listdir() if filename.endswith('.txt')]
    except paramiko.SSHException as e:
        st.error(f"Erreur SSH : {e}")
    except paramiko.SFTPError as e:
        st.error(f"Erreur SFTP : {e}")
    finally:
        # Fermer la connexion SFTP et transport
        sftp.close()
        transport.close()

    return file_list


# Fonction pour lire le fichier .txt et extraire les points
def lire_fichier_txt(_file):
    points = []
    lines = _file.readlines()
    for i in range(0, len(lines), 7):  # Chaque point a 7 lignes de données
        timestamp_reception = lines[i].strip()
        timestamp_envoi = lines[i + 1].strip()
        latitude = float(lines[i + 2].strip())
        longitude = float(lines[i + 3].strip())
        battery_level = float(lines[i + 4].strip())  # Niveau de batterie
        reception_mode = int(lines[i + 5].strip())
        info_alertes = lines[i + 6].strip()

        # Calculer la différence entre l'heure de réception et l'heure d'envoi
        reception_time = datetime.strptime(timestamp_reception, '%Y-%m-%dT%H:%M:%S')
        envoi_time = datetime.strptime(timestamp_envoi, '%Y-%m-%dT%H:%M:%S')
        diff = (reception_time - envoi_time).total_seconds()  # Différence en secondes

        points.append((latitude, longitude, battery_level, timestamp_reception, timestamp_envoi, reception_mode,
                       info_alertes, diff, reception_time))
    return points


# Fonction pour lire le fichier GPX et extraire les points
@st.cache_data
def lire_fichier_gpx(file):
    points = []
    gpx = gpxpy.parse(file)
    for track in gpx.tracks:
        for segment in track.segments:
            for point in segment.points:
                points.append((point.latitude, point.longitude, point.elevation, point.time))
    return points


# Fonction pour compter les points par type
def compter_points_par_type(points_txt, date_debut=None, date_fin=None):
    counts = {
        "GSM": 0,
        "SAT": 0,
        "BUFFER": 0,
        "REPIT_2": 0,
        "REPIT_3": 0
    }

    if date_debut:
        points_txt = [p for p in points_txt if p[8] >= date_debut]
    if date_fin:
        points_txt = [p for p in points_txt if p[8] <= date_fin]

    point_counts = {}
    for point in points_txt:
        lat_long = (point[0], point[1])
        if lat_long not in point_counts:
            point_counts[lat_long] = 0
        point_counts[lat_long] += 1

    for i, point in enumerate(points_txt):
        diff = point[7]
        reception_mode = point[5]
        lat_long = (point[0], point[1])
        count = point_counts[lat_long]

        if diff > buffer_threshold:
            counts["BUFFER"] += 1
        elif reception_mode == 1:
            counts["GSM"] += 1
        elif reception_mode == 0:
            counts["SAT"] += 1

        if i > 0 and lat_long == (points_txt[i - 1][0], points_txt[i - 1][1]):
            if count == 2:
                counts["REPIT_2"] += 1
            elif count > 2:
                counts["REPIT_3"] += 1

    last_point_time = points_txt[-1][8] if points_txt else None
    first_point_time = points_txt[0][8] if points_txt else None

    return counts, first_point_time, last_point_time


# Fonction pour générer et sauvegarder la carte en HTML
def generer_carte(points_txt1, points_txt2, points_gpx, position_slider, filename1=None, filename2=None, display_gsm=True, display_sat=True, display_buffer=True,
                  display_rep=True, color_gsm='blue', color_sat='red', color_buffer='green',
                  color_rep_2='yellow', color_rep_3='orange', color_gpx='purple', diameter_gsm=2, diameter_sat=7,
                  diameter_buffer=2, diameter_rep=5, diameter_gpx=2, buffer_threshold=120, date_debut=None,
                  date_fin=None, filename="map.html"):
    if not points_txt1 and not points_txt2 and not points_gpx:
        return None

    # Filtrer les points par date
    if date_debut:
        if points_txt1:
            points_txt1 = [p for p in points_txt1 if p[8] >= date_debut]
        if points_txt2:
            points_txt2 = [p for p in points_txt2 if p[8] >= date_debut]
        if points_gpx:
            points_gpx = [p for p in points_gpx if p[3] >= date_debut]
    if date_fin:
        if points_txt1:
            points_txt1 = [p for p in points_txt1 if p[8] <= date_fin]
        if points_txt2:
            points_txt2 = [p for p in points_txt2 if p[8] <= date_fin]
        if points_gpx:
            points_gpx = [p for p in points_gpx if p[3] <= date_fin]

    # Initialiser les points pour centrer la carte
    all_points = []
    if points_txt1:
        all_points.extend([(p[0], p[1]) for p in points_txt1])
    if points_txt2:
        all_points.extend([(p[0], p[1]) for p in points_txt2])
    if points_gpx:
        all_points.extend([(p[0], p[1]) for p in points_gpx])

    # Compter les points superposés
    point_counts = {}
    for point in (points_txt1 or []) + (points_txt2 or []):  # Utiliser une liste vide si None
        lat_long = (point[0], point[1])
        if lat_long not in point_counts:
            point_counts[lat_long] = 0
        point_counts[lat_long] += 1

    # Créer une carte Folium avec des options de zoom personnalisées
    m = folium.Map(location=[0, 0], zoom_start=2, control_scale=True, max_zoom=18, min_zoom=2, scrollWheelZoom=True)

    # Fonction pour ajouter des points à la carte
    def ajouter_points(points_txt, couleur, diametre, fichier=None):
        if points_txt:
            for i, point in enumerate(points_txt):
                latitude, longitude, battery_level, timestamp_reception, timestamp_envoi, reception_mode, info_alertes, diff, reception_time = point
                # Déterminer le mode de réception et la couleur
                color = None
                radius = None
                info = ""
                if diff > buffer_threshold and display_buffer:
                    reception_mode_str = "BUFFER"
                    color = color_buffer
                    radius = diameter_buffer
                elif reception_mode == 1 and display_gsm:
                    reception_mode_str = "GSM"
                    color = color_gsm
                    radius = diameter_gsm
                elif reception_mode == 0 and display_sat:
                    reception_mode_str = "SAT"
                    color = color_sat
                    radius = diameter_sat
                if i > 0 and (latitude, longitude) == (points_txt[i - 1][0], points_txt[i - 1][1]) and display_rep:
                    reception_mode_str = "REPIT"
                    count = point_counts[(latitude, longitude)]
                    if count == 2:
                        color = color_rep_2
                    elif count > 2:
                        color = color_rep_3
                    radius = diameter_rep
                    info = f"Nombre de points superposés: {count}<br>"
                if color is not None:
                    # Ajouter un marqueur pour chaque point avec une infobulle
                    folium.CircleMarker(
                        location=(latitude, longitude),
                        radius=radius,
                        color=color,
                        fill=True,
                        fill_color=color,
                        popup=(
                            f"Latitude: {latitude}<br>"
                            f"Longitude: {longitude}<br>"
                            f"Niveau de Batterie: {battery_level}<br>"
                            f"Réception: {timestamp_reception}<br>"
                            f"Envoi: {timestamp_envoi}<br>"
                            f"Mode: {reception_mode_str}<br>"
                            f"Différence: {diff} sec<br>"
                            f"{info}"
                            f"Alertes: {info_alertes}<br>"
                            f"Fichier: {fichier if fichier else 'N/A'}"
                        ),
                    ).add_to(m)

                # Ajouter des lignes entre les points
                if i > 0:
                    previous_point = points_txt[i - 1]
                    previous_lat, previous_lon = previous_point[0], previous_point[1]
                    time_diff = (reception_time - previous_point[8]).total_seconds()
                    line_color = 'red' if time_diff > 200 else 'blue'
                    folium.PolyLine(
                        locations=[(previous_lat, previous_lon), (latitude, longitude)],
                        color=line_color
                    ).add_to(m)

            # Ajouter une icône pour le dernier point reçu
            latest_point = points_txt[-1]
            folium.Marker(
                location=(latest_point[0], latest_point[1]),
                icon=folium.Icon(color='green', icon='info-sign'),
                popup=(
                    f"Latitude: {latest_point[0]}<br>"
                    f"Longitude: {latest_point[1]}<br>"
                    f"Niveau de Batterie: {latest_point[2]}<br>"
                    f"Réception: {latest_point[3]}<br>"
                    f"Envoi: {latest_point[4]}<br>"
                    f"Mode: {latest_point[5]}<br>"
                    f"Différence: {latest_point[7]} sec<br>"
                    f"Alertes: {latest_point[6]}<br>"
                    f"Fichier: {fichier if fichier else 'N/A'}"
                )
            ).add_to(m)

    # Ajouter les points des fichiers TXT
    if points_txt1:
        ajouter_points(points_txt1, color_gsm, diameter_gsm, filename1)
    if points_txt2:
        ajouter_points(points_txt2, color_sat, diameter_sat, filename2)

    # Ajouter les points GPX à la carte
    if points_gpx:
        for point in points_gpx:
            latitude, longitude, elevation, time = point
            folium.CircleMarker(
                location=(latitude, longitude),
                radius=diameter_gpx,
                color=color_gpx,
                fill=True,
                fill_color=color_gpx,
                popup=(
                    f"Latitude: {latitude}<br>"
                    f"Longitude: {longitude}<br>"
                    f"Élévation: {elevation}<br>"
                    f"Temps: {time}"
                ),
            ).add_to(m)

    # Ajouter un curseur pour la position sélectionnée
    total_points = len(all_points)
    if total_points > 0 and position_slider < total_points:
        cursor_point = all_points[position_slider]
        folium.Marker(
            location=cursor_point,
            icon=folium.Icon(color='orange'),
            popup="Curseur de position"
        ).add_to(m)

    # Centrer la carte sur les points importés
    if all_points:
        m.fit_bounds([(min(p[0] for p in all_points), min(p[1] for p in all_points)),
                      (max(p[0] for p in all_points), max(p[1] for p in all_points))])

    # Sauvegarder la carte en HTML
    m.save(filename)

    return points_txt1, points_txt2, points_gpx

# Fonction pour tracer la courbe de la batterie avec l'annotation et filtrer par date
def tracer_courbe_batterie(points_txt, position_slider, date_debut=None, date_fin=None):
    # Filtrer les points par date
    if date_debut:
        points_txt = [p for p in points_txt if p[8] >= date_debut]
    if date_fin:
        points_txt = [p for p in points_txt if p[8] <= date_fin]

    df = {
        "Temps": [p[8] for p in points_txt],
        "Niveau de Batterie": [p[2] for p in points_txt]
    }
    fig = px.line(df, x="Temps", y="Niveau de Batterie", title="Niveau de Batterie en Fonction du Temps")

    # Ajouter une annotation pour le point sélectionné
    if position_slider < len(points_txt):
        point = points_txt[position_slider]
        fig.add_trace(go.Scatter(
            x=[point[8]],
            y=[point[2]],
            mode='markers+text',
            text=["<b>Curseur de position</b>"],
            textposition="top center",
            marker=dict(color='orange', size=10)
        ))

    # Fixer l'axe Y de 0 à 100%
    fig.update_yaxes(range=[0, 100])

    return fig

def calculer_minutes_ecoulees(date_debut, date_fin):
    return (date_fin - date_debut).total_seconds() / 60

def calculer_points_perdus(minutes_ecoulees, nombre_de_points):
    return minutes_ecoulees - nombre_de_points

# Configure la page
st.set_page_config(page_title="Carte OSM avec Données TXT et GPX et Streamlit", layout="wide")

# Titre de la page
st.title("Carte OpenStreetMap avec Données TXT et GPX et Streamlit")

# Utiliser les variables de session pour stocker les points
if 'points_txt1' not in st.session_state:
    st.session_state.points_txt1 = None
if 'points_txt2' not in st.session_state:
    st.session_state.points_txt2 = None
if 'points_gpx' not in st.session_state:
    st.session_state.points_gpx = None
if 'selected_txt_files' not in st.session_state:
    st.session_state.selected_txt_files = None
if 'date_debut_time' not in st.session_state:
    st.session_state.date_debut_time = default_start_date.time()
if 'date_fin_time' not in st.session_state:
    st.session_state.date_fin_time = default_end_date.time()
if 'fix_now_clicked' not in st.session_state:
    st.session_state.fix_now_clicked = False

# Récupérer la liste des fichiers .txt disponibles via SFTP
txt_files = get_txt_files_sftp()

# Afficher la liste des fichiers .txt et permettre à l'utilisateur de sélectionner deux fichiers
selected_txt_files = st.multiselect("Sélectionnez un ou deux fichiers TXT", txt_files, default=txt_files[:2])

# Forcer la mise à jour des points lorsqu'un nouveau fichier est sélectionné
if selected_txt_files and selected_txt_files != st.session_state.selected_txt_files:
    st.session_state.selected_txt_files = selected_txt_files
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    if len(selected_txt_files) > 0:
        with sftp.file(f"data/{selected_txt_files[0]}", mode='r') as file:
            st.session_state.points_txt1 = lire_fichier_txt(file)
    if len(selected_txt_files) > 1:
        with sftp.file(f"data/{selected_txt_files[1]}", mode='r') as file:
            st.session_state.points_txt2 = lire_fichier_txt(file)
    else:
        st.session_state.points_txt2 = None
    sftp.close()
    transport.close()

# Autorefresh toutes les 30 secondes
st_autorefresh(interval=30 * 1000, key="datarefresh")

# Recharger les données des fichiers TXT sélectionnés
if selected_txt_files:
    transport = paramiko.Transport((hostname, port))
    transport.connect(username=username, password=password)
    sftp = paramiko.SFTPClient.from_transport(transport)
    if len(selected_txt_files) > 0:
        with sftp.file(f"data/{selected_txt_files[0]}", mode='r') as file:
            st.session_state.points_txt1 = lire_fichier_txt(file)
    if len(selected_txt_files) > 1:
        with sftp.file(f"data/{selected_txt_files[1]}", mode='r') as file:
            st.session_state.points_txt2 = lire_fichier_txt(file)
    sftp.close()
    transport.close()

# Chargement du fichier GPX si téléchargé
uploaded_file_gpx = st.file_uploader("Télécharger un fichier GPX", type="gpx")

if uploaded_file_gpx is not None:
    st.session_state.points_gpx = lire_fichier_gpx(uploaded_file_gpx)

# Vérifier s'il y a des points à afficher
if st.session_state.points_txt1 is not None or st.session_state.points_txt2 is not None or st.session_state.points_gpx is not None:
    # Options d'affichage
    col1, col2, col3 = st.columns(3)

    with col1:
        display_gsm = st.checkbox("Afficher les points GSM", value=True)
        display_sat = st.checkbox("Afficher les points SAT", value=True)
        display_buffer = st.checkbox("Afficher les points BUFFER", value=True)
        display_rep = st.checkbox("Afficher les points REPIT", value=True)  # Ajout du point REPIT
        display_gpx = st.checkbox("Afficher les points GPX", value=True)

    with col2:
        color_gsm = st.color_picker("Couleur pour GSM", "#0000ff")
        color_sat = st.color_picker("Couleur pour SAT", "#ff0000")
        color_buffer = st.color_picker("Couleur pour BUFFER", "#00ff00")
        color_rep_2 = st.color_picker("Couleur pour REPIT (2 points)", "#ffff00")  # Couleur pour REPIT (2 points)
        color_rep_3 = st.color_picker("Couleur pour REPIT (>2 points)", "#ffA500")  # Couleur pour REPIT (>2 points)
        color_gpx = st.color_picker("Couleur pour GPX", "#800080")

    with col3:
        diameter_gsm = st.slider("Diamètre pour GSM", min_value=1, max_value=10, value=2)
        diameter_sat = st.slider("Diamètre pour SAT", min_value=1, max_value=10, value=7)
        diameter_buffer = st.slider("Diamètre pour BUFFER", min_value=1, max_value=10, value=2)
        diameter_rep = st.slider("Diamètre pour REPIT", min_value=1, max_value=10, value=5)  # Diamètre pour REPIT
        diameter_gpx = st.slider("Diamètre pour GPX", min_value=1, max_value=10, value=2)

    # Définir le seuil de différence pour BUFFER
    buffer_threshold = st.number_input("Seuil de différence (en secondes) pour BUFFER", min_value=0, value=120)

    # Bouton "Fix NOW" pour mettre l'heure de début à l'heure actuelle moins 5 minutes
    if st.button("Fix NOW"):
        st.session_state.date_debut_time = (datetime.now() - timedelta(minutes=5)).time()
        st.session_state.fix_now_clicked = True

    # Bouton "Fix NOW" pour mettre l'heure de début à l'heure actuelle moins 5 minutes
    if st.button("Fix NOW-2"):
        st.session_state.date_debut_time = (datetime.now() - timedelta(hours=2,minutes=5)).time()
        st.session_state.fix_now_clicked = True

    # Sélecteurs de date et heure pour filtrer les points
    date_debut_date = st.date_input("Date de début", value=default_start_date.date())
    date_debut_time = st.time_input("Heure de début", value=st.session_state.date_debut_time)
    st.session_state.date_debut_time = date_debut_time

    date_fin_date = st.date_input("Date de fin", value=default_end_date.date())
    date_fin_time = st.time_input("Heure de fin", value=st.session_state.date_fin_time)
    st.session_state.date_fin_time = date_fin_time

    # Combine les dates et les heures en objets datetime
    date_debut = datetime.combine(date_debut_date, date_debut_time)
    date_fin = datetime.combine(date_fin_date, date_fin_time)

    # Vérifier si les listes ne sont pas None avant de calculer leur longueur
    points_txt1_length = len(st.session_state.points_txt1) if st.session_state.points_txt1 else 0
    points_txt2_length = len(st.session_state.points_txt2) if st.session_state.points_txt2 else 0
    points_gpx_length = len(st.session_state.points_gpx) if st.session_state.points_gpx else 0
    total_points = points_txt1_length + points_txt2_length + points_gpx_length

    # Curseur pour naviguer parmi les points
    position_slider = st.slider("Naviguer parmi les points", min_value=0,
                                max_value=total_points - 1 if total_points > 0 else 0, value=0)

    # Génération de la carte avec les points et sauvegarde en HTML
    points_txt1, points_txt2, points_gpx = generer_carte(
        st.session_state.points_txt1, st.session_state.points_txt2, st.session_state.points_gpx, position_slider,
        selected_txt_files[0] if len(selected_txt_files) > 0 else None,
        selected_txt_files[1] if len(selected_txt_files) > 1 else None,  # Passer les noms des fichiers ici
        display_gsm, display_sat, display_buffer, display_rep,  # Ajouter display_rep ici
        color_gsm, color_sat, color_buffer, color_rep_2, color_rep_3, color_gpx,  # Ajouter color_rep ici
        diameter_gsm, diameter_sat, diameter_buffer, diameter_rep, diameter_gpx,  # Ajouter diameter_rep ici
        buffer_threshold, date_debut, date_fin, filename="map.html"
    )

    # Afficher la carte dans un iframe
    st.markdown("<h3>Carte Générée</h3>", unsafe_allow_html=True)
    html_file = open("map.html", 'r', encoding='utf-8')
    source_code = html_file.read()
    html_file.close()
    html(source_code, height=600)

    # Tracer la courbe de la batterie avec l'annotation
    if st.session_state.points_txt1:
        fig1 = tracer_courbe_batterie(st.session_state.points_txt1, position_slider, date_debut, date_fin)
        st.plotly_chart(fig1)
    if st.session_state.points_txt2:
        fig2 = tracer_courbe_batterie(st.session_state.points_txt2, position_slider, date_debut, date_fin)
        st.plotly_chart(fig2)

    # Afficher les statistiques en bas de la page
    if st.session_state.points_txt1:
        counts1,first_point_time1, last_point_time1,  = compter_points_par_type(st.session_state.points_txt1, date_debut, date_fin)
        minutes_ecoulees1 = calculer_minutes_ecoulees(date_debut, last_point_time1)
        minutes_ecouleesfirstpoint1 = calculer_minutes_ecoulees(first_point_time1, last_point_time1)
        points_perdus1 = calculer_points_perdus(minutes_ecoulees1, points_txt1_length)
        time3min = 3
        st.markdown(f"### Statistiques des Points du Fichier V5 {selected_txt_files[0]}")
        st.markdown(f"- Nombre de points GSM : **{counts1['GSM']}**")
        st.markdown(f"- Nombre de points SAT : **{counts1['SAT']}**")
        st.markdown(f"- Nombre de points BUFFER : **{counts1['BUFFER']}**")
        st.markdown(f"- Nombre de points REPIT (2 points) : **{counts1['REPIT_2']}**")
        st.markdown(f"- Nombre de points REPIT (>2 points) : **{counts1['REPIT_3']}**")
        st.markdown(f"- Heure du dernier point : **{last_point_time1}**")
        st.markdown(f"- Minutes écoulées depuis le début : **{minutes_ecoulees1:.2f}**")
        st.markdown(f"- Minutes écoulées depuis le premier moint affiché : **{minutes_ecouleesfirstpoint1:.2f}**")  ####
        st.markdown(f"- Nombre de points perdus : **{(minutes_ecouleesfirstpoint1/time3min) - (counts1['SAT'] + counts1['GSM'] + (counts1['REPIT_2'] / 2) + (counts1['REPIT_3'] / 3)):.0f}**")
        st.markdown(f"- perte (%) : **{((minutes_ecouleesfirstpoint1/time3min) - (counts1['SAT'] + counts1['GSM'] + (counts1['REPIT_2'] / 2) + (counts1['REPIT_3'] / 3)))/(minutes_ecouleesfirstpoint1/time3min)*100:.1f}** %")
        st.markdown(f"- Couverture reseau GSM : **{counts1['GSM'] / (minutes_ecouleesfirstpoint1/time3min) * 100:.1f}** %")
        st.markdown(f"- Couverture reseau SAT : **{counts1['SAT'] / (minutes_ecouleesfirstpoint1/time3min) * 100:.1f}** %")
    if st.session_state.points_txt2:
        counts2,first_point_time2, last_point_time2 = compter_points_par_type(st.session_state.points_txt2, date_debut, date_fin)
        minutes_ecoulees2 = calculer_minutes_ecoulees(date_debut, last_point_time2)
        minutes_ecouleesfirstpoint2 = calculer_minutes_ecoulees(first_point_time2, last_point_time2)
        points_perdus2 = calculer_points_perdus(minutes_ecoulees2, points_txt2_length)
        st.markdown(f"### Statistiques des Points du Fichier V5 {selected_txt_files[1]}")
        st.markdown(f"- Nombre de points GSM : **{counts2['GSM']}**")
        st.markdown(f"- Nombre de points SAT : **{counts2['SAT']}**")
        st.markdown(f"- Nombre de points BUFFER : **{counts2['BUFFER']}**")
        st.markdown(f"- Nombre de points REPIT (2 points) : **{counts2['REPIT_2']}**")
        st.markdown(f"- Nombre de points REPIT (>2 points) : **{counts2['REPIT_3']}**")
        st.markdown(f"- Heure du dernier point : **{last_point_time2}**")
        st.markdown(f"- Minutes écoulées depuis le début : **{minutes_ecoulees2:.2f}**")
        st.markdown(f"- Minutes écoulées depuis le premier moint affiché : **{minutes_ecouleesfirstpoint2:.2f}**")####
        st.markdown(f"- Nombre de points perdus : **{(minutes_ecouleesfirstpoint2/time3min)-(counts2['SAT']+counts2['GSM']+(counts2['REPIT_2']/2)+(counts2['REPIT_3']/3)):.0f}**")
        st.markdown(f"- perte (%) : **{((minutes_ecouleesfirstpoint2/time3min) - (counts2['SAT'] + counts2['GSM'] + (counts2['REPIT_2'] / 2) + (counts2['REPIT_3'] / 3))) / (minutes_ecouleesfirstpoint2/time3min) * 100:.1f}** %")
        st.markdown(f"- Couverture reseau GSM : **{counts2['GSM']/(minutes_ecouleesfirstpoint2/time3min)*100:.1f}** %")
        st.markdown(f"- Couverture reseau SAT : **{counts2['SAT']/(minutes_ecouleesfirstpoint2/time3min)*100:.1f}** %")
else:
    st.info("Veuillez télécharger un fichier TXT ou GPX.")
