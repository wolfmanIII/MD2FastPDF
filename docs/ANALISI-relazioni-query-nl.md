# SC-Archive — Query in linguaggio naturale via Ollama (RF-11)

**Documento di analisi: requisiti + progettazione tecnica**
Versione 1.0 — 26 luglio 2026

---

## 0. Nota per Claude Code

Questo documento è il segnaposto promesso da RF-11 (Fase 3 esplorativa) di
`docs/ANALISI-relazioni-tipizzate.md` §4.3, aperto dopo aver verificato con l'utente
che Fase 1 (#3–#6) e Fase 2 (#7–#8, più le estensioni di vocabolario #11/#12) sono già
in uso reale sull'archivio della campagna — il gate esplicito di issue #9 è quindi
considerato soddisfatto.

Stesso principio di grounding empirico del documento padre: nessuna decisione qui
sostituisce una verifica sui dati reali quando l'implementazione la rende possibile
(es. quale formato di query il modello locale riesce davvero a produrre in modo
affidabile va verificato con il modello effettivo dell'utente, non assunto).

Questo documento **non** copre COMMS (`docs/aegis-comms.md`), che resta un sistema
distinto e non viene toccato.

---

## 1. Contesto

L'archivio ha ora un indice di relazioni tipizzate interrogabile in memoria
(`RelationIndex.related()` / `.relations_of()`, §5.3/5.7 del documento padre) e un
vocabolario stabile (`VOCABULARY`, 11 relazioni). COMMS esiste già come chat
utente-utente. L'idea di RF-11, discussa in issue #9: un secondo terminale chat —
**Terminale Archivio**, distinto da COMMS — dove l'input in linguaggio naturale
dell'utente viene tradotto da Ollama in una query strutturata sul `RelationIndex`,
invece di generare testo libero. Diegeticamente coerente con la presentazione del
programma come terminale *Library Data* di bordo.

### 1.1 Perché non bastano le query dirette già esistenti (RF-4/RF-5)

`GET /api/entities/{key}/relations/{relation}` risponde già a "equipaggio della
Beowulf" — ma richiede di conoscere la chiave esatta dell'entità e il nome esatto
della relazione. L'utente al tavolo non pensa in termini di `crew`/`beowulf`: pensa
"chi è ostile a Kira Venn?" o "quali navi possiede Malen Trast?". Il salto da
colmare è linguaggio naturale → `(entità, relazione)` risolti, non l'esecuzione della
query in sé, già disponibile.

---

## 2. Non-obiettivi

Espliciti, e vincolanti — stesso spirito di §3 del documento padre:

| Non-obiettivo | Motivo |
| --- | --- |
| Un chatbot generico | Il terminale traduce in query strutturate o fallisce esplicitamente (§5.5) — non genera conversazione libera senza scopo di query. |
| Sostituire o fondersi con COMMS | Restano due sistemi distinti: COMMS è chat utente-utente persistita su disco, il Terminale Archivio è utente-`RelationIndex` via Ollama, senza persistenza (§5.8). |
| Un nuovo motore di ricerca semantica/embedding | Il fallback (§5.5) riusa `DirectoryLister.search()`, già esistente — nessuna nuova infrastruttura di ricerca. |
| Rispondere con testo generato liberamente da Ollama sui fatti della campagna | La risposta è sempre ancorata ai dati restituiti da `RelationIndex` — mai un'allucinazione di Ollama spacciata per fatto della campagna. |
| Progettare qui la UI grafica in dettaglio | Solo l'architettura e il contratto dati; il markup HTMX/Jinja2 è un dettaglio implementativo dello step 7 del piano (§6). |

---

## 3. Requisiti funzionali

**RF-11.1 — Traduzione NL → query strutturata**
Data una frase in linguaggio naturale, Ollama produce un oggetto JSON con
un'interpretazione candidata: intento, entità di riferimento, relazione.

**RF-11.2 — Validazione ed esecuzione server-side**
Il server non si fida ciecamente dell'output del modello: valida `relation` contro
`VOCABULARY_BY_NAME`/`VOCABULARY_BY_INVERSE` ed `entity` contro `RelationIndex`
prima di eseguire qualunque query. Un output non valido è sempre trattato come
`unresolved` (§5.5), mai eseguito a scatola chiusa.

**RF-11.3 — Gestione ambiguità**
Se l'entità nominata corrisponde a più file (collisione, già tracciata da RF-7) o a
nessuna corrispondenza esatta ma a più candidati plausibili, il terminale **chiede
di disambiguare** nella stessa conversazione invece di scegliere in silenzio.

**RF-11.4 — Fallback a ricerca testuale**
Se la traduzione fallisce o non supera la validazione, il terminale ripiega su
`DirectoryLister.search()` (già esistente) e presenta i risultati come *menzioni
testuali*, etichettati esplicitamente come diversi da una risposta strutturata.

**RF-11.5 — Terminale Archivio (UI)**
Nuova vista chat-like, distinta da COMMS, senza persistenza su disco dei messaggi
(sono query, non comunicazioni — v. §5.8 per la ragione).

**RF-11.6 — Modello dedicato**
Nuovo slot di configurazione `neural_query` in `config/settings.py`, indipendente da
`neural_hint`/`neural_scan`/`mermaid_synthesis`, esposto nella UI di Settings con lo
stesso pattern già in uso per gli altri tre.

---

## 4. Progettazione tecnica

### 4.1 Schema della query strutturata

Ollama deve produrre un singolo oggetto JSON, mai prosa:

```json
{
  "intent": "relation_query",
  "entity": "Kira Venn",
  "relation": "hostile_to"
}
```

oppure, quando il modello stesso non trova una corrispondenza sensata:

```json
{ "intent": "unresolved" }
```

`relation` è il **nome libero prodotto dal modello** — non è ancora garantito che
corrisponda a una chiave di `VOCABULARY`: la validazione (§4.3) avviene sempre
dopo, lato server.

### 4.2 Prompt di traduzione

Il system prompt elenca **dinamicamente** le relazioni disponibili (name, inverse,
label) leggendo `VOCABULARY` a runtime — mai una lista hardcoded nel testo del
prompt, altrimenti ogni crescita del vocabolario (come già avvenuto due volte con
`npcs`/`organizations`) richiederebbe di ricordarsi di aggiornare anche il prompt.

```python
def _build_query_prompt() -> str:
    relations_desc = "\n".join(
        f"- {r.name} ({r.label}) / inverso: {r.inverse} ({r.inverse_label})"
        for r in VOCABULARY
    )
    return (
        "Sei il modulo di interrogazione dell'AEGIS Library Data terminal. "
        "Traduci la richiesta dell'utente in un oggetto JSON con questo schema: "
        '{"intent": "relation_query", "entity": "<nome>", "relation": "<chiave>"} '
        "oppure {\"intent\": \"unresolved\"} se non trovi una corrispondenza chiara. "
        "Relazioni disponibili:\n" + relations_desc + "\n"
        "Output SOLO il JSON, nessun altro testo."
    )
```

⚠️ Da verificare in fase di implementazione, con il modello locale effettivo
dell'utente (oggi `llama3.2` per gli slot esistenti): se l'endpoint Ollama in uso
supporta il parametro `format: "json"` (JSON mode) per forzare l'output — se sì,
usarlo sempre; se il modello configurato per `neural_query` non lo supporta bene,
serve un parsing difensivo (estrazione del primo blocco `{...}` valido dalla
risposta) prima di arrendersi a `unresolved`.

### 4.3 Validazione post-traduzione (mai fidarsi del modello)

```python
def _resolve_translated_query(raw: dict, index: RelationIndex) -> ResolvedQuery | Ambiguous | None:
    """None => unresolved (fallback a ricerca testuale, RF-11.4).
    Ambiguous => più candidati, il chiamante chiede di disambiguare (RF-11.3)."""
    if raw.get("intent") != "relation_query":
        return None

    relation_name = raw.get("relation")
    relation_def = VOCABULARY_BY_NAME.get(relation_name) or VOCABULARY_BY_INVERSE.get(relation_name)
    if relation_def is None:
        return None  # il modello ha inventato una relazione: unresolved, non un errore fatale

    candidates = index.find_by_display_name(raw.get("entity", ""))  # nuovo helper, v. §4.4
    if not candidates:
        return None
    if len(candidates) > 1:
        return Ambiguous(candidates)
    return ResolvedQuery(entity_key=candidates[0].key, relation=relation_name)
```

Una relazione inventata da Ollama (non presente in `VOCABULARY_BY_NAME`/
`_BY_INVERSE`) **non è un errore da propagare**: diventa semplicemente
`unresolved`, con lo stesso trattamento non bloccante già stabilito per
`DomainViolation`/`dangling` nel resto della feature.

### 4.4 Risoluzione dell'entità e ambiguità (RF-11.3)

`RelationIndex` oggi risolve per chiave canonica esatta (`entities[canonical_key(x)]`),
sufficiente per RF-4/RF-5 dove l'utente scrive il nome esatto. Qui l'input è
linguaggio naturale imperfetto ("Kira", non "Kira Venn"): serve un nuovo metodo di
lookup **per sottostringa sul `display_name`**, distinto dalla risoluzione esatta
esistente (che resta invariata per il frontmatter):

```python
def find_by_display_name(self, query: str) -> list[Entity]:
    """Sottostringa case-insensitive su display_name — usato solo dalla
    traduzione NL (RF-11), mai dalla risoluzione dei riferimenti in
    frontmatter (che resta canonical_key esatta, RF-3/RF-4)."""
    needle = query.strip().casefold()
    if not needle:
        return []
    return [e for e in self.entities.values() if needle in e.display_name.casefold()]
```

Zero, uno o più risultati guidano il flusso: zero → `unresolved` (§5.5), uno → query
eseguita direttamente, più di uno → disambiguazione (RF-11.3): il terminale elenca i
nomi candidati e aspetta il turno successivo. Lo stato "ultima domanda ambigua +
candidati" vive **in sessione** (stesso meccanismo di sessione già usato per
l'autenticazione), mai persistito su disco — coerente con RF-11.5 (nessuna
persistenza dei messaggi).

### 4.5 Fallback a ricerca testuale (RF-11.4)

Quando la risoluzione produce `None` (relazione inventata, entità non trovata, JSON
non parsabile, Ollama irraggiungibile): il terminale esegue
`DirectoryLister.search(messaggio_originale_utente)` — la stessa funzione già usata
da `routes/archive.py::perform_search` — e presenta i file trovati come "menzioni
testuali", con un'etichetta esplicita tipo *"Traduzione non riuscita — risultati di
ricerca testuale"*, per non far credere all'utente di aver ricevuto una risposta
strutturata quando non è così.

### 4.6 Modello dedicato (RF-11.6)

```python
DEFAULT_SETTINGS = {
    ...
    "models": {
        "neural_hint": "llama3.2",
        "neural_scan": "llama3.2",
        "mermaid_synthesis": "qwen2.5-coder:7b",
        "neural_query": "llama3.2",   # nuovo — RF-11
    }
}
```

Nuovo metodo su `OracleClient`, stesso stile di `generate_syntax`/`summarize`:

```python
async def translate_query(self, message: str) -> dict:
    """Traduce un messaggio in linguaggio naturale in una query strutturata
    grezza (non validata — la validazione è responsabilità del chiamante,
    §4.3). Ritorna {"intent": "unresolved"} su qualunque errore di rete,
    parsing o modello irraggiungibile — mai un'eccezione propagata fin qui,
    coerente con RF-11.4 (il fallback deve poter scattare sempre)."""
```

Esposto nella UI Settings esistente (stesso pattern già in uso per gli altri tre
slot — nessuna nuova sezione, solo un campo in più).

### 4.7 Endpoint HTTP

| Metodo | Path | Scopo |
| --- | --- | --- |
| `POST` | `/api/oracle/archive-query` | Riceve `{"message": "..."}`, ritorna `{"kind": "answer" \| "disambiguate" \| "fallback_search", ...}` |

`kind: "answer"` porta il risultato di `RelationIndex.related()`, serializzato con
lo stesso `_serialize_entity()` già usato da `routes/relations.py`. `"disambiguate"`
porta la lista di candidati. `"fallback_search"` porta i risultati di
`DirectoryLister.search()`.

### 4.8 UI — Terminale Archivio (RF-11.5)

Nuova route (es. `GET /archive-terminal`) + template dedicato, visivamente affine a
`comms_hub.html` per coerenza con il resto dell'app, ma **senza** lo storage
`inbound/outbound/staging` di COMMS: qui non ci sono messaggi da conservare, solo
lo stato minimo di disambiguazione in sessione (§4.4). Da tenere distinto anche
nella navigazione (voce di menu separata da COMMS), per non generare l'aspettativa
che un'altra persona stia "rispondendo" dall'altra parte.

---

## 5. Piano di implementazione

Ordine consigliato, ogni step verificabile in isolamento:

1. Nuovo slot `neural_query` in `config/settings.py` + esposizione nella UI Settings.
2. `RelationIndex.find_by_display_name()` (§4.4) — puro, testabile senza Ollama.
3. `OracleClient.translate_query()` (§4.6) — prompt dinamico, parsing difensivo del
   JSON, mai un'eccezione propagata.
4. Validazione server-side (§4.3) — `_resolve_translated_query()`, puro, testabile
   con input JSON fissi senza rete.
5. Fallback a `DirectoryLister.search()` (§4.5).
6. Stato di disambiguazione in sessione (§4.4).
7. Endpoint HTTP `/api/oracle/archive-query` (§4.7).
8. UI: nuova vista "Terminale Archivio" (§4.8).

Gli step 2 e 4 sono puri e non toccano Ollama: coprono l'80% della logica con test
verificabili senza un'istanza reale in esecuzione.

---

## 6. Strategia di test

⚠️ **Gap da colmare**: oggi non esiste nessun test su `logic/oracle.py` o
`routes/oracle.py` — zero precedenti da cui copiare un pattern di mock per Ollama, e
nessuna libreria di mocking HTTP (`respx` e simili) è tra le dipendenze. Per RF-11 si
propone `httpx.MockTransport` — già parte di `httpx`, già una dipendenza diretta del
progetto, **zero nuove dipendenze** — passato a `httpx.AsyncClient(transport=...)`
al posto di colpire un endpoint reale.

- **Unitari, senza Ollama**: `find_by_display_name` (zero/uno/più risultati,
  case-insensitive, sottostringa parziale); `_resolve_translated_query` con JSON
  fissi (relazione valida, relazione inventata, entità ambigua, entità assente,
  `intent` mancante/malformato).
- **`translate_query` con `MockTransport`**: risposta JSON valida, risposta non-JSON
  (il modello ha aggiunto prosa attorno), timeout, connessione rifiutata — in ogni
  caso deve ritornare `{"intent": "unresolved"}`, mai propagare l'eccezione.
- **Integrazione sull'endpoint**: `OracleClient.translate_query` mockato (non
  `MockTransport` qui, il confine è il metodo pubblico) per i tre `kind` di
  risposta (`answer`, `disambiguate`, `fallback_search`).
