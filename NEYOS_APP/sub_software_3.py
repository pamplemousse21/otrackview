import streamlit as st
import pyvisa
import time
import pandas as pd

st.title("Sous-Logiciel 3")
st.sidebar.title("Menu de Sous-Logiciel 3")

# Définir les sections du menu
menu_options = ["Accueil", "Config"]
choice = st.sidebar.radio("Menu", menu_options)


# Fonction pour obtenir le nom réel du périphérique
def get_device_name(resource):
    try:
        instrument = rm.open_resource(resource)
        idn = instrument.query("*IDN?")
        instrument.close()
        return idn.strip()
    except Exception:
        return None


# Fonction pour vérifier la connexion du périphérique
def check_device_connection(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.query("*IDN?")
        instrument.close()
        return "Connecté"
    except Exception:
        return "Déconnecté"


# Fonction pour activer le mode "Power Supply" sur l'alimentation
def activate_power_supply_mode(resource):
    try:
        instrument = rm.open_resource(resource)
        # Commande spécifique pour activer le mode Power Supply
        instrument.write(":ENTRy1:FUNCtion POWer")
        instrument.close()
        return "Mode Power Supply activé"
    except Exception as e:
        return f"Erreur lors de l'activation du mode Power Supply: {e}"


# Fonction pour activer le mode "Simulator" sur l'alimentation
def activate_simulator_mode(resource):
    try:
        instrument = rm.open_resource(resource)
        # Commande spécifique pour activer le mode Simulator
        instrument.write(":ENTRy1:FUNCtion SIMulator")
        instrument.close()
        return "Mode Simulator activé"
    except Exception as e:
        return f"Erreur lors de l'activation du mode Simulator: {e}"


# Fonction pour configurer la tension et le courant
def configure_power_supply(resource, voltage, current):
    try:
        instrument = rm.open_resource(resource)
        # Commandes spécifiques pour configurer la tension et le courant
        instrument.write(f":SOURce:VOLTage {voltage}")
        instrument.write(f":SOURce:CURRent {current}")
        instrument.close()
        return "Configuration envoyée avec succès"
    except Exception as e:
        return f"Erreur lors de l'envoi de la configuration : {e}"


# Fonction pour allumer la sortie
def turn_on_output(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(":OUTPut ON")
        instrument.close()
        st.session_state.output_on = True
        return "Sortie allumée"
    except Exception as e:
        return f"Erreur lors de l'allumage de la sortie : {e}"


# Fonction pour éteindre la sortie
def turn_off_output(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(":OUTPut OFF")
        instrument.close()
        st.session_state.output_on = False
        st.session_state.datalogging = False
        return "Sortie éteinte"
    except Exception as e:
        return f"Erreur lors de l'extinction de la sortie : {e}"


# Fonction pour lire le courant en temps réel
def read_output_current(instrument):
    try:
        # Envoi de la commande SCPI pour lire le courant de sortie
        current = instrument.query("MEASURE:CURRENT? 1")  # Cette commande peut varier selon le modèle de votre alimentation
        current_value = current.split('A')[0]
        return float(current_value)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture du courant de sortie: {e}")
        return None


# Initialiser le gestionnaire de ressources PyVISA
rm = pyvisa.ResourceManager()


def get_device_list():
    # Obtenir la liste des périphériques connectés
    resources = rm.list_resources()

    # Obtenir les noms réels des périphériques, en ignorant ceux qui causent des erreurs
    device_dict = {}
    for resource in resources:
        name = get_device_name(resource)
        if name:
            device_dict[name] = resource

    return device_dict


# Ajout de style pour les carrés de statut et le texte
st.markdown(
    """
    <style>
    .status-box {
        display: inline-block;
        width: 20px;
        height: 20px;
        margin-left: 10px;
    }
    .connected {
        background-color: green;
    }
    .disconnected {
        background-color: red;
    }
    .connected-text {
        color: green;
    }
    .disconnected-text {
        color: red;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialisation de l'état de l'application
if "device_dict" not in st.session_state:
    st.session_state.device_dict = {}

if "mode" not in st.session_state:
    st.session_state.mode = None

if "current_data" not in st.session_state:
    st.session_state.current_data = []

if "average_current_data" not in st.session_state:
    st.session_state.average_current_data = []

if "datalogging" not in st.session_state:
    st.session_state.datalogging = False

if "log_file" not in st.session_state:
    st.session_state.log_file = "current_log.txt"

if "output_on" not in st.session_state:
    st.session_state.output_on = False

if "reset_average" not in st.session_state:
    st.session_state.reset_average = False

if choice == "Accueil":
    st.write("Ceci est la page d'accueil de Sous-Logiciel 3.")

    # Afficher les champs de configuration et les boutons seulement si le mode Power Supply est sélectionné
    if st.session_state.mode == "Power Supply":
        st.subheader("Configuration de l'alimentation")
        col1, col2, col3 = st.columns([3, 1, 1])
        with col1:
            voltage = st.number_input("Tension (V)", min_value=0.0, max_value=60.0, value=12.0, step=0.1)
            current = st.number_input("Courant (A)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
        with col2:
            if st.button("Envoyer la configuration"):
                configure_power_supply(st.session_state.selected_device, voltage, current)
                st.session_state.voltage = voltage
                st.session_state.current = current
        with col3:
            if st.button("Allumer la sortie"):
                turn_on_output(st.session_state.selected_device)
            if st.button("Éteindre la sortie"):
                turn_off_output(st.session_state.selected_device)

        # Boutons pour démarrer et arrêter le datalogging
        if st.session_state.output_on:
            if st.button("Démarrer le datalogging"):
                st.session_state.datalogging = True
            if st.button("Arrêter le datalogging"):
                st.session_state.datalogging = False
            if st.button("Relancer le calcul de la moyenne"):
                st.session_state.reset_average = True
        else:
            st.warning("Allumez la sortie pour démarrer le datalogging.")

        # Afficher le courant en temps réel
        st.subheader("Courant en temps réel")
        current_placeholder = st.empty()
        current_chart = st.line_chart(pd.DataFrame({"Courant (A)": st.session_state.current_data}))

        st.subheader("Courant moyen")
        average_current_placeholder = st.empty()
        average_current_chart = st.line_chart(pd.DataFrame({"Courant moyen (A)": st.session_state.average_current_data}))

        # Mettre à jour le graphique en temps réel
        if st.session_state.datalogging:
            while st.session_state.datalogging:
                instrument = rm.open_resource(st.session_state.selected_device)
                current_value = read_output_current(instrument)
                instrument.close()
                if current_value is not None:
                    st.session_state.current_data.append(current_value)
                    current_placeholder.metric("Courant (A)", current_value)
                    current_chart.add_rows(pd.DataFrame({"Courant (A)": [current_value]}))

                    # Calculer le courant moyen
                    if st.session_state.reset_average:
                        st.session_state.average_current_data = []
                        st.session_state.reset_average = False

                    if len(st.session_state.current_data) > 0:
                        average_current_value = sum(st.session_state.current_data[-len(st.session_state.average_current_data):]) / len(st.session_state.current_data[-len(st.session_state.average_current_data):])
                        st.session_state.average_current_data.append(average_current_value)
                        average_current_placeholder.metric("Courant moyen (A)", average_current_value)
                        average_current_chart.add_rows(pd.DataFrame({"Courant moyen (A)": [average_current_value]}))

                    # Enregistrer les valeurs dans un fichier texte
                    with open(st.session_state.log_file, "a") as f:
                        f.write(f"{time.time()},{current_value},{average_current_value}\n")
                time.sleep(0.2)
    else:
        st.write("Sélectionnez le mode Power Supply dans la configuration pour accéder aux réglages.")

elif choice == "Config":
    st.header("Configuration des périphériques PyVISA")

    # Mettre à jour la liste des périphériques
    if st.button("Mettre à jour la liste des périphériques"):
        st.session_state.device_dict = get_device_list()

    # Afficher les périphériques dans un menu déroulant avec les noms réels
    if st.session_state.device_dict:
        selected_device_name = st.selectbox("Sélectionnez un périphérique PyVISA",
                                            list(st.session_state.device_dict.keys()))
        selected_device = st.session_state.device_dict[selected_device_name]

        # Vérifier le statut de connexion du périphérique sélectionné
        status = check_device_connection(selected_device)
        status_color = "connected" if status == "Connecté" else "disconnected"
        text_color_class = "connected-text" if status == "Connecté" else "disconnected-text"

        # Afficher la sélection du périphérique avec le statut de connexion
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f'<p class="{text_color_class}">{selected_device_name}</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="status-box {status_color}"></div>', unsafe_allow_html=True)

        # Stocker le périphérique sélectionné dans l'état de session
        st.session_state.selected_device = selected_device

        # Afficher les informations sur le périphérique sélectionné
        st.write(f"Adresse VISA : {selected_device}")

        # Menu déroulant pour choisir entre Power Supply et Battery Simulation
        st.session_state.mode = st.selectbox("Sélectionnez le mode", ["Power Supply", "Battery Simulation"])
        st.write(f"Mode sélectionné : {st.session_state.mode}")

        # Activer le mode Power Supply ou Simulator si sélectionné
        if st.session_state.mode == "Power Supply":
            activation_status = activate_power_supply_mode(selected_device)
            st.write(activation_status)
        elif st.session_state.mode == "Battery Simulation":
            activation_status = activate_simulator_mode(selected_device)
            st.write(activation_status)

    else:
        st.write("Aucun périphérique disponible.")
