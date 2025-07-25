# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time
import html
import xml.etree.ElementTree as ET

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore di Profili Avanzato", page_icon="📫", layout="centered")

# --- STILE CSS PERSONALIZZATO E SCRIPT JS ---
st.markdown("""
<style>
/* Stile per l'iframe dell'email */
iframe {
    color-scheme: light;
}
/* Stile per il testo semplice dell'email */
.email-text-body {
    white-space: pre-wrap;
    font-family: monospace;
    color: #FAFAFA;
    background-color: rgba(40, 43, 54, 0.5);
    padding: 1rem;
    border-radius: 0.5rem;
    border: 1px solid rgba(250, 250, 250, 0.2);
}
/* Stile per i campi di solo testo, per renderli selezionabili */
.selectable-text-field {
    border: 1px solid rgba(250, 250, 250, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 1rem;
    background-color: #0E1117;
    color: #FAFAFA;
    width: 100%;
    margin-bottom: 1rem;
    box-sizing: border-box;
}
/* Stile per il contenitore dell'email con icona di copia */
.email-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    border: 1px solid rgba(250, 250, 250, 0.2);
    border-radius: 0.5rem;
    padding: 0.75rem;
    background-color: #0E1117;
    margin-bottom: 1rem;
}
.email-container span {
    color: #FAFAFA;
    font-family: "Source Sans Pro", sans-serif;
    font-size: 1rem;
}
.copy-icon {
    cursor: pointer;
    font-size: 1rem; /* Dimensione ridotta per allinearsi meglio */
    margin-left: 10px;
    padding: 4px 8px;
    border-radius: 4px;
    transition: all 0.2s;
}
.copy-icon:hover {
    opacity: 0.7;
    background-color: rgba(250, 250, 250, 0.1);
}
</style>
<script>
// Funzione di copia robusta che funziona su HTTP e HTTPS
function copyToClipboard(element, text) {
    var tempInput = document.createElement("input");
    tempInput.style = "position: absolute; left: -1000px; top: -1000px";
    tempInput.value = text;
    document.body.appendChild(tempInput);
    tempInput.select();
    tempInput.setSelectionRange(0, 99999); /* For mobile devices */

    try {
        document.execCommand("copy");
        // Fornisce un feedback visivo all'utente
        var originalText = element.innerText;
        element.innerText = "Copiato!";
        element.style.color = "#28a745"; // Verde successo
        setTimeout(function() {
            element.innerText = originalText;
            element.style.color = ""; // Ripristina colore
        }, 1500); // Cambia di nuovo dopo 1.5 secondi
    } catch (err) {
        alert("Errore: impossibile copiare l'indirizzo.");
    }

    document.body.removeChild(tempInput);
}
</script>
""", unsafe_allow_html=True)


# --- COSTANTI E DATI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}

# ==============================================================================
#                      FUNZIONI API PER I SERVIZI EMAIL
# ==============================================================================

# --- GUERRILLA MAIL ---
def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER, timeout=10)
        r.raise_for_status()
        data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "service": "guerrilla"}
    except requests.exceptions.RequestException as e:
        st.error(f"Errore creazione email (Guerrilla): {e}")
        return None

# --- MAIL.TM ---
@st.cache_data(ttl=3600)
def get_mailtm_domains():
    try:
        r = requests.get("https://api.mail.tm/domains", headers=USER_AGENT_HEADER, timeout=10)
        r.raise_for_status()
        # FIX: L'API restituisce un dizionario, la lista è nella chiave 'hydra:member'
        return [domain['domain'] for domain in r.json().get('hydra:member', [])]
    except requests.exceptions.RequestException as e:
        print(f"Could not fetch Mail.tm domains: {e}")
        return []

def create_mailtm_account(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=12))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    try:
        requests.post("https://api.mail.tm/accounts", json={"address": address, "password": password}, headers=USER_AGENT_HEADER, timeout=10).raise_for_status()
        token_resp = requests.post("https://api.mail.tm/token", json={"address": address, "password": password}, headers=USER_AGENT_HEADER, timeout=10)
        token_resp.raise_for_status()
