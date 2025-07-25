Helvetica;
;;
  # -*- coding: utf-8 -*-\
import random\
import string\
import requests\
import pandas as pd\
import streamlit as st\
from faker import Faker\
import time\
import html # Importiamo html per decodificare le entit\'e0 HTML\
# --- CONFIGURAZIONE PAGINA ---\
st.set_page_config(page_title="Generatore di Profili (Guerrilla Mail)", page_icon="  ", layout="centered")\
# --- STILE CSS PERSONALIZZATO (FIX PER TESTO NERO E SELEZIONE) ---\
st.markdown("""\
<style>\
/* Forza il colore del testo nell'iframe dell'email a essere quello del tema */\
iframe \\
    color-scheme: light;\
\
/* Stile per il testo semplice dell'email, per renderlo bianco e leggibile */\
.email-text-body \\
    white-space: pre-wrap; /* Mantiene la formattazione come a capo e spazi */\
    font-family: monospace;\
    color: #FAFAFA; /* Testo bianco */\
    background-color: rgba(40, 43, 54, 0.5); /* Sfondo leggermente diverso per distinguerlo */\
    padding: 1rem;\
    border-radius: 0.5rem;\
    border: 1px solid rgba(250, 250, 250, 0.2);\
\
/* Stile per i campi di solo testo, per renderli simili a text_input ma selezionabili */\
.selectable-text-field \\
    border: 1px solid rgba(250, 250, 250, 0.2);\
    border-radius: 0.5rem;\
    padding: 0.75rem;\
    font-family: "Source Sans Pro", sans-serif;\
    font-size: 1rem;\
    background-color: #0E1117; /* Sfondo scuro di Streamlit */\
    color: #FAFAFA; /* Testo bianco di Streamlit */\
    width: 100%;\
    margin-bottom: 1rem;\
    box-sizing: border-box; /* Assicura che padding e border siano inclusi nella larghezza */\
\
</style>\
""", unsafe_allow_html=True)\
# --- COSTANTI E DATI PREDEFINITI ---\
PREDEFINED_IBANS = \\
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],\
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],\
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],\
    'LU': ['LU280019400644750000', 'LU120010001234567891']\
