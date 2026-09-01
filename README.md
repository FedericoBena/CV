# I miei dati, e il CV che ne esce

Questa cartella tiene in un posto solo tutto quello che ho fatto: studi, lavori,
progetti, certificazioni, competenze, lingue. Da lì escono il CV, il profilo
LinkedIn e le risposte ai moduli dei recruiter.

## Le due cose che ci sono dentro

**Il database** — `dati/profilo.json`. È la parte importante. Tutto è nella stessa
forma: un lavoro, una laurea, un corso e domani uno sport sono la stessa cosa con
una categoria diversa. Le competenze stanno in un elenco a parte e le voci le
richiamano, così il livello di una competenza è scritto in un punto solo. È
privato e non esce da qui: resta su questo computer, con una storia sua dentro
`dati/`.

**Il CV** — i file in alto nella cartella. Due versioni, con foto e senza, che
dicono le stesse cose. I contenuti li scrivo a mano, perché il CV va adattato
all'offerta.

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

## Dove sta cosa

```
CV_Federico_Bena...      il CV: sorgenti, PDF e Word, nelle due versioni
dati/                    il database (privato) e le regole che deve rispettare
sorgenti/                i testi del CV, scritti una volta e usati da entrambe le versioni
strumenti/               i due comandi qui sopra, più lo script che fa i Word
note/                    appunti di lavoro
```

Dettagli tecnici, vincoli e regole per lavorarci: `CLAUDE.md`.
