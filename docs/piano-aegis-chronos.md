# AEGIS CHRONOS // Piano di Implementazione
**Fase [4.3] — Versionamento Visivo per Archivi Narrativi**

---

## Obiettivo

Fornire uno strato di versionamento leggero e non invasivo per i documenti SC-ARCHIVE, pensato per scenari RPG e scrittura narrativa. L'utente deve poter recuperare contenuto eliminato, confrontare versioni e salvare snapshot senza mai uscire dall'interfaccia o rischiare di corrompere il repo.

Il modulo è **opt-in**: attivo solo se la cartella root selezionata tramite `SET_ARCHIVE` contiene già un repo Git inizializzato. Non crea mai repo, non opera mai sull'indice globale, non esegue mai operazioni distruttive.

Le operazioni verso remoti (pull/push) sono supportate in modalità **safe-only**: nessun merge automatico, nessuna gestione conflitti in-app, nessun force push. Se un'operazione remota non è fast-forward o viene rifiutata dal server, il modulo segnala l'errore e rimanda esplicitamente al terminale.

---

## Requisiti Funzionali

### RF-01 — Detect automatico
- Al cambio di root (SET_ARCHIVE) e all'avvio, eseguire `git -C <root> rev-parse --git-dir`.
- Se il comando fallisce → modulo in stato `GIT_REPO_NOT_DETECTED`.
- Se ha successo → modulo attivo, branch corrente rilevato.

### RF-02 — Stato GIT_REPO_NOT_DETECTED
- Il pannello Chronos è **visibile ma disabilitato** con messaggio di stato e istruzioni per inizializzare il repo:
  ```bash
  git init && git add . && git commit -m "init: archivio SC-ARCHIVE"
  ```
- Bottone `INIT_REPO` che esegue il comando sopra tramite subprocess e ricarica il modulo.

### RF-03 — Snapshot manuale
- Bottone `COMMIT_SNAPSHOT` nell'editor (toolbar EasyMDE) e nel pannello Chronos.
- Esegue: `git add <file_corrente> && git commit -m "snapshot: <nome_file> // <timestamp>"`.
- Opera **solo sul file aperto**, mai su `git add .`.
- Feedback visivo inline (successo / errore).

### RF-04 — Auto-snapshot
- Configurabile dal pannello Uplink Config (toggle on/off + intervallo: ogni N salvataggi oppure ogni X minuti).
- Messaggio commit automatico: `"auto-snapshot: <nome_file> // <timestamp>"`.
- Disabilitato di default.

### RF-05 — File history
- Pannello laterale o sezione nell'editor che mostra `git log --oneline -- <file>`.
- Ogni riga: hash corto + messaggio commit + data relativa.
- Click su una riga → apre il diff viewer (RF-06).

### RF-06 — Diff viewer (due colonne)
- Modal wide (1200px) con layout affiancato: **sinistra** = versione storica, **destra** = versione corrente.
- Righe eliminate evidenziate in rosso tenue, righe aggiunte in verde tenue (palette adattata al tema dark).
- Entrambe le colonne sono in sola lettura tranne il bottone inject (RF-07).

### RF-07 — Inject nel buffer
- Nella colonna sinistra (versione storica), ogni paragrafo/blocco ha un bottone `INJECT >>`.
- Il click appende il blocco selezionato in fondo al buffer dell'editor corrente.
- Nessuna sostituzione automatica: l'utente decide dove posizionarlo dopo l'inject.

### RF-08 — Branch indicator
- Header dell'editor e pannello Chronos mostrano il branch corrente (es. `campagna-ravenloft`).
- Nessuna gestione branch dall'interfaccia: solo visualizzazione.

### RF-09 — Pull (safe)
- Esegue `git pull --ff-only` sul branch corrente.
- Se il pull è fast-forward → successo, feedback inline.
- Se non è fast-forward (divergenza) → operazione rifiutata con messaggio: `DIVERGED — risolvi da terminale`.
- Nessun fetch separato, nessun merge automatico.

### RF-10 — Push (safe)
- Esegue `git push origin <branch>` (mai `--force`).
- Se il remote ha commit in più → push rifiutato con messaggio: `REMOTE_AHEAD — esegui pull prima`.
- Se non è configurato alcun remote → messaggio: `NO_REMOTE_CONFIGURED`.
- Credenziali gestite esclusivamente dall'agente SSH/credential helper del sistema operativo — l'app non gestisce né memorizza credenziali.

