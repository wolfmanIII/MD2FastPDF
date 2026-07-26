# SC-Archive — Relazioni tipizzate nel frontmatter

**Documento di analisi: requisiti + progettazione tecnica**
Versione 1.0 — 24 luglio 2026

---

## 0. Nota per Claude Code

Questo documento descrive **una singola feature**, deliberatamente stretta. Non è un
refactoring dell'applicazione. Se durante l'implementazione emerge la tentazione di
introdurre un database, un ORM o un formato di storage alternativo ai file `.md`,
**la risposta è no** — vedi §3 (Non-obiettivi) e il `MANIFESTO.md` del repo.

Alcune assunzioni sullo stack sono marcate con ⚠️ e vanno verificate nel codice
esistente prima di scrivere qualsiasi cosa.

---

## 1. Contesto

SC-Archive è nato come editor di file Markdown. Nel tempo ha acquisito una vista a
grafo e, più recentemente, funzionalità di **gruppi** e **COMMS**. Con queste ultime
aggiunte la natura del progetto è cambiata: non è più un editor generico di note, ma
uno **strumento di gestione di eventi per GDR sci-fi space opera** (Traveller Mongoose
2nd Edition), presentato diegeticamente come terminale *Library Data* di bordo.

Questo cambio di natura ha una conseguenza architetturale precisa, che è l'oggetto di
questo documento.

### 1.1 Stato attuale

- I contenuti sono file `.md` su filesystem. **Sono la source of truth.**
- I collegamenti tra entità sono espressi come `[[wikilink]]` nel corpo del testo.
- La vista a grafo è costruita estraendo i wikilink dai file.
- Non esiste database. L'indice del grafo è derivato e ricostruibile.

---

## 2. Problema

Un wikilink **non ha un tipo**.

Dato questo file, `Kira Venn.md`:

```markdown
Pilota della [[Beowulf]]. Odia [[Tarn Mekel]].
Ha servito nella [[Marina Imperiale]].
```

un lettore umano ricava tre relazioni semanticamente diverse (mestiere, ostilità,
carriera passata). Il programma ricava **tre archi indistinguibili**: `Kira Venn` è
collegata a tre nodi, senza informazione su *come*. La semantica esiste solo nella
prosa italiana.

### 2.1 Conseguenze concrete

1. **Query strutturate impossibili.** `CREW MANIFEST: BEOWULF` non è implementabile:
   il programma non può distinguere chi fa parte dell'equipaggio da chi ha semplicemente
   *menzionato* la nave in un rapporto.
2. **Vista a grafo poco informativa.** Tutti gli archi sono uguali: nessun colore per
   tipo, nessun filtro ("mostra solo le ostilità"), nessuna distinzione tra relazione
   strutturale e citazione di passaggio.
3. **Nessuna validazione possibile.** Un wikilink verso un file inesistente è
   rilevabile, ma un errore *semantico* (una nave elencata come membro di equipaggio)
   non lo è, perché non esiste un vocabolario contro cui validare.

### 2.2 Causa radice

Il filesystem modella bene i **documenti**. Modella male le **relazioni tra entità**.
SC-Archive ora ha bisogno di entrambe le cose.

---

## 3. Non-obiettivi

Espliciti, e vincolanti:

| Non-obiettivo | Motivo |
| --- | --- |
| Introdurre SQLite o qualsiasi DB | I volumi in gioco (ordine 10²–10⁴ nodi) stanno in memoria. Un DB aggiungerebbe stato duplicato da sincronizzare col filesystem. |
| Sostituire i wikilink nel corpo | Restano validi e utili come *menzioni*. La feature è additiva. |
| Rendere obbligatorio il frontmatter | I file senza frontmatter devono continuare a funzionare esattamente come oggi. |
| Migrare i file esistenti automaticamente | L'adozione è incrementale, file per file, a discrezione dell'utente. |
| Definire un'ontologia completa del setting Traveller | Si parte da 4–5 tipi di relazione. Il vocabolario cresce quando serve. |

