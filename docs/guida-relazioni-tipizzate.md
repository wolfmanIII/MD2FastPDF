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

| Chiave da scrivere | Significato | Etichetta (sul file che la dichiara) | Etichetta inversa (sull'altro file, automatica) | Esempio |
| --- | --- | --- | --- | --- |
| `crew` | equipaggio di una nave | **Equipaggio** | Equipaggio di | `crew: [Kira Venn, Tarn Mekel]` su `Beowulf.md` |
| `member_of` | membro di un gruppo/organizzazione | **Membro di** | Membri | `member_of: Pax Pirata` su `Kira Venn.md` |
| `located_in` | situato dentro un luogo (funziona anche per una scena: dove si svolge) | **Situato in** | Contiene | `located_in: Porozlo` su `Kira Venn.md` **oppure** su `Scena-0011-Parley-Con-Kira-Lonn.md` |
| `hostile_to` | ostilità reciproca | **Ostile a** | Ostile a *(uguale, è reciproca)* | `hostile_to: [Tarn Mekel]` su `Kira Venn.md` |
| `owns` | possiede/comanda qualcosa (nave, oggetto...) | **Possiede** | Posseduto da | `owns: [Maelstrom]` su `Kira Venn.md` |
| `owes_debt_to` | è in debito con qualcuno | **Debitore di** | Creditore di | `owes_debt_to: [Malen Trast]` su `Dorel Varr.md` |
| `reports_to` | risponde/è subordinato a qualcuno (catena di comando o lealtà, anche segreta) | **Risponde a** | Subordinati | `reports_to: [Malen Trast]` su `Tenente Vesk.md` |
| `allied_with` | alleanza reciproca | **Alleato di** | Alleato di *(uguale, è reciproca)* | `allied_with: [Jaro Vey]` su `Alto Sacerdote Khaeden.md` |
| `mentor_of` | è mentore/maestro di qualcuno | **Mentore di** | Allievo di | `mentor_of: [Fratello Malek]` su `Alto Sacerdote Khaeden.md` |
| `npcs` | quali NPC compaiono in una scena | **NPC coinvolti** | Scene | `npcs: [Kira Venn, Tarn Mekel]` su `Scena-0011-Parley-Con-Kira-Lonn.md` |
| `organizations` | quali organizzazioni/fazioni sono coinvolte in una scena | **Organizzazioni coinvolte** | Scene | `organizations: [Pax Pirata]` su `Scena-0011-Parley-Con-Kira-Lonn.md` |

La colonna "etichetta inversa" è quella che vedi **sull'altro file**, quello che non ha
scritto nulla — es. se `Beowulf.md` scrive `crew: [Kira Venn]`, tu su `Beowulf.md` vedi
"Equipaggio", ma su `Kira Venn.md` vedi "Equipaggio di" (non "Equipaggio" di nuovo — è
un'etichetta diversa, pensata apposta per leggersi al contrario). Per `npcs` e
`organizations` funziona uguale: scrivile solo sulla scena, e ogni NPC/organizzazione
coinvolti vedono da soli "Scene" comparire sulla propria scheda, senza doverlo scrivere
lì — anche se sono due chiavi diverse, "vedono" la stessa etichetta perché il significato
per chi legge è lo stesso, cambia solo di cosa parla la scheda che la mostra.

Le 4 relazioni `owes_debt_to`, `reports_to`, `allied_with`, `mentor_of` sono state aggiunte
dopo un'analisi del materiale di campagna reale — non sono teoriche, ricorrono più volte
nelle schede NPC. `member_of` resta la scelta giusta per l'appartenenza *formale* a un
gruppo/organizzazione; `reports_to` è per un rapporto di subordinazione/lealtà *personale*
verso un singolo individuo (anche quando è segreto o doppiogiochista). `npcs` e
`organizations` sono nate allo stesso modo, dall'archivio scene reale, per rispondere a
domande concrete: "in quali scene appare questo NPC?", "in quali scene è coinvolta questa
organizzazione?".

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

**Se il nome del file contiene `:` oppure `,`, mettilo tra apici doppi:**

Sono gli stessi due caratteri che nella sintassi YAML separano chiave/valore e gli
elementi di una lista — se compaiono dentro un nome senza apici, la riga viene letta
male. Con nomi Traveller ci si sbatte facilmente:

```yaml
owns: [Beowulf: Type-A]        # ROTTO — i due punti spezzano la riga
crew: [Vesk, Tenente]          # ROTTO — letto come DUE nomi, non uno

owns: ["Beowulf: Type-A"]      # corretto
crew: ["Vesk, Tenente"]        # corretto
```

Negli altri casi (nomi senza `:` o `,`) gli apici non servono e puoi ometterli.

---

## 5. Come vengono risolti i nomi

**Maiuscole e spazi non contano.** `kira venn`, `Kira Venn`, `KIRA VENN` risolvono
tutti allo stesso file `Kira Venn.md`. Anche gli spazi doppi/multipli vengono
ridotti a uno solo automaticamente. Non serve essere precisi al carattere.

**Se il nome non corrisponde a niente**, niente di grave: non è un errore, non
blocca il salvataggio. Il riferimento diventa **dangling** ("penzolante") —
visibile nel report diagnostico (`GET /api/diagnostics/relations`), ma invisibile
e innocuo altrove. Cause tipiche: refuso nel nome, il file non esiste ancora, o è
scritto diverso (es. `Kira Ven` invece di `Kira Venn`).

**Se due file diversi hanno lo stesso nome** (in cartelle diverse — es. due
`Manifest.md`), un riferimento a quel nome ne colpisce **uno solo**, e quale dipende
dall'ordine di scansione dell'archivio (non è scelta tua). La collisione viene
comunque registrata nel report diagnostico, distinta dai riferimenti dangling.
Soluzione pratica: dai ai file nomi distinti quando possono confondersi.

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

**E se la dichiari comunque da entrambi i lati?** Non succede nulla di rotto: per le
relazioni reciproche come `hostile_to` e `allied_with`, il pannello mostra il
collegamento **una volta sola**, mai duplicato, anche se sia A che B lo dichiarano
indipendentemente. Non c'è però un avviso dedicato nel report diagnostico per questo
caso — se vuoi evitare doppioni "manuali" nel testo, resta comunque meglio dichiarare
da un solo lato, ma non è un problema se ti scappa.

---

## 7. `type:` è libero — cosa scrivere per progetti, IA, oggetti e simili

Il valore di `type:` non è vincolato a una lista chiusa. Puoi scrivere `ship`,
`npc`, `organization`, `location`, `drone`, `item`, `scene` — ma anche una parola
che non esiste ancora da nessuna parte nel programma, e funzionerà comunque.
Non serve "registrarla" prima: basta scriverla.

Questo è utile per tutto il materiale che non è ovviamente un personaggio o una
nave — progetti di ricerca segreti (*Progetto Helix*, *Progetto Aran*),
intelligenze artificiali (*IUNO*), oggetti/artefatti (un cristallo, un manufatto
antico), o una partizione criptata su una nave. Due esempi concreti già in uso
nell'archivio reale:

```yaml
---
type: organization        # un progetto/fazione semi-ufficiale
member_of: Lysander-Consorzio
---
```

```yaml
---
type: ai                  # un'intelligenza artificiale — tipo inventato, nessun
                           # problema: non serve dichiararlo prima da nessuna parte
located_in: Luna-Octavia   # located_in funziona con qualsiasi tipo, essendo generica
---
```

**Regola pratica: quasi mai serve una chiave nuova in tabella per questo.** Nella
maggior parte dei casi bastano due cose:

1. Un `type:` sensato — riusa `organization` per progetti/fazioni, `item` per
   oggetti/artefatti, oppure inventane uno tuo (`ai`, e così via) se nessuno dei
   tipi esistenti calza.
2. Una delle chiavi **già in tabella** per collegarlo a qualcos'altro —
   `member_of`, `owns`, `located_in` (quest'ultima, non avendo vincoli, funziona
   con qualunque tipo, anche uno mai visto prima).

Una chiave *davvero* nuova serve solo quando ti trovi a voler fare una domanda
concreta a cui nessuna delle chiavi esistenti sa rispondere — non solo perché hai
in archivio un genere di contenuto diverso dal solito.

**E se il tipo "non torna" con una relazione?** Alcune chiavi (es. `owns`) hanno
un lato ristretto a certi tipi (nave, luogo, drone, oggetto). Se ci scrivi dentro
qualcosa di un tipo diverso e inatteso (es. `owns: [IUNO]` con `IUNO.md` che ha
`type: ai`), **non succede nulla di rotto**: il salvataggio funziona lo stesso,
niente errore, niente blocco. Compare solo una riga in più nel report diagnostico
(`GET /api/diagnostics/relations`), silenziosa e ignorabile — la stessa logica dei
riferimenti dangling. Verificato: oggi, nell'archivio reale, le entità `type: ai`
non generano nessuna di queste segnalazioni, perché l'unica relazione in cui
compaiono (`located_in`) non ha vincoli di tipo.

---

## 8. Esempio completo

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

## 9. Riepilogo lampo

1. Blocco `---` / `---` alla primissima riga del file, prima di tutto il resto.
2. Creano relazioni solo queste 11 chiavi: `crew`, `member_of`, `located_in`,
   `hostile_to`, `owns`, `owes_debt_to`, `reports_to`, `allied_with`, `mentor_of`,
   `npcs`, `organizations`. Qualunque altra chiave viene ignorata, mai un errore.
3. Valore = uno o più nomi di file (senza `.md`), tra `[quadre]` se sono più di uno.
   Nomi con `:` o `,` vanno tra apici doppi.
4. Maiuscole e spazi non contano nella risoluzione dei nomi.
5. Dichiara ogni relazione **da un solo lato** — l'altro compare da solo, con
   un'etichetta diversa e pensata per leggersi al contrario.
6. Nome sbagliato = dangling, non un crash. Nomi duplicati tra file = collisione.
   Entrambi finiscono nel report diagnostico, distinti.
7. `type:` è libero: puoi inventare un valore nuovo (es. `ai`) senza modificare
   nulla. Un tipo che non torna con una relazione non blocca niente — finisce solo
   nel report diagnostico, come i dangling.
