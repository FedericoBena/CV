"""Genera i .docx del CV dai sorgenti LaTeX.

    python tex2docx.py CV_Federico_Bena.tex CV_Federico_Bena.docx

Non e' una conversione automatica di LaTeX (non esiste: LaTeX sa produrre solo
PDF). E' un generatore che legge le macro con cui il CV e' scritto -- \\cvsection
e \\cvevent, definite in "sorgenti/Preambolo.tex" -- e ricostruisce il documento con
gli strumenti di Word: stili veri, tab stop, elenchi puntati nativi, link.

Il risultato NON e' una copia del PDF: e' un Word normale, pensato per il
recruiter che deve editarlo. Il documento "bello" resta il PDF.

Se il .tex smette di rispettare le assunzioni qui sotto, lo script si ferma con
un errore: meglio accorgersene qui che spedire un CV a cui manca un pezzo.

Dipendenze: python-docx (pip install python-docx).
"""

import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement
from docx.shared import Cm, Pt, RGBColor

# Stessi colori del CV LaTeX (definiti in "sorgenti/Preambolo.tex").
SECTCOL = RGBColor(0x00, 0x96, 0xFF)   # azzurro dei titoli di sezione
SOFTCOL = "E1E1E1"                     # grigio della riga sotto il titolo
FONT = "Calibri"                       # sans, presente su ogni Word (Raleway no)

LARGHEZZA_UTILE = Cm(18)               # A4 (21 cm) meno i margini da 1,5 cm


# --------------------------------------------------------------------------
# Lettura dei .tex
# --------------------------------------------------------------------------

def leggi(path):
    return Path(path).read_text(encoding="utf-8")


def gruppo(testo, i):
    """Legge un gruppo {...} bilanciato che inizia in posizione i.

    Serve perche' gli argomenti di \\cvevent contengono a loro volta graffe
    (\\textbf, \\item...): una regex non basta.
    """
    if testo[i] != "{":
        raise ValueError(f"attesa una graffa aperta in posizione {i}")
    livello, j = 0, i
    while j < len(testo):
        if testo[j] == "{":
            livello += 1
        elif testo[j] == "}":
            livello -= 1
            if livello == 0:
                return testo[i + 1:j], j + 1
        j += 1
    raise ValueError("graffa mai chiusa")


def argomenti(testo, i, n):
    """Legge n gruppi consecutivi a partire da i (saltando spazi e a capo)."""
    args = []
    for _ in range(n):
        while i < len(testo) and testo[i] in " \t\r\n":
            i += 1
        arg, i = gruppo(testo, i)
        args.append(arg)
    return args, i


def bullet(blocco):
    """Estrae gli \\item da un blocco LaTeX."""
    voci = [v.strip() for v in re.split(r"\\item\b", blocco)[1:]]
    return [v for v in voci if v]


def parse(path):
    """Trasforma un file di contenuto in una lista di elementi.

    Restituisce tuple: ("sezione", titolo) | ("testo", str) |
    ("evento", data, org, ruolo, [bullet]) | ("bullet", [bullet])
    """
    testo = leggi(path)

    # Rumore tipografico che in Word non ha senso: spaziature fini, colonne.
    for pat in (r"\\vspace\{[^}]*\}", r"\\begin\{multicols\}\{\d+\}",
                r"\\end\{multicols\}", r"\\columnbreak", r"\\itemsep0pt",
                r"\\noindent", r"\\hfill"):
        testo = re.sub(pat, "", testo)
    testo = re.sub(r"(?m)^\s*%.*$", "", testo)          # commenti

    elementi, i = [], 0
    while i < len(testo):
        if testo.startswith(r"\cvsection", i):
            (titolo,), i = argomenti(testo, i + len(r"\cvsection"), 1)
            elementi.append(("sezione", titolo.strip()))
        elif testo.startswith(r"\cvevent", i):
            (data, org, ruolo, corpo), i = argomenti(testo, i + len(r"\cvevent"), 4)
            elementi.append(("evento", data.strip(), org.strip(), ruolo.strip(),
                             bullet(corpo)))
        elif testo.startswith(r"\begin{itemize}", i):
            fine = testo.index(r"\end{itemize}", i)
            elementi.append(("bullet", bullet(testo[i:fine])))
            i = fine + len(r"\end{itemize}")
        else:
            # Testo libero fino alla prossima macro nota (il Profilo).
            prossima = min(
                (p for p in (testo.find(m, i + 1) for m in
                             (r"\cvsection", r"\cvevent", r"\begin{itemize}"))
                 if p != -1),
                default=len(testo))
            pezzo = testo[i:prossima].strip()
            if pezzo and not pezzo.startswith("\\"):
                elementi.append(("testo", pezzo))
            i = prossima if prossima > i else i + 1
    return elementi