**Criterio di regressione zero:** un vault che non contiene nessuna chiave di relazione
nel frontmatter deve comportarsi in modo bit-identico alla versione attuale.

---

## 4. Requisiti funzionali

### 4.1 MVP (Fase 1)

**RF-1 — Dichiarazione di relazioni nel frontmatter**
L'utente può dichiarare relazioni tipizzate nel frontmatter YAML di un file, usando il
nome della chiave come nome della relazione e una lista di riferimenti a entità come
valore.

```markdown
---
type: ship
crew: [Kira Venn, Tarn Mekel]
---

La Beowulf è un mercantile classe Type-A...
```

**RF-2 — Vocabolario di relazioni**
Esiste un vocabolario dichiarato dei tipi di relazione ammessi. Una chiave di frontmatter
è interpretata come relazione **solo se** presente nel vocabolario; qualsiasi altra chiave
è ignorata (retrocompatibilità con frontmatter già in uso).

**RF-3 — Indice in memoria**
All'avvio l'applicazione costruisce un indice delle entità e delle relazioni leggendo i
frontmatter. L'indice è interamente derivato: cancellabile e ricostruibile senza perdita.

**RF-4 — Query dirette**
Data un'entità e un tipo di relazione, il sistema restituisce le entità collegate.
Caso d'uso di riferimento: `crew_of(Beowulf) → [Kira Venn, Tarn Mekel]`.

**RF-5 — Query inverse**
Le relazioni sono navigabili in entrambe le direzioni. Se `Beowulf` dichiara
`crew: [Kira Venn]`, il sistema può rispondere anche a "su quali navi vola Kira Venn"
senza che Kira dichiari nulla.

**RF-6 — Reindex incrementale**
Alla modifica di un file, solo quel file viene riparsato. Nessun rescan completo del
vault a ogni salvataggio.

**RF-7 — Riferimenti non risolti**
Un riferimento a un'entità inesistente non è un errore fatale: viene registrato come
*dangling* ed è esposto all'utente in un report diagnostico.

### 4.2 Fase 2 (dopo validazione dell'MVP)

**RF-8 — Archi tipizzati nella vista a grafo**
Colore/stile per tipo di relazione; filtro per tipo; i wikilink del corpo sono resi come
archi debolmente marcati e distinguibili dalle relazioni strutturali.

**RF-9 — Validazione di dominio**
Il vocabolario dichiara i tipi di entità ammessi ai due estremi di ogni relazione
(es. `crew` va da `ship` a `npc`). Le violazioni sono segnalate nel report diagnostico.

**RF-10 — Identificatori stabili**
Campo `id:` opzionale nel frontmatter, per disaccoppiare l'identità dell'entità dal nome
del file. Da introdurre **quando** i rinomini iniziano a rompere i riferimenti, non prima.

### 4.3 Fase 3 (esplorativa)

**RF-11 — Query in linguaggio naturale via Ollama**
L'istanza Ollama locale traduce una richiesta in linguaggio naturale in una query
strutturata sull'indice. Diegeticamente coerente col terminale Library Data. Nessuna
progettazione prevista in questo documento.

---

## 5. Progettazione tecnica

### 5.1 Assunzioni da verificare ⚠️

- Stack Python asincrono con FastAPI.
- Presenza di `PathSanitizer` con isolamento per-richiesta via `ContextVar`: **ogni
  accesso al filesystem introdotto da questa feature deve passare da lì.**
- Dependency Inversion basata su `Protocol` (SOLID): i componenti nuovi seguono la stessa
  convenzione.
- Parsing del frontmatter: verificare se esiste già un parser nel repo. Se sì, riusarlo.
  Se no, `python-frontmatter` oppure `yaml.safe_load` sul blocco delimitato da `---`.
- Sanitizzazione XSS via Bleach prima del rendering: **i valori delle relazioni sono
  input utente e vanno trattati come tali** quando finiscono in output HTML.

### 5.2 Vocabolario delle relazioni

