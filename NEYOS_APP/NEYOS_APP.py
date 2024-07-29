import streamlit as st

# Définir les pages
sub_software_1_option_1 = st.Page("sub_software_1/option_1_1.py", title="analyse Saleae", icon="📄")
sub_software_1_option_2 = st.Page("sub_software_1/option_1_2.py", title="profil bat analyse", icon="📄")
sub_software_1_option_3 = st.Page("sub_software_1/option_1_3.py", title="extrat siglent", icon="📄")

sub_software_2 = st.Page("sub_software_2.py", title="Sous-Logiciel 2", icon="📄")
sub_software_3 = st.Page("sub_software_3.py", title="Datalogger", icon="📄")

# Définir la navigation
pg = st.navigation({
    "Sous-Logiciel 1": [sub_software_1_option_1, sub_software_1_option_2, sub_software_1_option_3],
    "Autres": [sub_software_2, sub_software_3]
})

# Configuration de la page
st.set_page_config(page_title="Mon Application", page_icon="🚀")

# Exécuter la page sélectionnée
pg.run()
