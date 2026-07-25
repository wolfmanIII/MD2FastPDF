# Guida — Relazioni tipizzate nel frontmatter

Guida pratica per l'utente. Per il progetto tecnico vedi `ANALISI-relazioni-tipizzate.md`.

---

## 1. Cos'è il frontmatter

Il **frontmatter** è un blocchetto di dati messo in cima a un file `.md`, separato dal
resto del testo da due righe `---`. Serve a dichiarare informazioni *sull'entità*
(la nave, il personaggio, il luogo...) invece che scriverle nel corpo del documento.

```markdown
---
type: ship
crew: [Kira Venn, Tarn Mekel]
---

# La Beowulf

Testo normale del documento, qui sotto...
```

**Regole di posizione — importanti:**

- Va alla **primissima riga** del file. Nessuna riga vuota prima.
- Delimitato da `---` sopra e `---` sotto.
- Tutto quello che scrivi *dopo* il secondo `---` è il documento normale, esattamente
  come prima — titoli, testo, immagini, tutto invariato.

Un file **senza** questo blocco continua a funzionare esattamente come oggi: il
frontmatter è opzionale, non è mai obbligatorio.

---

## 2. Terminologia: chiave e valore

Ogni riga dentro il blocco ha la forma:

```text
chiave: valore
```

- **Chiave** (in inglese *key*): la parola prima dei due punti. Es. `type`, `crew`.
  È lei a determinare *cosa* significa quella riga — il programma guarda **solo** il
  nome della chiave per capire se creare una relazione.
- **Valore**: quello che scrivi dopo i due punti. Può essere un nome singolo o una
  lista tra `[quadre]`.

```text
crew: [Kira Venn, Tarn Mekel]
^^^^  ^^^^^^^^^^^^^^^^^^^^^^^
chiave         valore (lista di due nomi)
```

---

## 3. Le uniche chiavi riconosciute

Il programma riconosce **solo queste chiavi** come relazioni. Qualunque altra parola
tu scriva come chiave (es. `note`, `colore`) viene **ignorata in silenzio**:
non è un errore, semplicemente non crea nessuna relazione, resta un'annotazione morta.

| Chiave da scrivere | Significato | Etichetta nel pannello RELAZIONI | Esempio |
| --- | --- | --- | --- |
| `crew` | equipaggio di una nave | **Equipaggio** | `crew: [Kira Venn, Tarn Mekel]` su `Beowulf.md` |
| `member_of` | membro di un gruppo/organizzazione | **Membro di** | `member_of: Pax Pirata` su `Kira Venn.md` |
| `located_in` | situato dentro un luogo | **Situato in** | `located_in: Porozlo` su `Kira Venn.md` |
| `hostile_to` | ostilità reciproca | **Ostile a** | `hostile_to: [Tarn Mekel]` su `Kira Venn.md` |
| `owns` | possiede/comanda qualcosa (nave, oggetto...) | **Possiede** | `owns: [Maelstrom]` su `Kira Venn.md` |
| `owes_debt_to` | è in debito con qualcuno | **Debitore di** | `owes_debt_to: [Malen Trast]` su `Dorel Varr.md` |
| `reports_to` | risponde/è subordinato a qualcuno (catena di comando o lealtà, anche segreta) | **Risponde a** | `reports_to: [Malen Trast]` su `Tenente Vesk.md` |
| `allied_with` | alleanza reciproca | **Alleato di** | `allied_with: [Jaro Vey]` su `Alto Sacerdote Khaeden.md` |
| `mentor_of` | è mentore/maestro di qualcuno | **Mentore di** | `mentor_of: [Fratello Malek]` su `Alto Sacerdote Khaeden.md` |

Le ultime 4 (`owes_debt_to`, `reports_to`, `allied_with`, `mentor_of`) sono state aggiunte
dopo un'analisi del materiale di campagna reale — non sono teoriche, ricorrono più volte
nelle schede NPC. `member_of` resta la scelta giusta per l'appartenenza *formale* a un
gruppo/organizzazione; `reports_to` è per un rapporto di subordinazione/lealtà *personale*
verso un singolo individuo (anche quando è segreto o doppiogiochista).