Definito in un unico punto, dichiarativo, non sparso nel codice.

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class RelationDef:
    name: str                              # chiave nel frontmatter
    inverse: str                            # nome della relazione inversa (per RF-5)
    label: str                              # etichetta leggibile diretta, per la UI
    inverse_label: str                      # etichetta leggibile inversa, per la UI
    domain: tuple[str, ...] | None = None   # tipi di entità ammessi alla sorgente (RF-9). None = non vincolato.
    range: tuple[str, ...] | None = None    # tipi di entità ammessi alla destinazione (RF-9). None = non vincolato.

VOCABULARY: tuple[RelationDef, ...] = (
    RelationDef("crew",          inverse="serves_on",       label="Equipaggio",    inverse_label="Equipaggio di",
                domain=("ship",), range=("npc",)),
    RelationDef("member_of",     inverse="has_member",       label="Membro di",     inverse_label="Membri",
                domain=("npc", "organization"), range=("organization",)),
    # non vincolata: troppo generica per limitarla ai soli tipi visti finora —
    # copre anche il caso scena→luogo ("dove si svolge la scena"), non ancora
    # osservato nei dati reali ma già esprimibile senza modifiche al codice.
    RelationDef("located_in",    inverse="contains",         label="Situato in",    inverse_label="Contiene"),
    RelationDef("hostile_to",    inverse="hostile_to",       label="Ostile a",      inverse_label="Ostile a",  # simmetrica
                domain=("npc",), range=("npc",)),
    RelationDef("owns",          inverse="owned_by",         label="Possiede",      inverse_label="Posseduto da",
                domain=("npc",), range=("ship", "location", "drone", "item")),
    # Aggiunte dopo analisi del materiale di campagna reale (Protocollo_SIGMA),
    # non teoriche — ricorrono più volte nelle schede NPC.
    RelationDef("owes_debt_to",  inverse="creditor_of",      label="Debitore di",   inverse_label="Creditore di",
                domain=("npc", "organization"), range=("npc", "organization")),
    RelationDef("reports_to",    inverse="has_subordinate",  label="Risponde a",    inverse_label="Subordinati",
                domain=("npc",), range=("npc",)),
    RelationDef("allied_with",   inverse="allied_with",      label="Alleato di",    inverse_label="Alleato di",  # simmetrica
                domain=("npc",), range=("npc",)),
    RelationDef("mentor_of",     inverse="student_of",       label="Mentore di",    inverse_label="Allievo di",
                domain=("npc",), range=("npc",)),
    # Grounded in un archivio reale di scene (Protocollo_SIGMA/Scene/, 34 file).
    RelationDef("npcs",          inverse="scenes",           label="NPC coinvolti", inverse_label="Scene",
                domain=("scene",), range=("npc",)),
    # inverse="scenes_org", non "scenes": VOCABULARY_BY_INVERSE è una mappa
    # 1:1 e "scenes" è già l'inverso di npcs — l'etichetta visibile resta
    # "Scene" in entrambi i casi, solo il nome interno di query è distinto.
    RelationDef("organizations", inverse="scenes_org",       label="Organizzazioni coinvolte", inverse_label="Scene",
                domain=("scene",), range=("organization",)),
)
```

Note:

- Una relazione **simmetrica** ha `inverse == name` (es. `hostile_to`). Il codice deve
  gestire il caso senza duplicare l'arco.
- I nomi inversi non sono chiavi valide di frontmatter: sono nomi di query. Solo i `name`
  sono riconosciuti in lettura.
- `domain`/`range` sono popolati (RF-9, Fase 2, issue #8) — derivati dall'uso reale
  osservato nell'archivio, non progettati a tavolino. Una relazione può restare
  volutamente senza vincoli (es. `located_in`) quando è troppo generica per limitarla
  ai soli tipi visti finora. Un tipo mancante sull'entità (frontmatter senza `type:`)
  non è mai trattato come violazione — solo un conflitto reale tra due tipi noti lo è.
- Non ogni nuovo caso d'uso richiede una nuova chiave in `VOCABULARY`: `located_in`,
  essendo non vincolata, copre già "una scena è ambientata in un luogo" (`located_in:
  Porozlo` su un file di scena) senza modifiche al codice — è un uso *documentato*,
  non ancora osservato nei dati reali, quindi non è stato aggiunto come voce separata
  (coerente con il criterio del §8: nuovo tipo solo quando la vocabolario esistente
  non basta già a rispondere alla domanda).

### 5.3 Modello dell'indice

```python
@dataclass
class Entity:
    key: str               # identificatore canonico normalizzato
    display_name: str      # nome originale, per la UI
    path: Path
    entity_type: str | None   # dal campo `type:` del frontmatter, se presente
    mtime: float

