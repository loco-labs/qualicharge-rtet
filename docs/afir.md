# Règlement AFIR

JO EU 2023/1804
concerne le RTE-T central et global ainsi que les véhicules légers et lourds

## Stations et parcs

Point de recharge : une interface fixe ou mobile, sur réseau ou hors réseau, qui permet de transférer de l’électricité vers un véhicule électrique et qui, bien qu’elle puisse être équipée d’un ou de plusieurs connecteurs pour prendre en charge différents types de connecteurs, n’est capable de recharger qu’un seul véhicule électrique à la fois,

Station : une installation physique en un lieu spécifique, composée d’un ou de plusieurs points de recharge

Parc : une ou plusieurs stations de recharge en un lieu spécifique

Puissance mini des points de recharge: 1,3 kW
Station proche du réseau RTE-T : Station à moins de 3 km d'une sortie

## Ratio réseau

RATIO = NUMERATEUR / DENOMINATEUR avec

NUMERATEUR : somme des longueurs des tronçons entre deux parcs répondant aux critères
DENOMINATEUR : longueur totale du réseau concerné

## Règlementation véhicules légers

### Exigences RTE-T central

- parc déployé dans chaque sens
- 60 km mini entre chaque parc proche du réseau RTE-T avec
- 31/12/2025: 400 kW par parc et un point de recharge à plus de 150 kW 
- 31/12/2027: 600 kW par parc et deux points de recharge à plus de 150 kW

### Exigences RTE-T global

- parc déployé dans chaque sens
- 60 km mini entre chaque parc proche du réseau RTE-T
- 31/12/2027: sur 50% du réseau, 300 kW par parc et un point de recharge à plus de 150 kW 
- 31/12/2030: idem mais pour 100 %
- 31/12/2035: 600 kW par parc et deux points de recharge à plus de 150 kW

### Dérogations VL

- trafic < 8 500 VL/j (parc desservant les deux sens, réduction de puissance)
- trafic < 3 000 VL/j (extension à 100 km)

## Règlementation véhicules lourds

### Exigences PL

- parc déployé dans chaque sens
- 31/12/2025
  - 120 km mini entre chaque parc proche du réseau RTE-T
  - sur 15% du réseau 1 400 kW par parc et un point de recharge à plus de 350 kW 
- 31/12/2027
  - 120 km mini entre chaque parc proche du réseau RTE-T avec sur 50% du réseau
  - RTE-T central : 2 800 kW par parc et un point de recharge à plus de 350 kW 
  - RTE-T global : 1 400 kW par parc et un point de recharge à plus de 350 kW 
- 31/12/2030: RTE-T central
  - 60 km mini entre chaque parc proche du réseau RTE-T
  - 3 600 kW par parc et deux points de recharge à plus de 350 kW 
- 31/12/2030: RTE-T global
  - 100 km mini entre chaque parc proche du réseau RTE-T
  - 1 500 kW par parc et un point de recharge à plus de 350 kW 
- 31/12/2027: Aires de stationnement
  - deux stations à plus de 100 kW
- 31/12/2030: Aires de stationnement
  - quatre stations à plus de 100 kW
- 31/12/2025: Noeuds urbains
  - parc d'au moins 900 kW à plus de 150 kW
- 31/12/2030: Noeuds urbains
  - parc d'au moins 1 800 kW à plus de 150 kW

### Dérogations PL

- trafic < 2 000 VL/j (parc desservant les deux sens, réduction de puissance)
- trafic < 800 VL/j (extension de 60 km à 100 km)

## Distance entre stations

La règlementation s'appuie sur la longueur des tronçons entre stations mais d'un autre coté, elle se mesure par un ratio de longueur de tronçons routiers.
Un tronçon entre stations étant constitué d'un ensemble de tronçons routiers, il convient de décliner l'exigence de distance entre stations au niveau des tronçons routiers.

Pour un réseau linéaire, cette exigence peut être transposée aux tronçons routiers de façon directe :

- un tronçon routier est valide si la distance entre les stations les plus proches de chaque extrémité du tonçon respecte l'exigence de distance

Pour un réseau maillé, la transposition est moins directe compte tenu du partage des tronçons routiers entre plusieurs trajets entre stations.

### Exemple 1

Par exemple, si l'on considère un réseau en étoile de trois stations A, B et C situées chacune à 50 km (A), 5 km (B) et 30 km (C) du centre de l'étoile, la distance entre stations serait de :

- A-B : 55 km
- A-C : 80 km
- B-C : 35 km

Deux interprétations de l'exigence de distance entre stations sont alors possibles :

- option 1 : Comme chaque tronçon routier appartient à au moins un tronçon entre stations inférieur à 60 km, on peut alors considérer que l'exigence est respectée pour tous les tronçonc routiers.
- option 2 : La distance entre A et C ne respecte pas la distance de 60 km, on peut dans ce cas considérer que les deux tronçons routiers qui constituent le trajet A-C sont non valides.

### Exemple 2

Si maintenant la distance de B au centre de l'étoile est de 20 km, les distances entre stations deviennent :

- A-B : 70 km
- A-C : 80 km
- B-C : 50 km

Dans ce cas, l'application des deux options donne les résultats suivants :

- option 1 : Les tronçons qui composent le tronçon B-C sont valides puisqu'ils permettent de respecter une distance interstations de 60km, ce qui n'est pas le cas pour le tronçon de A au centre de l'étoile
- option 2 : Les distance A-C et A-B ne repectent pas l'exigence de distance, on peut alors considérer que les tronçons routiers qui les composent (c'est à dire tous les tronçons) ne sont pas valides.

### Analyse

En s'appuyant sur les exemples précédents, on peut donc décliner la règle d'une distance à respecter entre stations de deux façons :

- option 1 : un tronçon routier est valide s'il appartient à au moins un trajet valide entre deux stations
- option 2 : un tronçon routier est valide si tous les trajets entre les stations les plus proches qui incluent ce tronçon routier sont valides

Dans l'exemple 1, on peut remarquer que pour effectuer le trajet A-C, on peut effectuer d'abord A-B puis B-C qui respectent tous les deux l'exigence de distance (ce qui appuierait l'option 1).
Dans l'exemple 2, on peut remarquer également que si l'on enlève le tronçon entre A et le centre de l'étoile, le réseau qui ne contient plus que B et C est valide (ce qui contredirait l'option 2).
On peut aussi préciser que l'option 2 est plus difficile à évaluer et cache peut-être des incohérences.

La proposition qui serait à retenir est donc de retenir l'option 1.

## Implémentation

Plusieurs approches sont possibles pour évaluer l'option 1:

- approche par tronçon :

  Pour chaque tronçon, on calcule pour chaque extrémité la distance de la station la plus proche. Si la somme de la longueur du tronçon et des deux distances est inférieure au seuil, le tronçon est valide.
  Cette méthode est simple et nécessite un calcul de distance minimale pour chaque noeud du réseau (fonctions `ego_graph` et `shortest_path_length` de NetworkX).

- approche par noeud :

  Pour chaque noeud, on recherche tous les trajets valides. Les tronçons associés à ces trajets sont alors validés.
  Cette méthode nécessite d'explorer pour chaque noeud l'arbre des noeuds situés à moins de 60 km (fonction spécifique ou bien combinaison des fonctions `ego_graph` et `shortest_path_length` de NetworkX).

Nota: L'approche par tronçon permet de traiter simplement des distances maximales différentes entre RTE-T central (ex.60 km) et global (ex. 100 km).
