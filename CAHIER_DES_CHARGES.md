# Développe un ERP complet de gestion des chutes de verre

Tu es un développeur Full Stack Senior spécialisé en Django, Django REST Framework, PostgreSQL, HTML, CSS, JavaScript et Bootstrap.

Ta mission est de développer un ERP professionnel destiné à une entreprise de vitrerie. Le projet doit être entièrement fonctionnel, maintenable, documenté et prêt à évoluer.

## Technologies imposées

### Backend

* Python 
* Django
* SQLite 


### Frontend

* Django Templates
* Bootstrap 5
* JavaScript (sans framework)
* AJAX avec Fetch API

Le projet doit fonctionner entièrement en local.

---

# Objectif principal

L'objectif est de gérer les panneaux de verre et toutes les chutes générées après chaque découpe.

Lorsqu'un panneau est découpé, le système doit créer automatiquement les chutes restantes.

Chaque chute doit être enregistrée.

Chaque chute doit posséder un emplacement précis.

Lorsqu'un utilisateur recherche une dimension, le système doit retrouver automatiquement les meilleures chutes disponibles.

Le logiciel doit toujours proposer l'utilisation d'une chute avant d'utiliser un panneau neuf.

---

# Architecture Django

Créer les applications suivantes :

accounts

types_verres

emplacements

panneaux

chutes

decoupes

mouvements

commandes

dashboard

impression

---

# Module Types de verre

Créer les modèles :

TypeVerre

* designation

Epaisseur

* valeur

Teinte

* designation

Finition

* designation

Chaque panneau ou chute sera relié à ces informations.

---

# Module Emplacements

Créer une gestion complète des rangements.

Exemple

Chariot A

Niveau 1

Case 3

Le modèle doit contenir :

id

code

chariot

niveau

case

description

actif

Chaque emplacement doit être unique.

---

# Module Panneaux

Créer le modèle :

Panneau

id

reference

longueur

largeur

surface

type_verre

epaisseur

teinte

finition

date_entree

prix

statut

Le calcul de la surface doit être automatique.

---

# Module Chutes

Créer le modèle :

Chute

numero

longueur

largeur

surface

type_verre

epaisseur

teinte

finition

emplacement

date_creation

origine

etat


La surface doit être calculée automatiquement.



---

# Module Découpe

Créer un écran permettant de sélectionner un panneau.

Exemple :

Panneau

3660 x 2140

L'utilisateur saisit une ou plusieurs découpes.

Exemple

1800 x 900

1500 x 600

etc.

Le logiciel doit calculer automatiquement :

les morceaux utilisés

les morceaux restants

les nouvelles chutes

Chaque chute restante est enregistrée automatiquement.

---

# Algorithme de découpe

Créer un moteur de calcul.

Entrée :

Longueur panneau

Largeur panneau

Liste des découpes

Sortie :

Découpes réalisées

Dimensions restantes

Création automatique des chutes

Ne jamais créer une chute dont :

largeur < 100 mm

ou

longueur < 100 mm

Ces morceaux doivent être considérés comme des déchets.

L'algorithme doit limiter les pertes.

---

# Utilisation des chutes

Avant de découper un panneau neuf, rechercher automatiquement dans les chutes.

Exemple :

Demande :

1200 x 800

Le système doit rechercher une chute compatible.

Si une chute est trouvée :

la proposer

mettre à jour ses dimensions après découpe

supprimer l'ancienne chute

créer automatiquement les nouvelles chutes restantes

Si aucune chute ne convient :

utiliser un panneau neuf.

---

# Recherche intelligente

Créer un moteur de recherche.

Recherche par :

longueur

largeur

surface

type

épaisseur

teinte

finition

emplacement

Le résultat doit être classé par la plus petite perte de matière.

---

# Gestion des mouvements

Créer un historique complet.

Entrée panneau

Création chute

Modification chute

Utilisation chute

Suppression chute

Chaque mouvement doit enregistrer :

date

utilisateur

action

objet

commentaire

---

# Dashboard

Créer un tableau de bord moderne.

Afficher :

Nombre de panneaux

Nombre de chutes

Surface totale

Surface utilisée

Surface restante

Valeur du stock

Nombre de découpes

Nombre de chutes utilisées

Graphiques Bootstrap.

---

# Impression

Créer une impression PDF.

Pour chaque chute afficher :


Numéro

Dimensions

Surface

Type

Épaisseur

Teinte

Finition

Emplacement

---

# Sécurité

Créer plusieurs rôles :

Administrateur

Magasinier

Découpeur

Consultation

Chaque rôle possède des permissions différentes.

---

# Interface

Créer une interface moderne.

Menu latéral.

Tableaux Bootstrap.

Recherche instantanée.

Pagination.

Tri.

Filtres.

Messages de confirmation.

Validation des formulaires.

---

# API REST

Créer une API complète.

CRUD pour tous les modules.

Utiliser ViewSets.

Utiliser Serializers.

Utiliser Router.

---

# Qualité du code

Respecter les principes SOLID.

Utiliser les services lorsque nécessaire.

Documenter chaque classe.

Utiliser les type hints.

Créer des tests unitaires.

Créer des fixtures de démonstration.

Ne jamais écrire de code dupliqué.

---





---

# Développement

Ne génère pas uniquement la structure.

Développe entièrement le projet.

Crée tous les modèles.

Crée toutes les vues.

Crée toutes les URL.

Crée tous les templates.

Crée tous les formulaires.

Crée les services métiers.

Crée les tests.

Crée les fichiers statiques.

Crée les migrations.

Le projet doit pouvoir être lancé directement après :

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver ss

Le code doit être organisé, professionnel, documenté et prêt pour une utilisation réelle dans une entreprise de vitrerie.