@dataclass
class Edge:
    source: str            # Entity.key
    target: str            # Entity.key
    relation: str          # RelationDef.name
    origin_path: Path      # file in cui la relazione è dichiarata
```

Strutture di lookup mantenute in memoria:

```text
entities:    dict[str, Entity]
out_edges:   dict[tuple[str, str], list[str]]   # (source_key, relation) -> [target_key]
in_edges:    dict[tuple[str, str], list[str]]   # (target_key, relation) -> [source_key]
by_path:     dict[Path, list[Edge]]             # per invalidazione incrementale
dangling:    list[tuple[Path, str, str]]        # (file, relation, riferimento non risolto)
```

`in_edges` è ciò che rende RF-5 gratuito: nessuna scansione, solo un secondo dizionario
popolato durante lo stesso passaggio.

### 5.4 Risoluzione delle entità

Il riferimento `Kira Venn` deve risolvere a `Kira Venn.md`. In Fase 1:

1. Chiave canonica = `casefold()` dello stem del nome file, con spazi normalizzati.
2. Un riferimento è risolto cercando la sua chiave canonica in `entities`.
3. Se non trovato → `dangling` (RF-7), **non** eccezione.
4. Sono accettate entrambe le forme `[[Kira Venn]]` e `Kira Venn` nei valori di relazione:
   le doppie parentesi vengono strippate prima della normalizzazione.

Collisioni (due file con lo stesso stem in cartelle diverse): in Fase 1 vince il primo
incontrato e la collisione è registrata nel report diagnostico. La soluzione definitiva
è RF-10.

### 5.5 Parsing e costruzione

```python
class RelationParser(Protocol):
    def parse(self, path: Path, frontmatter: dict) -> list[Edge]: ...
```

Algoritmo, per file:

1. Estrai il frontmatter. Se assente o non è un mapping → nessun arco, nessun errore.
2. Per ogni `RelationDef` nel vocabolario, verifica la presenza della chiave `name`.
3. Normalizza il valore: uno scalare è trattato come lista di un elemento; una lista è
   usata così com'è; qualsiasi altro tipo è ignorato e registrato come warning.
4. Per ogni elemento, strippa i wikilink, normalizza, produci un `Edge`.
5. La risoluzione dei target avviene **dopo** che tutte le entità sono note (secondo
   passaggio), perché un file può referenziare un'entità non ancora letta.

Quindi: **due passaggi**. Primo passaggio popola `entities`, secondo passaggio risolve
gli archi. Su volumi di questo ordine il costo è irrilevante.

### 5.6 Reindex incrementale (RF-6)

```python
async def reindex_file(self, path: Path) -> None:
    """Invalida e ricostruisce gli archi originati da un singolo file."""
```

1. Rimuovi tutti gli `Edge` con `origin_path == path`, usando `by_path` per trovarli
   senza scansioni.
2. Riparsa il file e reinserisci gli archi.
3. Se il file è stato cancellato: rimuovi anche l'entità e ricalcola come *dangling*
   tutti gli archi che la puntavano.

`mtime` in `Entity` serve al reindex completo di avvio, per saltare file non modificati
se in futuro si introduce una cache su disco. **In Fase 1 non serve cache su disco**: il
rescan completo di qualche migliaio di file all'avvio è nell'ordine dei millisecondi.

### 5.7 Interfaccia di query

```python
class GraphIndex(Protocol):
    def related(self, entity: str, relation: str) -> list[Entity]:
        """Segue una relazione in avanti o all'indietro (accetta name o inverse)."""

    def relations_of(self, entity: str) -> dict[str, list[Entity]]:
        """Tutte le relazioni di un'entità, per la scheda e per il grafo."""

    def diagnostics(self) -> Diagnostics:
        """Riferimenti non risolti, collisioni di chiave, warning di parsing."""
