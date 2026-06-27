# SPEC // PDF Bookmark Outline Injection

**Feature**: Aggiunta automatica di bookmark (outline PDF) ai documenti generati da SC-ARCHIVE.  
**Modulo target**: `logic/conversion.py`  
**Dipendenza nuova**: `pypdf >= 4.0`

---

## Contesto

Gotenberg (Chromium `printToPDF`) non genera bookmark PDF nativamente. I documenti SC-ARCHIVE sono Markdown lineari: i titoli appaiono nell'ordine esatto del sorgente, senza riordinamento dinamico. Questa garanzia rende affidabile un approccio di post-processing.

Pipeline attuale:

```text
Markdown → MarkdownRenderer → PdfHtmlBuilder → Gotenberg → PDF bytes
```

Pipeline con bookmark:

```text
Markdown → MarkdownRenderer → PdfHtmlBuilder → Gotenberg → PDF bytes → PdfOutlineInjector → PDF bytes con outline
```

---

## Nuova classe: `PdfOutlineInjector`

Responsabilità unica: ricevere i byte PDF grezzi e il sorgente Markdown, iniettare l'outline e restituire i byte PDF arricchiti.

```python
class PdfOutlineInjector:
    """Post-processes Gotenberg PDF output to inject a navigable bookmark outline."""

    def inject(self, pdf_bytes: bytes, markdown_content: str) -> bytes:
        ...
```

### Step 1 — Estrazione titoli dal Markdown

Regex su `^(#{1,6})\s+(.+)$` in modalità multiline. Per ogni match:

- `level` = lunghezza del gruppo `#` (1–6)
- `text` = gruppo testo, stripped

I titoli vengono poi **sanitizzati**: rimosso Markdown inline (bold `**`, italic `*`, backtick, link `[text](url)`) per ottenere testo puro confrontabile con il testo estratto dal PDF.

```python
_MD_INLINE = re.compile(r'\*{1,2}|`|!?\[([^\]]*)\]\([^)]*\)')

def _clean(text: str) -> str:
    return _MD_INLINE.sub(r'\1', text).strip()
```

### Step 2 — Estrazione testo per pagina

`pypdf.PdfReader` espone `page.extract_text()`. Si costruisce una lista ordinata di stringhe, una per pagina.

Edge case: se `extract_text()` restituisce `None` o stringa vuota, la pagina viene trattata come vuota (il titolo verrà cercato nelle pagine successive).

### Step 3 — Localizzazione titolo: text search + coordinate CTM×TM

> **Nota**: Gotenberg usa Chromium `printToPDF` che **non genera named destinations** nel PDF prodotto — `reader.named_destinations` è sempre vuoto. La localizzazione si basa interamente su text extraction e coordinate della matrice di testo.

**3a — Text search per numero di pagina:**

Per ogni heading (testo già sanitizzato in Step 1), si cerca nella lista `page_texts` costruita in Step 2, avanzando da `search_from` (puntatore che preserva l'ordinamento dei titoli nel documento):

```text
per i in range(search_from, n_pagine):
    se text in page_texts[i] oppure text.lower() in page_texts[i].lower():
        page_num = i
        break
```

**3b — Estrazione coordinata Y via visitor CTM×TM:**

Una volta trovata la pagina, si usa `page.extract_text(visitor_text=callback)` per ottenere le coordinate precise del testo. Chromium genera PDF con una CTM (Current Transformation Matrix) che scala e trasla le coordinate — `tm[5]` (Y della text matrix) non è direttamente in PDF user space.

Trasformazione corretta:

```text
y_pdf = um[1]*tm[4] + um[3]*tm[5] + um[5]
```

dove `um` è la CTM (matrice `[a,b,c,d,e,f]`) e `tm` è la text matrix. Il visitor accumula `(text_chunk, y_pdf)` per ogni frammento non vuoto. Dopo la visita si concatena il testo di tutti i chunk e si individua l'offset dell'heading — la Y del chunk corrispondente è la coordinata di scroll.

```python
chunks: list[tuple[str, float]] = []

def visitor(text, um, tm, _fd, _fs):
    if text.strip() and um and tm:
        y_pdf = float(um[1])*float(tm[4]) + float(um[3])*float(tm[5]) + float(um[5])
        chunks.append((text, y_pdf))

page.extract_text(visitor_text=visitor)

