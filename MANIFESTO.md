# MANIFESTO // SC-ARCHIVE

> *Italiano sotto. — English below.*

---

## 🇬🇧 ENGLISH

### // SHIP'S LIBRARY DATA — ACCESS GRANTED

```text
> CONNECTING TO SHIPBOARD ARCHIVE...
> AEGIS CLASS DOCUMENTATION CORE ONLINE
> OPERATOR AUTHENTICATED
> READ ACCESS: ALL CREW
> WRITE ACCESS: SECTOR-RESTRICTED
```

Every starship carries a memory.

Below the deck plating, between the jump drive and the life support, sits the
computer core — and on it, the *Library Data*. Planetary surveys. Xenobiology
files. Cargo manifests. Mission logs scrawled by an officer at 0300 ship-time
during a long burn. The crew doesn't "open an app" to read it. They query the
ship. The ship answers.

**SC-ARCHIVE is that computer, made real.**

It is the Library Data console of an *Aegis Class* vessel — a place where the
crew consults the high-level archive (read-only, available to all hands) and
where each officer maintains their own working records in their assigned
sector. The Captain and the ship's officers update the logs; the crew reads
them. The hierarchy isn't a setting buried in a menu. It *is* the architecture.

This is not a documentation tool dressed up as a spaceship. It is a spaceship's
documentation core that happens to run on a Raspberry Pi.

---

### // WHY IT IS BUILT THE WAY IT IS

This project has been criticized for one recurring reason: *"it uses the
filesystem, there's no database."*

That criticism mistakes the genre.

The central data of SC-ARCHIVE is **Markdown documents** — text files,
organized as a tree of directories, written and read and browsed and converted
to PDF. The data *is already a file by its very nature.* Putting that into a
relational database would mean reinventing a filesystem inside the database —
worse than the filesystem, and losing everything the filesystem gives for free:
documents you can open in any editor, put under `git`, `grep`, copy with
`rsync`.

But there is a deeper reason, and it is narrative.

A starship's Library Data **is** a hierarchical archive of technical files — not
a relational structure with foreign keys and joins. When a character "navigates
the Library," they navigate folders. The technical choice and the fiction
coincide. A database behind the scenes would be *less* faithful, not more: it
would impose a relational structure that does not exist in the fiction.

The same logic runs through the permission model. Each operator lives in their
own subtree (`~/sc-archive/<username>/`); shared sectors are group-writable; the
high archive is read-only to all. This is not a security afterthought — it is
the **operational protocol of a ship's crew**, modeled directly onto the
permissions of the operating system. We lean on the guarantees the OS already
provides instead of reimplementing them badly.

Even the neural layer is diegetic. The Oracle (local Ollama, `qwen2.5-coder`)
is the ship's computer *answering you* — ghost-text suggestions as you write a
report, the way a real shipboard AI would assist an officer drafting a log. It
runs **locally, offline, on isolated hardware** — because there is no internet
on a starship, and because the whole station should boot and breathe on a single
machine on a closed LAN, exactly like the sealed computer core of a real vessel.

---

### // SCOPE & HONESTY

SC-ARCHIVE is designed for a crew of **50–100 operators** on local hardware. It
is not built to scale to ten thousand users across twenty datacenters, and it
does not pretend to be. Within its intended scope, the filesystem-first design
is not a shortcut — it is the *correct* engineering choice for the domain.

There is exactly one place where "no database" begins to show tension, and we
name it openly rather than hide it: **COMMS**, the inter-crew messaging layer.
Messages, read/unread state, drafts, group filtering — these carry genuine
relational structure. At the intended scale the filesystem handles it cleanly;
at a much larger scale this is the component that would feel strain first. Not
the document storage. COMMS. We know where the seam is.

Concurrent writes to the shared registries (`users.json`, `groups.json`) are
guarded so that two simultaneous saves cannot clobber one another. Small care,
correctly placed.

---

### // FOR WHOM THIS WAS MADE

If you are a backend engineer looking for a CRUD app with a Postgres instance,
this project will confuse you, and you will grade it by the wrong rubric.

If you are a Traveller Referee, and you have ever described your players sitting
at a terminal querying the ship's Library Data — you already understand exactly
what this is, and why every choice was made the way it was made.

This was built for the storytellers of the station.

```text
> END OF FILE
> ARCHIVE REMAINS ONLINE
```

---
---

## 🇮🇹 ITALIANO

### // LIBRARY DATA DI BORDO — ACCESSO CONCESSO

```text
> CONNESSIONE ALL'ARCHIVIO DI BORDO...
> CORE DOCUMENTALE CLASSE AEGIS ONLINE
> OPERATORE AUTENTICATO
> ACCESSO LETTURA: TUTTA LA CIURMA
> ACCESSO SCRITTURA: RISTRETTO PER SETTORE
```

Ogni astronave porta con sé una memoria.