```

`related` risolve il nome ricevuto contro `VOCABULARY`: se corrisponde a un `name`
consulta `out_edges`, se corrisponde a un `inverse` consulta `in_edges`. Questo è l'unico
punto in cui la direzione conta.

### 5.8 Endpoint HTTP

Da allineare alle convenzioni di routing già presenti nel repo ⚠️.

| Metodo | Path | Scopo |
| --- | --- | --- |
| `GET` | `/api/entities/{key}/relations` | RF-4, RF-5 — tutte le relazioni di un'entità |
| `GET` | `/api/entities/{key}/relations/{relation}` | RF-4 — una relazione specifica |
| `GET` | `/api/graph` | dati per la vista a grafo, archi tipizzati |
| `GET` | `/api/diagnostics/relations` | RF-7 — report dei riferimenti non risolti |
| `POST` | `/api/index/reindex` | reindex completo su richiesta |

Il caso d'uso `CREW MANIFEST: BEOWULF` è servito da
`GET /api/entities/beowulf/relations/crew`.

### 5.9 `type:` non è un'ontologia chiusa

`entity_type` (il valore del campo `type:` in frontmatter) è una **stringa libera**,
non un enum. Il codice non mantiene nessuna lista di valori ammessi:

```python
entity_type = frontmatter.get("type") if frontmatter else None
if not isinstance(entity_type, str):
    entity_type = None
