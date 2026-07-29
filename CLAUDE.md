# Database personale di Federico Bena (e il CV che ne esce)

Questa cartella **non è il repo di un CV**: è il database personale di Federico,
e il CV è il suo primo consumatore. La cosa che conta è `dati/profilo.json` —
storico completo, collegato e aggiornato, da cui tirare fuori materiale per CV
adattati alla singola offerta, LinkedIn e moduli dei recruiter. Il contesto
completo sta in `README.md`, che è scritto per un essere umano: leggilo prima.

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
- **Dopo ogni modifica**, `python strumenti/valida.py` deve uscire senza errori.
  Non serve dopo le modifiche ai `.tex`: il database non entra nella build.

Quello che c'è dentro **è la verità**. Le stesure precedenti, dove non sono già
nel file, sono buttate: erano accrocchi fatti al volo, non si recuperano.

### Stato della migrazione

Il vecchio magazzino in prosa `note/CV_contenuti.md` sta finendo. Dentro al
database: profilo, link, sommario, lingue, preferenze, magistrale, tirocinio
Sensor Reply, 3 certificazioni MathWorks, 31 competenze. **Mancano**: triennale,
diploma, CIAC, Dalibot, Bena S.N.C.

Si migra **una voce per chat**, con Federico che porta i dati: le fonti sono
sparse e i dati non si deducono — date approssimate su un modulo di selezione
sono dati falsi. Finita la migrazione, `note/CV_contenuti.md` **si cancella**:
non si archivia.

## Il CV

Due varianti che condividono lo stesso contenuto, distinte da un flag:

| File principale (root) | PDF prodotto | Foto | GDPR |
|---|---|---|---|
| `CV_Federico_Bena.tex` | `CV_Federico_Bena.pdf` | no (`\photofalse`) | no |
| `CV_Federico_Bena_photo.tex` | `CV_Federico_Bena_photo.pdf` | sì (`\phototrue`) | sì |

Il nome del file principale **è** il nome del PDF che va ai recruiter. I testi
stanno in `sorgenti/` (`Preambolo`, `Intestazione`, `Profilo`, `Lavoro`,
`Educazione`, `Competenze`, `Lingue`), inclusi da entrambi i main. La fonte della
verità del CV sono i `.tex`.

## Regole che non si violano

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
4. **Dopo ogni modifica al database, `python strumenti/valida.py`.**
5. **Le regole ignore stanno in `.gitignore`, versionato.** Non in
   `.git/info/exclude`: la riga che tiene i dati personali fuori da un repo
   pubblico deve sopravvivere a un clone. Controlla comunque `git status` prima di
   un commit: quella è la riga di confine fra pubblico e privato, e non si sposta.
6. **Il repo è pubblico, ma non è una scusa per aggiungere dati sensibili nuovi.**
   Email e foto sono condivise di proposito; il telefono è stato tolto dal CV e non
   va rimesso (nel database sì, quello è fuori da git). Niente documenti di terzi.
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
- Il blocco GDPR si stampa **solo** nella variante con foto.
- La cartella sta in Google Drive: se compaiono file "fantasma" che Windows dà
  come inaccessibili, è Drive che deve finire di sincronizzare.