full_text = ''.join(c[0] for c in chunks)
idx = full_text.lower().find(heading_text.lower())
# trova il chunk che contiene idx → restituisce la sua y_pdf
```

Se il visitor fallisce o il testo non viene trovato nel chunk breakdown, `top` è `None` — il bookmark punta comunque alla pagina ma senza scroll preciso.

### Step 4 — Iniezione outline gerarchica

`pypdf.PdfWriter.add_outline_item(title, page_number, parent, fit)`. L'albero gerarchico si mantiene con uno stack. Il parametro `fit` è `Fit.xyz(...)` se la coordinata Y è disponibile, altrimenti omesso (comportamento default = cima pagina):

```text
stack = []   # lista di (level, outline_item_reference)

per ogni (level, text, page_num, top):
    mentre stack non vuoto e stack[-1].level >= level:
        pop dallo stack
    parent = stack[-1].item se stack non vuoto else None
    se top is not None:
        item = writer.add_outline_item(text, page_num, parent, fit=Fit.xyz(None, top, None))
    altrimenti:
        item = writer.add_outline_item(text, page_num, parent)
    push (level, item) sullo stack
```

Esempio con `# H1 / ## H2 / ## H2 / ### H3 / # H1`:

```text
H1 (p.1)
├── H2 (p.2)
├── H2 (p.3)
│   └── H3 (p.4)
H1 (p.5)
```

### Step 5 — Serializzazione

```python
writer = PdfWriter()
writer.append(PdfReader(BytesIO(pdf_bytes)))  # clona reader intero
# ... add_outline_item calls ...
output = BytesIO()
writer.write(output)
return output.getvalue()
```

`writer.append()` preserva metadati, permessi e struttura interna del PDF originale.

---

## Gestione errori

| Caso | Comportamento |
| ---- | ------------- |
| Nessun titolo nel Markdown | Restituisce `pdf_bytes` originale senza modifiche |
| Titolo non trovato in nessuna pagina | Skip silenzioso — outline parziale |
| `extract_text()` fallisce su tutte le pagine | Log warning, restituisce `pdf_bytes` originale |
| Eccezione generica in `inject()` | Log warning, restituisce `pdf_bytes` originale — mai propagare |

L'injector non deve mai bloccare la generazione PDF: worst case, il PDF esce senza outline.

---

## Integrazione in `GotenbergClient`

Il `PdfOutlineInjector` viene iniettato via costruttore (DIP), con default non-None per retrocompatibilità:

```python
class GotenbergClient:
    def __init__(
        self,
        url_provider: Callable[[], str],
        renderer: Optional[RendererProtocol] = None,
        builder: Optional[HtmlBuilderProtocol] = None,
        outline_injector: Optional[PdfOutlineInjector] = None,
    ):
        ...
        self._outline_injector = outline_injector or PdfOutlineInjector()
```

In `render_pdf`, dopo aver ricevuto la risposta da Gotenberg:

```python
pdf_bytes = response.content
pdf_bytes = self._outline_injector.inject(pdf_bytes, markdown_content)
return pdf_bytes
```

`markdown_content` è già disponibile come parametro di `render_pdf`.

---

## Dipendenze

Aggiungere a `pyproject.toml`:

```toml
"pypdf (>=4.0.0,<5.0.0)"
```

Nessuna dipendenza di sistema aggiuntiva — `pypdf` è pure Python.

---

## File modificati

| File | Modifica |
| ---- | -------- |
| `pyproject.toml` | Aggiunge `pypdf (>=4.0.0,<5.0.0)` alle dipendenze |
| `logic/conversion.py` | Aggiunge `PdfOutlineInjector` (con text search + visitor CTM×TM), aggiorna `GotenbergClient.__init__` e `render_pdf`, aggiunge `toc` extension a `MarkdownRenderer` |

Nessuna modifica a route, template o settings.

---

## Test

Casi da coprire nella test suite (`tests/test_conversion.py`):

1. **Markdown senza titoli** → PDF originale restituito invariato
2. **Titoli h1/h2/h3 su pagine diverse** → outline gerarchica corretta
3. **Titolo con Markdown inline** (`**bold**`, link) → testo sanitizzato correttamente
4. **Titolo non trovato nel PDF** → skip, outline parziale, nessuna eccezione
5. **Eccezione in `extract_text()`** → PDF originale restituito, nessuna eccezione propagata

I test useranno PDF sintetici generati con `pypdf` stesso (senza Gotenberg) per isolare la logica dell'injector.

---

SC-ARCHIVE // Aegis Engineering Spec — PDF Outline Protocol
