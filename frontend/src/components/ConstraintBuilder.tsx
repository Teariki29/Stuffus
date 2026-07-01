import type { Constraint, Operator } from "../types";
import { ALL_DIMS, COMMON_DIMS, DIM_LABELS } from "../constants";

interface Props {
  constraints: Constraint[];
  onChange: (c: Constraint[]) => void;
}

const OPERATORS: Operator[] = [">=", "<=", "==", ">", "<"];

// common dims first, then the rest, de-duplicated
const ORDERED_DIMS = [...COMMON_DIMS, ...ALL_DIMS.filter((d) => !COMMON_DIMS.includes(d))];

export function ConstraintBuilder({ constraints, onChange }: Props) {
  const update = (i: number, patch: Partial<Constraint>) => {
    onChange(constraints.map((c, idx) => (idx === i ? { ...c, ...patch } : c)));
  };
  const add = () => onChange([...constraints, { dim: "pa", op: ">=", value: 11 }]);
  const remove = (i: number) => onChange(constraints.filter((_, idx) => idx !== i));

  return (
    <section className="panel">
      <div className="panel-head">
        <h2>Contraintes</h2>
        <button className="btn-add" onClick={add}>
          + Ajouter
        </button>
      </div>

      {constraints.length === 0 && (
        <p className="muted">Aucune contrainte. Le build maximisera juste les dégâts.</p>
      )}

      <div className="constraints">
        {constraints.map((c, i) => (
          <div className="constraint-row" key={i}>
            <select value={c.dim} onChange={(e) => update(i, { dim: e.target.value })}>
              {ORDERED_DIMS.map((d) => (
                <option key={d} value={d}>
                  {DIM_LABELS[d] ?? d}
                </option>
              ))}
            </select>
            <select value={c.op} onChange={(e) => update(i, { op: e.target.value as Operator })}>
              {OPERATORS.map((op) => (
                <option key={op} value={op}>
                  {op}
                </option>
              ))}
            </select>
            <input
              type="number"
              value={c.value}
              onChange={(e) => update(i, { value: Number(e.target.value) })}
            />
            <button className="btn-remove" onClick={() => remove(i)} title="Supprimer">
              ✕
            </button>
          </div>
        ))}
      </div>
    </section>
  );
}
