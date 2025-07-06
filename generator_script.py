
import os
import random
import faker
import pandas as pd
import requests
import json
from faker.providers import address, phone_number, person, date_time, internet, company
from faker.providers.bank import Provider as BankProvider

IBAN_CACHE_FILE = "iban_cache.json"
EXCLUDED_IBAN_FILE = "iban_exclude.json"

def iban_valido(iban):
    url = f"https://openiban.com/validate/{iban}?getBIC=true&validateBankCode=true"
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data.get("valid", False)
        else:
            return False
    except Exception:
        return False

def carica_cache():
    if os.path.exists(IBAN_CACHE_FILE):
        with open(IBAN_CACHE_FILE, "r") as f:
            return json.load(f)
    return {}

def salva_cache(cache):
    with open(IBAN_CACHE_FILE, "w") as f:
        json.dump(cache, f)

def carica_esclusi():
    if os.path.exists(EXCLUDED_IBAN_FILE):
        with open(EXCLUDED_IBAN_FILE, "r") as f:
            return set(json.load(f))
    return set()

def salva_esclusi(exclude_set):
    with open(EXCLUDED_IBAN_FILE, "w") as f:
        json.dump(list(exclude_set), f)

def ottieni_o_aggiungi_iban(country_code):
    country_code = country_code.upper()
    cache = carica_cache()
    esclusi = carica_esclusi()
    if country_code not in cache:
        cache[country_code] = []

    if len(cache[country_code]) >= 5:
        salva_cache(cache)
        return random.choice(cache[country_code])

    tentativi = 0
    while len(cache[country_code]) < 5 and tentativi < 50:
        fake_temp = faker.Faker()
        fake_temp.add_provider(BankProvider)
        nuovo_iban = fake_temp.iban(country_code=country_code)
        if nuovo_iban in cache[country_code] or nuovo_iban in esclusi:
            tentativi += 1
            continue
        if iban_valido(nuovo_iban):
            cache[country_code].append(nuovo_iban)
            salva_cache(cache)
            return nuovo_iban
        tentativi += 1

    salva_cache(cache)
    return None

def escludi_iban(iban):
    esclusi = carica_esclusi()
    cache = carica_cache()

    for paese, lista in cache.items():
        if iban in lista:
            lista.remove(iban)
            esclusi.add(iban)
            break

    salva_cache(cache)
    salva_esclusi(esclusi)

def genera_dati(paese, n=1, campi=None):
    localizzazioni = {
        'italia': 'it_IT',
        'francia': 'fr_FR',
        'germania': 'de_DE',
        'lussemburgo': 'fr_LU'
    }
    iso_codes = {
        'italia': 'IT',
        'francia': 'FR',
        'germania': 'DE',
        'lussemburgo': 'LU'
    }

    paese = paese.lower()
    if paese not in localizzazioni:
        raise ValueError("Paese non valido. Scegli tra Italia, Francia, Germania, Lussemburgo.")

    fake = faker.Faker(localizzazioni[paese])
    fake.add_provider(address)
    fake.add_provider(phone_number)
    fake.add_provider(person)
    fake.add_provider(date_time)
    fake.add_provider(internet)
    fake.add_provider(company)

    dati = []
    for _ in range(n):
        profilo = {}
        if 'Nome' in campi: profilo['Nome'] = fake.first_name()
        if 'Cognome' in campi: profilo['Cognome'] = fake.last_name()
        if 'Data di Nascita' in campi: profilo['Data di Nascita'] = fake.date_of_birth(minimum_age=18, maximum_age=75).strftime('%d/%m/%Y')
        if 'Indirizzo' in campi: profilo['Indirizzo'] = fake.address().replace("\n", ", ")
        if 'Telefono' in campi: profilo['Telefono'] = fake.phone_number()
        if 'Email' in campi: profilo['Email'] = fake.email()
        if 'Codice Fiscale' in campi: profilo['Codice Fiscale'] = fake.ssn() if paese == 'italia' else 'N/A'
        if 'Partita IVA' in campi: profilo['Partita IVA'] = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'
        if 'IBAN' in campi:
            iban = ottieni_o_aggiungi_iban(iso_codes[paese])
            profilo['IBAN'] = iban if iban else "Non trovato"
        if 'Paese' in campi: profilo['Paese'] = paese.capitalize()
        dati.append(profilo)

    return pd.DataFrame(dati)
