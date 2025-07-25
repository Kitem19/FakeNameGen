# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import time
import html
import hashlib
from streamlit_js_eval import streamlit_js_eval

# --- CONFIGURAZIONE PAGINA ---
st.set_page_config(page_title="Generatore di Profili Multi-Provider", page_icon="📫", layout="centered")

# --- STILE CSS PERSONALIZZATO ---
st.markdown("""
<style>
/* Stile generale per la leggibilità */
iframe { color-scheme: light; }
.email-text-body { white-space: pre-wrap; font-family: monospace; color: #FAFAFA; background-color: rgba(40, 43, 54, 0.5); padding: 1rem; border-radius: 0.5rem; border: 1px solid rgba(250, 250, 250, 0.2); }
/* Stile per i campi di testo per permettere la selezione */
.selectable-text-field { padding: 0.75rem; font-family: "Source Sans Pro", sans-serif; font-size: 1rem; background-color: #0E1117; color: #FAFAFA; width: 100%; box-sizing: border-box; }
/* Stile per rendere il pulsante di copia piccolo e discreto */
div[data-testid*="stButton"] button {
    padding: 0.25rem 0.5rem;
    font-size: 1.2rem;
    line-height: 1.5;
    width: auto; /* Permette al pulsante di adattarsi al contenuto (l'icona) */
    margin-top: 29px; /* Allinea verticalmente l'icona con il campo di testo */
}
</style>
""", unsafe_allow_html=True)

# --- COSTANTI E DATI PREDEFINITI ---
PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}
USER_AGENT_HEADER = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
TEMPMAIL_DOMAINS = ["greencafe24.com", "chacuo.net", "fexpost.com"]

# ==============================================================================
#                      FUNZIONI API PER OGNI PROVIDER
# ==============================================================================
def create_guerrillamail_account():
    try:
        r = requests.get("https://api.guerrillamail.com/ajax.php?f=get_email_address", headers=USER_AGENT_HEADER)
        r.raise_for_status(); data = r.json()
        return {"address": data['email_addr'], "sid_token": data['sid_token'], "provider": "Guerrilla Mail"}
    except Exception as e: st.error(f"Errore Guerrilla Mail: {e}"); return None