Sotto le lamiere del ponte, tra il motore a salto e il supporto vitale, c'è il
core del computer — e su di esso, il *Library Data*. Rilevazioni planetarie.
Schede di xenobiologia. Manifesti di carico. Log di missione scarabocchiati da
un ufficiale alle 03:00 di bordo durante una lunga accelerazione. La ciurma non
"apre un'app" per leggerlo. Interroga la nave. La nave risponde.

**SC-ARCHIVE è quel computer, reso reale.**

È la console del Library Data di un vascello *Classe Aegis* — un luogo dove la
ciurma consulta l'archivio di alto livello (sola lettura, disponibile a tutti i
membri) e dove ogni ufficiale mantiene i propri documenti di lavoro nel settore
assegnato. Il Capitano e gli ufficiali aggiornano i log; la ciurma li legge. La
gerarchia non è un'impostazione sepolta in un menu. *È* l'architettura.

Non è uno strumento di documentazione travestito da astronave. È il core
documentale di un'astronave che, per caso, gira su un Raspberry Pi.

---

### // PERCHÉ È COSTRUITO COSÌ

Questo progetto è stato criticato per una ragione ricorrente: *"usa il
filesystem, non c'è un database."*

Quella critica sbaglia genere.

Il dato centrale di SC-ARCHIVE sono **documenti Markdown** — file di testo,
organizzati ad albero in directory, scritti, letti, navigati e convertiti in
PDF. Il dato *è già un file per sua natura.* Metterlo in un database relazionale
significherebbe reinventare un filesystem dentro il database — peggio del
filesystem, perdendo tutto ciò che il filesystem dà gratis: documenti apribili
con qualsiasi editor, versionabili con `git`, cercabili con `grep`, copiabili
con `rsync`.

Ma c'è una ragione più profonda, ed è narrativa.

Il Library Data di un'astronave **è** un archivio gerarchico di schede tecniche
— non una struttura relazionale con chiavi esterne e join. Quando un personaggio
"naviga la Library", naviga cartelle. La scelta tecnica e la finzione
coincidono. Un database dietro le quinte sarebbe *meno* fedele, non più:
imporrebbe una struttura relazionale che nella finzione non esiste.

La stessa logica attraversa il modello dei permessi. Ogni operatore vive nel
proprio subtree (`~/sc-archive/<username>/`); i settori condivisi sono
scrivibili dal gruppo; l'archivio alto è in sola lettura per tutti. Non è un
ripensamento sulla sicurezza — è il **protocollo operativo della ciurma di una
nave**, modellato direttamente sui permessi del sistema operativo. Ci appoggiamo
alle garanzie che il SO già fornisce, invece di reimplementarle male.

Persino lo strato neurale è diegetico. L'Oracle (Ollama locale,
`qwen2.5-coder`) è il computer di bordo che *ti risponde* — suggerimenti
ghost-text mentre scrivi un rapporto, come una vera IA di bordo assisterebbe un
ufficiale nella stesura di un log. Gira **localmente, offline, su hardware
isolato** — perché su un'astronave non c'è internet, e perché l'intera stazione
deve avviarsi e respirare su una singola macchina in LAN chiusa, esattamente
come il core sigillato di un vascello reale.

---

### // PORTATA & ONESTÀ

SC-ARCHIVE è progettato per una ciurma di **50–100 operatori** su hardware
locale. Non è costruito per scalare a diecimila utenti su venti datacenter, e
non finge di esserlo. Entro la portata prevista, il design filesystem-first non
è una scorciatoia — è la scelta ingegneristica *corretta* per il dominio.

C'è esattamente un punto in cui il "niente database" inizia a mostrare tensione,
e lo dichiariamo apertamente invece di nasconderlo: **COMMS**, lo strato di
messaggistica tra membri della ciurma. Messaggi, stato letto/non letto, bozze,
filtraggio per gruppo — questi portano una vera struttura relazionale. Alla
scala prevista il filesystem la gestisce senza problemi; a una scala molto
maggiore è questo il componente che sentirebbe per primo lo sforzo. Non lo
storage dei documenti. COMMS. Sappiamo dov'è la cucitura.

Le scritture concorrenti ai registri condivisi (`users.json`, `groups.json`)
sono protette affinché due salvataggi simultanei non si sovrascrivano a vicenda.
Piccola accortezza, messa al posto giusto.

---

### // PER CHI È STATO FATTO

Se sei un backend engineer in cerca di un'app CRUD con un'istanza Postgres,
questo progetto ti confonderà, e lo giudicherai col metro sbagliato.

Se sei un Referee di Traveller, e hai mai descritto i tuoi giocatori seduti a un
terminale a interrogare il Library Data della nave — allora hai già capito
esattamente cos'è questo, e perché ogni scelta è stata fatta nel modo in cui è
stata fatta.

È stato costruito per i narratori della stazione.

```text
> FINE FILE
> ARCHIVIO RIMANE ONLINE
```
