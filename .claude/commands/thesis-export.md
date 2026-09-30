---
description: Final tez metnini birleştir (bölümler + kaynakça); ekler dışa aktarılmaz
argument-hint: "[--format md|docx|pdf ...] [--out DİZİN]"
---

Tez dışa aktarımı. `python -m tools.atw.cli export` alt komutunu `$ARGUMENTS`
ile çalıştır. Bölümler + kaynakça birleştirilir; appendices alanı şemada
olmadığı için ekler dışa aktarılmaz.

`--format` verilmezse **iki** dosya üretilir: `md` (okunabilir metin, farkı
incelenebilir) ve `docx` (teslim edilebilir). Markdown insaya teslim
biçimi **değildir**; yalnız Markdown üretmek, teslim edilebilir biçimi
aramak zorunda bırakırdı.

`--format` birden fazla değer alabilir ve sırayı korur:
`--format docx md` → önce `.docx`, sonra `.md`.

Tüm biçimler **önce bellekte** üretilir; hepsi başarılı olmadan hiçbir
dosya yazılmaz. Yarı teslim bir teslim değildir.

Çalıştır: `python -m tools.atw.cli export $ARGUMENTS`

Oluşan dosya(ları) ve yolu kullanıcıya raporla.