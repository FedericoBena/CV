# Database personale di Federico Bena (e il CV che ne esce)

Questa cartella **non è il repo di un CV**: è il database personale di Federico,
e il CV è il suo primo consumatore. La cosa che conta è `dati/profilo.json` —
storico completo, collegato e aggiornato, da cui tirare fuori materiale per CV
adattati alla singola offerta, LinkedIn e moduli dei recruiter. Accanto c'è un
secondo database, `contatti/persone.json`: le persone incontrate lungo la strada,
tenute con le stesse regole. Il contesto completo sta in `README.md`, che è
scritto per un essere umano: leggilo prima.

## Il database

`dati/profilo.json`, con accanto `profilo.schema.json` che ne detta la forma.
**È l'unico file della cartella che nessuno può ricostruire**, e nessun altro
file lo controlla: schema e validatore sono la sola rete che ha.

- **Non genera niente**: i `.tex` del CV si scrivono a mano. È una miniera, non un
  motore.
- **Non si committa mai** nel repo pubblico: contiene codice fiscale, telefono,
  voti, RAL e nomi di terzi. Lo blocca `.gitignore`.
- **Ha una storia sua**, in un repo git privato dentro `dati/` (locale, senza
  remote): il file più prezioso non poteva essere l'unico senza storia. Quando lo
  modifichi, il commit si fa lì dentro — sempre chiedendo prima.
- **Dopo ogni modifica**, `python strumenti/valida_profilo.py` deve uscire senza
  errori. Non serve dopo le modifiche ai `.tex`: il database non entra nella
  build.
- **`profilo.schema.json` è tracciato da tutti e due i repo**: da quello pubblico
  come `dati/profilo.schema.json`, da quello privato dentro `dati/`. È un file
  solo con due storie. Se lo cambi, il commit va fatto in entrambi, o la copia
  pubblica resta indietro in silenzio.

Quello che c'è dentro **è la verità**. Le stesure precedenti, dove non sono già
nel file, sono buttate: erano accrocchi fatti al volo, non si recuperano.

### Da dove arrivano i dati

Il database è completo: profilo, link, sommario, lingue, preferenze, magistrale,
triennale, diploma, tirocinio Sensor Reply, docenza CIAC, stage Dalibot,
alternanza Bena S.R.L., lavoro in Bena S.N.C., le consegne per il kebab,
3 certificazioni MathWorks, la stampa 3D per hobby, 51 competenze. Non c'è nessun
altro posto da cui pescare: i vecchi appunti in prosa non esistono più.

**I dati li porta Federico, e non si deducono.** Le fonti sono sparse e le tiene
lui: buste paga, autocertificazioni, attestati. Una data approssimata perché
serviva riempire un campo su un modulo di selezione è un dato falso, e nel
database non ci entra. Vale per ogni voce nuova, esattamente come è valso per
quelle che ci sono già.

### Come si scrive una voce

Convenzioni che il file rispetta ma che lo schema non può imporre. Guardare una
voce già scritta resta il modo migliore: `dalibot-progettista` per un lavoro,
`polito-magistrale` per uno studio.

- **Ordine**: le voci stanno raggruppate per categoria — prima gli studi, poi i
  lavori, poi le certificazioni, poi il resto — e dentro ogni gruppo dalla più
  recente alla più vecchia, per data di inizio. Una voce nuova si infila al suo
  posto, non in fondo.
- **Id**: `ente-ruolo` in minuscolo con i trattini, es. `dalibot-progettista`,
  `bena-srl-alternanza`. Stabile: non si rinomina e non si riusa.
- **Luogo**: `Città, Italia`. Senza provincia e senza indirizzo: se l'indirizzo
  serve (i moduli lo chiedono) va nel `note`.
- **`usato_in`**: dice in quale documento quel testo è finito davvero.
  `CV luglio 2026` per quello che è sul CV di oggi, `CV fino al 14/07/2026` per
  una formulazione sostituita. Elenco vuoto = mai spedita.
- **`riferimenti`**: percorsi assoluti di questa macchina. `valida_profilo.py`
  controlla che esistano ancora e avvisa se no; gli URL li salta. Se cambi
  computer o riordini le cartelle, si lamenteranno tutti insieme e vanno
  rimappati.
