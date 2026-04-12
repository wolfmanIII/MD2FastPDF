# Protocollo di Installazione: Pyenv & Poetry (Ubuntu 24.04)

## **SC-ARCHIVE // AEGIS CLASS STANDARDS**

Questa guida documenta la procedura per configurare un ambiente di sviluppo Python 3.13+ isolato utilizzando `pyenv` per la gestione delle versioni e `poetry` per la gestione delle dipendenze e degli ambienti virtuali.

---

## 🛰 1. Dipendenze di Build (Cruciale)

Prima di compilare versioni Python tramite `pyenv`, il sistema deve possedere le librerie di sviluppo fondamentali. Senza queste, i moduli critici come `ssl`, `bz2` e `ctypes` non verranno compilati.

Eseguire questo comando sul terminale:

```bash
sudo apt update && sudo apt install -y \
    build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    git libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev
```

---

## 🛠 2. Installazione Pyenv

Il protocollo raccomandato per l'installazione di `pyenv` è tramite lo script automatico:

1 **Eseguire l'installatore**:

```bash
curl https://pyenv.run | bash
```

2 **Configurare la shell**: Aggiungere queste righe al file `~/.bashrc` (o `~/.zshrc` se usi Zsh):

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

3  **Ricaricare la shell**:
    ```bash
    source ~/.bashrc
    ```

---

## 📦 3. Installazione Poetry

Poetry deve essere installato tramite il suo script di installazione ufficiale per non inquinare il Python di sistema:

1 **Eseguire l'installatore**:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

2 **Aggiungere al PATH**: Assicurarsi che `~/.local/bin` sia nel PATH del proprio sistema.
3 **Test**: Verificare l'installazione con `poetry --version`.

---

## 🔄 4. Workflow Aegis (Sincronizzazione)

Per inizializzare un progetto con Python 3.13 e Poetry:

1 **Installare la versione Python**:
    ```bash
    pyenv install 3.13:latest
    ```
2 **Impostare la versione locale**:
    ```bash
    pyenv local 3.13 (nella cartella del progetto)
    ```
3 **Configurazione In-Project (Consigliata)**: Per mantenere l'ambiente virtuale all'interno del progetto (come Pipenv). Va impostata **prima** di `poetry init` per avere effetto sul virtualenv creato successivamente:
    ```bash
    poetry config virtualenvs.in-project true
    ```
4 **Inizializzare Poetry**:
    ```bash
    poetry init
    ```
5 **Installazione Dipendenze**:
    ```bash
    poetry install
    ```
6 **Installazione Dipendenze di Sviluppo** (include pytest):
    ```bash
    poetry install --with dev
    ```

---

## 🧪 5. Esecuzione Test Suite

Il progetto include una suite pytest con 170 test (unit + async I/O). Richiede le dipendenze dev installate.

```bash
# Tutti i test
poetry run pytest

# Con report copertura
poetry run pytest --cov=logic --cov-report=term-missing

# File specifico
poetry run pytest tests/test_comms_async.py -v
```

---
*Designed for the narrators of the SC-ARCHIVE station.*
