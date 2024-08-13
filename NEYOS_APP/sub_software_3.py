import streamlit as st
import pyvisa
import time
import pandas as pd
from datetime import datetime
import os
import plotly.express as px

st.title("Sous-Logiciel 3")
st.sidebar.title("Menu de Sous-Logiciel 3")

# Définir les sections du menu
menu_options = ["Accueil", "Config", "Simulateur Batterie"]
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
        instrument.write(":ENTRy1:FUNCtion POWer")
        instrument.close()
        return "Mode Power Supply activé"
    except Exception as e:
        return f"Erreur lors de l'activation du mode Power Supply: {e}"

# Fonction pour activer le mode "Simulator" sur l'alimentation
def activate_simulator_mode(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(":ENTRy1:FUNCtion SIMulator")
        instrument.close()
        return "Mode Simulator activé"
    except Exception as e:
        return f"Erreur lors de l'activation du mode Simulator: {e}"

# Fonction pour configurer la tension et le courant
def configure_power_supply(resource, voltage, current):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(f":SOURce:VOLTage {voltage}")
        instrument.write(f":SOURce:CURRent {current}")
        instrument.close()
        return "Configuration envoyée avec succès"
    except Exception as e:
        return f"Erreur lors de l'envoi de la configuration : {e}"

# Fonction pour configurer le courant limite et la capacité
def configure_battery_simulator(resource, current_limit, capacity):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(f":BATT:SIM:CURR:LIM {current_limit}")
        instrument.write(f":BATT:SIM:CAP:LIM {capacity}mAh")
        instrument.close()
        return "Configuration du simulateur envoyée avec succès"
    except Exception as e:
        return f"Erreur lors de l'envoi de la configuration du simulateur : {e}"

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

# Fonction pour lire le courant en mode Power Supply
def read_output_current_power_supply(instrument):
    try:
        current = instrument.query("MEASURE:CURRENT? 1")
        current_value = current.split('A')[0]
        return float(current_value)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture du courant de sortie: {e}")
        return None

# Fonction pour lire le courant en mode Battery Simulation
def read_output_current_battery_simulator(instrument):
    try:
        current = instrument.query(":BATTery1:SIMulator:CURRent?")
        return float(current)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture du courant de sortie: {e}")
        return None

# Fonction pour lire la tension en mode Power Supply
def read_output_voltage_power_supply(instrument):
    try:
        voltage = instrument.query("MEASURE:VOLTAGE? 1")
        voltage_value = voltage.split('V')[0]
        return float(voltage_value)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture de la tension de sortie: {e}")
        return None

# Fonction pour lire la tension en mode Battery Simulation
def read_output_voltage_battery_simulator(instrument):
    try:
        voltage = instrument.query(":BATTery1:SIMulator:TVOLtage?")
        return float(voltage)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture de la tension de sortie: {e}")
        return None

# Fonction pour lire le SOC en mode Battery Simulation
def read_soc_battery_simulator(instrument):
    try:
        soc = instrument.query(":BATTery1:SIMulator:SOC?")
        return float(soc)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture du SOC: {e}")
        return None

# Fonction pour charger un modèle de batterie
def load_battery_model(resource, model_index):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(f":BATTery1:MODel:RCL {model_index}")
        instrument.close()
        return f"Modèle de batterie {model_index} chargé"
    except Exception as e:
        return f"Erreur lors du chargement du modèle de batterie : {e}"

# Fonction pour définir le SOC (State of Charge)
def set_soc(resource, soc):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(f":BATTery1:SIMulator:SOC {soc}")
        instrument.close()
        return f"SOC défini à {soc}%"
    except Exception as e:
        return f"Erreur lors de la définition du SOC : {e}"

# Fonction pour lancer le simulateur
def start_simulator(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(":BATTery1:OUTPut ON")
        instrument.close()
        return "Simulateur lancé"
    except Exception as e:
        return f"Erreur lors du lancement du simulateur : {e}"

# Fonction pour arrêter le simulateur
def stop_simulator(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(":BATTery1:OUTPut OFF")
        instrument.close()
        return "Simulateur arrêté"
    except Exception as e:
        return f"Erreur lors de l'arrêt du simulateur : {e}"

# Fonction pour configurer le multimètre
def configure_multimeter(resource, range_value="2A"):
    try:
        instrument = rm.open_resource(resource)
        instrument.write(f"CONFigure:CURRent:DC {range_value}")
        instrument.close()
        return f"Multimètre configuré sur le range {range_value}"
    except Exception as e:
        return f"Erreur lors de la configuration du multimètre : {e}"

# Fonction pour lire le courant avec le multimètre
def read_multimeter_current(resource):
    try:
        instrument = rm.open_resource(resource)
        instrument.write("INITiate")
        current = instrument.query("READ?")
        current_value = current.split(',')[0]
        return float(current_value)
    except pyvisa.VisaIOError as e:
        print(f"Erreur lors de la lecture du courant avec le multimètre: {e}")
        return None

# Fonction pour initialiser le fichier Excel
def initialize_excel_file(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
    file_path = os.path.join(directory, f"simulation_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
    with pd.ExcelWriter(file_path, engine='xlsxwriter') as writer:
        pd.DataFrame(columns=["Timestamp", "Current (A)", "Voltage (V)", "SOC (%)", "Average Current per SOC (%) (A)","Multimeter Current (A)"]).to_excel(writer, index=False)
    return file_path

# Fonction pour ajouter des données au fichier Excel
def append_to_excel(file_path, data):
    df = pd.DataFrame(data, index=[0])
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, index=False, header=False, startrow=writer.sheets['Sheet1'].max_row)

# Initialiser le gestionnaire de ressources PyVISA
rm = pyvisa.ResourceManager()

def get_device_list():
    resources = rm.list_resources()
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

if "datalogging" not in st.session_state:
    st.session_state.datalogging = False

if "log_file" not in st.session_state:
    st.session_state.log_file = "current_log.txt"

if "output_on" not in st.session_state:
    st.session_state.output_on = False

if "selected_device" not in st.session_state:
    st.session_state.selected_device = None

if "multimeter_device" not in st.session_state:
    st.session_state.multimeter_device = None

if "use_multimeter" not in st.session_state:
    st.session_state.use_multimeter = False

if "battery_model" not in st.session_state:
    st.session_state.battery_model = 1

if "current_limit" not in st.session_state:
    st.session_state.current_limit = 3.0

if "capacity" not in st.session_state:
    st.session_state.capacity = 200

if "soc" not in st.session_state:
    st.session_state.soc = 50

if "interval" not in st.session_state:
    st.session_state.interval = 1000

if "excel_directory" not in st.session_state:
    st.session_state.excel_directory = r"C:\Users\kevin\Downloads"

if "excel_file_path" not in st.session_state:
    st.session_state.excel_file_path = None

if "previous_soc" not in st.session_state:
    st.session_state.previous_soc = st.session_state.soc

if "instant_current" not in st.session_state:
    st.session_state.instant_current = 0.0

if "instant_voltage" not in st.session_state:
    st.session_state.instant_voltage = 0.0

if "instant_soc" not in st.session_state:
    st.session_state.instant_soc = 0.0

if "instant_multimeter_current" not in st.session_state:
    st.session_state.instant_multimeter_current = 0.0

if choice == "Accueil":
    st.write("Ceci est la page d'accueil de Sous-Logiciel 3.")

elif choice == "Config":
    st.header("Configuration des périphériques PyVISA")

    # Éteindre le simulateur lorsqu'on entre dans l'interface de configuration
    if st.session_state.output_on:
        stop_simulator(st.session_state.selected_device)
        st.session_state.output_on = False
        st.session_state.datalogging = False

    # Mettre à jour la liste des périphériques
    if st.button("Mettre à jour la liste des périphériques"):
        st.session_state.device_dict = get_device_list()

    # Afficher les périphériques dans un menu déroulant avec les noms réels
    if st.session_state.device_dict:
        selected_device_name = st.selectbox("Sélectionnez un périphérique PyVISA pour la source d'alimentation",
                                            list(st.session_state.device_dict.keys()), index=list(st.session_state.device_dict.values()).index(st.session_state.selected_device) if st.session_state.selected_device else 0)
        st.session_state.selected_device = st.session_state.device_dict[selected_device_name]

        available_multimeter_devices = {k: v for k, v in st.session_state.device_dict.items() if v != st.session_state.selected_device}
        use_multimeter = st.checkbox("Utiliser un multimètre", value=st.session_state.use_multimeter)
        st.session_state.use_multimeter = use_multimeter

        if use_multimeter:
            if available_multimeter_devices:
                multimeter_device_name = st.selectbox("Sélectionnez un périphérique PyVISA pour le multimètre",
                                                      list(available_multimeter_devices.keys()), index=list(available_multimeter_devices.values()).index(st.session_state.multimeter_device) if st.session_state.multimeter_device else 0)
                st.session_state.multimeter_device = available_multimeter_devices[multimeter_device_name]

                status_multimeter = check_device_connection(st.session_state.multimeter_device)
                status_multimeter_color = "connected" if status_multimeter == "Connecté" else "disconnected"
                text_color_multimeter_class = "connected-text" if status_multimeter == "Connecté" else "disconnected-text"

                col3, col4 = st.columns([3, 1])
                with col3:
                    st.markdown(f'<p class="{text_color_multimeter_class}">{multimeter_device_name}</p>', unsafe_allow_html=True)
                with col4:
                    st.markdown(f'<div class="status-box {status_multimeter_color}"></div>', unsafe_allow_html=True)

        # Vérifier le statut de connexion du périphérique sélectionné
        status = check_device_connection(st.session_state.selected_device)
        status_color = "connected" if status == "Connecté" else "disconnected"
        text_color_class = "connected-text" if status == "Connecté" else "disconnected-text"

        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f'<p class="{text_color_class}">{selected_device_name}</p>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<div class="status-box {status_color}"></div>', unsafe_allow_html=True)

        st.write(f"Adresse VISA de la source d'alimentation : {st.session_state.selected_device}")

        if use_multimeter and available_multimeter_devices:
            st.write(f"Adresse VISA du multimètre : {st.session_state.multimeter_device}")

        # Menu déroulant pour choisir entre Power Supply et Battery Simulation
        st.session_state.mode = st.selectbox("Sélectionnez le mode", ["Power Supply", "Battery Simulation"], index=["Power Supply", "Battery Simulation"].index(st.session_state.mode) if st.session_state.mode else 0)
        st.write(f"Mode sélectionné : {st.session_state.mode}")

        # Activer le mode Power Supply ou Simulator si sélectionné
        if st.session_state.mode == "Power Supply":
            activation_status = activate_power_supply_mode(st.session_state.selected_device)
            st.write(activation_status)
        elif st.session_state.mode == "Battery Simulation":
            activation_status = activate_simulator_mode(st.session_state.selected_device)
            st.write(activation_status)

            st.session_state.battery_model = st.selectbox("Sélectionnez un modèle de batterie", list(range(1, 10)), index=st.session_state.battery_model - 1)
            load_status = load_battery_model(st.session_state.selected_device, st.session_state.battery_model)
            st.write(load_status)

            st.session_state.current_limit = st.number_input("Courant Limite (A)", min_value=0.0, max_value=10.0, value=st.session_state.current_limit, step=0.1)
            st.session_state.capacity = st.number_input("Capacité (mAh)", min_value=0, max_value=10000, value=st.session_state.capacity, step=1)
            configure_status = configure_battery_simulator(st.session_state.selected_device, st.session_state.current_limit, st.session_state.capacity)
            st.write(configure_status)

        st.session_state.excel_directory = st.text_input("Répertoire de sauvegarde du fichier Excel", value=st.session_state.excel_directory)

        st.session_state.interval = st.number_input("Intervalle de prise de mesure (ms)", min_value=100, max_value=10000, value=st.session_state.interval, step=100)

        if use_multimeter and available_multimeter_devices:
            configure_multimeter_status = configure_multimeter(st.session_state.multimeter_device)
            st.write(configure_multimeter_status)

elif choice == "Simulateur Batterie":
    st.header("Simulateur Batterie")

    if st.session_state.selected_device:
        st.session_state.soc = st.number_input("State of Charge (SOC) (%)", min_value=0, max_value=100, value=st.session_state.soc)
        set_soc_status = set_soc(st.session_state.selected_device, st.session_state.soc)
        st.write(set_soc_status)

        if st.button("Lancer le simulateur"):
            start_status = start_simulator(st.session_state.selected_device)
            st.write(start_status)
            st.session_state.output_on = True
            st.session_state.datalogging = True

            st.session_state.excel_file_path = initialize_excel_file(st.session_state.excel_directory)
            st.session_state.previous_soc = st.session_state.soc

        if st.button("Arrêter le simulateur"):
            stop_status = stop_simulator(st.session_state.selected_device)
            st.write(stop_status)
            st.session_state.output_on = False
            st.session_state.datalogging = False
            st.session_state.instant_current = 0.0
            st.session_state.instant_voltage = 0.0
            st.session_state.instant_soc = 0.0
            st.session_state.instant_multimeter_current = 0.0

        st.subheader("Moniteur en temps réel")
        col1, col2 = st.columns(2)
        with col1:
            st.write("Courant (A)")
            current_placeholder = st.empty()
            st.write("Courant Mesuré par le Multimètre (A)")
            multimeter_current_placeholder = st.empty()
            st.write("Courant Moyen par % SOC (A)")
            average_current_placeholder = st.empty()
        with col2:
            st.write("Tension (V)")
            voltage_placeholder = st.empty()
            st.write("SOC (%)")
            soc_placeholder = st.empty()

        if st.session_state.datalogging:
            current_sum = 0
            count = 0
            average_current_perc = 0
            while st.session_state.datalogging:
                instrument = rm.open_resource(st.session_state.selected_device)
                if st.session_state.mode == "Power Supply":
                    current_value = read_output_current_power_supply(instrument)
                    voltage_value = read_output_voltage_power_supply(instrument)
                else:
                    current_value = read_output_current_battery_simulator(instrument)
                    voltage_value = read_output_voltage_battery_simulator(instrument)
                    soc_value = read_soc_battery_simulator(instrument)

                instrument.close()

                multimeter_current_value = read_multimeter_current(st.session_state.multimeter_device) if st.session_state.use_multimeter else None

                if current_value is not None and voltage_value is not None:
                    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    st.session_state.instant_current = current_value
                    st.session_state.instant_voltage = voltage_value
                    st.session_state.instant_soc = soc_value
                    if multimeter_current_value is not None:
                        st.session_state.instant_multimeter_current = multimeter_current_value

                    current_sum += current_value
                    count += 1

                    current_placeholder.metric("Courant (A)", current_value)
                    voltage_placeholder.metric("Tension (V)", voltage_value)
                    soc_placeholder.metric("SOC (%)", soc_value)
                    if multimeter_current_value is not None:
                        multimeter_current_placeholder.metric("Multimeter Current (A)", multimeter_current_value)

                    if soc_value < st.session_state.previous_soc - 2:
                        average_current_perc = current_sum / count
                        st.session_state.previous_soc = soc_value
                        current_sum = 0
                        count = 0
                        average_current_placeholder.metric("Courant Moyen par % SOC (A)", average_current_perc)

                    data = {
                        "Timestamp": timestamp,
                        "Current (A)": current_value,
                        "Voltage (V)": voltage_value,
                        "SOC (%)": soc_value,
                        "Average Current per SOC (%) (A)": average_current_perc,
                        "Multimeter Current (A)": multimeter_current_value if multimeter_current_value is not None else ''
                    }
                    append_to_excel(st.session_state.excel_file_path, data)

                    if soc_value <= 0:
                        st.session_state.datalogging = False
                        st.write("Simulation terminée : SOC est inférieur ou égal à 0%")
                        stop_status = stop_simulator(st.session_state.selected_device)
                        st.write(stop_status)

                    # Afficher les acquisitions dans le terminal
                    print(data)

                time.sleep(st.session_state.interval / 1000.0)

        if st.button("Charger et visualiser les données"):
            if st.session_state.excel_file_path:
                df = pd.read_excel(st.session_state.excel_file_path)
                fig_current = px.line(df, x='Timestamp', y='Current (A)', title='Courant (A) en fonction du temps')
                fig_voltage = px.line(df, x='Timestamp', y='Voltage (V)', title='Tension (V) en fonction du temps')
                fig_soc = px.line(df, x='Timestamp', y='SOC (%)', title='SOC (%) en fonction du temps')
                st.plotly_chart(fig_current)
                st.plotly_chart(fig_voltage)
                st.plotly_chart(fig_soc)
                if 'Multimeter Current (A)' in df.columns:
                    fig_multimeter_current = px.line(df, x='Timestamp', y='Multimeter Current (A)', title='Courant Mesuré par le Multimètre (A) en fonction du temps')
                    st.plotly_chart(fig_multimeter_current)
                if 'Average Current per SOC (%) (A)' in df.columns:
                    fig_avg_current_perc = px.line(df, x='SOC (%)', y='Average Current per SOC (%) (A)', title='Courant Moyen par % SOC (A)')
                    st.plotly_chart(fig_avg_current_perc)
