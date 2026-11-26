"""
Réinitialise la base PostgreSQL du projet « contrôle des marchés publics »
et recrée : comptes réels (organigramme CRM Haute-Matsiatra) + 25 marchés de démo.

Usage (PowerShell) :
    pip install psycopg2-binary werkzeug
    $env:DATABASE_URL = "postgresql://postgres:MOTDEPASSE@localhost:5432/NOM_BD"
    python reset_seed.py
    (ajouter --yes pour ne pas demander de confirmation)

Données conservées (références) : etapes, types_document, natures_marche,
modes_passation, objets_marche, entites 1-5, prmp 1-5.
"""
import os
import random
import sys
import unicodedata
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

MOT_DE_PASSE_INITIAL = os.environ.get("SEED_PASSWORD", "Crm@2026")
CREER_COMPTE_DEV = True          # compte « annie » (ADMIN) pour tes tests ; mets False pour l'omettre
EMAIL_DEV = "andrimamonjyannie@gmail.com"

SERVICES = {"A": "Service de Contrôle A", "B": "Service de Contrôle B", "C": "Service de Contrôle C"}

# (nom, prénom, rôle, service, titre affiché sur l'organigramme)
PERSONNEL = [
    ("RAMILSON", "Z. Amédé", "ADMIN", None, "Directeur / Chef de Commission"),
    ("ANDRIANANTENAINA", "Harimisa J.", "CHEF_SERVICE", "A", "Chef de Service du Contrôle A - Membre de Commission"),
    ("RAKOTONDRAINY", "J. Frédéric", "CHEF_SERVICE", "B", "Chef de Service du Contrôle B - Membre de Commission"),
    ("BEZAKA", "Jessy Loréno", "CHEF_SERVICE", "C", "Chef de Service du Contrôle C - Membre de Commission"),
    ("RAKOTOSALAMA", "Lovasoa N. O.", "CV", "A", "Contrôleur Vérificateur (Suppléant)"),
    ("ANDRIANOELINA", "Voahangimbolana H.", "CV", "B", "Contrôleur Vérificateur (Suppléant)"),
    ("RASOLONJATOVO", "H. Patrick", "CV", "C", "Contrôleur Vérificateur"),
    ("HAJANANTENAINA", "Doudou Stanislas", "ACV", "A", "Assistant Contrôleur Vérificateur"),
    ("LAHIFINDAY", "Adoré Wilform", "ACV", "B", "Assistant Contrôleur Vérificateur"),
    ("ANDRIAHARIJAONA", "Léa Sahondra", "ACV", "C", "Assistant Contrôleur Vérificateur"),
    ("RAKOTOMALALA", "Haingosoa Lova", "INVITE", None, "Responsable des Affaires Générales (RAG)"),
    ("RABENANDRAISANA", "Miora T.", "INVITE", None, "Assistante RAG"),
    ("RANDRIATSALAMA", "Harifetra", "INVITE", None, "Accueil et réception des dossiers"),
]

TITULAIRES = [
    "Tech Madagascar SARL", "Entreprise Fitiavana BTP", "Mobilier Plus", "Vatomandry Construction",
    "Station Jovenna Fianarantsoa", "Cabinet Ravinala Conseil", "AgriMad", "Pharma Distribution Sud",
    "BioMed Océan Indien", "ElectroServ", "PostalTech", "Papeterie Centrale", "Imprimerie Tsiry",
    "Garage Antsirabe Auto", "SOMACO Services", "Matsiatra Fournitures", "BTP Haute Terre",
    "Info Concept", "Pharmacie Centrale FNR", "Transports Betsileo", "Atelier Mandroso",
    "Optima Bureautique", "Rova Construction", "Sanitas Distribution", "Hery Logistique",
]


