import { useState } from "react";
import type { BuildResponse, ConditionNode, ResultItem } from "../types";
import { DIM_LABELS, DIM_META } from "../constants";
import { Icon, iconFile } from "../icons";

const OP_LABEL: Record<string, string> = { ">": "≥", "<": "≤", "=": "=", "!": "≠", ">=": "≥", "<=": "≤" };

// human-readable condition string; skips non-enforced (player-state) leaves
function formatCondition(node?: ConditionNode | null): string {
  if (!node || node.op === "true") return "";
  if (node.op === "cmp") {
    const label = DIM_LABELS[node.dim ?? ""] ?? node.dim;
    // ">" means strictly greater → show "≥ value+1" to match in-game wording
    const op = node.operator ?? "=";
    const v = op === ">" ? (node.value ?? 0) + 1 : op === "<" ? (node.value ?? 0) - 1 : node.value;
    return `${label} ${OP_LABEL[op] ?? op} ${v}`;
  }
  const parts = (node.children ?? []).map(formatCondition).filter(Boolean);
  if (parts.length === 0) return "";
  if (parts.length === 1) return parts[0];
  const sep = node.op === "or" ? " ou " : " et ";
  return parts.join(sep);
}

interface Props {
  result: BuildResponse;
  shareUrl: string | null;
}

const STATUS_LABEL: Record<string, string> = {
  OPTIMAL: "Optimal (prouvé)",
  FEASIBLE: "Solution trouvée",
  INFEASIBLE: "Aucune solution",
  UNKNOWN: "Délai dépassé",
};

const LEFT_COL: { slot: string; ring?: number }[] = [
  { slot: "amulette" },
  { slot: "coiffe" },
  { slot: "anneau", ring: 0 },
  { slot: "ceinture" },
  { slot: "bottes" },
];
const RIGHT_COL: { slot: string; ring?: number }[] = [
  { slot: "cape" },
  { slot: "familier" },
  { slot: "arme" },
  { slot: "bouclier" },
  { slot: "anneau", ring: 1 },
];

