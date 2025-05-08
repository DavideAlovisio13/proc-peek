# proc-peek

**proc-peek** è un monitor di processi interattivo cross-platform (TUI) costruito con Python, Rich e Textual. Funziona su Windows, macOS e Linux.

![Screenshot di proc-peek](https://via.placeholder.com/800x450.png?text=proc-peek+Screenshot)

## Caratteristiche

- 🖥️ **Interfaccia TUI** - Interfaccia utente testuale interattiva facile da usare
- 🚀 **Leggero** - Basso consumo di risorse del sistema
- 🔄 **Aggiornamenti in tempo reale** - Monitoraggio continuo delle prestazioni del sistema
- 🔍 **Dettagli dei processi** - Visualizzazione dettagliata delle informazioni sui processi
- ⚡ **Sorting flessibile** - Ordina processi per CPU, memoria, nome o PID
- 🌐 **Cross-platform** - Funziona su Windows, macOS e Linux

## Installazione

### Utilizzando pip

```bash
pip install proc-peek
```

### Dalla fonte

```bash
git clone https://github.com/tuousername/proc-peek.git
cd proc-peek
pip install poetry  # se non lo hai già installato
poetry install
```

## Utilizzo

### Interfaccia TUI

Per avviare l'interfaccia TUI interattiva:

```bash
proc-peek
```

Comandi nell'interfaccia:

- `q` - Esci dall'applicazione
- `?` - Mostra la guida
- Usa i tasti freccia per navigare tra i processi
- Premi `Enter` per selezionare un processo e visualizzarne i dettagli

### Modalità CLI

Per elencare i processi in modalità non interattiva:

```bash
proc-peek list
```

Opzioni:

- `--sort`, `-s` - Ordina per: cpu, memory, name, pid (default: cpu)
- `--count`, `-n` - Numero di processi da mostrare (default: 10)

Esempio:

```bash
proc-peek list --sort memory --count 15
```

## Requisiti

- Python 3.9 o superiore
- Librerie:
  - psutil
  - rich
  - textual
  - typer
  - colorama (per il supporto dei colori sui terminali Windows)

## Sviluppo

### Configurazione dell'ambiente di sviluppo

```bash
git clone https://github.com/tuousername/proc-peek.git
cd proc-peek
pip install poetry
poetry install
```

### Esecuzione dei test

```bash
poetry run pytest
```

### Analisi del codice

```bash
poetry run black proc_peek
poetry run ruff check proc_peek
poetry run mypy proc_peek
```

## Licenza

Questo progetto è distribuito con licenza MIT. Vedi il file LICENSE per maggiori dettagli.

---

Realizzato con ❤️ in Python. Contribuisci al progetto su GitHub!