def intestazione(path):
    """Nome, contatti e link dal file Intestazione.tex."""
    t = leggi(path)
    def cerca(pat, nome):
        m = re.search(pat, t)
        if not m:
            raise ValueError(f"{nome} non trovato in {path}")
        return m.group(1).strip()

    # Il telefono e' opzionale: se non c'e' nell'intestazione, il .docx lo omette.
    tel = re.search(r"(\+39[\d\s~]+)", t)
    return {
        "nome": cerca(r"\\LARGE\s*\\textbf\{([^}]+)\}", "il nome"),
        "citta": cerca(r"\{([^{}]*Italy)[^{}]*\}", "la citta'"),
        "tel": tel.group(1).replace("~", " ").strip() if tel else None,
        "email": cerca(r"mailto:([^}]+)\}", "l'email"),
        "linkedin": cerca(r"href\{(https://[^}]*linkedin[^}]*)\}", "LinkedIn"),
        "github": cerca(r"href\{(https://[^}]*github[^}]*)\}", "GitHub"),
    }


# --------------------------------------------------------------------------
# Testo inline: LaTeX -> run di Word (grassetto, corsivo, link)
# --------------------------------------------------------------------------

INLINE = re.compile(r"\\(textbf|textit|emph|href)\b|\\LaTeX\{?\}?")

def pulisci(s):
    s = re.sub(r"\\vspace\{[^}]*\}|\\\\|\\,|\\ ", " ", s)
    s = s.replace(r"\textbar", "|").replace("~", " ")
    s = s.replace("---", "—").replace("--", "–")
    s = re.sub(r"\\([&%$#_])", r"\1", s)
    return re.sub(r"[ \t]+", " ", s).strip()


def link(par, url, testo):
    """Aggiunge un hyperlink cliccabile (python-docx non ha un'API sua)."""
    rid = par.part.relate_to(
        url,
        "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True)
    h = OxmlElement("w:hyperlink")
    h.set(qn("r:id"), rid)
    run = par.add_run(testo)
    run.font.color.rgb = RGBColor(0x05, 0x63, 0xC1)
    run.font.underline = True
    h.append(run._r)
    par._p.append(h)


def scrivi(par, testo, size=10, bold=False, italic=False, color=None):
    """Scrive testo LaTeX in un paragrafo, rispettando grassetti e link."""
    i = 0
    while i < len(testo):
        m = INLINE.search(testo, i)
        if not m:
            resto = pulisci(testo[i:])
            if resto:
                r = par.add_run(resto)
                r.bold, r.italic, r.font.size, r.font.name = bold, italic, Pt(size), FONT
                if color:
                    r.font.color.rgb = color
            break

        prima = pulisci(testo[i:m.start()])
        if prima:
            # pulisci() toglie gli spazi ai bordi: qui servono, li rimetto.
            if testo[i:m.start()][:1].isspace():
                prima = " " + prima
            if testo[i:m.start()][-1:].isspace():
                prima += " "
            r = par.add_run(prima)
            r.bold, r.italic, r.font.size, r.font.name = bold, italic, Pt(size), FONT
            if color:
                r.font.color.rgb = color

        cmd = m.group(1)
        if cmd is None:                                   # \LaTeX
            r = par.add_run("LaTeX")
            r.bold, r.italic, r.font.size, r.font.name = bold, italic, Pt(size), FONT
            i = m.end()
        elif cmd == "href":
            (url, etichetta), i = argomenti(testo, m.end(), 2)
            link(par, url, pulisci(etichetta))
        else:
            (arg,), i = argomenti(testo, m.end(), 1)
            scrivi(par, arg, size, bold or cmd == "textbf",
                   italic or cmd in ("textit", "emph"), color)


# --------------------------------------------------------------------------
# Costruzione del documento
# --------------------------------------------------------------------------

def bordo_sotto(par):
    """La riga grigia sotto il titolo di sezione (come \\rule nel .tex)."""
    pPr = par._p.get_or_add_pPr()
    bordi = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "8")
    bottom.set(qn("w:space"), "1")
    bottom.set(qn("w:color"), SOFTCOL)
    bordi.append(bottom)
    pPr.append(bordi)


