"""Controlla contatti/persone.json contro le regole di contatti/persone.schema.json.

Stessi due livelli del controllo del profilo, perche' guardano cose diverse:

  - lo SCHEMA guarda la forma: i campi ci sono tutti? il canale e' fra quelli
    ammessi? la data e' scritta gg/mm/aaaa? l'email ha una chiocciola?
  - questo SCRIPT guarda la coerenza, che lo schema non puo' vedere: il 31/02
    ha la forma giusta ma non esiste, un'azienda citata deve stare nel registro,
    due schede non possono avere lo stesso numero di telefono, e una persona
    sentita l'ultima volta due anni fa non e' un contatto: e' un ricordo.

Si lancia cosi', da qualsiasi cartella:

    python strumenti/valida_persone.py                controlla contatti/persone.json
    python strumenti/valida_persone.py altro.json     controlla un altro file

Il secondo modo serve per le prove: si controlla una copia sbagliata apposta
senza mettere le mani sui dati veri.

Esce con codice 0 se e' tutto a posto, 1 se c'e' almeno un errore. Gli avvisi
non fanno fallire il controllo: segnalano cose da guardare, non errori. Qui piu'
che altrove sono la parte utile, perche' un contatto non si rompe: invecchia.
"""

import sys
from datetime import date
from pathlib import Path

from condiviso import (
    RADICE,
    a_data,
    controlla_identificatori,
    controlla_schema,
    etichetta_percorso,
    leggi_json,
    prepara_stdout,
    quantifica,
    stampa_esito,
)

DATI = RADICE / "contatti" / "persone.json"
SCHEMA = RADICE / "contatti" / "persone.schema.json"

# Come per il profilo: se il file non c'e', non e' un guasto del repo.
MANCA_DATI = (
    "  contatti/persone.json non sta in git: sono nomi, numeri e email di\n"
    "  altre persone, e vivono solo sul computer di Federico.\n"
    "  Un clone di questo repo ha lo schema e i controlli, non i dati."
)

SEZIONI_CON_ID = ["aziende", "persone"]

# Come si chiama un singolo elemento di ogni sezione, al singolare e al plurale.
# Serve solo a scrivere messaggi in italiano corretto.
NOMI = {
    "persone": ("persona", "persone"),
    "aziende": ("azienda", "aziende"),
}

# Sei mesi senza sentirsi. Oltre, non e' piu' un contatto caldo: se ti serve,
# tanto vale saperlo prima di scrivergli "come promesso l'altro giorno".
GIORNI_FREDDO = 182


def nome_completo(persona):
    """"Mario Rossi", per i messaggi che parlano di una persona vera."""
    return f'{persona.get("nome", "?")} {persona.get("cognome", "?")}'.strip()


def controlla_date(dati, errori, avvisi):
    """Le date di contatto esistono, non sono nel futuro, sono in ordine."""
    oggi = date.today()

    for persona in dati.get("persone", []):
        etichetta = f'persona "{persona.get("id", "?")}"'
        quando = []

        for esperienza in persona.get("esperienze", []):
            testo = esperienza.get("data_contatto")
            if testo is None:
                continue
            giorno = a_data(testo)
            if giorno is None:
                errori.append(f'{etichetta}: la data "{testo}" non esiste')
                continue
            if giorno > oggi:
                errori.append(f"{etichetta}: il contatto del {testo} e' nel futuro")
            quando.append(giorno)

        # Le esperienze stanno dalla piu' recente alla piu' vecchia, come le
        # voci del profilo. Non e' un errore nei dati, ma un elenco mezzo
        # ordinato smette di dirti a colpo d'occhio a che punto sei.
        if quando != sorted(quando, reverse=True):
            avvisi.append(
                f"{etichetta}: le esperienze non sono in ordine, "
                "dalla piu' recente alla piu' vecchia"
            )


def controlla_ordine(dati, avvisi):
    """Le schede stanno in ordine alfabetico: le persone per cognome, le aziende
    per nome.

    Una rubrica si legge cercando un nome con l'occhio, non con il find: appena
    l'ordine si rompe si smette di fidarsi, e le aggiunte finiscono tutte in
    fondo. Come per le esperienze fuori ordine, e' un avviso: il dato resta
    vero, e' la rubrica che diventa scomoda.
    """
    persone = [
        (p.get("cognome", "").casefold(), p.get("nome", "").casefold())
        for p in dati.get("persone", [])
    ]
    if persone != sorted(persone):
        avvisi.append(
            "le persone non sono in ordine alfabetico per cognome"
        )

    aziende = [a.get("nome", "").casefold() for a in dati.get("aziende", [])]
    if aziende != sorted(aziende):
        avvisi.append("le aziende non sono in ordine alfabetico per nome")


def controlla_aziende(dati, errori, avvisi):
    """Ogni azienda citata da una persona deve esistere nel registro.

    Stessa idea delle competenze nel profilo: il nome dell'azienda e' scritto in
    un punto solo, e le esperienze lo richiamano. Se il rimando non aggancia
    niente, il campo dice un id e non un'azienda.
    """
    registro = {a.get("id") for a in dati.get("aziende", [])}
    citate = set()

    for persona in dati.get("persone", []):
        for esperienza in persona.get("esperienze", []):
            identificatore = esperienza.get("azienda_id")
            if identificatore is None:
                continue
            citate.add(identificatore)
            if identificatore not in registro:
                errori.append(
                    f'persona "{persona.get("id", "?")}": '
                    f'azienda "{identificatore}" non presente nel registro'
                )

    for identificatore in sorted(registro - citate):
        avvisi.append(
            f'azienda "{identificatore}": nel registro ma non ci lavora nessuno dei contatti'
        )