def sans_accent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def construire_donnees():
    """Retourne (utilisateurs, marches). Pur Python, testable sans base."""
    rnd = random.Random(2026)
    utilisateurs = []
    for nom, prenom, role, svc, titre in PERSONNEL:
        utilisateurs.append(dict(login=sans_accent(nom).lower(), nom=nom, prenom=prenom, role=role, svc=svc, titre=titre))
    if CREER_COMPTE_DEV:
        utilisateurs.append(dict(login="annie", nom="ANDRIMAMONJY", prenom="Haingoniaina Annie", role="ADMIN",
                                 svc=None, titre="Compte développeur", email=EMAIL_DEV))

    # Plan des 25 marchés : par service 3 chez le CV + 4 chez le chef ; 4 au niveau du CC
    plan = []
    for svc in "ABC":
        plan += [(svc, "demarrer"), (svc, "encours"), (svc, "termine")]
        plan += [(svc, "chef")] * 4
    plan += [(None, "cc")] * 4
    rnd.shuffle(plan)  # mélange l'ordre de création (les références restent uniques)

    notes_termine = {"A": [3, 3, 2, 3, 4, 3, 3], "B": [2, 1, 2, 1, 2, 2, 1], "C": [3, 2, 3, 3, 2, 4, 3]}
    notes_encours = {"A": [3, 2, 3], "B": [2, 3, 2], "C": [3, 3, 1]}
    titulaires = TITULAIRES[:]
    rnd.shuffle(titulaires)

    marches = []
    for i, (svc, etat) in enumerate(plan, start=1):
        ent = rnd.randint(1, 5)
        m = dict(
            reference=f"M-{i:03d}/26", id_entite=ent, id_prmp=ent, id_nature=rnd.randint(1, 4),
            id_mode=rnd.randint(1, 6), montant=rnd.randrange(2_000_000, 250_000_000, 50_000),
            titulaire=titulaires[i - 1], id_objet=rnd.randint(1, 6), numero_saisie=f"2026-{i:03d}",
            svc=svc, etat=etat,
            date_creation=datetime(2026, 11, 3) + timedelta(days=i % 20, hours=8 + i % 6),
        )
        if etat in ("demarrer", "encours", "termine"):  # infos remplies par le CV
            m.update(
                date_signature=date(2026, 10, 1) + timedelta(days=i), date_approbation=date(2026, 10, 6) + timedelta(days=i),
                date_notification=date(2026, 10, 10) + timedelta(days=i),
                direction_service=rnd.choice(["Service Administratif et Financier", "Service Technique",
                                              "Service Logistique", "Direction Commerciale"]),
                forme_contrat=rnd.choice(["QUANTITE_FIXE", "COMMANDES"]),
                forme_prix=rnd.choice(["UNITAIRE", "FORFAITAIRE"]),
                delai_execution=rnd.choice(["30 jours", "60 jours", "3 mois", "6 mois"]),
                financement=rnd.choice(["Budget de l'État", "Ressources propres", "Budget de la Région"]),
            )
            m["montant_tef"] = m["montant"]
            m["notes"] = notes_termine[svc] if etat == "termine" else notes_encours[svc] if etat == "encours" else []
        marches.append(m)
    return utilisateurs, marches