- **Attenzione ai `testi`**: le formulazioni marcate `cv` sono copie di quello che
  sta nei `.tex`. Nessuno controlla che restino allineate: se riscrivi un bullet
  nel sorgente, aggiorna anche il testo nella voce, o il database invecchia in
  silenzio.

### Come si annotano gli esami

Il `note` di un esame dice **cosa è stato fatto**, in una riga: `Solo esame.`
oppure `Esame più progetto: <cosa>`. Niente motivazioni, niente rimandi ad altri
campi, niente materiale di studio. Il modello è la magistrale: si guarda come
sono scritti quegli esami e si fa uguale.

Il progetto vero sta in `attivita`, agganciato al codice del corso, con le
`competenze_usate` e i `riferimenti` a dove sta la roba. Una competenza usata in
un progetto va anche nel `registro_competenze`, se non c'è già.

## Il database dei contatti

`contatti/persone.json`, con accanto `persone.schema.json`. È la stessa cosa di
`dati/`, con dentro le persone invece dei fatti: chi hai conosciuto, come lo
raggiungi, e dove lavorava quando vi siete sentiti. Vale tutto quello che vale per il profilo —
non genera niente, non si committa, ha una storia sua, si controlla dopo ogni
modifica — con una differenza che pesa più di tutte le altre:

**Quei dati non sono di Federico.** Sono nomi, ruoli, numeri e email di altre
persone, che non hanno mai acconsentito a stare in un repo pubblico. Il file è
bloccato da `.gitignore`, e lì deve restare: nel repo pubblico non ci va nemmeno
un nome. Si tiene il minimo che serve a ricontattare qualcuno, e si scrive solo
quello che si direbbe in faccia alla persona.

- **Il controllo è `python strumenti/valida_persone.py`**, gemello di
  `valida_profilo.py`. Le parti in comune fra i due (leggere un file, capire una
  data, tradurre un errore in italiano) stanno in `strumenti/condiviso.py`: si
  toccano lì, una volta sola, non copiate in tutti e due.
- **`persone.schema.json` è tracciato da tutti e due i repo**, come
  `profilo.schema.json`: se lo cambi, il commit va fatto in entrambi.
- **Gli avvisi qui sono la parte utile.** Un contatto non si rompe, invecchia: il
  controllo segnala chi non senti da più di sei mesi, chi non ha nessun recapito,
  e due schede che condividono un'email — quasi sempre la stessa persona scritta
  due volte.

### Come si scrive una scheda

- **Id**: `nome-cognome` per una persona (`mario-rossi`), il nome corto per
  un'azienda (`banco-bpm`). L'id dice chi è, non dove lavora: se cambia lavoro
  resta lo stesso e cambia l'esperienza. Stabile: non si rinomina e non si riusa.
- **L'azienda si cita per id**, e sta scritta per esteso una volta sola nel
  registro `aziende`. Tre persone in Leonardo non sono tre modi di scrivere
  Leonardo.
- **Le schede stanno in ordine alfabetico**: le persone per cognome, le aziende
  per nome. Al contrario del profilo, dove le voci vanno dalla più recente alla
  più vecchia: qui non c'è una storia da seguire, c'è un nome da cercare con
  l'occhio. Una scheda nuova si infila al suo posto, non in fondo.
- **Le esperienze stanno dalla più recente alla più vecchia**, come le voci del
  profilo. Ognuna dice azienda, ruolo, `data_contatto` — l'ultima volta che vi
  siete sentiti mentre era lì — e la sede dove lavora lei, che non è per forza
  quella dell'azienda: Banco BPM sta a Milano, Valentina a Ivrea.
- **Date `gg/mm/aaaa`, luoghi `Città, Italia`**: le stesse convenzioni del
  profilo, perché è la stessa cartella.
- **`null` quando non lo sai.** Un ruolo tirato a indovinare è un dato falso
  esattamente come una data approssimata nel profilo, e qui riguarda qualcun
  altro.

## Il CV

Due varianti che condividono lo stesso contenuto, distinte da un flag:

| File principale (root) | PDF prodotto | Foto | GDPR |
|---|---|---|---|
| `CV_Federico_Bena.tex` | `CV_Federico_Bena.pdf` | no (`\photofalse`) | no |
| `CV_Federico_Bena_photo.tex` | `CV_Federico_Bena_photo.pdf` | sì (`\phototrue`) | sì |

