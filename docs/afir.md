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

### Exigences TRE-T central

- parc déployé dans chaque sens
- 60 km mini entre chaque parc proche du réseau RTE-T avec
- 31/12/2025: 400 kW par parc et un point de recharge à plus de 150 kW 
- 31/12/2027: 600 kW par parc et deux points de recharge à plus de 150 kW

### Exigences TRE-T global

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
 Un tronçon entre station étant constitué d'un ensemble de tronçons routiers, il convient de décliner l'exigence de distance entre stations au niveau des tronçons routiers. 

Pour un réseau linéaire, cette exigence peut être transposée aux tronçons routiers de la façon directe :

- un tronçon routier est valide si le trajet entre les stations les plus proches de chaque extrémité du tonçon respecte l'exigence de distance

Pour un réseau maillé, la transposition est moins directe compte tenu du partage des tronçons routiers entre plusieurs tronçons entre stations. 

Par exemple, si l'on considère un réseau en étoile de trois stations A, B et C situées chacune à 50 km (A), 5 km (B) et 30 km (C) du centre de l'étoile, 
la distance entre stations est de :

- A-B : 55 km
- A-C : 80 km
- B-C : 35 km

Deux interprétations de l'exigence de distance entre stations sont alors possibles :

- option 1 : Chaque tronçon routier appartient à au moins un tronçon entre stations inférieur à 60 km, il peut alors être considéré comme valide,
- option 2 : Le tronçon entre A et le centre de l'étoile induit au moins un tronçon entre stations non valide (A-C), il peut alors être considéré comme non valide. 
C'est également le cas du tronçon entre C et le centre de l'étoile. 

Si maintenant la distance de B au centre de l'étoile est de 20 km, les distances entre stations deviennent :

- A-B : 70 km
- A-C : 80 km
- B-C : 50 km

Dans ce cas, l'application des deux options donne les résultats suivants :

- option 1 : Les tronçons qui composent le tronçon B-C sont valides, le tronçon de A au centre de l'étoile ne l'est pas
'appartient à aucun tronçon entre stations inférieur à 60 km. Pour les deux options,  et si on enlève ce tronçon, on a bien un réseau valide.

On peut donc décliner la règle d'une distance à respecter entre stations de deux façons :

- un tronçon routier est valide si tous les trajets entre les stations les plus proches qui incluent ce tronçon routier sont valides
- un tronçon routier est valide si au moins un trajet entre deux stations qui inclut ce tronçon routier est valide
