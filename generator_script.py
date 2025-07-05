import random
import faker
import pandas as pd
from faker.providers import bank, address, phone_number, person, date_time, internet, company

def genera_dati(paese, n=1, campi=None):
    localizzazioni = {
        'italia': 'it_IT',
        'francia': 'fr_FR',
        'germania': 'de_DE',
        'lussemburgo': 'fr_LU'
    }

    paese = paese.lower()
    if paese not in localizzazioni:
        raise ValueError("Paese non valido. Scegli tra Italia, Francia, Germania, Lussemburgo.")

    fake = faker.Faker(localizzazioni[paese])
    fake.add_provider(bank)
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
        if 'IBAN' in campi: profilo['IBAN'] = fake.iban()
        if 'Paese' in campi: profilo['Paese'] = paese.capitalize()
        dati.append(profilo)

    return pd.DataFrame(dati)
