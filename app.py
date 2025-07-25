# -*- coding: utf-8 -*-
import random
import string
import requests
import pandas as pd
import streamlit as st
from faker import Faker
import xml.etree.ElementTree as ET

st.set_page_config(page_title="Fake Profile Generator (mail.tm full + copy email)", page_icon="📨", layout="centered")

PREDEFINED_IBANS = {
    'IT': ['IT60X0542811101000000123456', 'IT12A0306912345100000067890'],
    'FR': ['FR1420041010050500013M02606', 'FR7630006000011234567890189'],
    'DE': ['DE89370400440532013000', 'DE02100100100006820101'],
    'LU': ['LU280019400644750000', 'LU120010001234567891']
}

def get_mailtm_domains():
    try:
        r = requests.get("https://api.mail.tm/domains", headers={'Accept': 'application/xml'})
        r.raise_for_status()
        xml_root = ET.fromstring(r.text)
        return list({el.text for el in xml_root.findall(".//domain")})
    except:
        return []

def create_mailtm_account(domain):
    username = ''.join(random.choices(string.ascii_lowercase + string.digits, k=10))
    password = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
    address = f"{username}@{domain}"
    data = {"address": address, "password": password}
    try:
        requests.post("https://api.mail.tm/accounts", json=data).raise_for_status()
        token_resp = requests.post("https://api.mail.tm/token", json=data)
        token_resp.raise_for_status()
        return {"address": address, "token": token_resp.json()['token']}
    except:
        return None

def inbox_mailtm(address, token):
    st.subheader(f"📬 Inbox per [{address}](mailto:{address})")

    # Copy-to-clipboard HTML button (safe)
    st.markdown(f'''
        <input type="text" value="{address}" id="copyEmail" style="position:absolute; left:-1000px;">
        <button onclick="navigator.clipboard.writeText(document.getElementById('copyEmail').value)">Copia indirizzo email</button>
        ''', unsafe_allow_html=True)

    if st.button("🔁 Controlla inbox (mail.tm)"):
        headers = {'Authorization': f'Bearer {token}'}
        try:
            r = requests.get("https://api.mail.tm/messages", headers=headers)
            messages = r.json().get("hydra:member", [])
            if not messages:
                st.info("📭 Nessun messaggio trovato.")
            for m in messages:
                msg_id = m["id"]
                detail_resp = requests.get(f"https://api.mail.tm/messages/{msg_id}", headers=headers)
                msg = detail_resp.json()
                with st.expander(f"✉️ {msg.get('from',{}).get('address')} | {msg.get('subject')}"):
                    st.markdown(f"**Oggetto:** {msg.get('subject', 'N/A')}")
                    st.markdown(f"**Mittente:** {msg.get('from',{}).get('address', 'N/A')}")
                    st.markdown(f"**Data:** {msg.get('createdAt', '')}")
                    st.markdown("---")
                    html_content = msg.get("html")
                    if html_content and isinstance(html_content, str):
                        st.markdown("**Contenuto (HTML):**", unsafe_allow_html=True)
                        st.components.v1.html(html_content, height=300, scrolling=True)
                    elif msg.get("text"):
                        st.markdown("**Contenuto (Testo):**")
                        st.code(msg["text"])
                    else:
                        st.markdown("**Anteprima:**")
                        st.code(msg.get("intro", "Nessun contenuto."))
                    if msg.get("attachments"):
                        st.markdown("**📎 Allegati:**")
                        for att in msg["attachments"]:
                            st.markdown(f"- [{att.get('filename')}]({att.get('downloadUrl')})")
        except Exception as e:
            st.warning(f"Errore nella lettura: {e}")

def get_next_iban(cc):
    cc = cc.upper()
    if 'iban_state' not in st.session_state: st.session_state.iban_state = {}
    if cc not in st.session_state.iban_state or st.session_state.iban_state[cc]['index'] >= len(st.session_state.iban_state[cc]['list']):
        lst = PREDEFINED_IBANS.get(cc, ["N/A"]); random.shuffle(lst)
        st.session_state.iban_state[cc] = {'list': lst, 'index': 0}
    st.session_state.iban_state[cc]['index'] += 1
    return st.session_state.iban_state[cc]['list'][st.session_state.iban_state[cc]['index'] - 1]

def generate_profile(country, extra_fields, selected_domain):
    locs = {'Italia': 'it_IT', 'Francia': 'fr_FR', 'Germania': 'de_DE', 'Lussemburgo': 'fr_LU'}
    codes = {'Italia': 'IT', 'Francia': 'FR', 'Germania': 'DE', 'Lussemburgo': 'LU'}
    locale, code = locs[country], codes[country]
    fake = Faker(locale)
    p = {
        'Nome': fake.first_name(),
        'Cognome': fake.last_name(),
        'Data di Nascita': fake.date_of_birth(minimum_age=18, maximum_age=80).strftime('%d/%m/%Y'),
        'Indirizzo': fake.address().replace("\n", ", "),
        'IBAN': get_next_iban(code),
        'Paese': country
    }

    if 'Email' in extra_fields:
        result = create_mailtm_account(selected_domain)
        st.session_state.email_info = result
        p["Email"] = result["address"] if result else "Errore"

    if 'Telefono' in extra_fields: p['Telefono'] = fake.phone_number()
    if 'Codice Fiscale' in extra_fields: p['Codice Fiscale'] = fake.ssn() if locale == 'it_IT' else 'N/A'
    if 'Partita IVA' in extra_fields: p['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
    return pd.DataFrame([p])

# ---------------- UI ---------------- #

st.title("📨 Generatore di Profili Fake (mail.tm - HTML completo + copia email)")

if 'final_df' not in st.session_state: st.session_state.final_df = None
if 'email_info' not in st.session_state: st.session_state.email_info = None

with st.sidebar:
    st.header("⚙️ Opzioni")
    country = st.selectbox("Paese", ["Italia", "Francia", "Germania", "Lussemburgo"])
    n = st.number_input("Numero di profili", 1, 25, 1)
    fields = st.multiselect("Campi aggiuntivi", ["Email", "Telefono", "Codice Fiscale", "Partita IVA"], default=["Email"])

    all_domains = get_mailtm_domains()
    if not all_domains:
        st.error("⚠️ Nessun dominio disponibile da mail.tm")
        st.stop()
    selected_domain = st.selectbox("Dominio mail.tm", all_domains)

    if st.button("🚀 Genera Profili"):
        dfs = [generate_profile(country, fields, selected_domain) for _ in range(n)]
        st.session_state.final_df = pd.concat(dfs, ignore_index=True)

if st.session_state.final_df is not None:
    st.success(f"✅ Generati {len(st.session_state.final_df)} profili.")
    st.dataframe(st.session_state.final_df)
    csv = st.session_state.final_df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Scarica CSV", csv, "profili.csv", "text/csv")

    info = st.session_state.email_info
    if 'Email' in st.session_state.final_df.columns and info:
        inbox_mailtm(info["address"], info["token"])
