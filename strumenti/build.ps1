# Genera i due PDF del CV e, dagli stessi sorgenti, i due .docx.
#
#   powershell -File strumenti/build.ps1
#
# In sequenza: latexmk su entrambe le varianti, pulizia degli ausiliari,
# generazione dei .docx con tex2docx.py, verifica che nei .docx ci sia tutto.
# Lo script e' l'unico modo previsto per rigenerare il CV: non lanciare
# latexmk a mano, altrimenti i .docx restano indietro rispetto ai PDF.
#
# Dipendenze: MiKTeX (latexmk), Python con python-docx, pdftotext, Perl.

$ErrorActionPreference = 'Stop'

# Questo script sta in strumenti/, ma i main e i PDF/DOCX vivono in root: e' li'
# che latexmk deve girare e che i prodotti devono finire. Lavoro dalla root.
$repo = Split-Path -Parent $PSScriptRoot
Set-Location $repo

$varianti = @('CV_Federico_Bena', 'CV_Federico_Bena_photo')

# Sezioni che devono comparire in ogni .docx: se una manca, la conversione
# ha perso un pezzo per strada e va segnalato invece che spedito.
$sezioniAttese = @(
    'Profile',
    'Professional Experience',
    'Education',
    'Skills',
    'Languages'
)

# latexmk e' uno script Perl: MiKTeX si rifiuta di eseguirlo se non trova un
# interprete Perl nel PATH. Su questa macchina Perl arriva con Git for Windows,
# che pero' e' nel PATH solo di Git Bash: da PowerShell va aggiunto a mano.
if (-not (Get-Command perl -ErrorAction SilentlyContinue)) {
    $perl = @(
        'C:\Program Files\Git\usr\bin',
        'C:\Strawberry\perl\bin'
    ) | Where-Object { Test-Path (Join-Path $_ 'perl.exe') } | Select-Object -First 1

    if (-not $perl) { throw "Perl non trovato: latexmk non puo' girare. Installa Git for Windows o Strawberry Perl." }
    $env:PATH = "$perl;$env:PATH"
}

foreach ($cmd in 'latexmk', 'python', 'pdftotext') {
    if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
        throw "$cmd non e' installato o non e' nel PATH."
    }
}

# --- 1. PDF ------------------------------------------------------------------

foreach ($v in $varianti) {
    Write-Host "[PDF]  $v.tex" -ForegroundColor Cyan
    latexmk -pdf -interaction=nonstopmode "$v.tex" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "latexmk ha fallito su $v.tex (guarda $v.log)" }
    latexmk -c "$v.tex" | Out-Null   # -c pulisce gli ausiliari e tiene il PDF; -C cancellerebbe anche quello
}

# --- 2. DOCX -----------------------------------------------------------------

# LaTeX sa produrre solo PDF: il .docx non e' una conversione ma una
# ricostruzione del CV con gli strumenti di Word, fatta da tex2docx.py leggendo
# gli stessi sorgenti .tex. Non e' una copia del PDF e non deve esserlo.
foreach ($v in $varianti) {
    Write-Host "[DOCX] $v.docx" -ForegroundColor Cyan
    python (Join-Path $PSScriptRoot 'tex2docx.py') "$v.tex" "$v.docx"
    if ($LASTEXITCODE -ne 0) { throw "tex2docx.py ha fallito su $v.tex" }
}

# --- 3. Verifica -------------------------------------------------------------

# "Ha girato senza errori" non e' una verifica. Quello che conta e' che nel
# .docx ci sia lo stesso CONTENUTO del PDF (l'aspetto no: quello e' diverso per
# scelta). Confronto parola per parola il testo estratto dai due file.
function Parole($testo) {
    # pdftotext spezza le parole a fine riga ("elec-\n trical"): ricuce.
    $t = $testo -replace '-\s*\r?\n\s*', ''
    # I trattini (\p{Pd}: ASCII, en dash, em dash, non-separabile) spariscono da
    # entrambi i lati, cosi' "model-based" e "modelbased" non risultano parole
    # diverse solo per come sono andate a capo.
    $t = $t -replace '\p{Pd}', ''
    ($t.ToLower() -split '[^\p{L}\p{Nd}]+') | Where-Object { $_.Length -ge 3 }
}

$txt = Join-Path $env:TEMP "cv-verifica-$PID"
New-Item -ItemType Directory -Force -Path $txt | Out-Null

try {
    foreach ($v in $varianti) {
        pdftotext -layout -enc UTF-8 "$v.pdf" (Join-Path $txt "$v.pdf.txt")
        $env:PYTHONIOENCODING = 'utf-8'
        python (Join-Path $PSScriptRoot 'tex2docx.py') --testo "$v.docx" |
            Out-File -FilePath (Join-Path $txt "$v.docx.txt") -Encoding utf8

        $daPdf  = Parole ([System.IO.File]::ReadAllText((Join-Path $txt "$v.pdf.txt")))
        $daDocx = Parole ([System.IO.File]::ReadAllText((Join-Path $txt "$v.docx.txt")))

        $mancanti = $sezioniAttese | Where-Object { $daDocx -notcontains $_.Split(' ')[0].ToLower() }
        if ($mancanti) {
            throw "$v.docx e' incompleto, mancano le sezioni: $($mancanti -join ', ')"
        }

        # Ogni parola che sta nel PDF deve stare anche nel .docx.
        $vocabolario = [System.Collections.Generic.HashSet[string]]::new(
            [string[]]$daDocx, [System.StringComparer]::Ordinal)
        $persi = $daPdf | Where-Object { -not $vocabolario.Contains($_) } | Select-Object -Unique
        if ($persi) {
            throw "$v.docx: contenuto perso rispetto al PDF, mancano le parole:`n  $($persi -join ', ')"
        }

        Write-Host "  $v.docx: contenuto identico al PDF ($($daPdf.Count) parole)" -ForegroundColor DarkGray
    }
} finally {
    Remove-Item -Recurse -Force $txt -ErrorAction SilentlyContinue
}

# Il CV sta in UNA pagina: vale per il PDF e vale per il .docx. Il conteggio lo
# fa Word, che e' l'unico a sapere davvero come impagina il proprio formato.
$word = $null
try {
    $word = New-Object -ComObject Word.Application
    $word.Visible = $false
} catch {
    Write-Warning "Word non disponibile: salto il controllo del numero di pagine dei .docx."
}

if ($word) {
    try {
        foreach ($v in $varianti) {
            $doc = $word.Documents.Open((Join-Path $repo "$v.docx"), $false, $true)
            $pagine = $doc.ComputeStatistics(2)   # 2 = wdStatisticPages
            $doc.Close(0)
            if ($pagine -ne 1) {
                throw "$v.docx occupa $pagine pagine: il CV deve starne in una. Stringi le spaziature in tex2docx.py o taglia contenuto."
            }
            Write-Host "  $v.docx: 1 pagina" -ForegroundColor DarkGray
        }
    } finally {
        $word.Quit()
        [void][Runtime.InteropServices.Marshal]::ReleaseComObject($word)
    }
}

Write-Host "`nFatto: 2 PDF + 2 DOCX aggiornati." -ForegroundColor Green
Get-ChildItem *.pdf, *.docx | Select-Object Name, Length, LastWriteTime | Format-Table -AutoSize