def paragrafo(contenitore, prima=0, dopo=0, stile=None):
    """Un paragrafo con spaziature esplicite.

    Word, lasciato a se', mette 8 pt di stacco dopo ogni paragrafo e interlinea
    1,08: su un CV denso valgono mezza pagina. Qui ogni spazio e' dichiarato.
    Il contenitore puo' essere il documento o una cella di tabella.
    """
    p = (contenitore.add_paragraph(style=stile) if stile
         else contenitore.add_paragraph())
    p.paragraph_format.space_before = Pt(prima)
    p.paragraph_format.space_after = Pt(dopo)
    p.paragraph_format.line_spacing = 1.0
    return p


def costruisci(doc, header, foto, sezioni, gdpr):
    # --- intestazione: nome e contatti.
    # Con la foto serve una tabella (foto a sinistra, testo a destra): e' il modo
    # con cui Word affianca due blocchi, dove il .tex usa multicols.
    if foto:
        testa = doc.add_table(rows=1, cols=2)
        testa.alignment = WD_TABLE_ALIGNMENT.CENTER
        testa.columns[0].width, testa.columns[1].width = Cm(4), Cm(14)
        cella_foto, contenitore = testa.rows[0].cells
        cella_foto.paragraphs[0].add_run().add_picture(str(foto), width=Cm(2.8))
        # La cella nasce con un paragrafo vuoto: riusalo invece di aggiungerne uno.
        vuoto = contenitore.paragraphs[0]._p
        vuoto.getparent().remove(vuoto)
    else:
        contenitore = doc

    p = paragrafo(contenitore, dopo=1)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(header["nome"])
    r.bold, r.font.size, r.font.name = True, Pt(18), FONT

    p = paragrafo(contenitore, dopo=0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    contatti = (f'{header["citta"]} | {header["tel"]} | ' if header["tel"]
                else f'{header["citta"]} | ')
    r = p.add_run(contatti)
    r.font.size, r.font.name = Pt(9.5), FONT
    link(p, f'mailto:{header["email"]}', header["email"])

    p = paragrafo(contenitore, dopo=0)
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    link(p, header["linkedin"], "LinkedIn")
    r = p.add_run(" | ")
    r.font.size, r.font.name = Pt(9.5), FONT
    link(p, header["github"], "GitHub")

    # --- corpo
    for elementi in sezioni:
        for el in elementi:
            tipo = el[0]

            if tipo == "sezione":
                p = paragrafo(doc, prima=7, dopo=3)
                r = p.add_run(el[1])
                r.bold, r.font.size, r.font.name = True, Pt(11.5), FONT
                r.font.color.rgb = SECTCOL
                bordo_sotto(p)

            elif tipo == "testo":
                p = paragrafo(doc, dopo=1)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                scrivi(p, el[1])

            elif tipo == "evento":
                _, data, org, ruolo, voci = el
                # organizzazione a sinistra, data a destra: tab stop destro,
                # che e' il modo con cui Word fa quello che in LaTeX fa \hfill.
                p = paragrafo(doc, prima=4, dopo=0)
                p.paragraph_format.tab_stops.add_tab_stop(
                    LARGHEZZA_UTILE, WD_TAB_ALIGNMENT.RIGHT)
                r = p.add_run(pulisci(org))
                r.bold, r.font.size, r.font.name = True, Pt(10.5), FONT
                p.add_run("\t")
                r = p.add_run(pulisci(data))
                r.font.size, r.font.name = Pt(10), FONT
                r.font.color.rgb = SECTCOL

                p = paragrafo(doc, dopo=1)
                scrivi(p, ruolo, size=10, italic=True)

                for v in voci:
                    p = paragrafo(doc, dopo=1, stile="List Bullet")
                    scrivi(p, v)

            elif tipo == "bullet":
                for v in el[1]:
                    p = paragrafo(doc, dopo=1, stile="List Bullet")
                    scrivi(p, v)

    if gdpr:
        p = paragrafo(doc, prima=10)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        r = p.add_run(gdpr)
        r.font.size, r.font.name = Pt(6.5), FONT
        r.font.color.rgb = RGBColor(0x80, 0x80, 0x80)


def estrai_testo(docx):
    """Ristampa il testo di un .docx: serve a build.ps1 per verificarlo."""
    doc = Document(docx)
    righe = [p.text for p in doc.paragraphs]
    for t in doc.tables:                      # l'intestazione con foto e' una tabella
        for riga in t.rows:
            righe += [c.text for c in riga.cells]
    print("\n".join(righe))


def main():
    # Modalita' di servizio: python tex2docx.py --testo file.docx
    if len(sys.argv) == 3 and sys.argv[1] == "--testo":
        estrai_testo(sys.argv[2])
        return

    if len(sys.argv) != 3:
        sys.exit("uso: python tex2docx.py <principale.tex> <uscita.docx>\n"
                 "     python tex2docx.py --testo <file.docx>")

    principale, uscita = Path(sys.argv[1]), Path(sys.argv[2])
    radice = principale.parent

    sorgente = leggi(principale)
    foto = (radice / "sorgenti" / "fede.jpg") if r"\phototrue" in sorgente else None

    # I file di contenuto, nell'ordine in cui il .tex li include. Ora stanno in
    # sorgenti/, quindi gli \input portano il prefisso (es. \input{sorgenti/Profilo}).
    inclusi = re.findall(r"(?m)^\s*\\input\{([^}]+)\}", sorgente)
    contenuti = [n for n in inclusi
                 if n not in ("sorgenti/Preambolo", "sorgenti/Intestazione", "sorgenti/GDPR")]

    # Il GDPR sta in "sorgenti/GDPR.tex", incluso da entrambi i main ma stampato
    # solo dove il flag e' \phototrue: la stessa condizione che il .tex risolve
    # con \ifphoto, qui la decide "foto". Non e' una sezione, quindi resta fuori
    # dai contenuti qui sopra.
    gdpr = None
    if foto and "sorgenti/GDPR" in inclusi:
        m = re.search(r"\\tiny\s*(Autorizzo.*?)\s*\\end\{center\}",
                      leggi(radice / "sorgenti" / "GDPR.tex"), re.S)
        if not m:
            sys.exit("sorgenti/GDPR.tex: non trovo il testo dell'autorizzazione")
        gdpr = re.sub(r"\s+", " ", m.group(1))
    if not contenuti:
        sys.exit(f"{principale}: nessun file di contenuto incluso, qualcosa non torna")

    doc = Document()
    sez = doc.sections[0]
    sez.top_margin = sez.bottom_margin = Cm(1.5)
    sez.left_margin = sez.right_margin = Cm(1.5)

    # Gli stili da cui eredita tutto il resto. Senza questo, Word aggiunge di suo
    # 8 pt dopo ogni paragrafo e interlinea 1,08, e il CV sfora la pagina.
    for nome in ("Normal", "List Bullet"):
        stile = doc.styles[nome]
        stile.font.name = FONT
        stile.font.size = Pt(10)
        stile.paragraph_format.space_before = Pt(0)
        stile.paragraph_format.space_after = Pt(0)
        stile.paragraph_format.line_spacing = 1.0

    costruisci(doc,
               intestazione(radice / "sorgenti" / "Intestazione.tex"),
               foto,
               [parse(radice / f"{n}.tex") for n in contenuti],
               gdpr)
    doc.save(uscita)
    print(f"  {uscita.name}: {len(contenuti)} sezioni" + (", con foto" if foto else ""))


if __name__ == "__main__":
    main()
