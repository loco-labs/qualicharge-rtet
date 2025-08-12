# Analyse des IRVE du RTE-T

## Présentation

Ce repository présente plusieurs fonctions :

- Génération d'un graphe du réseau RTE-T (directionnel et non directionnel)
- Affectation des stations aux aires de service, échangeurs et rond-points du réseau
- Analyse des distance minimales entre stations et parcs du réseau RTE-T (règlementation AFIR)
- Analyse de la saturation des stations 

## Génération du réseau RTE-T

Le réseau intégrant les aires de service, échangeurs et rond-points est créé à partir :

- réseau RTE-T : 'roads_GL2017_Council_FR'
- aires de service : 'aire_de_services' et 'echangeurs_aires' (issus de l'ASFA et de BD CARTO)
- échangeurs et rond-points : 'noeuds_ech' et 'noeuds_rp' (issus de Route 500)

Il est stocké sous la forme de deux fichiers geojson (noeuds et tronçons)

## Réseau AFIR

Le réseau AFIR est le réseau RTET auquel on ajoute les stations IRVE situées a proximité du réseau (données issues de Qualicharge). 

Pour chaque station, on ajoute:

- un noeud (nature : 'station_IRVE') correspondant à la station avec les attributs suivants :
  - p_cum: puissance de la station (puissance cumulée des points de recharge)
  - p_max: puissance maximale des points de recharge
- un tronçon (nature : 'liaison aire de service' ou 'liaison aire de recharge' ou 'liaison exterieur') correspondant à la liaison entre la station et le noeud du réseau associé

Dans quelques cas, on complète le réseau RTET avec un noeud supplémentaire lorsqu'aucun noeud est suffisamment proche de la station (nature : 'aire de recharge')

Le réseau construit est stocké sous la forme de deux fichiers GeoPandas (geojson) ainsi que d'un fichier pandas contenant les liens entre stations et parcs.

## Analyse de la saturation

La saturation des stations et parcs est analysée à partir de :

- stations et points de recharge issues de Qualicharge,
- sessions et statuts issus du stockage S3 de Qualicharge
- liens entre stations et parcs issus du réseau AFIR
- réseau AFIR

Elle est restituée sous la forme d'un fichier regroupant les temps passés dans chaque état pour les stations et parcs ainsi que par des représentation géographiques.