\
USER_AGENT_HEADER = \'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'\\
# ==============================================================================\
#                      FUNZIONI API PER GUERRILLA MAIL\
# ==============================================================================\
def create_guerrillamail_account():\
    try:\
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER)\
        r.raise_for_status(); data = r.json()\
        return \"address": data['email_addr'], "sid_token": data['sid_token']\\
    except requests.exceptions.RequestException as e: st.error(f"Errore nella creazione dell'email: \e\"); return None\
def inbox_guerrillamail(info):\
    st.subheader(f"   Inbox per: `\info['address']\`")\
    if st.button("   Controlla/Aggiorna messaggi"):\
        with st.spinner("Recupero messaggi..."):\
            try:\
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token=\info['sid_token']\", headers=USER_AGENT_HEADER)\
                r.raise_for_status(); st.session_state.messages = r.json().get("list", [])\
            except Exception as e: st.error(f"Errore lettura posta: \e\"); st.session_state.messages = []\
    \
    if 'messages' in st.session_state and st.session_state.messages is not None:\
        messages = st.session_state.messages\
        if not messages: st.info("   La casella di posta \'e8 vuota.")\
        else:\
            st.success(f"Trovati \len(messages)\ messaggi.")\
            for m in reversed(messages):\
                with st.expander(f"   **Da:** \m['mail_from']\ | **Oggetto:** \m['mail_subject']\"):\
                    with st.spinner("Caricamento corpo..."):\
                        full_email_resp = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id=\m['mail_id']\&sid_token=\info['sid_token']\", headers=USER_AGENT_HEADER)\
                        full_email_data = full_email_resp.json()\
                    timestamp = int(m['mail_timestamp']); date_str = time.strftime('%d/%m/%Y %H:%M:%S', time.localtime(timestamp))\
                    st.markdown(f"**Data:** \date_str\"); st.markdown("---")\
                    \
                    email_body_html = full_email_data.get('mail_body')\
                    \
                    # FIX: Se c'\'e8 HTML, usalo. Altrimenti, mostra il testo semplice con il nostro stile CSS.\
                    if "<html>" in email_body_html.lower() or "<div>" in email_body_html.lower():\
                        st.components.v1.html(email_body_html, height=400, scrolling=True)\
                    else:\
                        # Decodifica le entit\'e0 HTML (es. & -> &) e mostra in un div stilizzato\
                        plain_text = html.unescape(email_body_html)\
                        st.markdown(f"<div class='email-text-body'>\plain_text\</div>", unsafe_allow_html=True)\
# ==============================================================================\
#                      FUNZIONI DI LOGICA E UI\
# ==============================================================================\
def get_next_iban(cc):\
    cc = cc.upper()\
    if 'iban_state' not in st.session_state: st.session_state.iban_state = \\
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):\
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)\
        st.session_state.iban_state[cc] = \'list': lst, 'index': 0\\
    st.session_state.iban_state[cc]['index'] += 1\
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]\
def generate_profile(country, extra_fields):\
    locs = \'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'\\
    codes = \'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'\\
    locale, code = locs[country], codes[country]; fake = Faker(locale)\
    p = \'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\", ", "), 'IBAN': get_next_iban(code), 'Paese': country\\
    if 'Email' in extra_fields:\
        result = create_guerrillamail_account(); st.session_state.email_info = result\
        p["Email"] = result["address"] if result else "Creazione email fallita"\
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()\
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'\
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'\
    return pd.DataFrame([p])\
def display_profile_card(profile_data):\
    st.subheader("   Dettagli del Profilo Generato")\
    def render_field(label, value):\
        st.markdown(f"**\label\**")\
        st.markdown(f"<div class='selectable-text-field'>\value\</div>", unsafe_allow_html=True)\
    col1, col2 = st.columns(2)\
    with col1: render_field("Nome", profile_data.get("Nome", "N/A"))\
    with col2: render_field("Cognome", profile_data.get("Cognome", "N/A"))\
    render_field("Data di Nascita", profile_data.get("Data di Nascita", "N/A"))\
    render_field("Indirizzo", profile_data.get("Indirizzo", "N/A"))\
    render_field("IBAN", profile_data.get("IBAN", "N/A"))\
    if "Telefono" in profile_data: render_field("Telefono", profile_data.get("Telefono"))\
    if "Codice Fiscale" in profile_data: render_field("Codice Fiscale", profile_data.get("Codice Fiscale"))\
    if "Partita IVA" in profile_data: render_field("Partita IVA", profile_data.get("Partita IVA"))\
    if "Email" in profile_data and "fallita" not in profile_data["Email"]:\
        st.markdown(f"**Email:** [\profile_data['Email']\](mailto:\profile_data['Email']\)")\
    st.markdown("---")\
# --- INTERFACCIA UTENTE (UI) ---\
st.title("   Generatore di Profili con Guerrilla Mail")\
st.markdown("Genera profili fittizi completi di un'email temporanea funzionante e affidabile.")\
if 'final_df' not in st.session_state: st.session_state.final_df = None\
if 'email_info' not in st.session_state: st.session_state.email_info = None\
if 'messages' not in st.session_state: st.session_state.messages = None\
if 'show_success' not in st.session_state: st.session_state.show_success = False\
with st.sidebar:\
    st.header("   Opzioni")\
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])\
    n = st.number_input("Numero di profili", 1, 25, 1)\
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])\
    \
    if st.button("   Genera Profili", type="primary"):\
        with st.spinner("Generazione in corso..."):\
            dfs = [generate_profile(country, fields) for _ in range(n)]\
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)\
        st.session_state.messages = None; st.session_state.show_success = True\
if st.session_state.final_df is not None:\
    if st.session_state.show_success:\
        st.success(f"  Generati \len(st.session_state.final_df)\ profili.")\
        st.session_state.show_success = False\
    \
    if len(st.session_state.final_df) == 1:\
        display_profile_card(st.session_state.final_df.iloc[0])\
    else:\
        st.dataframe(st.session_state.final_df)\
    \
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')\
    st.download_button("   Scarica CSV", csv, "profili.csv", "text/csv")\
    info = st.session_state.email_info\
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):\
        inbox_guerrillamail(info)\

# --- Funzioni mail.tm ---
get_mailtm_domains

# --- Icona per copiare l'email ---

email_address = f"{username}@{domain}"
st.markdown(f"<b>Email:</b> {email_address} <button onClick=\"navigator.clipboard.writeText('{email_address}')\">📋</button>", unsafe_allow_html=True)


# --- Pulsante aggiorna messaggi ---

if st.button("Aggiorna Messaggi"):
    start_time = time.time()
    while time.time() - start_time < 120:
        messages = get_mailtm_messages(token)
        if messages:
            st.success("Hai ricevuto un nuovo messaggio!")
            break
        time.sleep(10)
