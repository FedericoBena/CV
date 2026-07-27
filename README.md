# CV di Federico Bena

Sorgenti LaTeX del CV, in due varianti (con e senza foto) che condividono **gli
stessi identici contenuti**. Repo **pubblico**: contiene email e foto, condivise
di proposito. Il numero di telefono è stato tolto — chi vuole i contatti scrive
una mail.

## Come è fatto

Due file principali, uno per variante. L'unica differenza fra i due è un flag:

| File principale | PDF prodotto | Foto | Blocco GDPR |
|---|---|---|---|
| `CV_Federico_Bena.tex` | `CV_Federico_Bena.pdf` | no (`\photofalse`) | no |
| `CV_Federico_Bena_photo.tex` | `CV_Federico_Bena_photo.pdf` | sì (`\phototrue`) | sì |

Tutto il resto è **condiviso**: il contenuto esiste in una sola copia.

In **root** stanno solo le cose che si spediscono — i due main, i due PDF e i due
DOCX prodotti, e questo README — così aprendo la cartella si vede solo il CV. Il
resto è nelle sottocartelle:

```
CV_Federico_Bena.tex          i 2 main (il loro nome è il nome del PDF)
CV_Federico_Bena_photo.tex
CV_Federico_Bena.pdf          i 2 PDF prodotti (quelli che spedisci)
CV_Federico_Bena_photo.pdf
CV_Federico_Bena.docx         i 2 DOCX prodotti (per i recruiter)
CV_Federico_Bena_photo.docx
README.md

sorgenti/     il contenuto condiviso, in una sola copia:
  Preambolo.tex      preambolo, stili, macro, \graphicspath, flag \ifphoto
  Intestazione.tex   nome e contatti (2 versioni, sceglie \ifphoto)
  Profilo.tex        Profile
  Lavoro.tex         Professional Experience
  Educazione.tex     Education
  Competenze.tex     Skills
  Lingue.tex         Languages
  fede.jpg           la foto

strumenti/    build.ps1, tex2docx.py   (li lanci, non li apri)
note/         CV_contenuti.md, prompt-aggiorna-cv.md
```

I due main includono i sorgenti con `\input{sorgenti/...}`. I PDF/DOCX in root non
sono versionati: le regole ignore stanno in `.git/info/exclude` (non in un
`.gitignore`, per tenere la root pulita) e i file restano su disco, sincronizzati
da Drive.

Il nome del file principale **è** il nome del PDF che finisce in mano ai
recruiter: se lo rinomini, cambia il nome del PDF.

`sorgenti/Preambolo.tex` definisce anche i due comandi con cui è scritto tutto il CV:
`\cvsection{Titolo}` (titolo di sezione con la riga sotto) e
`\cvevent{date}{azienda}{ruolo}{bullet}` (una voce di esperienza o di studio).

## Come si compila

```
powershell -File strumenti/build.ps1
```

Un comando solo, ed è l'unico previsto. Fa tutto in sequenza:

1. i due **PDF** con `latexmk`;
2. la **pulizia** degli ausiliari (`latexmk -c`, che lascia il PDF; `-C`
   cancellerebbe anche quello: non usarlo), così non restano ausiliari in giro;
3. i due **DOCX** con `tex2docx.py`, dagli stessi sorgenti `.tex`;
4. due **verifiche**: ogni parola che sta nei PDF deve stare anche nei DOCX (se
   ne manca una, lo script si ferma invece di lasciarti spedire un CV mutilo), e
   anche i DOCX devono stare in **una pagina sola** — il conteggio lo fa Word,
   che è l'unico a sapere davvero come impagina il proprio formato.