def controlla_recapiti(dati, avvisi):
    """Una scheda deve dire almeno un modo per raggiungere la persona.

    Non e' un errore: puoi aver conosciuto qualcuno a una fiera e avere solo il
    nome e l'azienda. Ma se resta cosi', quella scheda non serve a niente.
    """
    for persona in dati.get("persone", []):
        campi = [persona.get("email"), persona.get("telefono"), persona.get("linkedin")]
        if not any(campi):
            avvisi.append(
                f'persona "{persona.get("id", "?")}" ({nome_completo(persona)}): '
                "nessun recapito, non hai modo di raggiungerla"
            )


def controlla_doppioni(dati, avvisi):
    """Due schede con lo stesso recapito sono quasi sempre la stessa persona.

    Capita scrivendo la stessa persona due volte con id diversi, per esempio
    dopo che ha cambiato azienda. Non e' vietato, ma va guardato: se sono
    davvero due schede della stessa persona, la storia si spezza in due.
    """
    campi = [
        ("email", "la stessa email", lambda v: v.strip().lower()),
        ("telefono", "lo stesso telefono", lambda v: v.replace(" ", "")),
        ("linkedin", "lo stesso profilo LinkedIn", lambda v: v.strip().lower().rstrip("/")),
    ]

    for campo, etichetta, normalizza in campi:
        visti = {}
        for persona in dati.get("persone", []):
            valore = persona.get(campo)
            if not isinstance(valore, str) or not valore:
                continue
            chiave = normalizza(valore)
            if chiave in visti:
                avvisi.append(
                    f'persona "{persona.get("id", "?")}": ha {etichetta} di '
                    f'"{visti[chiave]}". Sono due schede della stessa persona?'
                )
            else:
                visti[chiave] = persona.get("id", "?")


def controlla_linkedin(dati, avvisi):
    """Il profilo di una persona e la pagina di un'azienda hanno indirizzi diversi.

    Un URL /company/ finito nel campo di una persona (o viceversa) e' un
    copia-incolla sbagliato: la forma e' quella di un URL e lo schema lo accetta.
    """
    for persona in dati.get("persone", []):
        url = persona.get("linkedin")
        if isinstance(url, str) and "linkedin.com" in url and "/in/" not in url:
            avvisi.append(
                f'persona "{persona.get("id", "?")}": il link LinkedIn "{url}" '
                "non sembra un profilo personale (manca /in/)"
            )

    for azienda in dati.get("aziende", []):
        url = azienda.get("linkedin")
        if isinstance(url, str) and "linkedin.com" in url and "/company/" not in url:
            avvisi.append(
                f'azienda "{azienda.get("id", "?")}": il link LinkedIn "{url}" '
                "non sembra una pagina aziendale (manca /company/)"
            )


def controlla_freschezza(dati, avvisi):
    """Da quanto non vi sentite: e' l'unica cosa che scade da sola.

    Il database del profilo ha lo stesso controllo sulle preferenze. Qui vale
    per ogni scheda: un contatto non si rompe, invecchia, e nessuno te lo dice.
    """
    oggi = date.today()

    for persona in dati.get("persone", []):
        etichetta = f'persona "{persona.get("id", "?")}" ({nome_completo(persona)})'
        giorni_noti = [
            g
            for g in (a_data(e.get("data_contatto")) for e in persona.get("esperienze", []))
            if g is not None and g <= oggi
        ]

        if not giorni_noti:
            avvisi.append(f"{etichetta}: nessuna data di contatto, non ci hai mai parlato")
            continue

        ultima = max(giorni_noti)
        giorni = (oggi - ultima).days
        if giorni > GIORNI_FREDDO:
            avvisi.append(
                f"{etichetta}: sentito l'ultima volta il {ultima.strftime('%d/%m/%Y')} "
                f"({giorni} giorni fa)"
            )


def main():
    prepara_stdout()

    percorso = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DATI
    dati = leggi_json(percorso, MANCA_DATI if percorso == DATI else None)
    schema = leggi_json(SCHEMA)

    errori, avvisi = [], []
    controlla_schema(dati, schema, errori, NOMI)
    controlla_identificatori(dati, SEZIONI_CON_ID, errori)
    controlla_date(dati, errori, avvisi)
    controlla_ordine(dati, avvisi)
    controlla_aziende(dati, errori, avvisi)
    controlla_recapiti(dati, avvisi)
    controlla_doppioni(dati, avvisi)
    controlla_linkedin(dati, avvisi)
    controlla_freschezza(dati, avvisi)

    esperienze = sum(len(p.get("esperienze", [])) for p in dati.get("persone", []))
    conteggi = ", ".join([
        quantifica(len(dati.get("persone", [])), *NOMI["persone"]),
        quantifica(len(dati.get("aziende", [])), *NOMI["aziende"]),
        quantifica(esperienze, "esperienza", "esperienze"),
    ])

    return stampa_esito(etichetta_percorso(percorso), errori, avvisi, conteggi)


if __name__ == "__main__":
    sys.exit(main())
