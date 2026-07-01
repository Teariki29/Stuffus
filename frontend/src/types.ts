export type StuffType = "force" | "intel" | "chance" | "agi" | "multi" | "sagesse";
export type Element = "terre" | "feu" | "eau" | "air";
export type Operator = ">=" | "<=" | ">" | "<" | "==" | "!=";
export type DamageProfile = "generique" | "melee" | "distance" | "sorts" | "armes";

export interface Constraint {
  dim: string;
  op: Operator;
  value: number;
}

export interface OptimizeRequest {
  stuff_type: StuffType;
  level: number;
  elements: Element[];
  damage_profile?: DamageProfile;
  constraints: Constraint[];
  tiebreak_weights?: Record<string, number>;
  allocate_points?: boolean;
  obtainable_only?: boolean;
  time_limit?: number;
}

export interface ConditionNode {
  op: "and" | "or" | "cmp" | "true";
  dim?: string;
  operator?: string;
  value?: number;
  code?: string | null;
  children?: ConditionNode[];
}

export interface ResultItem {
  id: number;
  name: string;
  slot: string;
  type_name?: string | null;
  level: number;
  set_id?: number | null;
  img_url?: string | null;
  stats: Record<string, number>;
  conditions?: ConditionNode | null;
}

export interface ActiveSet {
  set_id: number;
  name: string;
  pieces: number;
  bonus: Record<string, number>;
}

export interface Kpi {
  damage_normal?: number | null;
  damage_crit?: number | null;
  cc: number;
  resistances: Record<string, number>;
}

export interface BuildResponse {
  status: string;
  optimality_gap: number;
  items: ResultItem[];
  point_allocation: Record<string, number>;
  totals: Record<string, number>;
  kpi: Kpi;
  active_sets: ActiveSet[];
  message?: string | null;
}
