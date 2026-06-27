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

### Step 3 — Localizzazione titolo: Named Destinations (primary) + text search (fallback)

Chromium crea **named destinations** PDF per ogni elemento HTML con attributo `id`. L'estensione `toc` di Python-Markdown assegna automaticamente `id` agli heading usando la stessa funzione `slugify`:

```text
"## 2.1 Ship Profiles"  →  id="21-ship-profiles"
"## Dashboard"          →  id="dashboard"
"### Actions Phase"     →  id="actions-phase"
```

`slugify` replica la logica dell'estensione `toc`:
1. NFKD normalize → encode ASCII (strip non-ASCII)
2. Rimuove caratteri non-word, non-space, non-hyphen
3. Strip + lowercase
4. Sostituisce sequenze di `[\s_-]+` con `-`

**Algoritmo di localizzazione per ogni heading:**

```text
slug = slugify(clean_text)

se slug in reader.named_destinations:
    dest = named_destinations[slug]
    page_num = dest.page           ← numero pagina esatto
    top = dest.top                 ← coordinata Y in punti PDF
    → usa Fit.xyz(left=None, top=top, zoom=None)   ← scroll esatto

altrimenti (fallback text search):
    per i in range(search_from, n_pagine):
        se text in page_texts[i]:
            page_num = i, top = None
            → usa add_outline_item senza Fit (cima pagina)
            break
```

Il puntatore `search_from` avanza comunque in avanti su entrambi i path.

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
| `pyproject.toml` | Aggiunge `pypdf` alle dipendenze |
| `logic/conversion.py` | Aggiunge `PdfOutlineInjector` (con slugify + named dest lookup), aggiorna `GotenbergClient.__init__` e `render_pdf`, aggiunge `toc` extension a `MarkdownRenderer` |

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
