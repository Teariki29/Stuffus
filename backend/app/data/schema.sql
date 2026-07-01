-- SQLite schema for the optimizer's item database (plan §4.2).
-- Stat vectors are stored as JSON dicts {dim: value} (jet parfait).

PRAGMA journal_mode = WAL;

DROP TABLE IF EXISTS items;
DROP TABLE IF EXISTS sets;
DROP TABLE IF EXISTS meta;

CREATE TABLE items (
    id              INTEGER PRIMARY KEY,   -- ankama_id
    name            TEXT NOT NULL,
    slot            TEXT NOT NULL,         -- coiffe|cape|amulette|anneau|ceinture|
                                           -- bottes|bouclier|arme|familier|dofus|trophee
    type_name       TEXT,                  -- raw dofusdude type (Épée, Anneau, …)
    level           INTEGER NOT NULL,
    set_id          INTEGER,               -- NULL if not in a set
    is_weapon       INTEGER NOT NULL DEFAULT 0,
    obtainable      INTEGER NOT NULL DEFAULT 1,  -- player can get it (cf config)
    stats_json      TEXT NOT NULL,         -- {dim: value} jet parfait
    conditions_json TEXT,                  -- parsed condition tree (cf criterion_parser)
    weapon_json     TEXT,                  -- {ap_cost, range, crit, crit_bonus, hits:[…]} or NULL
    img_url         TEXT
);

CREATE TABLE sets (
    id            INTEGER PRIMARY KEY,
    name          TEXT NOT NULL,
    item_ids      TEXT NOT NULL,           -- JSON list of member ankama ids
    -- per-tier bonus: {"2": {dim:val,…}, "3": {…}, …}
    bonuses_json  TEXT NOT NULL
);

-- free-form key/value store (ingest timestamps, source versions, …)
CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

CREATE INDEX idx_items_slot  ON items(slot);
CREATE INDEX idx_items_level ON items(level);
CREATE INDEX idx_items_set   ON items(set_id);