```

Qualunque stringa passa. Il confronto con `domain`/`range` (RF-9) avviene solo
`casefold()`-normalizzato contro le tuple dichiarate nel `VOCABULARY`, mai contro
un registro globale di "tipi validi" — non esiste un simile registro.

**Conseguenza pratica:** classificare un nuovo genere di contenuto (un progetto di
ricerca, un'intelligenza artificiale, la partizione criptata di una nave, un
oggetto/artefatto) **non richiede quasi mai una nuova voce in `VOCABULARY`**. Bastano
due cose, entrambe a costo zero di codice:

1. Un valore di `type:` adatto — riusando uno esistente (`organization` per un
   progetto/fazione come *Progetto Helix*, `item` per un oggetto come un cristallo)
   oppure inventandone uno nuovo (`ai` per un'intelligenza artificiale come *IUNO*:
   già in uso in 4 file dell'archivio reale, senza che sia mai stato dichiarato da
   nessuna parte nel codice — funziona perché non serve dichiararlo).
2. Le relazioni **già esistenti** per collegarlo (`member_of`, `owns`, `located_in` —
   quest'ultima non vincolata, quindi utilizzabile subito con qualsiasi tipo, noto o
   nuovo che sia).

Una nuova voce in `VOCABULARY` serve solo quando emerge una **query strutturale
concreta** che le chiavi esistenti non possono già esprimere (criterio del rischio
in §8) — non per il solo fatto di introdurre un nuovo genere di entità.

**Le violazioni di dominio restano sempre diagnostiche, mai bloccanti.** Un tipo
nuovo o inatteso su un lato di una relazione vincolata (es. `owns`, il cui `range`
è `("ship", "location", "drone", "item")`) può produrre una `DomainViolation` se
usato contro quella relazione — ma è solo una riga in più nel report di
`/api/diagnostics/relations`, mai un errore, mai un salvataggio bloccato. Verificato
sull'archivio reale: le 4 entità `type: ai` esistenti (`IUNO`, `Daedalus`,
`Aran-Echo`, `Custode-01`) generano oggi **zero violazioni** — l'unico arco che le
coinvolge è `Custode-01 --located_in--> Luna-Octavia`, e `located_in` non è
vincolata. Se in futuro comparisse ad esempio `owns: [IUNO]` su un NPC, verrebbe
segnalata una violazione (perché `"ai"` non è nella tupla `range` di `owns`) — a
quel punto, e solo a quel punto, varrebbe la pena valutare se estendere `owns.range`.

---

## 6. Piano di implementazione

Ordine consigliato, ogni step verificabile in isolamento:

1. `VOCABULARY` + `RelationDef`. Nessuna dipendenza, test puri.
2. Normalizzazione delle chiavi e stripping dei wikilink. Funzioni pure, molti casi limite.
3. Parsing frontmatter → `list[Edge]` per un singolo file, con target non ancora risolti.
4. Costruzione dell'indice a due passaggi + risoluzione + `dangling`.
5. `related` / `relations_of` / `diagnostics`.
6. `reindex_file` e integrazione con l'evento di salvataggio esistente ⚠️.
7. Endpoint HTTP.
8. Esposizione nella UI: sezione relazioni nella scheda dell'entità.
9. **Solo dopo che 1–8 sono in produzione e usati in una sessione reale:** RF-8 (grafo
   tipizzato).

Gli step 1–5 non toccano nulla di esistente e sono l'80% del valore.

---

## 7. Strategia di test

Coerente con la copertura già presente nel repo (170+ test asincroni) ⚠️.

### **Unitari**

- Normalizzazione: maiuscole, spazi multipli, accenti, `[[wikilink]]`, stringa vuota.
- Frontmatter assente, malformato, non-mapping, chiave con valore scalare, valore `null`,
  lista vuota, lista con elementi non-stringa.
- Chiavi di frontmatter fuori vocabolario: devono essere ignorate silenziosamente.
- Relazione simmetrica: nessun arco duplicato.

### **Integrazione**

- Vault di fixture con 3–4 entità e relazioni note → asserzioni su `related` in entrambe
  le direzioni.
- Riferimento dangling → presente in `diagnostics`, assente da `related`, nessuna
  eccezione propagata.
- Reindex dopo modifica: gli archi vecchi del file scompaiono, i nuovi appaiono, gli archi
  degli *altri* file restano intatti.
- Cancellazione di un file target: gli archi entranti diventano dangling.

### **Regressione (critico, vedi §3)**

- Vault senza nessuna chiave di relazione → output identico alla versione precedente.

### **Sicurezza**

- Valore di relazione contenente path traversal (`../../etc/passwd`): deve essere trattato
  come riferimento non risolto, mai come path. Verificare che passi da `PathSanitizer`.
- Valore contenente markup HTML: sanitizzato prima di finire in una risposta renderizzata.

---

## 8. Rischi

| Rischio | Mitigazione |
| --- | --- |
| Il vocabolario cresce a dismisura e diventa un'ontologia ingestibile | Nuovo tipo di relazione solo quando esiste una query concreta che lo richiede. |
| L'utente dichiara le relazioni nel frontmatter *e* le ripete nel corpo, con divergenze | Nessuna: sono due piani diversi (dati vs prosa). Documentare che il frontmatter è autoritativo per le query, il corpo per la lettura. |
| Duplicazione di informazione tra file (`crew` su nave e `serves_on` su PNG) | Convenzione: ogni relazione è dichiarata da **un solo lato**. L'inverso si ottiene via `in_edges`, non riscrivendolo. Segnalare i doppioni in `diagnostics`. |
| Feature creep verso un DB | §3 è vincolante. |

---

## 9. Definition of done (Fase 1)

- [ ] Un file `.md` con `crew: [...]` nel frontmatter produce archi tipizzati nell'indice.
- [ ] `GET /api/entities/beowulf/relations/crew` restituisce l'equipaggio.
- [ ] La query inversa funziona senza dichiarazioni aggiuntive.
- [ ] Un riferimento inesistente non rompe niente e appare in `/api/diagnostics/relations`.
- [ ] Modificare un file aggiorna solo i suoi archi.
- [ ] Un vault privo di relazioni si comporta esattamente come prima.
- [ ] Nessuna nuova dipendenza di storage. Nessun file di database nel repo.