def inbox_guerrillamail(info, auto_refresh_placeholder):
    st.subheader(f"📬 Inbox per: `{info['address']}`")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Controlla messaggi"):
            st.session_state.auto_refresh = False
            with st.spinner("Recupero messaggi..."):
                r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
                r.raise_for_status(); st.session_state.messages = r.json().get("list", [])
            st.rerun()
    with col2:
        if st.button("🔄 Auto-Refresh (2 min)"):
            st.session_state.auto_refresh = True; st.session_state.refresh_stop_time = time.time() + 120
            st.session_state.initial_message_count = len(st.session_state.get('messages') or [])
            st.rerun()

    if st.session_state.get('auto_refresh'):
        if time.time() > st.session_state.refresh_stop_time:
            auto_refresh_placeholder.warning("Auto-Refresh terminato."); st.session_state.auto_refresh = False; st.rerun()
        else:
            remaining = int(st.session_state.refresh_stop_time - time.time())
            auto_refresh_placeholder.info(f"Ricerca automatica attiva... Tempo rimasto: {remaining}s")
            r = requests.get(f"https://api.guerrillamail.com/ajax.php?f=check_email&seq=0&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER)
            r.raise_for_status(); st.session_state.messages = r.json().get("list", [])
            if len(st.session_state.messages) > st.session_state.initial_message_count:
                auto_refresh_placeholder.success("Nuovo messaggio trovato! Auto-refresh interrotto."); st.session_state.auto_refresh = False; st.rerun()
            else:
                time.sleep(10); st.rerun()
    
    if 'messages' in st.session_state and st.session_state.messages is not None:
        messages = st.session_state.messages
        if not messages: st.info("📭 La casella di posta è vuota.")
        else:
            st.success(f"Trovati {len(messages)} messaggi.")
            for m in reversed(messages):
                with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                    email_body = requests.get(f"https://api.guerrillamail.com/ajax.php?f=fetch_email&email_id={m['mail_id']}&sid_token={info['sid_token']}", headers=USER_AGENT_HEADER).json().get('mail_body', '<i>Corpo non disponibile.</i>')
                    if "<html>" in email_body.lower() or "<div>" in email_body.lower(): st.components.v1.html(email_body, height=400, scrolling=True)
                    else: st.markdown(f"<div class='email-text-body'>{html.unescape(email_body)}</div>", unsafe_allow_html=True)

def create_mailtm_account():
    domain = random.choice(TEMPMAIL_DOMAINS)
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    address = f"{username}@{domain}"
    return {"address": address, "provider": "Mail.tm"}

def inbox_mailtm(info, auto_refresh_placeholder):
    st.subheader(f"📬 Inbox per: `{info['address']}`")
    api_key = st.secrets.get("rapidapi", {}).get("key")
    if not api_key: st.error("Chiave API per Mail.tm (RapidAPI) non configurata nei Secrets di Streamlit!"); return
    url = f"https://privatix-temp-mail-v1.p.rapidapi.com/request/mail/id/{hashlib.md5(info['address'].encode('utf-8')).hexdigest()}/"
    headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": "privatix-temp-mail-v1.p.rapidapi.com"}
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Controlla messaggi (Mail.tm)"):
            st.session_state.auto_refresh = False
            with st.spinner("Recupero messaggi..."):
                r = requests.get(url, headers=headers); r.raise_for_status()
                messages = r.json(); st.session_state.messages = messages if isinstance(messages, list) else []
            st.rerun()
    with col2:
        if st.button("🔄 Auto-Refresh (2 min)"):
            st.session_state.auto_refresh = True; st.session_state.refresh_stop_time = time.time() + 120
            st.session_state.initial_message_count = len(st.session_state.get('messages') or [])
            st.rerun()
            
    if st.session_state.get('auto_refresh'):
        if time.time() > st.session_state.refresh_stop_time:
            auto_refresh_placeholder.warning("Auto-Refresh terminato."); st.session_state.auto_refresh = False; st.rerun()
        else:
            remaining = int(st.session_state.refresh_stop_time - time.time())
            auto_refresh_placeholder.info(f"Ricerca automatica attiva... Tempo rimasto: {remaining}s")
            r = requests.get(url, headers=headers); r.raise_for_status()
            messages = r.json(); st.session_state.messages = messages if isinstance(messages, list) else st.session_state.messages
            if len(st.session_state.messages) > st.session_state.initial_message_count:
                auto_refresh_placeholder.success("Nuovo messaggio trovato! Auto-refresh interrotto."); st.session_state.auto_refresh = False; st.rerun()
            else:
                time.sleep(10); st.rerun()

    if 'messages' in st.session_state and st.session_state.messages is not None:
        messages = st.session_state.messages
        if not messages: st.info("📭 La casella di posta è vuota.")
        else:
            st.success(f"Trovati {len(messages)} messaggi.")
            for m in reversed(messages):
                with st.expander(f"✉️ **Da:** {m['mail_from']} | **Oggetto:** {m['mail_subject']}"):
                    email_body = m.get('mail_html') or m.get('mail_text') or "<i>Corpo non disponibile.</i>"
                    st.components.v1.html(email_body, height=400, scrolling=True)

# ==============================================================================
#                      LOGICA PRINCIPALE E UI
# ==============================================================================
def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, provider):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]; fake = Faker(locale)
    p = {'Nome': fake.first_name(), 'Cognome': fake.last_name(), 'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'), 'Indirizzo': fake.address().replace("\n", ", "), 'IBAN': get_next_iban(code), 'Paese': country}
    if 'Email' in extra_fields:
        if provider == "Guerrilla Mail": result = create_guerrillamail_account()
        elif provider == "Mail.tm (richiede chiave API)": result = create_mailtm_account()
        st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Creazione email fallita"
    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