export function BuildResult({ result, shareUrl }: Props) {
  if (
    result.status === "INFEASIBLE" ||
    result.status === "UNKNOWN" ||
    result.items.length === 0
  ) {
    return (
      <section className="panel result-empty">
        <h2>{STATUS_LABEL[result.status] ?? result.status}</h2>
        <p className="muted">{result.message ?? "Aucun build à afficher."}</p>
      </section>
    );
  }

  const t = (dim: string) => result.totals[dim] ?? 0;
  const pts = (c: string) => result.point_allocation[c] ?? 0;
  const bySlot = (slot: string) => result.items.filter((i) => i.slot === slot);
  const rings = bySlot("anneau");
  const slotItem = (slot: string, ring?: number): ResultItem | undefined =>
    ring !== undefined ? rings[ring] : bySlot(slot)[0];
  const pool = result.items.filter((i) => i.slot === "dofus" || i.slot === "trophee");
  const k = result.kpi;

  return (
    <section className="sheet">
      <div className="sheet-topbar">
        <span className={`status-badge ${result.status.toLowerCase()}`}>
          {STATUS_LABEL[result.status] ?? result.status}
        </span>
        {result.optimality_gap > 0 && (
          <span className="gap">écart {(result.optimality_gap * 100).toFixed(1)}%</span>
        )}
        <ShareButton url={shareUrl} />
        <div className="topbar-dmg">
          <span>
            Dégâts <strong>{k.damage_normal ?? "—"}</strong>
          </span>
          <span>
            Crit <strong>{k.damage_crit ?? "—"}</strong>
          </span>
        </div>
      </div>

      <div className="sheet-grid">
        {/* ------------------------------------------------------ LEFT */}
        <div className="sheet-col">
          <div className="card summary">
            <Stat dim="vitalite" v={t("vitalite")} label="PdV" />
            <Stat dim="prospection" v={t("prospection")} label="PP" />
            <Stat dim="pa" v={t("pa")} />
            <Stat dim="pm" v={t("pm")} />
            <Stat dim="po" v={t("po")} />
            <Stat dim="initiative" v={t("initiative")} label="Initiative" />
            <Stat dim="cc" v={k.cc} label="Critique" />
            <Stat dim="invocations" v={t("invocations")} label="Invoc." />
            <Stat dim="do_soins" v={t("do_soins")} label="Soin" />
          </div>

          <div className="card carac">
            <div className="carac-head">
              <span></span>
              <span>Total</span>
              <span>Points</span>
            </div>
            {[...CARACS, ["puissance", "Puissance"] as const].map(([dim, label]) => (
              <div className="carac-row" key={dim}>
                <span className="carac-lbl">
                  <Icon name={DIM_META[dim]?.icon ?? "dot"} color={DIM_META[dim]?.color} file={iconFile(dim)} />
                  {label}
                </span>
                <strong>{t(dim)}</strong>
                <em>{pts(dim) || ""}</em>
              </div>
            ))}
          </div>

          <div className="card mini-grid">
            <Stat dim="fuite" v={t("fuite")} label="Fuite" small />
            <Stat dim="tacle" v={t("tacle")} label="Tacle" small />
            <Stat dim="esquive_pa" v={t("esquive_pa")} label="Esq. PA" small />
            <Stat dim="esquive_pm" v={t("esquive_pm")} label="Esq. PM" small />
            <Stat dim="retrait_pa" v={t("retrait_pa")} label="Ret. PA" small />
            <Stat dim="retrait_pm" v={t("retrait_pm")} label="Ret. PM" small />
            <Stat dim="pods" v={t("pods")} label="Pods" small />
          </div>
        </div>

        {/* ---------------------------------------------------- CENTER */}
        <div className="sheet-center">
          <div className="equip-columns">
            <div className="equip-side">
              {LEFT_COL.map((s, i) => (
                <SlotCell key={i} item={slotItem(s.slot, s.ring)} place="right" />
              ))}
            </div>
            <div className="equip-mannequin">
              {result.active_sets.length > 0 && (
                <div className="sets-box">
                  <h4>Panoplies</h4>
                  {result.active_sets.map((s) => (
                    <div className="set-block" key={s.set_id}>
                      <div className="set-line">
                        <span>{s.name}</span>
                        <span className="pieces">{s.pieces} pces</span>
                      </div>
                      <ul className="set-bonus">
                        {Object.entries(s.bonus)
                          .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
                          .map(([dim, val]) => (
                            <li key={dim} className={val < 0 ? "neg" : ""}>
                              <Icon name={DIM_META[dim]?.icon ?? "dot"} color={DIM_META[dim]?.color} file={iconFile(dim)} />
                              <span className="sb-val">{val > 0 ? `+${val}` : val}</span>
                              <span className="sb-lbl">{DIM_LABELS[dim] ?? dim}</span>
                            </li>
                          ))}
                      </ul>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="equip-side">
              {RIGHT_COL.map((s, i) => (
                <SlotCell key={i} item={slotItem(s.slot, s.ring)} place="left" />
              ))}
            </div>
          </div>
          <div className="equip-pool">
            {Array.from({ length: 6 }).map((_, i) => (
              <SlotCell key={i} item={pool[i]} small place="up" />
            ))}
          </div>
        </div>

        {/* ----------------------------------------------------- RIGHT */}
        <div className="sheet-col">
          <div className="card stat-grid">
            <Stat dim="do_neutre" v={t("do_neutre")} label="Do Neutre" />
            <Stat dim="do_critiques" v={t("do_critiques")} label="Do Critique" />
            <Stat dim="do_terre" v={t("do_terre")} label="Do Terre" />
            <Stat dim="pct_do_armes" v={t("pct_do_armes")} label="% Do Armes" pct />
            <Stat dim="do_feu" v={t("do_feu")} label="Do Feu" />
            <Stat dim="pct_do_sorts" v={t("pct_do_sorts")} label="% Do Sorts" pct />
            <Stat dim="do_eau" v={t("do_eau")} label="Do Eau" />
            <Stat dim="pct_do_melee" v={t("pct_do_melee")} label="% Do Mêlée" pct />
            <Stat dim="do_air" v={t("do_air")} label="Do Air" />
            <Stat dim="pct_do_distance" v={t("pct_do_distance")} label="% Do Dist" pct />
            <Stat dim="do_fixe" v={t("do_fixe")} label="Dommages" />
            <Stat dim="pct_do" v={t("pct_do")} label="% Dommages" pct />
          </div>
          <div className="card stat-grid">
            {(["terre", "feu", "eau", "air", "neutre"] as const).map((el) => (
              <Stat key={"f" + el} dim={`res_fixe_${el}`} v={t(`res_fixe_${el}`)} label={`Ré ${cap(el)}`} />
            ))}
            <div className="stat-row stat-hidden" />
            {(["terre", "feu", "eau", "air", "neutre"] as const).map((el) => (
              <Stat key={"p" + el} dim={`res_${el}`} v={t(`res_${el}`)} label={`% Ré ${cap(el)}`} pct />
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}

const CARACS: readonly (readonly [string, string])[] = [
  ["vitalite", "Vitalité"],
  ["sagesse", "Sagesse"],
  ["force", "Force"],
  ["intelligence", "Intelligence"],
  ["chance", "Chance"],
  ["agilite", "Agilité"],
];

function cap(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function Stat({
  dim,
  v,
  label,
  small,
  pct,
}: {
  dim: string;
  v: number;
  label?: string;
  small?: boolean;
  pct?: boolean;
}) {
  const meta = DIM_META[dim];
  return (
    <div className={`stat-row ${small ? "sm" : ""}`}>
      <Icon name={meta?.icon ?? "dot"} color={meta?.color} file={iconFile(dim)} />
      <span className={`stat-val ${v < 0 ? "neg" : ""}`}>
        {v}
        {pct ? "%" : ""}
      </span>
      <span className="stat-lbl">{label ?? DIM_LABELS[dim] ?? dim}</span>
    </div>
  );
}

function SlotCell({
  item,
  small,
  place = "up",
}: {
  item?: ResultItem;
  small?: boolean;
  place?: "left" | "right" | "up";
}) {
  if (!item) return <div className={`slot ${small ? "sm" : ""} empty`} />;
  const stats = Object.entries(item.stats).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]));
  const condText = formatCondition(item.conditions);
  return (
    <div className={`slot ${small ? "sm" : ""}`}>
      {item.img_url ? <img src={item.img_url} alt={item.name} loading="lazy" /> : null}
      <span className="slot-name">{item.name}</span>
      <div className={`slot-tooltip tt-${place}`}>
        <div className="tt-head">
          <strong>{item.name}</strong>
          <span className="tt-level">Niv. {item.level}</span>
        </div>
        <ul>
          {stats.map(([dim, val]) => (
            <li key={dim} className={val < 0 ? "neg" : ""}>
              <Icon name={DIM_META[dim]?.icon ?? "dot"} color={DIM_META[dim]?.color} file={iconFile(dim)} />
              <span className="tt-val">{val > 0 ? `+${val}` : val}</span>
              <span className="tt-lbl">{DIM_LABELS[dim] ?? dim}</span>
            </li>
          ))}
        </ul>
        {condText && <div className="tt-cond">Conditions&nbsp;: {condText}</div>}
      </div>
    </div>
  );
}

function ShareButton({ url }: { url: string | null }) {
  const [copied, setCopied] = useState(false);
  if (!url) return null;
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(url);
    } catch {
      window.prompt("Lien de partage :", url);
    }
    setCopied(true);
    setTimeout(() => setCopied(false), 1800);
  };
  return (
    <button className="btn-share" onClick={copy} title="Copier le lien de partage">
      {copied ? "✓ Copié" : "🔗 Partager"}
    </button>
  );
}
