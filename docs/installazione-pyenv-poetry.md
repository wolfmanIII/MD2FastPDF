# Protocollo di Installazione: Pyenv & Poetry (Ubuntu 24.04)

## **SC-ARCHIVE // AEGIS CLASS STANDARDS**

Questa guida documenta la procedura completa per configurare un ambiente di sviluppo Python 3.13+ su una macchina Linux fresh, utilizzando `pyenv` per la gestione delle versioni e `poetry` per le dipendenze.

---

## 1. Dipendenze di Build

Prima di compilare Python tramite `pyenv`, installare le librerie di sviluppo necessarie. Senza queste, i moduli `ssl`, `bz2` e `ctypes` non vengono compilati.

```bash
sudo apt update && sudo apt install -y \
    build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev curl \
    git libncursesw5-dev xz-utils tk-dev libxml2-dev \
    libxmlsec1-dev libffi-dev liblzma-dev
```

---

## 2. Installazione Pyenv

```bash
curl https://pyenv.run | bash
```

Aggiungere al `~/.bashrc` (o `~/.zshrc`):

```bash
export PYENV_ROOT="$HOME/.pyenv"
[[ -d $PYENV_ROOT/bin ]] && export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"
```

Ricaricare la shell:

```bash
source ~/.bashrc
```

---

## 3. Installazione Python 3.13

Eseguire dalla directory del progetto (dove si trova `.python-version`):

```bash
pyenv install $(cat .python-version)
pyenv local $(cat .python-version)
```

Verificare:

```bash
python --version   # deve restituire 3.13.x
```

---

## 4. Installazione Poetry

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

Se `~/.local/bin` non è nel PATH, aggiungerlo al `~/.bashrc`:

```bash
export PATH="$HOME/.local/bin:$PATH"
source ~/.bashrc
```

Verificare:

```bash
poetry --version
```

---

## 5. Configurazione e Installazione Dipendenze

Configurare Poetry per creare il virtualenv nella directory del progetto (`.venv/`). Va impostato **prima** di `poetry install`:

```bash
poetry config virtualenvs.in-project true
```

Installare le dipendenze incluse quelle di sviluppo (pytest, pytest-anyio, ecc.):

```bash
poetry install --with dev
```

---

## 6. Tailwind CSS v4 (Standalone CLI)

Il progetto usa il binario standalone Tailwind v4. Scaricarlo nella root del progetto:

```bash
curl -fsSL https://github.com/tailwindlabs/tailwindcss/releases/download/v4.2.2/tailwindcss-linux-x64 \
    -o tailwindcss
chmod +x tailwindcss
```

> Per ARM64 (es. Raspberry Pi): sostituire `tailwindcss-linux-x64` con `tailwindcss-linux-arm64`.

---

## 7. Esecuzione Test Suite

```bash
# Tutti i test
poetry run pytest

# Con report di copertura
poetry run pytest --cov=logic --cov-report=term-missing

# File specifico
poetry run pytest tests/test_comms_async.py -v
```

---

*Designed for the narrators of the SC-ARCHIVE station.*
