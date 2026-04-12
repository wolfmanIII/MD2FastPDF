# Guida alla rimozione di Ruflo (ex Claude-Flow)

> Ruflo è un framework di orchestrazione di agenti AI che si integra con Claude Code.
> La rimozione richiede più passaggi perché lascia diversi artefatti nel sistema.

---

## Passo 1 — Cleanup ufficiale (v3.5.40+)

A partire dalla versione 3.5.40, Ruflo include un comando di cleanup ufficiale.

```bash
# Prima esegui in modalità dry-run (mostra cosa verrà rimosso, senza cancellare)
npx ruflo@latest cleanup

# Poi esegui la rimozione effettiva
npx ruflo@latest cleanup --force
```

---

## Passo 2 — Disinstalla i pacchetti npm globali

```bash
npm uninstall -g claude-flow ruflo @claude-flow/cli
npm cache clean --force
```

---

## Passo 3 — Rimuovi la cache npx

```bash
rm -rf ~/.npm/_npx
```

---

## Passo 4 — Rimuovi gli artefatti lasciati nei progetti

Esegui questi comandi nella cartella di ogni progetto in cui avevi inizializzato Ruflo:

```bash
rm -rf .swarm/
rm -rf .hive-mind/
rm -rf memory/
rm -rf coordination/
rm -f claude-flow.config.json
rm -f .mcp.json
rm -f CLAUDE.md
```

---

## Passo 5 — Pulisci la configurazione di Claude Code

Apri e modifica i seguenti file rimuovendo ogni riferimento a `ruflo`, `claude-flow` o agli hook MCP aggiunti da Ruflo:

- **Configurazione globale:** `~/.claude/settings.json`
- **Configurazione locale del progetto:** `.claude/settings.json` (nella cartella del progetto)

In particolare, cerca e rimuovi eventuali voci sotto `hooks` (es. `PreToolUse`) e riferimenti a server MCP di Ruflo.

---

## Passo 6 — Verifica finale

Controlla che non rimangano tracce:

```bash
# Verifica che il comando non sia più disponibile
which claude-flow
which ruflo

# Cerca cartelle .swarm residue nel progetto corrente
find . -name ".swarm" -type d
find . -name ".hive-mind" -type d
```

Se i comandi non vengono trovati e le cartelle non esistono, la rimozione è completa.

---

## ⚠️ Problema noto: cartelle che si rigenerano

Alcuni utenti hanno segnalato che le cartelle `.swarm` e `.hive-mind` continuano a rigenerarsi anche dopo la disinstallazione. Questo accade quando sono ancora presenti **hook `PreToolUse`** nella configurazione di Claude Code.

**Soluzione:** controlla entrambi i file `settings.json` (globale e locale) e rimuovi manualmente tutti gli hook registrati da Ruflo.

---

## Note per Windows

Su Windows, sostituisci i comandi `rm -rf` con:

```powershell
Remove-Item -Recurse -Force .swarm
Remove-Item -Recurse -Force .hive-mind
Remove-Item -Recurse -Force memory
Remove-Item -Recurse -Force coordination
Remove-Item -Force claude-flow.config.json
Remove-Item -Force .mcp.json
Remove-Item -Force CLAUDE.md
```

---

*Riferimento: [ruvnet/ruflo su GitHub](https://github.com/ruvnet/ruflo)*