---

## Requisiti Non Funzionali

- **Sicurezza repo**: nessuna operazione distruttiva (`reset`, `checkout .`, `clean`), nessun merge/rebase, mai `--force`.
- **Pull safe**: solo `--ff-only` — se la storia è divergente, l'operazione viene rifiutata.
- **Push safe**: solo push standard — se il remote è ahead, l'operazione viene rifiutata.
- **Credenziali**: delegate interamente all'agente SSH o al credential helper del SO — l'app non vede né memorizza token o password.
- **Scope file**: snapshot e log operano esclusivamente sul file correntemente aperto, mai su `git add .`.
- **Subprocess async**: tutte le chiamate Git tramite `asyncio.create_subprocess_exec` (no `shell=True`).
- **Graceful degradation**: se il repo diventa inaccessibile mid-session, il modulo torna silenziosamente a `GIT_REPO_NOT_DETECTED`.

---

## Architettura

### Backend

**`logic/chronos.py`** — Core Git interface
```
ChronosClient
├── detect_repo(root: Path) -> bool
├── current_branch(root: Path) -> str
├── remote_name(root: Path) -> str | None
├── file_log(root: Path, file: Path) -> list[CommitEntry]
├── file_snapshot(root: Path, file: Path, hash: str) -> str
├── file_diff(root: Path, file: Path, hash: str) -> DiffResult
├── commit_snapshot(root: Path, file: Path, message: str) -> None
├── pull_ff_only(root: Path) -> PullResult
├── push_safe(root: Path) -> PushResult
└── init_repo(root: Path) -> None
```

**`routes/chronos.py`** — APIRouter (`/chronos`)
```
GET  /chronos/status           → stato repo + branch + remote (HTMX fragment)
GET  /chronos/log?path=        → lista commit per file
GET  /chronos/diff?path=&hash= → diff viewer fragment
POST /chronos/snapshot?path=   → commit snapshot manuale
POST /chronos/pull             → git pull --ff-only
POST /chronos/push             → git push safe
POST /chronos/init             → git init + primo commit
```

### Frontend

**`templates/components/chronos_status.html`** — Badge branch nell'header editor
**`templates/components/chronos_log.html`** — Lista commit (pannello laterale editor)
**`templates/components/chronos_diff_modal.html`** — Modal diff due colonne con inject
**`templates/components/chronos_init.html`** — Stato GIT_REPO_NOT_DETECTED con bottone INIT

### Config (Uplink Config)

Nuovi campi in `config.json`:
```json
{
  "chronos_enabled": true,
  "chronos_auto_snapshot": false,
  "chronos_auto_interval_saves": 5,
  "chronos_auto_interval_minutes": 0
}
```

---

## Fasi di Sviluppo

| Step | Descrizione | Dipendenze |
|------|-------------|-----------|
| 1 | `logic/chronos.py` — detect, branch, log, snapshot | — |
| 2 | `routes/chronos.py` — status + snapshot endpoints | Step 1 |
| 3 | Badge branch nell'editor + bottone COMMIT_SNAPSHOT toolbar | Step 2 |
| 4 | Pannello log file (lista commit) | Step 2 |
| 5 | Diff viewer modal due colonne | Step 4 |
| 6 | Inject nel buffer dal diff viewer | Step 5 |
| 7 | Auto-snapshot + Uplink Config integration | Step 3 |
| 8 | Pull safe + Push safe + indicatore remote nel pannello | Step 2 |
| 9 | Stato GIT_REPO_NOT_DETECTED + INIT_REPO | Step 1 |

---

## Vincoli e Limiti Espliciti

- **Mai `--force`**: nessun push forzato in nessuna circostanza.
- **Nessun merge/rebase**: se pull non è fast-forward → rifiuto con messaggio esplicito.
- **Credenziali delegate al SO**: l'app non gestisce token, password o chiavi SSH.
- **Nessuna gestione branch**: solo lettura del branch corrente, nessun checkout o creazione.
- **Solo file singolo per snapshot/log**: mai `git add .` o operazioni multi-file.
- **No `shell=True`**: prevenzione command injection su path file.
- **Init opzionale**: se l'utente non inizializza il repo, il modulo resta in standby senza bloccare il workflow.
- **Conflitti → terminale**: qualsiasi scenario non risolvibile in modo sicuro automaticamente viene segnalato con istruzioni per la risoluzione manuale da terminale.
