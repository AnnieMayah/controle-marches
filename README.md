# Backend — Contrôle a posteriori des marchés publics

API REST Flask + PostgreSQL (projet de soutenance L3, inspiré du processus réel de la
Commission Régionale des Marchés — Haute Matsiatra, Madagascar).

## Stack
Flask · SQLAlchemy · PostgreSQL · ReportLab (PDF) · python-docx + matplotlib (rapport Word)

## Installation
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```
1. Crée la base PostgreSQL, puis exécute `schema_postgresql.sql` (tables + référentiels).
2. Dans `app.py`, remplace `ton_mot_de_passe` dans `SQLALCHEMY_DATABASE_URI` par ton mot de passe PostgreSQL.
3. Lance le serveur : `python app.py` (API sur http://127.0.0.1:5000/api).

## Données de démonstration
```bash
python seed_demo.py
```
Crée des comptes, 5 entités, 12 marchés, 11 contrôles (validés / en cours / à démarrer),
des constats, des documents PDF d'exemple et des recommandations.
Le script s'arrête sans rien écraser si des utilisateurs existent déjà.

Pour repartir d'une base vide de tests (référentiels conservés), exécute avant le seed :
```sql
TRUNCATE recommandations, documents_irregularites, irregularites, controle_etapes, controles,
         documents, marches, prmp, utilisateurs, entites RESTART IDENTITY CASCADE;
```

| Identifiant | Mot de passe | Rôle |
|---|---|---|
| admin | admin123 | Administrateur |
| collecte | collecte123 | Assistant contrôleur |
| verif | verif123 | Contrôleur vérificateur |
| analyse | analyse123 | Membre / Chef de contrôle |
| pcnm | pcnm123 | PCNM (validation) |

## Structure
```
app.py            configuration + enregistrement des routes
models.py         modèles SQLAlchemy
services.py       logique métier : conformité, détection d'irrégularités (règles)
seed_demo.py      données de démonstration
routes/           marches, entites, controles, irregularites, documents, recommandations,
                  statistiques, rapports (PDF), auth, recherche, notifications, reference
```

## Règles métier
- Chaque étape est notée de 0 à 4 ; conformité si la moyenne est ≥ 2.
- Non conforme automatiquement : marché hors PPM, de régularisation, ou irrégularité impactant l'attribution.
- La validation exige que les 7 étapes soient notées ; un contrôle validé n'est plus modifiable.
- Les statistiques ne comptent que les contrôles validés.
- Module d'aide à la décision : règles explicites (`services.py::detecter_anomalies`), pas de machine learning.

## Limites connues
- Les droits par rôle sont appliqués dans l'interface ; l'API ne les impose pas encore (pas de JWT).
- Le journal d'audit détaillé (qui a modifié quoi) n'existe pas ; le fil de notifications est calculé à partir des données.

## Comptes, e-mails et mot de passe oublié
- **Créer un compte** (écran de connexion) : un code à 6 chiffres est envoyé par e-mail ; le compte est créé avec le rôle `INVITE` (lecture seule). L'administrateur attribue ensuite le bon rôle (Paramètres).
- **Mot de passe oublié** : code par e-mail (valable 10 min, 5 essais, usage unique, renvoi après 60 s), puis nouveau mot de passe.
- Mot de passe : 8 caractères minimum, avec une lettre et un chiffre.
- La table `codes_verification` se crée automatiquement au démarrage (voir aussi `migration_codes.sql`).

### Configurer l'envoi des e-mails
Édite `config_mail.py` (ou définis les variables d'environnement `SMTP_HOST`, `SMTP_PORT`, `SMTP_UTILISATEUR`, `SMTP_MOT_DE_PASSE`, `SMTP_SECURITE`).
Exemple Gmail : `smtp.gmail.com`, port `587`, `starttls`, avec un « mot de passe d'application » (validation en 2 étapes requise).
Tant que `SMTP_HOST` est vide : **mode développement**, aucun e-mail n'est envoyé et le code s'affiche dans la console de `python app.py`.
⚠ Ne partage jamais `config_mail.py` une fois rempli.

## Rapport global Word
`GET /api/rapports/global/docx?annee=2024&debut=2024-01-01&fin=2024-12-31&region=Haute Matsiatra`
Génère le rapport de tous les contrôles **validés** au format des rapports de la Commission (couverture, méthodologie, tableaux, camemberts,
histogrammes, irrégularités, recommandations, conclusion, annexes). Les passages à rédiger sont surlignés « [À compléter] ». Code : `rapport_word.py`.

## Détection automatique
`GET /api/marches/risques` : score de risque et anomalies par marché (règles de `services.py`). Affichée dans le menu « Détection automatique »,
dans l'onglet du même nom de chaque contrôle et sur le tableau de bord.
