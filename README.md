# Optimiseur de stuff Dofus

Application web qui retourne **le build optimal prouvé** sous contraintes
utilisateur. Backend **FastAPI + OR-Tools (CP-SAT)** résolvant un modèle linéaire
en nombres entiers (sélection d'items, répartition de points par tranches,
paliers de panoplie linéarisés, conditions d'équipement en indicatrices) qui
maximise une fonction de **dégâts théoriques linéaire**, alimenté par une base
**SQLite** ingérée une fois, le tout exposé à un front **React + Vite**.

> Implémentation du plan `plan-dofus-optimizer.md`.

## Architecture

```
React (Vite)  ──HTTP/JSON──▶  FastAPI /optimize  ──▶  OR-Tools CP-SAT
                                     │
                                     ▼
                              items.sqlite  ◀── ingestion offline (dofusdude + DofusDB)
```

- **Objectif** : dégâts théoriques (coup max, jet parfait) selon le type de stuff.
  Multi-élément = moyenne des dégâts ; Sagesse = lexicographique (max sagesse,
  puis tiebreak pondéré).
- **Contraintes** : chaque stat (PA, PM, PV, CC, résistances, …) avec un
  opérateur. Conditions d'items et panoplies modélisées *dans* le solveur.
- **Optimum prouvé** : grâce au choix « jet parfait + coup max », la fonction de
  dégâts est linéaire ⇒ CP-SAT renvoie l'optimum prouvé (pas une approximation).

## Données & licence

Les données proviennent de :

- **[dofusdude](https://docs.dofusdu.de/)** (`api.dofusdu.de`) — effets typés,
  emplacements et bonus de panoplie par palier.
- **[DofusDB](https://api.dofusdb.fr/)** — chaînes `criterions` (conditions
  d'équipement) et appartenance aux panoplies.

Les données du jeu Dofus appartiennent à **© Ankama**. Données issues de
**DofusDB** — utilisation soumise à la **LPNC-IA 1.0** : usage **non commercial**,
**attribution obligatoire**, **partage dans les mêmes conditions**. Ce projet est
personnel et non commercial.

## Prérequis

- Python ≥ 3.12 (testé sur 3.14) — `ortools` doit fournir une wheel pour ta version.
- Node ≥ 18.

## Installation & lancement

### 1. Backend

```bash
cd backend
python -m venv .venv
.venv/Scripts/python -m pip install -e ".[dev]"   # Windows
# source .venv/bin/activate && pip install -e ".[dev]"  # Linux/Mac

# (1) ingestion : un seul crawl, mis en cache dans data/raw/
python -m app.data.ingest
# (2) normalisation -> data/items.sqlite
python -m app.data.normalize

# lancer l'API
python -m uvicorn app.main:app --reload --port 8000
```

API sur http://127.0.0.1:8000 — docs interactives sur `/docs`.

### 2. Frontend

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173 (proxy /api -> :8000)
```

## Tests & qualité

```bash
cd backend
.venv/Scripts/python -m pytest      # tests solveur + API + dégâts
.venv/Scripts/python -m ruff check app tests
```

## Contrat API (`POST /optimize`)

```jsonc
// Requête
{
  "stuff_type": "force",            // force|intel|chance|agi|multi|sagesse
  "elements": ["terre", "air"],     // requis si multi
  "level": 200,
  "damage_profile": "generique",    // generique|melee|distance|sorts|armes
  "obtainable_only": true,          // exclut le matériel non obtenable (cf §limites)
  "banned_ids": [17997],            // items exclus du pool (bannis par l'utilisateur)
  "constraints": [
    { "dim": "pa", "op": ">=", "value": 11 },
    { "dim": "pm", "op": ">=", "value": 6 }
  ],
  "tiebreak_weights": { "vitalite": 1 },  // optionnel (sagesse / égalités)
  "time_limit": 20
}
```

```jsonc
// Réponse (extrait)
{
  "status": "OPTIMAL",              // OPTIMAL | FEASIBLE | INFEASIBLE | UNKNOWN
  "optimality_gap": 0.0,
  "items": [ { "id": 17997, "name": "...", "slot": "amulette", "img_url": "..." } ],
  "point_allocation": { "force": 398 },
  "totals": { "force": 2368, "pa": 12, "...": 0 },
  "kpi": { "damage_normal": 3040, "damage_crit": 3040, "cc": 3, "resistances": {} },
  "active_sets": [ { "set_id": 270, "name": "Panoplie du Comte Harebourg", "pieces": 2 } ]
}
```

Autres endpoints : `GET /items?slot=&level_max=&search=&limit=`, `GET /sets`,
`GET /health`.

## Structure

```
backend/app/
├── main.py                 # FastAPI + CORS
├── config.py               # constantes de jeu (points, tranches, slots) — à vérifier sur le live
├── api/routes.py           # /optimize, /items, /sets, /health
├── models/                 # pydantic (request / response)
├── data/
│   ├── ingest.py           # crawl dofusdude + DofusDB -> data/raw/
│   ├── effect_mapping.py   # effet typé -> dimension canonique
│   ├── criterion_parser.py # "CS>200" -> arbre de conditions
│   ├── normalize.py        # raw -> items.sqlite (vecteurs jet parfait)
│   └── repository.py       # SQLite -> objets domaine
└── solver/
    ├── stats.py            # dimensions canoniques (ordre figé)
    ├── damage.py           # fonction de dégâts linéaire (+ scaling entier)
    ├── prefilter.py        # cap niveau + dominance Pareto (capacité par slot)
    ├── model.py            # construction du modèle CP-SAT
    ├── solve.py            # orchestration + lexicographique sagesse
    └── service.py          # requête HTTP -> solveur -> réponse
```

## Notes / limites connues

- **Valeurs de jeu** (`config.py`) : tranches de points, points/niveau, vie de
  base — valeurs Dofus 2/3 classiques, à revérifier sur le jeu live (Dofus 3 a pu
  bouger). Tout est paramétré, rien n'est codé en dur ailleurs.
- **Conditions d'items** : les conditions *déterminées par le build* sont
  appliquées dans le solveur (indicatrices) — caractéristiques (Force, Vita,
  Sagesse, Chance, Agi, Intel), **PA, PM, Portée, Puissance**, et le **nombre de
  bonus de panoplie** (ex. trophées « < 3 bonus de panoplie » : une panoplie à
  *k* pièces compte **(k-1)** bonus — 2 pièces → +1, 3 pièces → +2 — et on somme
  sur toutes les panoplies actives), en AND/OR. Les conditions sont lues
  depuis l'arbre **structuré de dofusdude** (mappé par *nom* d'élément), bien plus
  fiable que les codes 2-lettres bruts de DofusDB (qui cachaient un piège :
  `CS` = Force, pas Sagesse). Les conditions liées à l'**état externe du joueur**
  (niveau via le champ level, quêtes, alignement, abonnement, kamas, serveur…) ne
  peuvent pas être satisfaites depuis un build : elles restent supposées remplies.
  Le niveau requis (`level`) est appliqué via le cap de niveau. Chaque condition
  est affichée dans l'infobulle de l'item.
- **Dégâts** : base de sort générique (`BASE_GENERIQUE`). Un **profil de dégâts**
  optionnel (`generique`/`melee`/`distance`/`sorts`/`armes`) ajoute le `% Do`
  correspondant à l'objectif. ⚠️ Ces stats sont **rares** sur l'équipement
  Dofus 3, donc le profil change rarement le build à haut niveau. Les
  crits/résistances restent des contraintes optionnelles + affichage.
- **Classe** : sans impact sur l'optimisation — toutes les classes partagent les
  mêmes caractéristiques de base, règles de points et pool d'items ; seules les
  *sorts* diffèrent, or l'objectif utilise un coefficient générique. Pas de
  sélecteur de classe (il ne changerait rien).
- **Items exclus** : le matériel MJ est retiré dès l'ingestion via
  `EXCLUDED_NAME_SUBSTRINGS` dans `config.py` (ex. `(MJ)`, `Maître Jarbo`).
- **Obtenabilité** : DofusDB n'a pas de flag « obtenable » fiable. On utilise le
  bit `1024` de `m_flags` (= *échangeable en HDV*) comme proxy : il écarte tout le
  matériel MJ/PNJ/test/blague. Les rares items *liés* mais réels qu'il écarterait
  à tort (surtout des Dofus) sont rattrapés par `OBTAINABLE_KEEP_SLOTS`
  (slot `dofus` toujours gardé) et `OBTAINABLE_ALLOWLIST` (ids à conserver).
  Exposé via le toggle `obtainable_only` (défaut activé) — désactivable pour
  considérer toute la base. ⚠️ Quelques armes liées (non échangeables mais
  droppables) sont donc masquées par défaut ; ajoutez-les à l'allowlist au besoin.
