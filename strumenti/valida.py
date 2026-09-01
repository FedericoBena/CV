"""Controlla dati/profilo.json contro le regole di dati/profilo.schema.json.

Due livelli di controllo, perche' guardano cose diverse:

  - lo SCHEMA guarda la forma: i campi ci sono tutti? i nomi sono quelli giusti?
    la categoria e' fra quelle ammesse? la data e' scritta gg/mm/aaaa?
  - questo SCRIPT guarda la coerenza, che lo schema non puo' vedere: il 31/02
    ha la forma giusta ma non esiste, la fine non puo' precedere l'inizio, una
    competenza citata deve esistere nel registro, un percorso su disco deve
    puntare a qualcosa che c'e' ancora.

Si lancia cosi', da qualsiasi cartella:

    python strumenti/valida.py               controlla dati/profilo.json
    python strumenti/valida.py altro.json    controlla un altro file

Il secondo modo serve per le prove: si controlla una copia sbagliata apposta
senza mettere le mani sui dati veri.

Esce con codice 0 se e' tutto a posto, 1 se c'e' almeno un errore. Gli avvisi
non fanno fallire il controllo: segnalano cose da guardare, non errori.
"""

import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.exit(
        "Manca la libreria jsonschema. Installala con:\n"
        "    pip install jsonschema"
    )

# I percorsi si calcolano dalla posizione di questo file, non dalla cartella
# da cui lo lanci: cosi' funziona anche chiamandolo da altrove.
RADICE = Path(__file__).resolve().parent.parent
DATI = RADICE / "dati" / "profilo.json"
SCHEMA = RADICE / "dati" / "profilo.schema.json"

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


def quantifica(numero, singolare, plurale):
    """"1 voce" / "4 voci": i messaggi si leggono, tanto vale scriverli bene."""
    return f"{numero} {singolare if numero == 1 else plurale}"


def leggi_json(percorso):
    """Carica un file JSON, spiegando in italiano cosa non va se fallisce."""
    if not percorso.exists():
        if percorso == DATI:
            # Caso tipico di chi clona il repo: i dati non ci sono e non e' un
            # guasto. Senza questa spiegazione sembra un repo rotto.
            sys.exit(
                f"File non trovato: {percorso}\n"
                "  dati/profilo.json non sta in git: contiene codice fiscale, voti,\n"
                "  RAL e nomi di terzi, e vive solo sul computer di Federico.\n"
                "  Un clone di questo repo ha lo schema e i controlli, non i dati."
            )
        sys.exit(f"File non trovato: {percorso}")
    try:
        return json.loads(percorso.read_text(encoding="utf-8"))
    except json.JSONDecodeError as errore:
        sys.exit(
            f"{percorso.name} non e' un JSON valido.\n"
            f"  riga {errore.lineno}, colonna {errore.colno}: {errore.msg}"
        )


def a_data(testo):
    """Converte 'gg/mm/aaaa' in una data vera, o restituisce None se non esiste.

    Serve a bocciare il 31/02: ha la forma giusta e lo schema lo accetta, ma
    quel giorno non e' mai esistito.
    """
    try:
        return datetime.strptime(testo, "%d/%m/%Y").date()
    except (ValueError, TypeError):
        return None


def descrivi(percorso, dati):
    """Trasforma il percorso interno di un errore in qualcosa di leggibile.

    Da deque(['voci', 0, 'categoria']) a: voce "sensor-reply-tesi" -> categoria
    """
    parti = list(percorso)
    if not parti:
        return "il file"

    sezione = parti[0]
    if len(parti) >= 2 and isinstance(parti[1], int):
        elemento = dati.get(sezione, [])[parti[1]] if isinstance(dati.get(sezione), list) else {}
        etichetta = elemento.get("id") if isinstance(elemento, dict) else None
        nome = NOMI.get(sezione, (sezione, sezione))[0]
        testa = f'{nome} "{etichetta}"' if etichetta else f"{sezione}[{parti[1]}]"
        coda = ".".join(str(p) for p in parti[2:])
        return f"{testa} -> {coda}" if coda else testa

    return ".".join(str(p) for p in parti)


def descrivi_forma(schema):
    """Dice a parole che forma accetta un pezzo di schema.

    Serve per i campi che ammettono piu' forme (un voto e' un numero da 18 a 30
    *oppure* la parola "superato"): senza questo il messaggio d'errore ne
    elencherebbe una sola, facendo credere che l'altra sia vietata.
    """
    if "enum" in schema:
        return " o ".join(f'"{v}"' for v in schema["enum"])
    if "$ref" in schema:
        return str(schema["$ref"]).rsplit("/", 1)[-1]

    tipo = schema.get("type")
    if tipo == "null":
        return "null"
    if tipo in ("integer", "number"):
        minimo, massimo = schema.get("minimum"), schema.get("maximum")
        if minimo is not None and massimo is not None:
            return f"un numero da {minimo} a {massimo}"
        return "un numero"
    if tipo == "string":
        return "un testo"
    if tipo == "array":
        return "un elenco"
    if tipo == "object":
        return "un blocco di campi"
    return "un altro valore"


