# Icônes de stats Dofus (optionnel)

Dépose ici des PNG pour remplacer automatiquement les icônes SVG par défaut.
Aucune icône n'est fournie (ce sont des assets Ankama, non redistribués ici) :
c'est à toi d'ajouter les fichiers. Dès qu'un fichier est présent, il est utilisé
automatiquement (détection au build via `import.meta.glob`), sinon le SVG reste.

Nomme chaque fichier **exactement** comme ci-dessous (`.png`), taille conseillée
~24×24 px, fond transparent :

## Caractéristiques
`vitalite` · `sagesse` · `force` · `intelligence` · `chance` · `agilite`
· `puissance` · `pa` · `pm` · `po`

## Dégâts
`do_fixe` (Dommages) · `do_terre` · `do_feu` · `do_eau` · `do_air` · `do_neutre`
· `do_critiques` · `pct_do` · `pct_do_armes` · `pct_do_sorts` · `pct_do_melee`
· `pct_do_distance`

## Résistances (les rés. fixes et % partagent le même fichier)
`res_terre` · `res_feu` · `res_eau` · `res_air` · `res_neutre`

## Divers
`cc` (% Critique) · `prospection` · `initiative` · `invocations` · `do_soins`
· `tacle` · `fuite` · `pods` · `esquive_pa` · `esquive_pm` · `retrait_pa`
· `retrait_pm` · `nb_panoplies`

Exemple : `frontend/src/assets/icons/force.png` → l'icône Force réelle s'affiche
partout à la place de l'imitation SVG.
