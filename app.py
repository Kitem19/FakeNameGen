# app.py

import streamlit as st
import pandas as pd
# Non servono più os, json, datetime in questa versione semplificata
# from datetime import datetime
# import os
# import json

# Importa solo la funzione per generare un singolo profilo con campi specifici
from generator_script import genera_profilo_singolo # Il nome funzione rimane lo stesso

st.set_page_config(page_title="Generatore Profilo Fittizio Personalizzato", layout="centered")
st.title("👤 Generatore di Profilo Fittizio Personalizzato con IBAN Predefinito")

st.markdown("""
Questo strumento genera un profilo fittizio alla volta.
I campi **Nome, Cognome, Data di Nascita, Indirizzo e IBAN** sono sempre inclusi.
Puoi selezionare quali altri campi aggiungere al profilo.
L'IBAN viene selezionato da una lista predefinita per il paese scelto.
""")

# Seleziona il paese per i dati di base e l'IBAN
paese = st.selectbox("🌍 Scegli un paese", ["Italia", "Francia", "Germania", "Lussemburgo"])

# Definisci i campi opzionali che l'utente può aggiungere
campi_opzionali = ["Telefono", "Email", "Codice Fiscale", "Partita IVA"]

# Multiselect per scegliere i campi opzionali
campi_opzionali_scelti = st.multiselect(
    "➕ Scegli i campi aggiuntivi da includere",
    options=campi_opzionali,
    default=[] # Di default, nessun campo opzionale è selezionato
)

# Pulsante per generare un singolo profilo
if st.button("🎲 Genera Nuovo Profilo"):
    # Chiamiamo la funzione che genera un singolo profilo.
    # Passiamo il paese e la lista dei campi opzionali scelti.
    with st.spinner(f"Generazione di un profilo per {paese} con i campi selezionati..."):
        profilo_df = genera_profilo_singolo(paese, campi_opzionali_scelti) # Passiamo la lista

    # Controlla se un profilo è stato generato con successo
    if profilo_df is None or profilo_df.empty:
        # Questo dovrebbe accadere solo se la lista IBAN è esaurita o c'è un errore grave in Faker
        st.error("Impossibile generare un profilo in questo momento (forse la lista IBAN predefinita è esaurita per il paese selezionato?).")
    else:
        st.success(f"✅ Profilo generato per {paese}:")
        # Mostra il DataFrame con una sola riga. Usiamo hide_index=True per pulizia.
        st.dataframe(profilo_df, hide_index=True)

        # Offri il download per questo singolo profilo
        csv = profilo_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Scarica CSV",
            data=csv,
            file_name="profilo_fittizio_singolo.csv",
            mime="text/csv"
        )
