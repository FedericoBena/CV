# Prompt per aggiornare il CV

Da incollare all'inizio di una nuova sessione di Claude Code aperta in questa
cartella (`G:\Il mio Drive\CV`).

Le misure di spazio qui sotto sono state prese il 14 luglio 2026, dopo la
revisione che ha aggiunto il tirocinio in Sensor Reply e la tesi, con
`\the\pagetotal` / `\the\textheight`. Se il CV cambia parecchio, rimisurale.

---

Lavoriamo sul mio CV in LaTeX, in questa cartella. Leggi il CLAUDE.md per la
struttura e le regole del repo, e leggi i sorgenti prima di propormi qualsiasi cosa.

OBIETTIVO
Aggiornare il CV mantenendolo su UNA SOLA PAGINA. Non è un dettaglio estetico:
è il vincolo principale. Ogni cosa che aggiungiamo deve essere pagata togliendo
o accorciando qualcos'altro.

SPAZIO DISPONIBILE (misurato, altezza utile 785 pt)
- CV_Federico_Bena.tex (senza foto): usa 704 pt -> restano ~81 pt.
- CV_Federico_Bena_photo.tex (con foto): usa 752 pt -> restano ~33 pt, cioè 3 righe.
Il vincolo vero lo detta la variante con foto: la foto costa ~48 pt di
intestazione in più. Verifica sempre entrambe.

Attenzione a `Competenze.tex`: è in `multicols` con `\columnbreak`, quindi
l'altezza della sezione la detta la colonna PIÙ ALTA (oggi la sinistra).
Togliere una voce dalla colonna destra non libera un solo punto.

COME VOGLIO CHE PROCEDIAMO
1. Prima fai l'inventario: leggi Profilo, Lavoro, Educazione, Competenze, Lingue
   e riassumimi cosa c'è oggi, sezione per sezione, con quanto spazio occupa.
   Leggi anche `CV_contenuti.md`: è il magazzino di tutto quello che è già stato
   scritto e poi tagliato. Prima di scrivere una voce nuova, guarda se esiste già lì.
2. Poi propommi, in modo critico e non compiacente:
   - cosa TOGLIERE o accorciare (voci vecchie, poco rilevanti, ridondanti,
     descrizioni troppo lunghe);
   - cosa AGGIUNGERE che oggi manca;
   - cosa RISCRIVERE perché è scritto male o è generico.
   Per ogni proposta dimmi quanto spazio libera o costa.
3. Solo dopo che ho scelto, fai le modifiche.

COSE DA CONSIDERARE PER L'AGGIUNTA (chiedimi, non dare per scontato)
- Progetti, certificazioni, competenze acquisite dopo l'ultima stesura.
Fammi domande finché non hai abbastanza materiale per scrivere qualcosa di
concreto: preferisco una voce specifica e verificabile a una riga generica.

ONESTÀ (non negoziabile)
Non scrivere competenze che non ho. Il CV punta a difesa/aerospace, dove il
colloquio tecnico ti smonta: `Python (basic)` è la verità e va difeso, non
gonfiato in "Python, scikit-learn, ML". La sostanza tecnica la porta la tesi e
il tirocinio, non la riga delle skill. Se una voce non regge a una domanda in
colloquio, non ci va.

REGOLE OPERATIVE
- Un'informazione vive in UN SOLO file, condiviso dalle due varianti. Non
  duplicare file per creare varianti: si usa il flag \ifphoto.
- Dopo ogni modifica ricompila ENTRAMBE le varianti con latexmk, ripulisci gli
  ausiliari, e verifica con pdftotext che sia cambiato solo quello che volevamo
  e che il PDF sia ancora di una pagina sola.
- Aggiorna `CV_contenuti.md`: il testo nuovo come ATTUALE, quello che togliamo
  come ARCHIVIO (con data e motivo). Niente si butta via.
- Non committare e non pushare senza che te lo chieda io.
- Il CV contiene dati personali: non pubblicarlo da nessuna parte.

Parti dal punto 1: fammi l'inventario.

---

## Come rimisurare lo spazio

Su una copia temporanea (non toccare i sorgenti del repo), inserisci dopo
`\input{sorgenti/Lingue}` le due righe:

```latex
\typeout{MISURA-USATO: \the\pagetotal}
\typeout{MISURA-TOTALE: \the\textheight}
```

poi `pdflatex CV_Federico_Bena.tex` e cerca `MISURA` nel `.log`.