Servono una distribuzione LaTeX con `latexmk` (MiKTeX o TeX Live), Python con
[python-docx](https://python-docx.readthedocs.io) (`pip install python-docx`),
`pdftotext`, e Perl (`latexmk` è uno script Perl; su Windows arriva con Git for
Windows, e `build.ps1` lo trova da sé anche se non è nel PATH di PowerShell).

**Non lanciare `latexmk` a mano**: aggiorneresti i PDF lasciando indietro i DOCX,
e ti ritroveresti documenti che dicono cose diverse.

Se `latexmk` dice "up-to-date" pur avendo tu modificato un file incluso, è un
problema di timestamp di Google Drive: forza con `latexmk -g -pdf`.

## I .docx, e perché non somigliano al PDF

`CV_Federico_Bena.docx` e `CV_Federico_Bena_photo.docx` servono ai recruiter che
vogliono Word per **editarlo** (togliere i tuoi contatti e metterci il logo
dell'agenzia prima di girarlo al cliente) e ai portali che rifiutano il PDF.

**LaTeX sa produrre solo PDF: un Word "identico al PDF" non esiste.** L'aspetto
del CV è il risultato degli algoritmi di LaTeX — `multicols` per le due colonne,
`\hfill` che spinge le date a destra, `\rule` per le righe, la giustificazione,
il font Raleway — e Word non ha nessuno di quei meccanismi. Chi prova a forzare
la somiglianza (pandoc, tex4ht, LibreOffice) produce un documento sfasato oppure
una pila di caselle di testo che non si riesce a modificare, cioè l'esatto
contrario di quello che serve.

Quindi `tex2docx.py` **non converte: rigenera**. Legge le macro `\cvsection` e
`\cvevent` dagli stessi `.tex` e ricostruisce il CV con gli strumenti di Word:
stili veri, tab stop che allineano le date a destra, elenchi puntati nativi, link
cliccabili. Il **contenuto** è identico al PDF (`build.ps1` lo verifica parola
per parola); l'**aspetto** no, ed è giusto così. Il documento bello resta il PDF:
quello mandi quando puoi scegliere.

Sono **prodotti derivati**, come i PDF: si rigenerano, non si modificano (una
correzione fatta dentro Word sparisce alla build successiva — la modifica va
fatta nel `.tex`) e **non si versionano**: le regole ignore stanno in
`.git/info/exclude` (non in un `.gitignore`, per tenere la root pulita) e bloccano
`*.pdf` e `*.docx`. Restano comunque sul disco, sincronizzati da Google Drive,
sempre pronti da spedire — semplicemente non stanno nella storia git.

## Come si verifica

**Compilare senza errori non è una verifica.** Su un documento che spedisci, un
blocco che sparisce in silenzio è peggio di un errore di compilazione. Quindi:

1. prima di modificare, salva il testo dei PDF: `pdftotext -layout CV_Federico_Bena.pdf prima.txt`
2. dopo, rifallo e confronta: `diff prima.txt dopo.txt`. L'unica differenza deve
   essere la modifica voluta;
3. controlla che i PDF siano ancora di **una pagina sola**: `pdfinfo CV_Federico_Bena.pdf`
4. controlla che il log non contenga `Overfull \hbox`. Oggi non ce ne sono: se ne
   compare uno, è una regressione (di solito è un trattino non-separabile `U+2011`
   dentro una parola: usa il trattino ASCII normale).

## Il vincolo: una pagina

Il CV deve stare in **una pagina**, e la variante con foto è quella stretta:
l'intestazione con la foto costa ~48 pt in più. Ogni cosa che aggiungi va pagata
togliendo o accorciando qualcos'altro.

Vale anche per i DOCX, dove il margine è ancora più risicato: Word di suo mette
8 pt di stacco dopo ogni paragrafo e interlinea 1,08, e basta quello a mandare la
variante con foto in seconda pagina. Per questo `tex2docx.py` dichiara **tutte**
le spaziature invece di fidarsi dei valori di default. `build.ps1` conta le pagine
a ogni build e si ferma se sono due.

Le misure aggiornate (spazio usato / spazio disponibile) e il metodo per
rimisurarle stanno in **`note/prompt-aggiorna-cv.md`**, insieme al prompt da incollare
in una sessione di Claude Code per rifare un giro di aggiornamento del CV.

## Gli altri file

In **`note/`**:

- **`note/CV_contenuti.md`** — il magazzino. Tiene quello che è nel CV (`ATTUALE`),
  quello che è stato tagliato (`ARCHIVIO`, con data e motivo), il materiale
  disponibile non ancora usato, e una **scheda dati** (voti, date, titoli di tesi,
  relatori, trigramma) che il CV non contiene ma che ogni form aziendale chiede.
  Non è un sorgente e non è la fonte della verità: se contraddice un `.tex`, ha
  ragione il `.tex`.
- **`note/prompt-aggiorna-cv.md`** — il prompt operativo per aggiornare il CV con
  Claude Code, più le misure di spazio.

In **`strumenti/`**:

- **`strumenti/build.ps1`** — lo script di rigenerazione: PDF, pulizia, DOCX, verifica.
- **`strumenti/tex2docx.py`** — il generatore dei DOCX: legge i `.tex` e ricostruisce
  il CV in Word. Lo chiama `build.ps1`, non serve lanciarlo a mano.

In **root**:

- **`CLAUDE.md`** — le regole del repo per Claude Code (struttura, compilazione,
  verifica, divieti). Deve stare in root: è lì che Claude Code lo cerca.

## Regole che non si violano

1. **Mai duplicare un file per creare una variante.** È già successo: due copie di
   `Lavoro.tex` erano divergute in silenzio e i due PDF dicevano cose diverse. Se
   serve una variante, si usa un flag (`\newif`, come `\ifphoto`), mai un secondo
   file con lo stesso contenuto. L'unica deroga è `CV_contenuti.md`, ed è
   sorvegliata: va riallineato a ogni modifica dei sorgenti.
2. **Il repo è pubblico: non aggiungere dati sensibili nuovi.** Email e foto sono
   condivise di proposito; il numero di telefono è stato tolto, non rimetterlo.
3. **Documenti di terzi non si committano** (moduli aziendali, elaborati, roba
   consegnata a clienti). Le regole ignore in `.git/info/exclude` bloccano già ogni
   `*.pdf` e `*.docx`. Quello che vale la pena tenere si riassume in
   `note/CV_contenuti.md`.
