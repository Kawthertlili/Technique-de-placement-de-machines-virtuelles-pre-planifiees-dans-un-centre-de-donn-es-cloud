
#  TECHNIQUE DE PLACEMENT DE MACHINES VIRTUELLES PRÉ-PLANIFIÉES  
## Optimisation basée sur l’algorithme de Recherche Taboue

Ce projet implémente une méthode d’optimisation destinée à améliorer le **placement de machines virtuelles (VMs)** dans un **centre de données cloud**, en tenant compte des capacités limitées des **machines physiques (PMs)** et des contraintes temporelles (arrival/departure).  
Il s’inscrit dans le cadre du Projet de Fin d’Année intitulé :

> **« TECHNIQUE DE PLACEMENT DE MACHINES VIRTUELLES PRÉ-PLANIFIÉES DANS UN CENTRE DE DONNÉES CLOUD »**

La solution repose sur l’algorithme **Tabu Search**, une métaheuristique puissante permettant :

- d’explorer un grand espace de solutions,  
- d’éviter les minima locaux grâce à la **liste taboue**,  
- et de maximiser le **nombre de machines virtuelles placées**.

Le projet comprend :  
✔️ un moteur d’optimisation complet (Python)  
✔️ une interface graphique interactive (Tkinter)  
✔️ des visualisations avancées (Matplotlib)  
✔️ un module de génération/chargement de scénarios

##  Contexte et Motivation

Comme expliqué dans le rapport (pages 8–14) ✦, les datacenters cloud affrontent des défis clés :

- utilisation inefficace des ressources,  
- surcharge ou sous-utilisation des serveurs,  
- fragmentation CPU/RAM/stockage,  
- augmentation de la consommation énergétique.


##  Objectifs

- Maximiser le nombre total de VMs placées.  
- Réduire le taux de rejet des VMs non allouables.  
- Maintenir un équilibre d'utilisation des ressources.  
- Respecter les contraintes CPU / RAM / stockage / temporalité.  
- Permettre une simulation multi-scénarios configurable.  
- Offrir une interface utilisateur intuitive.  



##  Approche Adoptée : Recherche Taboue
- exploration du **voisinage** d’une solution,
- interdiction temporaire de certaines solutions via la **liste taboue**,  
- acceptation exceptionnelle via **critère d’aspiration**,  
- équilibre entre **exploration** et **exploitation**.

Ses avantages :

- évite les minima locaux,  
- efficace pour les grandes instances,  
- flexible et robuste,  
- idéal pour le placement VM/PM multi-contraintes.

##  Fonctionnalités Principales

### 🔹 Génération Automatique de Scénarios
- Création réaliste de PMs (CPU, RAM, Stockage).  
- Génération de VMs avec intervalles temporels et demandes variées.  
- Sauvegarde automatique (`machines_physiques.txt`, `machines_virtuelles_X.txt`).

### 🔹 Optimisation via Tabu Search
- Placement initial basé sur l’ordre temporel.  
- Recherche itérative des solutions voisines.  
- Gestion de la liste taboue.  
- Calcul dynamique du taux de rejet et de l’utilisation des ressources.

### 🔹 Visualisation Graphique des Résultats
- CPU utilisé (%)  
- RAM utilisée (%)  
- Stockage utilisé (%)  
- Nombre de VMs / PM  
- Taux de rejet par scénario

Ces visualisations correspondent aux figures du rapport (Figures 3.4 → 3.12) ✦.

### 🔹 Interface Graphique Tkinter
Vue similaire à la Figure 3.1 du rapport ✦ :

- champs de paramètres,  
- bouton *“Générer et Calculer”*,  
- bouton *“Charger scénarios existants”*,  
- zone de résultats,  
- affichage instantané des graphiques.

## Architecture du Projet

###  Fichier principal
`Optimisation_TB.py` — regroupe :

- génération de PMs/VMs  
- placement initial  
- algorithme Tabu Search  
- calcul d’utilisation  
- affichages graphiques  
- interface Tkinter

###  Structure Simplifiée

```text
/
├─ Optimisation_TB.py
├─ README.md
├─ (fichiers générés automatiquement)scenarios_timestamp/
│   ├─ machines_physiques.txt
│   ├─ machines_virtuelles_1.txt
│   ├─ machines_virtuelles_2.txt
│   └─ ...
 