- **Regressione**: nessuna richiesta esistente a `/api/entities/.../relations` o a
  COMMS deve cambiare comportamento — questa feature è additiva.

---

## 7. Rischi

| Rischio | Mitigazione |
| --- | --- |
| Il modello locale configurato (es. `llama3.2`, piccolo) non rispetta in modo affidabile lo schema JSON richiesto | Validazione server-side rigorosa (§4.3) che scarta qualunque campo fuori vocabolario; fallback a ricerca testuale sempre disponibile (§4.5) — mai un errore visibile all'utente, mai un dato inventato spacciato per risposta. |
| L'utente confonde Terminale Archivio e COMMS (due chat nella stessa app) | Etichettatura e navigazione esplicitamente separate (§4.8); nessuna condivisione di storage o di stato tra i due. |
| Il prompt dinamico (§4.2) cresce in token man mano che il vocabolario si espande | Il vocabolario resta piccolo per design esplicito (§8 del documento padre — "nuovo tipo solo quando serve una query concreta"); rischio strutturalmente contenuto, non richiede mitigazione dedicata qui. |
| Introdurre un `find_by_display_name` a sottostringa apre a falsi positivi su archivi grandi (es. "Aran" trova sia `Progetto-Aran` che `Aran-Echo`) | Comportamento intenzionale: è esattamente il caso RF-11.3 (disambiguazione), non un bug — verificato che il flusso di disambiguazione lo gestisce esplicitamente. |

---

## 8. Definition of done

- [ ] `find_by_display_name()` risolve zero/uno/più candidati su nomi parziali,
      case-insensitive, con test puri senza Ollama.
- [ ] `OracleClient.translate_query()` non propaga mai un'eccezione: ogni fallimento
      (rete, timeout, JSON malformato) produce `{"intent": "unresolved"}`.
- [ ] Una relazione inventata dal modello (non in `VOCABULARY`) non viene mai
      eseguita — sempre trattata come `unresolved`.
- [ ] Un'entità ambigua produce una richiesta di disambiguazione, mai una scelta
      silenziosa.
- [ ] Un intento non risolto ripiega su `DirectoryLister.search()`, con
      etichettatura esplicita che distingue il risultato da una risposta
      strutturata.
- [ ] Nuovo slot `neural_query` configurabile dalla UI Settings esistente.
- [ ] Nuova vista "Terminale Archivio" raggiungibile e visivamente distinta da
      COMMS, senza persistenza su disco dei messaggi.
- [ ] Nessuna modifica di comportamento per le query dirette (RF-4/RF-5) o per
      COMMS — criterio di regressione zero.