def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        sys.exit("Définis DATABASE_URL (postgresql://user:mdp@hote:5432/base)")
    if "--yes" not in sys.argv and input("Toutes les données seront SUPPRIMÉES. Tape OUI : ") != "OUI":
        sys.exit("Annulé.")
    import psycopg2

    utilisateurs, marches = construire_donnees()
    h = generate_password_hash(MOT_DE_PASSE_INITIAL)  # même mot de passe initial pour tous
    conn = psycopg2.connect(url)
    try:
        with conn, conn.cursor() as cur:
            # 1) Vidage
            cur.execute("""TRUNCATE codes_verification, controle_etapes, controles, documents,
                documents_irregularites, irregularites, marches, recommandations, transferts,
                observation_type, utilisateurs RESTART IDENTITY CASCADE""")
            cur.execute("DELETE FROM prmp WHERE id > 5")
            cur.execute("DELETE FROM entites WHERE id > 5")
            cur.execute("SELECT setval('public.entites_id_seq', 5, true)")
            cur.execute("SELECT setval('public.prmp_id_seq', 5, true)")

            # 2) Services
            for k, nom in zip("ABC", SERVICES.values()):
                cur.execute("UPDATE services SET nom=%s WHERE id=%s", (nom, "ABC".index(k) + 1))
            cur.execute("SELECT setval('public.services_id_seq', 3, true)")
            svc_id = {"A": 1, "B": 2, "C": 3}

            # 3) Comptes
            uid = {}
            for u in utilisateurs:
                cur.execute(
                    """INSERT INTO utilisateurs (nom, prenom, email, login, mot_de_passe_hash, role, id_service)
                       VALUES (%s,%s,%s,%s,%s,%s::role_utilisateur,%s) RETURNING id""",
                    (u["nom"], u["prenom"], u.get("email"), u["login"], h, u["role"], svc_id.get(u["svc"])))
                uid[u["login"]] = cur.fetchone()[0]
            directeur = uid["ramilson"]
            chef = {s: next(uid[u["login"]] for u in utilisateurs if u["role"] == "CHEF_SERVICE" and u["svc"] == s) for s in "ABC"}
            cv = {s: next(uid[u["login"]] for u in utilisateurs if u["role"] == "CV" and u["svc"] == s) for s in "ABC"}

            # 4) Marchés + contrôles
            for m in marches:
                cur.execute(
                    """INSERT INTO marches (reference, objet, id_entite, id_prmp, id_nature, id_mode_passation, montant,
                         titulaire, date_signature, date_approbation, date_notification, annee_exercice, id_utilisateur_saisie,
                         date_creation, id_objet, numero_saisie, direction_service, forme_contrat, forme_prix, montant_tef,
                         delai_execution, financement, statut_controle)
                       VALUES (%s,(SELECT libelle FROM objets_marche WHERE id=%s),%s,%s,%s,%s,%s,%s,%s,%s,%s,2026,%s,%s,%s,%s,
                               %s,%s,%s,%s,%s,%s,%s) RETURNING id""",
                    (m["reference"], m["id_objet"], m["id_entite"], m["id_prmp"], m["id_nature"], m["id_mode"], m["montant"],
                     m["titulaire"], m.get("date_signature"), m.get("date_approbation"), m.get("date_notification"),
                     directeur, m["date_creation"], m["id_objet"], m["numero_saisie"], m.get("direction_service"),
                     m.get("forme_contrat"), m.get("forme_prix"), m.get("montant_tef"), m.get("delai_execution"),
                     m.get("financement"), "A_CONTROLER" if m["etat"] == "cc" else "ENVOYE"))
                id_marche = cur.fetchone()[0]
                if m["etat"] == "cc":
                    continue  # pas encore à contrôler : aucun contrôle créé

                s = m["svc"]
                envoi = m["date_creation"] + timedelta(days=1)
                assigne = None if m["etat"] == "chef" else cv[s]
                notes = m.get("notes", [])
                termine = m["etat"] == "termine"
                glob = round(sum(notes) / 7, 2) if termine else None
                concl = ("CONFORME" if glob > 2 else "NON_CONFORME") if termine else "EN_COURS"
                cur.execute(
                    """INSERT INTO controles (id_marche, date_controle, note_globale, conclusion, id_utilisateur_validateur,
                         date_validation, id_service, id_utilisateur_assigne, date_envoi)
                       VALUES (%s,%s,%s,%s::conclusion_controle,%s,%s,%s,%s,%s) RETURNING id""",
                    (id_marche, envoi.date(), glob, concl, chef[s] if termine else None,
                     envoi + timedelta(days=6) if termine else None, svc_id[s], assigne, envoi))
                id_ctrl = cur.fetchone()[0]
                for n, note in enumerate(notes, start=1):
                    cur.execute(
                        """INSERT INTO controle_etapes (id_controle, id_etape, note, observations, id_utilisateur, date_saisie)
                           VALUES (%s,%s,%s,'',%s,%s) RETURNING id""",
                        (id_ctrl, n, note, cv[s], envoi + timedelta(days=n // 2, hours=n)))
                    id_ce = cur.fetchone()[0]
                    if note <= 1:  # constat pour les étapes très mal notées
                        cur.execute(
                            """INSERT INTO irregularites (id_controle_etape, description, texte_applicable, risque,
                                 recommandation, impacte_attribution)
                               VALUES (%s,%s,%s,%s,%s,%s)""",
                            (id_ce, "Pièce essentielle manquante ou non conforme au dossier.",
                             "Code des marchés publics (Loi n°2016-055)", "Moyen",
                             "Régulariser le dossier et transmettre les pièces manquantes.", False))
        print(f"OK : {len(utilisateurs)} comptes, {len(marches)} marchés. Mot de passe initial : {MOT_DE_PASSE_INITIAL}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()