Il nome del file principale **è** il nome del PDF che va ai recruiter. I testi
stanno in `sorgenti/` (`Preambolo`, `Intestazione`, `Profilo`, `Lavoro`,
`Educazione`, `Competenze`, `Lingue`, `GDPR`), inclusi da entrambi i main. La
fonte della verità del CV sono i `.tex`.

## Regole che non si violano

Queste regole valgono **per chi lavora al posto di Federico**, non per Federico.
Se lui chiede una cosa che va contro una di queste righe, decide lui e si fa
quello che chiede: un CV di dieci pagine lo può fare quando vuole. Quello che non
si fa è deciderlo da soli, o zittire una regola per comodità. Se la richiesta
stride con una di queste, si dice in una riga e poi si esegue.

1. **Mai duplicare un file per creare una variante.** È già successo: due copie di
   `Lavoro.tex` divergute in silenzio, e i due PDF dicevano cose diverse. Se serve
   una variante si usa un flag (`\newif`, come `\ifphoto`).
2. **Rigenera con `build.ps1`, mai con `latexmk` a mano.**
   ```
   powershell -File strumenti/build.ps1
   ```
   Fa i due PDF, pulisce gli ausiliari, fa i due `.docx`, e verifica che ogni
   parola dei PDF stia anche nei `.docx` e che tutto entri in una pagina. Da solo,
   `latexmk` aggiorna i PDF e lascia indietro i `.docx`.
3. **Dopo ogni modifica ai sorgenti, ricompila entrambe le varianti e verifica.**
   Confronta il testo prima e dopo (`pdftotext -layout`): l'unica differenza deve
   essere quella voluta. "Compila senza errori" non è una verifica — su un CV che
   si spedisce, un blocco che sparisce in silenzio è peggio di un errore.
4. **Dopo ogni modifica a un database, il suo controllo.** `python
   strumenti/valida_profilo.py` per il profilo, `python strumenti/valida_persone.py` per
   i contatti.
5. **Le regole ignore stanno in `.gitignore`, versionato.** Non in
   `.git/info/exclude`: la riga che tiene i dati personali fuori da un repo
   pubblico deve sopravvivere a un clone. Controlla comunque `git status` prima di
   un commit: quella è la riga di confine fra pubblico e privato, e non si sposta.
6. **Il repo è pubblico, ma non è una scusa per aggiungere dati sensibili nuovi.**
   Email e foto sono condivise di proposito; il telefono è stato tolto dal CV e non
   va rimesso (nel database sì, quello è fuori da git). Niente documenti di terzi,
   e niente dati di terzi: i contatti stanno in `contatti/persone.json`, che è
   fuori da git per lo stesso motivo per cui ci sta fuori il profilo — con
   l'aggravante che quei dati non sono suoi.
7. **Niente che non regga a un colloquio tecnico.** `Python (basic)` è la verità e
   si difende; "Python, scikit-learn, ML" no. Il CV punta a difesa e aerospace,
   dove il colloquio tecnico smonta le righe gonfiate.

## Note

- I PDF e i `.docx` sono **prodotti derivati**: si rigenerano, non si modificano
  (una correzione fatta in Word sparisce alla build successiva) e non si
  versionano. `tex2docx.py` dà per buone le assunzioni sui sorgenti — macro,
  percorsi, ordine degli `\input`: se le cambi, aggiornalo.
- **Il vincolo è una pagina**, e la variante con foto è quella stretta (la foto
  costa ~48 pt di intestazione): ogni cosa che aggiungi va pagata togliendo
  qualcos'altro. Misure e metodo per rimisurarle in `note/spazio-cv.md`.
- **Oggi il CV compila senza nessun `Overfull \hbox`.** Se ne compare uno è una
  regressione: di solito è un trattino non-separabile U+2011 (`‑`) dentro una
  parola come `driving‑risk`, su cui LaTeX non può andare a capo. Usa il trattino
  ASCII normale.
- Il blocco GDPR sta in `sorgenti/GDPR.tex`, incluso da entrambi i main e
  stampato **solo** nella variante con foto: dentro c'è un `\ifphoto`, come
  nell'intestazione. `tex2docx.py` rispecchia la stessa condizione.
- La cartella sta in Google Drive: se compaiono file "fantasma" che Windows dà
  come inaccessibili, è Drive che deve finire di sincronizzare.
