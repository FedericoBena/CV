"""Le parti che i due controllori si dividono.

Nella cartella ci sono due database, e uno script che li controlla per ciascuno:
valida_profilo.py per dati/profilo.json, valida_persone.py per contatti/persone.json.
Guardano cose diverse, ma il modo di leggere un file, di capire una data e
soprattutto di *spiegare un errore in italiano* e' lo stesso.

Sta qui, in un posto solo, e non copiato in tutti e due: due copie della stessa
traduzione divergono al primo messaggio ritoccato, e nessuno se ne accorge finche'
i due comandi non raccontano lo stesso errore in due modi diversi.

Questo file non si lancia: si importa.
"""

import json
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import jsonschema
except ImportError:
    sys.exit(
        "Manca la libreria jsonschema. Installala con:\n"
        "    pip install jsonschema"
    )

# I percorsi si calcolano dalla posizione di questo file, non dalla cartella
# da cui lo lanci: cosi' funziona anche chiamandolo da altrove. Questo file sta
# in strumenti/, quindi la radice e' la cartella che lo contiene.
RADICE = Path(__file__).resolve().parent.parent


def prepara_stdout():
    """Mette il terminale in UTF-8, se si lascia mettere.

    Senza questo, su Windows le accentate dei messaggi si rompono."""
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass


def quantifica(numero, singolare, plurale):
    """"1 voce" / "4 voci": i messaggi si leggono, tanto vale scriverli bene."""
    return f"{numero} {singolare if numero == 1 else plurale}"


def leggi_json(percorso, spiegazione=None):
    """Carica un file JSON, spiegando in italiano cosa non va se fallisce.

    `spiegazione` e' il testo da aggiungere quando il file manca: serve per i
    database veri, che non stanno in git, dove "file non trovato" da solo fa
    sembrare rotto un repo che invece e' a posto.
    """
    if not percorso.exists():
        messaggio = f"File non trovato: {percorso}"
        if spiegazione:
            messaggio += f"\n{spiegazione}"
        sys.exit(messaggio)
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


def descrivi(percorso, dati, nomi):
    """Trasforma il percorso interno di un errore in qualcosa di leggibile.

    Da deque(['voci', 0, 'categoria']) a: voce "sensor-reply-tesi" -> categoria

    `nomi` dice come si chiama un elemento di ogni sezione al singolare e al
    plurale, perche' "voci[3]" non si legge e 'voce "mario-rossi-acme"' si'.
    """
    parti = list(percorso)
    if not parti:
        return "il file"

    sezione = parti[0]
    if len(parti) >= 2 and isinstance(parti[1], int):
        elemento = dati.get(sezione, [])[parti[1]] if isinstance(dati.get(sezione), list) else {}
        etichetta = elemento.get("id") if isinstance(elemento, dict) else None
        nome = nomi.get(sezione, (sezione, sezione))[0]
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


def controlla_schema(dati, schema, errori, nomi):
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
        errori.append(f"{descrivi(errore.absolute_path, dati, nomi)}: {traduci(dettaglio)}")


def controlla_identificatori(dati, sezioni, errori):
    """Gli id sono unici dentro la loro sezione: sono l'aggancio di tutto."""
    for sezione in sezioni:
        visti = set()
        for elemento in dati.get(sezione, []):
            identificatore = elemento.get("id")
            if identificatore in visti:
                errori.append(f'{sezione}: id "{identificatore}" usato piu\' di una volta')
            visti.add(identificatore)


def riferimento_rotto(valore):
    """Dice se un riferimento punta a un posto su disco che non c'e' piu'.

    Si guardano solo i valori che hanno la forma di un percorso Windows
    ("C:\\..." o "\\\\server\\..."): un certificato online sta nello stesso campo,
    ma e' un URL e non si cerca sul disco.
    """
    if not re.match(r"^([A-Za-z]:[\\/]|\\\\)", valore):
        return False
    return not Path(valore).exists()


def etichetta_percorso(percorso):
    """Il percorso accorciato alla radice della cartella, quando ci sta dentro."""
    try:
        return percorso.relative_to(RADICE)
    except ValueError:
        return percorso


def stampa_esito(etichetta, errori, avvisi, contenuto):
    """Stampa il verdetto e restituisce il codice d'uscita.

    Gli avvisi non fanno fallire il controllo: segnalano cose da guardare, non
    errori. Il conteggio finale c'e' anche quando e' tutto a posto, perche' un
    "nessun errore" su un file che si e' svuotato per sbaglio sarebbe una bugia
    tranquillizzante.
    """
    print(f"Controllo di {etichetta}\n")

    for messaggio in errori:
        print(f"ERRORE  {messaggio}")
    for messaggio in avvisi:
        print(f"AVVISO  {messaggio}")

    if errori:
        print(
            f"\n{quantifica(len(errori), 'errore', 'errori')}, "
            f"{quantifica(len(avvisi), 'avviso', 'avvisi')}. Contenuto: {contenuto}."
        )
        return 1

    print(
        f"Nessun errore, {quantifica(len(avvisi), 'avviso', 'avvisi')}. "
        f"Contenuto: {contenuto}."
    )
    return 0
