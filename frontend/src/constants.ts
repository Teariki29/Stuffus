import type { DamageProfile, StuffType } from "./types";

// Stat dimensions exposed in the constraint builder, with French labels.
export const DIM_LABELS: Record<string, string> = {
  vitalite: "Vitalité",
  pa: "PA",
  pm: "PM",
  po: "Portée",
  force: "Force",
  intelligence: "Intelligence",
  chance: "Chance",
  agilite: "Agilité",
  sagesse: "Sagesse",
  puissance: "Puissance",
  do_fixe: "Dommages",
  do_terre: "Do. Terre",
  do_feu: "Do. Feu",
  do_eau: "Do. Eau",
  do_air: "Do. Air",
  do_neutre: "Do. Neutre",
  do_critiques: "Do. Critiques",
  cc: "% Critique",
  res_terre: "% Rés. Terre",
  res_feu: "% Rés. Feu",
  res_eau: "% Rés. Eau",
  res_air: "% Rés. Air",
  res_neutre: "% Rés. Neutre",
  pct_do: "% Dommages",
  pct_do_melee: "% Do Mêlée",
  pct_do_distance: "% Do Distance",
  pct_do_sorts: "% Do Sorts",
  pct_do_armes: "% Do Armes",
  res_fixe_terre: "Rés. Terre (fixe)",
  res_fixe_feu: "Rés. Feu (fixe)",
  res_fixe_eau: "Rés. Eau (fixe)",
  res_fixe_air: "Rés. Air (fixe)",
  res_fixe_neutre: "Rés. Neutre (fixe)",
  prospection: "Prospection",
  pods: "Pods",
  initiative: "Initiative",
  tacle: "Tacle",
  fuite: "Fuite",
  invocations: "Invocations",
  esquive_pa: "Esq. PA",
  esquive_pm: "Esq. PM",
  retrait_pa: "Ret. PA",
  retrait_pm: "Ret. PM",
  soins: "% Soins",
  do_soins: "Soins",
  nb_panoplies: "Bonus de panoplie",
};

// dims offered first in the dropdown (most common constraints)
export const COMMON_DIMS = [
  "pa",
  "pm",
  "vitalite",
  "po",
  "cc",
  "force",
  "intelligence",
  "chance",
  "agilite",
  "sagesse",
  "prospection",
];

export const ALL_DIMS = Object.keys(DIM_LABELS);

export const STUFF_TYPES: { value: StuffType; label: string; color: string }[] = [
  { value: "force", label: "Force", color: "#c0563a" },
  { value: "intel", label: "Intelligence", color: "#b14ec0" },
  { value: "chance", label: "Chance", color: "#3a7bc0" },
  { value: "agi", label: "Agilité", color: "#5aae54" },
  { value: "multi", label: "Multi-élément", color: "#c0a13a" },
  { value: "sagesse", label: "Sagesse", color: "#46b3a0" },
];

export const ELEMENTS: { value: "terre" | "feu" | "eau" | "air"; label: string }[] = [
  { value: "terre", label: "Terre" },
  { value: "feu", label: "Feu" },
  { value: "eau", label: "Eau" },
  { value: "air", label: "Air" },
];

export const DAMAGE_PROFILES: { value: DamageProfile; label: string; hint: string }[] = [
  { value: "generique", label: "Générique", hint: "Aucun % spécifique" },
  { value: "melee", label: "Mêlée", hint: "+ % Do Mêlée" },
  { value: "distance", label: "Distance", hint: "+ % Do Distance" },
  { value: "sorts", label: "Sorts", hint: "+ % Do Sorts" },
  { value: "armes", label: "Armes", hint: "+ % Do Armes" },
];

// display order for the equipment grid
export const SLOT_ORDER = [
  "amulette",
  "coiffe",
  "anneau",
  "cape",
  "ceinture",
  "bottes",
  "bouclier",
  "arme",
  "familier",
  "dofus",
  "trophee",
];

export const SLOT_LABELS: Record<string, string> = {
  amulette: "Amulette",
  coiffe: "Coiffe",
  anneau: "Anneau",
  cape: "Cape",
  ceinture: "Ceinture",
  bottes: "Bottes",
  bouclier: "Bouclier",
  arme: "Arme",
  familier: "Familier",
  dofus: "Dofus",
  trophee: "Trophée",
};

// Dofus element colours.
const EL = {
  terre: "#b5763a",
  feu: "#d35a5a",
  eau: "#4aa3d6",
  air: "#5aae54",
  neutre: "#c9ccd4",
};

// dim -> { icon name (see icons.tsx), color }
export const DIM_META: Record<string, { icon: string; color?: string }> = {
  vitalite: { icon: "heart", color: "var(--hp)" },
  pa: { icon: "star", color: "var(--ap)" },
  pm: { icon: "diamond", color: "var(--mp)" },
  po: { icon: "eye", color: "#7fb0c0" },
  prospection: { icon: "sparkle", color: "var(--accent)" },
  initiative: { icon: "bolt", color: "#d6c24a" },
  cc: { icon: "crosshair", color: "#d68a4a" },
  invocations: { icon: "skull", color: "#9a6fc0" },
  do_soins: { icon: "cross", color: "var(--hp)" },
  soins: { icon: "cross", color: "var(--hp)" },
  sagesse: { icon: "book", color: "var(--accent-2)" },
  force: { icon: "droplet", color: EL.terre },
  intelligence: { icon: "droplet", color: EL.feu },
  chance: { icon: "droplet", color: EL.eau },
  agilite: { icon: "droplet", color: EL.air },
  puissance: { icon: "burst", color: "var(--accent)" },
  do_fixe: { icon: "burst", color: "#c9ccd4" },
  do_terre: { icon: "droplet", color: EL.terre },
  do_feu: { icon: "droplet", color: EL.feu },
  do_eau: { icon: "droplet", color: EL.eau },
  do_air: { icon: "droplet", color: EL.air },
  do_neutre: { icon: "droplet", color: EL.neutre },
  do_critiques: { icon: "crosshair", color: "#d68a4a" },
  pct_do: { icon: "burst", color: "#c9ccd4" },
  pct_do_armes: { icon: "burst", color: "#c9ccd4" },
  pct_do_sorts: { icon: "burst", color: "#c9ccd4" },
  pct_do_melee: { icon: "fist", color: "#c9ccd4" },
  pct_do_distance: { icon: "arrows", color: "#c9ccd4" },
  res_terre: { icon: "shield", color: EL.terre },
  res_feu: { icon: "shield", color: EL.feu },
  res_eau: { icon: "shield", color: EL.eau },
  res_air: { icon: "shield", color: EL.air },
  res_neutre: { icon: "shield", color: EL.neutre },
  res_fixe_terre: { icon: "shield", color: EL.terre },
  res_fixe_feu: { icon: "shield", color: EL.feu },
  res_fixe_eau: { icon: "shield", color: EL.eau },
  res_fixe_air: { icon: "shield", color: EL.air },
  res_fixe_neutre: { icon: "shield", color: EL.neutre },
  fuite: { icon: "arrows", color: "#8a90a0" },
  tacle: { icon: "fist", color: "#8a90a0" },
  esquive_pa: { icon: "star", color: "#8a90a0" },
  esquive_pm: { icon: "diamond", color: "#8a90a0" },
  retrait_pa: { icon: "star", color: "#8a90a0" },
  retrait_pm: { icon: "diamond", color: "#8a90a0" },
  pods: { icon: "pods", color: "#a08a5a" },
};
