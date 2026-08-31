# I miei dati, e il CV che ne esce

Questa cartella tiene in un posto solo tutto quello che ho fatto: studi, lavori,
progetti, certificazioni, competenze, lingue. Da lì escono il CV, il profilo
LinkedIn e le risposte ai moduli dei recruiter.

Il punto non è avere un CV. È avere **lo storico completo, aggiornato e
collegato**, pronto a darmi l'informazione giusta quando serve: la data esatta di
un contratto mentre compilo un form, il testo di un'esperienza da adattare a
un'offerta, il voto di un esame che non ricordo.

## A che punto sono

Il database sta prendendo il posto degli appunti in prosa che stavano in `note/`.
Dentro ci sono già tutti gli studi (magistrale e triennale, esame per esame, con
i progetti fatti), il tirocinio in Sensor Reply, l'anno da insegnante in CIAC,
l'anno da progettista in Dalibot e le certificazioni. Mancano quattro cose: il
diploma, le due aziende Bena — che nel database stanno separate, anche se sul CV
possono finire in una riga sola — e un lavoro in un kebab. Finché non entrano,
quegli appunti restano.

## Le due cose che ci sono dentro

**Il database** — `dati/profilo.json`. È la parte importante. Tutto è nella stessa
forma: un lavoro, una laurea, un corso e domani uno sport sono la stessa cosa con
una categoria diversa. Le competenze stanno in un elenco a parte e le voci le
richiamano, così il livello di una competenza è scritto in un punto solo.

**Il CV** — i file in alto nella cartella. Due versioni, con foto e senza, che
dicono le stesse cose. I contenuti li scrivo a mano, perché il CV va adattato
all'offerta: il database è la miniera, non la macchina che lo stampa.

## Cosa non esce da qui

Il database contiene codice fiscale, telefono, voti, stipendio, date esatte e
nomi di persone che non sono io. **Non viene mai condiviso e non finisce online**:
resta su questo computer, salvato su Drive, con una sua storia privata dentro
`dati/`.

La cartella del CV invece è pubblica, e va bene così: contiene email e foto, che
sul CV ci vanno comunque. Il numero di telefono l'ho tolto — chi mi vuole
scrivere ha la mail.

## Come si usa

**Ho cambiato qualcosa nel CV** → un comando lo rifà tutto, nelle due versioni e
nei due formati (PDF e Word):

```
powershell -File strumenti/build.ps1
```

Controlla da sé che non sia sparito niente e che stia in una pagina. Se si ferma
con un errore, è perché qualcosa non torna: non aggirarlo.

**Ho cambiato qualcosa nel database** → un comando controlla che sia tutto in
ordine (date che esistono, niente doppioni, niente rimandi rotti):

```
python strumenti/valida.py
```

**Word e PDF non si somigliano**, ed è voluto. Il PDF è il documento bello, quello
che mando quando posso scegliere. Il Word serve ai recruiter che devono
modificarlo e ai siti che il PDF non lo accettano. Sono tutti e due prodotti
automaticamente: se li correggo a mano, la correzione sparisce alla prossima
rigenerata. Le modifiche si fanno nei file sorgente.

## Le tre regole

1. **Il CV sta in una pagina.** Non è estetica: è il vincolo. Ogni cosa che
   aggiungo va pagata togliendo qualcos'altro, e la versione con la foto è quella
   che ha meno spazio.
2. **Niente che non regga a un colloquio.** `Python (basic)` è la verità e si
   difende; "Python, machine learning" no. La sostanza la portano la tesi e il
   tirocinio, non la riga delle competenze.
3. **Una cosa scritta in un posto solo.** Se la stessa informazione sta in due
   file, prima o poi i due file si contraddicono — è già successo, e sono uscite
   due versioni del CV che dicevano cose diverse.

## Dove sta cosa

```
CV_Federico_Bena...      il CV: sorgenti, PDF e Word, nelle due versioni
dati/                    il database (privato) e le regole che deve rispettare
sorgenti/                i testi del CV, scritti una volta e usati da entrambe le versioni
strumenti/               i tre comandi: si lanciano, non si aprono
note/                    appunti di lavoro
```

Dettagli tecnici, vincoli e regole per lavorarci: `CLAUDE.md`.
