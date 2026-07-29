# Lo spazio sul CV

Il vincolo è **una pagina**, e non è estetica: è il limite dentro cui sta ogni
scelta di contenuto. Ogni cosa che aggiungi va pagata togliendo o accorciando
qualcos'altro.

## Le misure

Prese il **14 luglio 2026** (dopo la revisione che ha aggiunto Sensor Reply e la
tesi) con `\the\pagetotal` / `\the\textheight`. Altezza utile: **785 pt**.

| Variante | Spazio usato | Margine |
|---|---|---|
| `CV_Federico_Bena.tex` (senza foto) | 704 pt | ~81 pt |
| `CV_Federico_Bena_photo.tex` (con foto) | 752 pt | ~33 pt, cioè 3 righe |

**Il vincolo vero lo detta la variante con foto**: l'intestazione con la foto
costa ~48 pt in più. Verifica sempre entrambe. Se il CV cambia parecchio, queste
misure vanno rifatte.

Attenzione a `sorgenti/Competenze.tex`: è in `multicols` con `\columnbreak`,
quindi l'altezza della sezione la detta la colonna **più alta** (oggi la
sinistra). Togliere una voce dalla colonna destra non libera un solo punto.

Nei `.docx` il margine è ancora più risicato: Word di suo mette 8 pt di stacco
dopo ogni paragrafo e interlinea 1,08, e basta quello a mandare la variante con
foto in seconda pagina. Per questo `tex2docx.py` dichiara tutte le spaziature
invece di fidarsi dei default, e `build.ps1` conta le pagine a ogni build.

## Come rimisurare

Su una copia temporanea (non toccare i sorgenti del repo), inserisci dopo
`\input{sorgenti/Lingue}` le due righe:

```latex
\typeout{MISURA-USATO: \the\pagetotal}
\typeout{MISURA-TOTALE: \the\textheight}
```

poi `pdflatex CV_Federico_Bena.tex` e cerca `MISURA` nel `.log`.
