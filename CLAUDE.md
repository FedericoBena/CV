# CV di Federico Bena

Sorgenti LaTeX del CV. Il repo è **privato**: i file contengono dati personali
(telefono, email, foto). La spiegazione completa — struttura, build, verifica, il
perché dei `.docx` — sta in `README.md`: **leggilo prima di toccare qualcosa.**
Qui sotto stanno solo le regole operative da rispettare quando ci lavori.

## Struttura in breve

In **root** stanno solo le cose che si spediscono: i due file principali (`.tex`),
i due PDF e i due DOCX prodotti, e il `README.md`. Tutto il resto è nelle
sottocartelle, così aprendo la cartella si vede solo il CV. Il nome del file
principale **è** il nome del PDF inviato ai recruiter: se lo rinomini, cambi il
nome del PDF.

| File principale (root) | PDF prodotto | Foto | GDPR |
|---|---|---|---|
| `CV_Federico_Bena.tex` | `CV_Federico_Bena.pdf` | no (`\photofalse`) | no |
| `CV_Federico_Bena_photo.tex` | `CV_Federico_Bena_photo.pdf` | sì (`\phototrue`) | sì |

- **`sorgenti/`** — tutto il contenuto condiviso, in una sola copia: il preambolo
  (`sorgenti/Preambolo.tex`, che definisce il flag `\ifphoto`, il `\graphicspath` e
  le macro `\cvsection` / `\cvevent`), l'intestazione (`sorgenti/Intestazione.tex`,
  entrambe le versioni, sceglie con `\ifphoto`), le sezioni (`sorgenti/Profilo.tex`,
  `Lavoro`, `Educazione`, `Competenze`, `Lingue`) e la foto (`sorgenti/fede.jpg`).
  I due main la includono con `\input{sorgenti/...}`.
- **`strumenti/`** — `build.ps1` e `tex2docx.py`: li lanci, non li apri.
- **`note/`** — `CV_contenuti.md` (il **magazzino dei contenuti**: quello che è nel
  CV, quello tagliato con data e motivo, il materiale non ancora usato) e
  `prompt-aggiorna-cv.md`. `CV_contenuti.md` non è un sorgente e **non è la fonte
  della verità**: quella sono i `.tex`.

I PDF e i DOCX in root **non sono versionati**: le regole ignore stanno in
`.git/info/exclude` (non in un `.gitignore`, per tenere la root pulita) e restano
su disco, sincronizzati da Drive.

## Regole che non si violano

1. **Mai duplicare un file per creare una variante.** È già successo: due copie di
   `Lavoro.tex` erano divergute in silenzio e i due PDF dicevano cose diverse. Se
   serve una variante, si usa un flag (`\newif`, come `\ifphoto`), mai un secondo
   file con lo stesso contenuto.
2. **Rigenera sempre con `build.ps1`, mai con `latexmk` a mano.** Da solo, latexmk
   aggiorna i PDF e lascia indietro i `.docx`: ti ritrovi documenti che dicono cose
   diverse.
   ```
   powershell -File strumenti/build.ps1
   ```
   Fa in sequenza i due PDF, la pulizia degli ausiliari, i due `.docx`, e verifica
   che ogni parola dei PDF stia anche nei `.docx` e che tutto entri in una pagina.
3. **Dopo ogni modifica ai sorgenti, ricompila entrambe le varianti e verifica.**
   Confronta il testo del PDF prima e dopo (`pdftotext -layout`): l'unica differenza
   deve essere quella voluta. "Compila senza errori" non è una verifica — su un CV
   che si spedisce, un blocco che sparisce in silenzio è peggio di un errore.
4. **Dopo ogni modifica ai sorgenti, riallinea `note/CV_contenuti.md`** (testo nuovo
   come `ATTUALE`, quello tolto come `ARCHIVIO`, con data e motivo). È l'unica deroga
   sorvegliata al divieto di duplicazione: se diverge dal `.tex`, ha ragione il
   `.tex`. Un magazzino che mente è peggio che non averlo.
5. **Non pubblicare mai questi file all'esterno** (repo pubblici, gist, pastebin,
   artifact, servizi di terzi): contengono telefono, email e foto.

I `.docx` e i PDF sono **prodotti derivati**: si rigenerano, non si modificano (una
correzione fatta in Word sparisce alla build successiva) e non si versionano (vedi
sopra). `tex2docx.py` dà per buone le assunzioni sui sorgenti — le macro, i percorsi
`sorgenti/`, l'ordine degli `\input`, la struttura di `Intestazione.tex`: se le
cambi, aggiornalo. Si ferma con un errore invece di produrre un CV mutilo.

## Note

- **Oggi il CV compila senza nessun `Overfull \hbox`.** Se ne compare uno è una
  regressione: sistemala, non conviverci. I due overfull storici erano trattini
  non-separabili U+2011 (`‑`) dentro parole come `driving‑risk` o `ROC‑AUC`, su cui
  LaTeX non può andare a capo: usa il trattino ASCII normale (`-`).
- Il blocco GDPR (autorizzazione al trattamento dati) viene stampato **solo** nella
  variante con foto.
- Il vincolo è **una pagina**, e la variante con foto è quella stretta (la foto
  costa ~48 pt di intestazione): ogni cosa che aggiungi va pagata togliendo
  qualcos'altro. Vale anche per i `.docx`, dove `build.ps1` conta le pagine e si
  ferma se sono due. Misure aggiornate e metodo in `note/prompt-aggiorna-cv.md`.
- La cartella sta dentro Google Drive: se compaiono file o cartelle "fantasma" che
  Windows dà come inaccessibili, è Drive che deve finire di sincronizzare.