Se in futuro serve un'altra relazione diversa da queste, si aggiunge al vocabolario — ma
solo quando c'è un caso d'uso concreto nel testo, per non gonfiare la lista all'infinito.

C'è anche `type:`, che **non è una relazione**: è solo un'etichetta libera per dire
che tipo di entità è il file (`ship`, `npc`, `location`...). Utile per tenere ordine,
ma il programma non la usa per validare nulla in questa fase.

---

## 4. Come scrivere i valori

Due regole indipendenti, non vanno mescolate.

**Quante parentesi quadre singole `[ ]` — dipende solo dal numero di nomi:**

```yaml
crew: Kira Venn                   # 1 solo nome -> niente parentesi
crew: [Kira Venn, Tarn Mekel]     # 2 o più nomi -> UNA coppia di parentesi attorno a tutti
```

Non esiste una via di mezzo (niente "una coppia di parentesi per ogni nome") — o le
ometti del tutto (un nome solo), o ne metti esattamente una coppia attorno all'intera
lista separata da virgole.

**Le doppie parentesi `[[ ]]` sono una cosa completamente diversa — puoi ignorarle:**

Sono lo stile "wikilink" (es. Obsidian). Se ti capita di incollare un nome che le ha
già, tipo `[[Kira Venn]]`, il programma te le toglie da solo automaticamente. Ma
**non serve mai scriverle tu di proposito** — non aggiungono nessuna funzionalità in
più, sono solo tollerate se già presenti. Scrivi sempre i nomi lisci, senza `[[ ]]`.

Il nome che scrivi **deve corrispondere al nome del file** dell'altra entità (senza
`.md`), ovunque si trovi nell'archivio — non serve il percorso. `Kira Venn` risolve
a `Kira Venn.md`, non importa in che cartella sia.

---

## 5. Cosa succede se il nome non corrisponde a niente

Niente di grave. Non è un errore, non blocca il salvataggio. Il riferimento diventa
**dangling** ("penzolante") — visibile nel report diagnostico
(`GET /api/diagnostics/relations`), ma invisibile e innocuo altrove.

Cause tipiche: refuso nel nome, il file non esiste ancora, o è scritto diverso
(es. `Kira Ven` invece di `Kira Venn`).

---

## 6. La parte comoda: la query inversa è gratis

Non devi mai dichiarare la relazione **da entrambi i lati**. Se `Beowulf.md` scrive:

```yaml
crew: [Kira Venn]
```

...aprendo `Kira Venn.md` vedrai comunque, nel pannello RELAZIONI:

```text
Equipaggio di: Beowulf
```

...anche se il file di Kira non dichiara assolutamente nulla. Il programma segue la
freccia al contrario da solo.

**Regola pratica: dichiara la relazione da un solo lato**, quello che ti sembra più
naturale (di solito: la nave dichiara il proprio equipaggio, non ogni membro
dell'equipaggio dichiara la propria nave).

---

## 7. Esempio completo

**`Beowulf.md`:**

```yaml
---
type: ship
crew: [Kira Venn, Tarn Mekel]
owns: [Cargo Manifest]
---

# La Beowulf

Mercantile classe Type-A...
```

**`Kira Venn.md`** (nessun frontmatter necessario da parte sua):

```markdown
# Kira Venn

Pilota della Beowulf.
```

Risultato nel pannello RELAZIONI:

- Su **Beowulf**: *Equipaggio* → Kira Venn, Tarn Mekel · *Possiede* → Cargo Manifest
- Su **Kira Venn**: *Equipaggio di* → Beowulf (comparso da solo, senza scrivere niente)

---

## 8. Riepilogo lampo

1. Blocco `---` / `---` alla primissima riga del file, prima di tutto il resto.
2. Solo `crew`, `member_of`, `located_in`, `hostile_to`, `owns` creano relazioni —
   qualunque altra chiave viene ignorata, mai un errore.
3. Valore = uno o più nomi di file (senza `.md`), tra `[quadre]` se sono più di uno.
4. Dichiara ogni relazione **da un solo lato** — l'altro compare da solo.
5. Nome sbagliato = dangling, non un crash. Controllabile nel report diagnostico.
