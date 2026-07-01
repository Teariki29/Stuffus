import type { DamageProfile, Element, StuffType } from "../types";
import { DAMAGE_PROFILES, ELEMENTS, STUFF_TYPES } from "../constants";

interface Props {
  stuffType: StuffType;
  elements: Element[];
  level: number;
  damageProfile: DamageProfile;
  onStuffType: (t: StuffType) => void;
  onElements: (e: Element[]) => void;
  onLevel: (l: number) => void;
  onDamageProfile: (p: DamageProfile) => void;
}

export function StuffTypeSelector({
  stuffType,
  elements,
  level,
  damageProfile,
  onStuffType,
  onElements,
  onLevel,
  onDamageProfile,
}: Props) {
  const toggleElement = (e: Element) => {
    onElements(elements.includes(e) ? elements.filter((x) => x !== e) : [...elements, e]);
  };

  return (
    <section className="panel">
      <h2>Type de stuff</h2>
      <div className="chips">
        {STUFF_TYPES.map((t) => (
          <button
            key={t.value}
            className={`chip ${stuffType === t.value ? "active" : ""}`}
            style={stuffType === t.value ? { borderColor: t.color, color: t.color } : undefined}
            onClick={() => onStuffType(t.value)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {stuffType === "multi" && (
        <div className="multi-elements">
          <label>Éléments (min. 2)</label>
          <div className="chips">
            {ELEMENTS.map((e) => (
              <button
                key={e.value}
                className={`chip ${elements.includes(e.value) ? "active" : ""}`}
                onClick={() => toggleElement(e.value)}
              >
                {e.label}
              </button>
            ))}
          </div>
        </div>
      )}

      {stuffType !== "sagesse" && (
        <div className="multi-elements">
          <label>Profil de dégâts</label>
          <div className="chips">
            {DAMAGE_PROFILES.map((p) => (
              <button
                key={p.value}
                className={`chip ${damageProfile === p.value ? "active" : ""}`}
                onClick={() => onDamageProfile(p.value)}
                title={p.hint}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="level-row">
        <label htmlFor="level">Niveau&nbsp;: {level}</label>
        <input
          id="level"
          type="range"
          min={1}
          max={200}
          value={level}
          onChange={(e) => onLevel(Number(e.target.value))}
        />
        <input
          type="number"
          min={1}
          max={200}
          value={level}
          onChange={(e) => onLevel(Math.min(200, Math.max(1, Number(e.target.value))))}
        />
      </div>
    </section>
  );
}
