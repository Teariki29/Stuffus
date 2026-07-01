import { useEffect, useState } from "react";
import { optimize } from "./api";
import type {
  BuildResponse,
  Constraint,
  DamageProfile,
  Element,
  OptimizeRequest,
  StuffType,
} from "./types";
import { StuffTypeSelector } from "./components/StuffTypeSelector";
import { ConstraintBuilder } from "./components/ConstraintBuilder";
import { BuildResult } from "./components/BuildResult";
import { buildShareUrl, readBuildFromHash } from "./share";

const shared = readBuildFromHash();

export default function App() {
  const [stuffType, setStuffType] = useState<StuffType>(shared?.stuff_type ?? "force");
  const [elements, setElements] = useState<Element[]>(
    shared?.elements?.length ? shared.elements : ["terre", "feu"],
  );
  const [level, setLevel] = useState(shared?.level ?? 200);
  const [damageProfile, setDamageProfile] = useState<DamageProfile>(
    shared?.damage_profile ?? "generique",
  );
  const [obtainableOnly, setObtainableOnly] = useState<boolean>(
    shared?.obtainable_only ?? true,
  );
  const [constraints, setConstraints] = useState<Constraint[]>(
    shared?.constraints ?? [
      { dim: "pa", op: ">=", value: 11 },
      { dim: "pm", op: ">=", value: 6 },
    ],
  );
  const [result, setResult] = useState<BuildResponse | null>(null);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runWith = async (req: OptimizeRequest) => {
    setLoading(true);
    setError(null);
    try {
      const res = await optimize(req);
      setResult(res);
      const url = buildShareUrl(req);
      setShareUrl(url);
      window.history.replaceState(null, "", url);
    } catch (e) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setLoading(false);
    }
  };

  const run = () =>
    runWith({
      stuff_type: stuffType,
      level,
      elements,
      damage_profile: damageProfile,
      constraints,
      obtainable_only: obtainableOnly,
      time_limit: 20,
    });

  // auto-run when the page is opened from a shared link
  useEffect(() => {
    if (shared) runWith(shared);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="app">
      <header className="app-header">
        <h1>Optimiseur de stuff Dofus</h1>
        <p className="subtitle">Le meilleur build prouvé sous vos contraintes.</p>
      </header>

      <div className="layout">
        <div className="controls">
          <StuffTypeSelector
            stuffType={stuffType}
            elements={elements}
            level={level}
            damageProfile={damageProfile}
            onStuffType={setStuffType}
            onElements={setElements}
            onLevel={setLevel}
            onDamageProfile={setDamageProfile}
          />
          <ConstraintBuilder constraints={constraints} onChange={setConstraints} />
          <label className="option-toggle" title="Ignore le matériel MJ / PNJ / non échangeable">
            <input
              type="checkbox"
              checked={obtainableOnly}
              onChange={(e) => setObtainableOnly(e.target.checked)}
            />
            Items obtenables uniquement
          </label>
          <button className="btn-solve" onClick={run} disabled={loading}>
            {loading ? "Calcul en cours…" : "Optimiser"}
          </button>
          {error && <p className="error">{error}</p>}
        </div>

        <main className="output">
          {loading && (
            <div className="loading">
              <div className="spinner" />
              <p>Résolution du modèle (CP-SAT)…</p>
            </div>
          )}
          {!loading && result && <BuildResult result={result} shareUrl={shareUrl} />}
          {!loading && !result && (
            <div className="placeholder">
              <p>Choisissez un type de stuff, ajoutez vos contraintes, puis lancez l'optimisation.</p>
            </div>
          )}
        </main>
      </div>

      <footer className="app-footer">
        Données issues de DofusDB / dofusdude (© Ankama). Utilisation soumise à la LPNC-IA 1.0 —
        projet personnel non commercial.
      </footer>
    </div>
  );
}