def display_profile_card(profile_data):
    st.subheader("📄 Dettagli del Profilo Generato")
    def render_field(label, value):
        st.markdown(f"**{label}**")
        col1, col2 = st.columns([0.9, 0.1])
        with col1:
            st.markdown(f"<div class='selectable-text-field' style='border: 1px solid rgba(250, 250, 250, 0.2); border-radius: 0.5rem;'>{value}</div>", unsafe_allow_html=True)
        with col2:
            if st.button("📋", key=f"copy_{label.lower()}", help=f"Copia {label}"):
                streamlit_js_eval(js_expressions=f"navigator.clipboard.writeText('{value}')")
                st.toast(f"'{value}' copiato!")
    
    col1, col2 = st.columns(2)
    with col1: render_field("Nome", profile_data.get("Nome", "N/A"))
    with col2: render_field("Cognome", profile_data.get("Cognome", "N/A"))
    
    email = profile_data.get("Email")
    if email and "fallita" not in email:
        st.markdown(f"**Email**")
        col1, col2 = st.columns([0.9, 0.1])
        with col1: st.markdown(f"<div class='selectable-text-field' style='border: 1px solid rgba(250, 250, 250, 0.2); border-radius: 0.5rem;'><a href='mailto:{email}'>{email}</a></div>", unsafe_allow_html=True)
        with col2:
            if st.button("📋", key="copy_email", help="Copia Email"):
                streamlit_js_eval(js_expressions=f"navigator.clipboard.writeText('{email}')")
                st.toast(f"Email '{email}' copiata!")

    render_field("Data di Nascita", profile_data.get("Data di Nascita", "N/A"))
    render_field("Indirizzo", profile_data.get("Indirizzo", "N/A"))
    render_field("IBAN", profile_data.get("IBAN", "N/A"))
    if "Telefono" in profile_data: render_field("Telefono", profile_data.get("Telefono"))
    if "Codice Fiscale" in profile_data: render_field("Codice Fiscale", profile_data.get("Codice Fiscale"))
    if "Partita IVA" in profile_data: render_field("Partita IVA", profile_data.get("Partita IVA"))
    st.markdown("---")

st.title("📫 Generatore di Profili Multi-Provider")
st.markdown("Genera profili fittizi completi di email temporanee funzionanti.")

for key in ['final_df', 'email_info', 'messages', 'show_success', 'auto_refresh', 'refresh_stop_time', 'initial_message_count']:
    if key not in st.session_state: st.session_state[key] = None if key not in ['show_success', 'auto_refresh'] else False

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])
    provider = st.selectbox("Provider Email", ["Guerrilla Mail", "Mail.tm (richiede chiave API)"])
    
    is_button_disabled = False
    if provider == "Mail.tm (richiede chiave API)":
        if not st.secrets.get("rapidapi", {}).get("key"):
            st.error("Per usare Mail.tm, imposta la chiave API nei Secrets di Streamlit.")
            is_button_disabled = True
    
    if st.button("🚀 Genera Profili", type="primary", disabled=is_button_disabled):
        with st.spinner("Generazione in corso..."):
            dfs = [generate_profile(country, fields, provider) for _ in range(n)]
        st.session_state.final_df = pd.concat([df for df in dfs if not df.empty], ignore_index=True)
        st.session_state.messages = None; st.session_state.show_success = True; st.session_state.auto_refresh = False

if st.session_state.final_df is not None:
    if st.session_state.show_success: st.success(f"✅ Generati {len(st.session_state.final_df)} profili."); st.session_state.show_success = False
    if len(st.session_state.final_df) == 1: display_profile_card(st.session_state.final_df.iloc[0])
    else: st.dataframe(st.session_state.final_df)
    
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info and "fallita" not in info.get("address", "fallita"):
        auto_refresh_placeholder = st.empty()
        if info['provider'] == "Guerrilla Mail": inbox_guerrillamail(info, auto_refresh_placeholder)
        elif info['provider'] == "Mail.tm": inbox_mailtm(info, auto_refresh_placeholder)
