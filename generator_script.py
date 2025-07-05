
import random
import faker
import pandas as pd
from faker.providers import bank, address, phone_number, person, date_time, internet, company

def genera_dati(paese, n=1):
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
        nome = fake.first_name()
        cognome = fake.last_name()
        data_nascita = fake.date_of_birth(minimum_age=18, maximum_age=75).strftime('%d/%m/%Y')
        indirizzo = fake.address().replace("\n", ", ")
        telefono = fake.phone_number()
        iban = fake.iban()
        email = fake.email()
        codice_fiscale = fake.ssn() if paese == 'italia' else 'N/A'
        partita_iva = fake.vat_id() if hasattr(fake, 'vat_id') else 'N/A'

        dati.append({
            'Nome': nome,
            'Cognome': cognome,
            'Data di Nascita': data_nascita,
            'Indirizzo': indirizzo,
            'Telefono': telefono,
            'Email': email,
            'Codice Fiscale': codice_fiscale,
            'Partita IVA': partita_iva,
            'IBAN': iban,
            'Paese': paese.capitalize()
        })

    df = pd.DataFrame(dati)
    return df
