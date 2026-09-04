"""Controlla dati/profilo.json contro le regole di dati/profilo.schema.json.

Due livelli di controllo, perche' guardano cose diverse:

  - lo SCHEMA guarda la forma: i campi ci sono tutti? i nomi sono quelli giusti?
    la categoria e' fra quelle ammesse? la data e' scritta gg/mm/aaaa?
  - questo SCRIPT guarda la coerenza, che lo schema non puo' vedere: il 31/02
    ha la forma giusta ma non esiste, la fine non puo' precedere l'inizio, una
    competenza citata deve esistere nel registro, un percorso su disco deve
    puntare a qualcosa che c'e' ancora.

Qui stanno solo i controlli che riguardano il profilo. Il modo di leggere un
file e di spiegare un errore sta in strumenti/condiviso.py, insieme al gemello
valida_persone.py.

Si lancia cosi', da qualsiasi cartella:

    python strumenti/valida_profilo.py               controlla dati/profilo.json
    python strumenti/valida_profilo.py altro.json    controlla un altro file

Il secondo modo serve per le prove: si controlla una copia sbagliata apposta
senza mettere le mani sui dati veri.

Esce con codice 0 se e' tutto a posto, 1 se c'e' almeno un errore. Gli avvisi
non fanno fallire il controllo: segnalano cose da guardare, non errori.
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
    riferimento_rotto,
    stampa_esito,
)

DATI = RADICE / "dati" / "profilo.json"
SCHEMA = RADICE / "dati" / "profilo.schema.json"

# Caso tipico di chi clona il repo: i dati non ci sono e non e' un guasto.
# Senza questa spiegazione sembra un repo rotto.
MANCA_DATI = (
    "  dati/profilo.json non sta in git: contiene codice fiscale, voti,\n"
    "  RAL e nomi di terzi, e vive solo sul computer di Federico.\n"
    "  Un clone di questo repo ha lo schema e i controlli, non i dati."
)

# Sezioni che contengono elenchi di elementi con un id: qui si cercano i duplicati.
SEZIONI_CON_ID = ["link", "sommario", "lingue", "voci", "registro_competenze"]

# Come si chiama un singolo elemento di ogni sezione, al singolare e al plurale.
# Serve solo a scrivere messaggi in italiano corretto.
NOMI = {
    "voci": ("voce", "voci"),
    "registro_competenze": ("competenza", "competenze"),
    "lingue": ("lingua", "lingue"),
    "link": ("link", "link"),
    "sommario": ("sommario", "sommari"),
}


def controlla_date(dati, errori):
    """Le date esistono davvero, sono in ordine, e non stanno nel futuro."""
    oggi = date.today()

    nascita = dati.get("profilo", {}).get("nascita")
    if nascita and a_data(nascita) is None:
        errori.append(f'profilo -> nascita: la data "{nascita}" non esiste')

    for voce in dati.get("voci", []):
        etichetta = f'voce "{voce.get("id", "?")}"'
        inizio = a_data(voce.get("inizio"))
        fine = a_data(voce.get("fine")) if voce.get("fine") else None

        if voce.get("inizio") and inizio is None:
            errori.append(f'{etichetta}: la data di inizio "{voce["inizio"]}" non esiste')
        if voce.get("fine") and fine is None:
            errori.append(f'{etichetta}: la data di fine "{voce["fine"]}" non esiste')

        if inizio and fine and fine < inizio:
            errori.append(
                f'{etichetta}: la fine ({voce["fine"]}) precede l\'inizio ({voce["inizio"]})'
            )
        if inizio and inizio > oggi:
            errori.append(f'{etichetta}: l\'inizio ({voce["inizio"]}) e\' nel futuro')
        if fine and fine > oggi:
            errori.append(f'{etichetta}: la fine ({voce["fine"]}) e\' nel futuro')


def controlla_preferenze(dati, errori, avvisi):
    """Cosa cerchi adesso: e' l'unica sezione che scade da sola."""
    preferenze = dati.get("preferenze")
    if not isinstance(preferenze, dict):
        return

    aggiornato = preferenze.get("aggiornato_il")
    quando = a_data(aggiornato) if aggiornato else None
    if aggiornato and quando is None:
        errori.append(f'preferenze -> aggiornato_il: la data "{aggiornato}" non esiste')
        return

    if quando is None:
        return
    if quando > date.today():
        errori.append(f"preferenze -> aggiornato_il: la data ({aggiornato}) e' nel futuro")
        return

    # Sei mesi: oltre, RAL e preavviso vanno riletti prima di dirli a qualcuno.
    giorni = (date.today() - quando).days
    if giorni > 182:
        avvisi.append(
            f"preferenze: aggiornate l'ultima volta il {aggiornato} "
            f"({giorni} giorni fa). Rileggi RAL e preavviso prima di usarle."
        )


def controlla_competenze(dati, errori, avvisi):
    """Ogni competenza citata deve esistere nel registro.

    Le competenze si dichiarano su due livelli: sulla voce quelle trasversali,
    sulla singola attivita' quelle di quel lavoro. Vanno guardati entrambi.
    """
    registro = {c.get("id") for c in dati.get("registro_competenze", [])}
    usate = set()

    for voce in dati.get("voci", []):
        etichetta = f'voce "{voce.get("id", "?")}"'
        citazioni = [(etichetta, voce.get("competenze_usate", []))]
        for attivita in voce.get("attivita", []):
            citazioni.append(
                (f'{etichetta} -> attivita "{attivita.get("titolo", "?")}"',
                 attivita.get("competenze_usate", []))
            )

        for dove, elenco in citazioni:
            for identificatore in elenco:
                usate.add(identificatore)
                if identificatore not in registro:
                    errori.append(
                        f'{dove}: competenza "{identificatore}" non presente nel registro'
                    )

    for identificatore in sorted(registro - usate):
        avvisi.append(
            f'competenza "{identificatore}": definita nel registro ma non usata da nessuna voce'
        )


def controlla_riferimenti(dati, avvisi):
    """I percorsi su disco esistono ancora.

    I `riferimenti` sono il campo che fra due anni ti fa ritrovare il lavoro
    invece di ricordartelo e basta: se la cartella e' stata spostata o
    rinominata, il rimando e' carta straccia e nessuno se ne accorge. Sono
    decine, tutti percorsi assoluti di questa macchina.

    E' un avviso e non un errore: il dato resta vero, e' il puntatore a essersi
    rotto. Su un altro computer si lamenteranno tutti insieme, ed e' giusto
    cosi': vuol dire che vanno rimappati.
    """
    for voce in dati.get("voci", []):
        etichetta = f'voce "{voce.get("id", "?")}"'
        gruppi = [(etichetta, voce.get("riferimenti", []))]
        for attivita in voce.get("attivita", []):
            gruppi.append(
                (f'{etichetta} -> attivita "{attivita.get("titolo", "?")}"',
                 attivita.get("riferimenti", []))
            )

        for dove, elenco in gruppi:
            for riferimento in elenco:
                valore = riferimento.get("valore", "")
                if riferimento_rotto(valore):
                    avvisi.append(f'{dove}: il percorso "{valore}" non esiste piu\'')


def controlla_rimandi(dati, errori):
    """Un rimando a un'altra voce deve puntare a una voce che esiste davvero.

    Oggi il caso e' uno solo: la tesi svolta in azienda, che punta alla voce di
    quell'azienda. Il posto giusto per aggiungerne altri e' qui.
    """
    esistenti = {voce.get("id") for voce in dati.get("voci", [])}

    for voce in dati.get("voci", []):
        etichetta = f'voce "{voce.get("id", "?")}"'
        dettagli = voce.get("dettagli") or {}

        tesi = dettagli.get("tesi")
        if isinstance(tesi, dict):
            rimando = tesi.get("svolta_presso")
            if rimando and rimando not in esistenti:
                errori.append(
                    f"{etichetta} -> tesi.svolta_presso: "
                    f'non esiste nessuna voce con id "{rimando}"'
                )

        # Un'attivita' nata da un corso deve puntare a un esame di questa voce:
        # e' il legame che fa risalire da un progetto al suo esame e viceversa.
        codici = {esame.get("codice") for esame in dettagli.get("esami", [])}
        for attivita in voce.get("attivita", []):
            corso = attivita.get("corso")
            if corso and corso not in codici:
                errori.append(
                    f'{etichetta} -> attivita "{attivita.get("titolo", "?")}": '
                    f'il codice corso "{corso}" non e\' fra gli esami di questa voce'
                )


def main():
    prepara_stdout()

    percorso = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DATI
    dati = leggi_json(percorso, MANCA_DATI if percorso == DATI else None)
    schema = leggi_json(SCHEMA)

    errori, avvisi = [], []
    controlla_schema(dati, schema, errori, NOMI)
    controlla_date(dati, errori)
    controlla_preferenze(dati, errori, avvisi)
    controlla_identificatori(dati, SEZIONI_CON_ID, errori)
    controlla_competenze(dati, errori, avvisi)
    controlla_riferimenti(dati, avvisi)
    controlla_rimandi(dati, errori)

    conteggi = ", ".join(
        quantifica(len(dati.get(sezione, [])), *NOMI[sezione])
        for sezione in ["voci", "registro_competenze", "lingue", "link"]
    )

    return stampa_esito(etichetta_percorso(percorso), errori, avvisi, conteggi)


if __name__ == "__main__":
    sys.exit(main())