def traduci(errore):
    """Rende il messaggio di jsonschema comprensibile a chi non lo conosce."""
    tipo = errore.validator
    if tipo == "anyOf":
        forme = " oppure ".join(descrivi_forma(s) for s in errore.validator_value)
        return f"valore {errore.instance!r} non ammesso: qui ci va {forme}"
    if tipo == "required":
        # Il messaggio originale e': "'fine' is a required property"
        campo = str(errore.message).split("'")[1]
        return f'manca il campo obbligatorio "{campo}"'
    if tipo == "additionalProperties":
        # Il messaggio originale e': "Additional properties are not allowed
        # ('azienda' was unexpected)"
        intrusi = ", ".join(f'"{p}"' for p in str(errore.message).split("'")[1::2])
        return f"campo non previsto dallo schema: {intrusi}"
    if tipo == "enum":
        ammessi = ", ".join(f'"{v}"' for v in errore.validator_value)
        return f'valore "{errore.instance}" non ammesso: i valori validi sono {ammessi}'
    if tipo == "pattern":
        return f'"{errore.instance}" non ha la forma richiesta'
    if tipo == "type":
        return f"tipo di dato sbagliato (atteso {errore.validator_value})"
    if tipo == "minLength":
        return "il campo non puo' essere vuoto"
    if tipo == "minimum":
        return f"il valore {errore.instance} e' minore del minimo ammesso ({errore.validator_value})"
    if tipo == "uniqueItems":
        return "ci sono elementi ripetuti nell'elenco"
    return errore.message


def controlla_schema(dati, schema, errori):
    """Primo livello: la forma. Raccoglie tutti gli errori, non solo il primo."""
    validatore = jsonschema.Draft202012Validator(schema)
    for errore in sorted(validatore.iter_errors(dati), key=lambda e: list(e.absolute_path)):
        # Per if/then jsonschema produce un errore generico piu' un elenco di
        # errori interni: quello preciso e' fra questi ultimi. Per anyOf invece
        # no: li' l'errore generico e' quello giusto, perche' le alternative
        # vanno elencate tutte e non sostituite con una sola.
        dettaglio = errore
        if errore.context and errore.validator != "anyOf":
            dettaglio = jsonschema.exceptions.best_match(errore.context) or errore
        errori.append(f"{descrivi(errore.absolute_path, dati)}: {traduci(dettaglio)}")


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


def controlla_identificatori(dati, errori):
    """Gli id sono unici dentro la loro sezione: sono l'aggancio di tutto."""
    for sezione in SEZIONI_CON_ID:
        visti = set()
        for elemento in dati.get(sezione, []):
            identificatore = elemento.get("id")
            if identificatore in visti:
                errori.append(f'{sezione}: id "{identificatore}" usato piu\' di una volta')
            visti.add(identificatore)


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

    Si controllano solo i valori che hanno la forma di un percorso Windows
    ("C:\\..." o "\\\\server\\..."): un certificato online sta nello stesso campo,
    ma e' un URL e non si guarda sul disco.
    """
    def e_percorso(valore):
        return bool(re.match(r"^([A-Za-z]:[\\/]|\\\\)", valore))

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
                if e_percorso(valore) and not Path(valore).exists():
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
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

    percorso = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else DATI
    dati = leggi_json(percorso)
    schema = leggi_json(SCHEMA)

    errori, avvisi = [], []
    controlla_schema(dati, schema, errori)
    controlla_date(dati, errori)
    controlla_preferenze(dati, errori, avvisi)
    controlla_identificatori(dati, errori)
    controlla_competenze(dati, errori, avvisi)
    controlla_riferimenti(dati, avvisi)
    controlla_rimandi(dati, errori)

    try:
        etichetta = percorso.relative_to(RADICE)
    except ValueError:
        etichetta = percorso
    print(f"Controllo di {etichetta}\n")

    for messaggio in errori:
        print(f"ERRORE  {messaggio}")
    for messaggio in avvisi:
        print(f"AVVISO  {messaggio}")

    conteggi = ", ".join(
        quantifica(len(dati.get(sezione, [])), *NOMI[sezione])
        for sezione in ["voci", "registro_competenze", "lingue", "link"]
    )

    if errori:
        print(
            f"\n{quantifica(len(errori), 'errore', 'errori')}, "
            f"{quantifica(len(avvisi), 'avviso', 'avvisi')}. Contenuto: {conteggi}."
        )
        return 1

    print(
        f"Nessun errore, {quantifica(len(avvisi), 'avviso', 'avvisi')}. "
        f"Contenuto: {conteggi}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
