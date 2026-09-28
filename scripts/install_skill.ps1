<#
.SYNOPSIS
    Skill paketini ~/.agents/skills/ altina tekrarlanabilir sekilde aynalar.

.DESCRIPTION
    Aynalama daha once ad-hoc `robocopy /MIR` ile yapiliyordu. Iki sonuc
    oldu: kurulu kopyada 4 adet derleme artigi (*.pyc) birikti ve kopya
    SKILL.md'nin icerik agaci atiflarini tasidigi halde o dosyalar
    olmadigi icin eksik gorunuyordu.

    Bu betigin yaptigi:
      1. Kaynagi depo kokunden DEGIL, skill dizininden alir. Boylece
         ikinci bir kaynak olusmaz.
      2. Derleme artiklarini disarida birakir.
      3. Kopyanin NE OLDUGUNU soyler: yalnizca metadata. Komutlar
         calistirilabilir degildir; onlar deponun kokunden calisir.
         Bu, skill.yaml'daki `runtime.execution_root` degeriyle ayni
         kaynaktan okunur, ayri bir iddia degildir.

    Satirlar ASCII yazildi: Windows PowerShell 5.1, BOM'suz dosyayi
    ANSI okur ve Turkce karakterleri bozar. Turkce metin iceren bir
    .ps1 uretiyorsan BOM ekle.

.PARAMETER DryRun
    Hicbir sey yazmaz; yalnizca kopyalanacak dosyalari listeler.

.PARAMETER Target
    Aynalama hedefi. Varsayilan: ~/.agents/skills/academic-thesis-writer

.EXAMPLE
    .\scripts\install_skill.ps1 -DryRun
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [string]$Target
)

$ErrorActionPreference = 'Stop'

# --- kaynak: depo koku degil, skill dizini --------------------------------
$Kaynak = Join-Path $PSScriptRoot '..\.opencode\skill\academic-thesis-writer'
$Kaynak = (Resolve-Path $Kaynak).Path

if (-not $Target) {
    $Target = Join-Path $HOME '.agents\skills\academic-thesis-writer'
}

if (-not (Test-Path $Kaynak)) {
    Write-Error "Kaynak bulunamadi: $Kaynak"
    exit 1
}

# --- ilan edilen modeli oku: uyari bu degeri kullanir ---------------------
# Uyarinin skill.yaml'dan dogrudan beslenmesi, uyarinin ilan edilen
# modelle celismesini yapamaz hale getirir.
$Yapilandirma = Get-Content (Join-Path $Kaynak 'skill.yaml') -Raw -Encoding UTF8
$Eslesme = [regex]::Match($Yapilandirma, '(?m)^\s*execution_root:\s*(\S+)')
if ($Eslesme.Success) {
    $Kok = $Eslesme.Groups[1].Value
} else {
    $Kok = 'ILAN-EDILMEMIS'
}

# --- kopyalanacak dosyalar: derleme artiklari haric -----------------------
$Dosyalar = Get-ChildItem -Path $Kaynak -Recurse -File | Where-Object {
    $_.FullName -notmatch '\\__pycache__\\' -and $_.Extension -ne '.pyc'
} | Sort-Object FullName

# Kopyalanmayan ama diskte durabilecek seyler: kullaniciya goster ki
# var olduklarini bilsin, sessizce kaybolmasinlar.
$Atlanan = Get-ChildItem -Path $Kaynak -Recurse -File | Where-Object {
    $_.FullName -match '\\__pycache__\\' -or $_.Extension -eq '.pyc'
}

Write-Output "Kaynak : $Kaynak"
Write-Output "Hedef  : $Target"
Write-Output ""

if ($DryRun) {
    Write-Output "DryRun: HICBIR SEY YAZILMADI. Kopyalanacak dosyalar:"
    foreach ($d in $Dosyalar) {
        $Goreli = $d.FullName.Substring($Kaynak.Length).TrimStart('\', '/')
        Write-Output "  + $Goreli"
    }
} else {
    if (-not (Test-Path $Target)) {
        New-Item -ItemType Directory -Path $Target -Force | Out-Null
    }
    foreach ($d in $Dosyalar) {
        $Goreli = $d.FullName.Substring($Kaynak.Length).TrimStart('\', '/')
        $HedefYol = Join-Path $Target $Goreli
        $HedefDizin = Split-Path $HedefYol -Parent
        if (-not (Test-Path $HedefDizin)) {
            New-Item -ItemType Directory -Path $HedefDizin -Force | Out-Null
        }
        Copy-Item $d.FullName $HedefYol -Force
    }
    Write-Output "Aynalandi: $($Dosyalar.Count) dosya -> $Target"

    # Onceki aynalamadan kalan derleme artiklarini temizle.
    Get-ChildItem -Path $Target -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
        ForEach-Object { Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue }
}

if ($Atlanan) {
    Write-Output ""
    Write-Output "Atlanan derleme artiklari: $($Atlanan.Count)"
    foreach ($a in $Atlanan) {
        $Goreli = $a.FullName.Substring($Kaynak.Length).TrimStart('\', '/')
        Write-Output "  - $Goreli"
    }
}

# --- kopyanin ne oldugunu soyle --------------------------------------------
Write-Output ""
Write-Output "----------------------------------------------------------------"
Write-Output "Kopya YALNIZCA metadata'dir. execution_root = $Kok"
Write-Output ""
Write-Output "Bu dizin SKILL.md, skill.yaml, agents/ ve hooks/ tasir. Skill"
Write-Output "orada anlattigi diger yollar deponun kokunden cozulur ve bu"
Write-Output "kopya onlari icermez. Ayrica hicbir komut buradan"
Write-Output "calistirilamaz: komutlar `python -m tools.atw.cli` cagirir ve"
Write-Output "calistirilabilir kod deponun kokundadir."
Write-Output ""
Write-Output "Yani: ajan tanimlari ve skill icerigi bu dizinden okunur;"
Write-Output "tez isleri her zaman deponun kokunden calistirilir."
Write-Output "----------------------------------------------------------------"
