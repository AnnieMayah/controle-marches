"""
Données de démonstration pour la soutenance.

Utilisation (après avoir exécuté schema_postgresql.sql et lancé le backend au moins une fois) :
    python seed_demo.py

Crée : comptes utilisateurs, entités (celles du rapport de la CRM Haute Matsiatra),
marchés variés, contrôles (validés, en cours, à démarrer), irrégularités, documents
(PDF d'exemple) et recommandations.

Comptes créés (login / mot de passe) :
    admin / admin123      (ADMIN)
    collecte / collecte123  (COLLECTE)
    verif / verif123        (VERIFICATION)
    analyse / analyse123    (ANALYSE)
    pcnm / pcnm123          (PCNM)
"""
import os
import sys
from datetime import date, datetime, timedelta

from werkzeug.security import generate_password_hash

from app import create_app
from extensions import db
from models import (Utilisateur, Entite, Prmp, Marche, NatureMarche, ModePassation, Etape,
                    TypeDocument, Controle, ControleEtape, Irregularite, Document, Recommandation)
from services import recalculer_conclusion


def _pdf_exemple(chemin, titre):
    """Génère un petit PDF d'exemple pour les documents de démo."""
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    c = canvas.Canvas(chemin, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(60, 780, titre)
    c.setFont("Helvetica", 11)
    c.drawString(60, 750, "Document d'exemple généré pour la démonstration de l'application.")
    c.save()


def seed(app):
    if Utilisateur.query.count() > 0:
        print("Des données existent déjà : abandon pour ne rien écraser.")
        return

    natures = {n.libelle: n for n in NatureMarche.query.all()}
    modes = {m.libelle: m for m in ModePassation.query.all()}
    etapes = Etape.query.order_by(Etape.ordre).all()
    types_doc = {t.libelle: t for t in TypeDocument.query.all()}
    if not natures or not modes or not etapes:
        print("Les données de référence sont absentes : exécute d'abord schema_postgresql.sql.")
        return

    # ---------- Utilisateurs ----------
    comptes = [
        ("Rakotomalala", "Amélie", "admin", "admin123", "ADMIN"),
        ("Randrianarisoa", "Lalaina", "collecte", "collecte123", "COLLECTE"),
        ("Rasolonjatovo", "Patrick", "verif", "verif123", "VERIFICATION"),
        ("Andrianantenaina", "Jenselme", "analyse", "analyse123", "ANALYSE"),
        ("Ramilson", "Amédé", "pcnm", "pcnm123", "PCNM"),
    ]
    utilisateurs = {}
    for nom, prenom, login, mdp, role in comptes:
        u = Utilisateur(nom=nom, prenom=prenom, login=login, role=role, email=f"{login}@demo.local",
                        mot_de_passe_hash=generate_password_hash(mdp))
        db.session.add(u)
        utilisateurs[login] = u
    db.session.commit()

    # ---------- Entités + PRMP ----------
    defs_entites = [
        ("Direction Régionale des Travaux Publics", "STD", "Haute Matsiatra", "Rakoto Hery"),
        ("Préfecture de Fianarantsoa et ses Districts rattachés", "STD", "Haute Matsiatra", "Razafy Miora"),
        ("Région Haute Matsiatra", "CTD", "Haute Matsiatra", "Rabe Solo"),
        ("Centre Hospitalier Universitaire Tambohobe", "EPN", "Haute Matsiatra", "Andry Tiana"),
        ("Paositra Malagasy - Direction Interrégionale de Fianarantsoa", "EPN", "Haute Matsiatra", "Fanja Nirina"),
    ]
    entites = []
    for nom, type_, region, prmp_nom in defs_entites:
        e = Entite(nom=nom, type=type_, region=region)
        db.session.add(e)
        db.session.flush()
        db.session.add(Prmp(nom=prmp_nom, id_entite=e.id))
        entites.append(e)
    db.session.commit()
    prmps = {p.id_entite: p for p in Prmp.query.all()}

    # ---------- Marchés ----------
    # (ref, objet, entité#, nature, mode, montant, titulaire, hors_ppm, régularisation)
    defs_marches = [
        ("M-DRTP-001/24", "Fourniture de matériel informatique", 0, "Fournitures", "Affichage / Consultation", 18_088_000, "Tech Madagascar SARL", False, False),
        ("M-DRTP-002/24", "Réhabilitation de la route communale RC12", 0, "Travaux", "Appel d'offres ouvert", 235_630_000, "Entreprise Fitiavana BTP", False, False),
        ("M-PREF-001/24", "Fourniture de mobilier de bureau", 1, "Fournitures", "Affichage / Consultation", 42_500_000, "Mobilier Plus", False, False),
        ("M-PREF-002/24", "Construction du bâtiment du district d'Ambohimahasoa", 1, "Travaux", "Affichage / Consultation", 208_849_500, "Vatomandry Construction", False, False),
        ("M-PREF-003/24", "Achat de carburant pour véhicules administratifs", 1, "Fournitures", "Achat direct", 9_998_000, "Station Jovenna Fianarantsoa", True, False),
        ("M-REG-001/24", "Étude de faisabilité du marché régional", 2, "Prestations intellectuelles", "Appel à manifestation d'intérêt", 78_990_000, "Cabinet Ravinala Conseil", False, False),
        ("M-REG-002/24", "Fourniture de matériel agricole", 2, "Fournitures", "Affichage / Consultation", 24_660_000, "AgriMad", False, False),
        ("M-CHU-001/24", "Fourniture de médicaments et consommables", 3, "Fournitures", "Appel d'offres ouvert", 119_523_316, "Pharma Distribution Sud", False, False),
        ("M-CHU-002/24", "Fourniture de matériel biomédical", 3, "Fournitures", "Affichage / Consultation", 179_618_752, "BioMed Océan Indien", False, False),
        ("M-CHU-003/24", "Entretien des groupes électrogènes", 3, "Services", "Gré à gré", 62_000_000, "ElectroServ", False, True),
        ("M-PAO-001/24", "Fourniture de matériel postal", 4, "Fournitures", "Affichage / Consultation", 69_920_700, "PostalTech", False, False),
        ("M-PAO-002/24", "Achat direct de fournitures de bureau", 4, "Fournitures", "Achat direct", 650_000, "Papeterie Centrale", False, False),
    ]
    marches = []
    for ref, objet, idx, nature, mode, montant, titulaire, hors_ppm, regul in defs_marches:
        m = Marche(reference=ref, objet=objet, id_entite=entites[idx].id, id_prmp=prmps[entites[idx].id].id,
                   id_nature=natures[nature].id, id_mode_passation=modes[mode].id, montant=montant,
                   titulaire=titulaire, annee_exercice=2024, hors_ppm=hors_ppm,
                   marche_regularisation=regul, id_utilisateur_saisie=utilisateurs["collecte"].id,
                   date_signature=date(2024, 6, 1))
        db.session.add(m)
        marches.append(m)
    db.session.commit()

    # ---------- Contrôles ----------
    aujourd_hui = date.today()
    # (marché#, jours écoulés, notes par étape, validé ?)
    scenarios = [
        (0, 150, [3, 3, 2, 3, 3, 3, 3], True),
        (1, 125, [2, 3, 3, 2, 3, 3, 2], True),
        (2, 100, [1, 2, 1, 1, 2, 1, 1], True),
        (3, 80, [1, 1, 2, 0, 1, 1, 1], True),
        (4, 60, [3, 3, 3, 3, 3, 3, 3], True),     # hors PPM -> non conforme automatique
        (5, 45, [3, 3, 3, 4, 3, 3, 4], True),
        (7, 30, [2, 2, 3, 2, 2, 3, 2], True),
        (9, 8, [2, 2, 2, 2, 2, 2, 2], True),     # marché de régularisation -> non conforme automatique
        (8, 12, [2, 1, 2, 1, 1, 2, 2], False),    # toutes notées, à valider
        (10, 6, [2, 3, None, None, None, None, None], False),  # en cours d'analyse
        (11, 2, [None] * 7, False),               # à démarrer
    ]
    controles = {}
    for idx_marche, jours, notes, valide in scenarios:
        date_ctrl = aujourd_hui - timedelta(days=jours)
        c = Controle(id_marche=marches[idx_marche].id, date_controle=date_ctrl)
        db.session.add(c)
        db.session.flush()
        for etape, note in zip(etapes, notes):
            if note is not None:
                db.session.add(ControleEtape(id_controle=c.id, id_etape=etape.id, note=note,
                                             id_utilisateur=utilisateurs["analyse"].id))
        db.session.commit()
        if any(n is not None for n in notes):
            recalculer_conclusion(c.id)
        if valide:
            c = Controle.query.get(c.id)
            c.id_utilisateur_validateur = utilisateurs["pcnm"].id
            c.date_validation = datetime.combine(date_ctrl + timedelta(days=5), datetime.min.time())
            db.session.commit()
        controles[idx_marche] = c.id

    # ---------- Irrégularités (inspirées du rapport de la CRM) ----------
    def etape_ctrl(idx_marche, ordre):
        etape = next(e for e in etapes if e.ordre == ordre)
        return ControleEtape.query.filter_by(id_controle=controles[idx_marche], id_etape=etape.id).first()

    irregs = [
        (2, 1, "Document de planification non transmis au Contrôle Financier", "Code des marchés publics (Loi n°2016-055)", "Moyen", "Transmettre le PPM au Contrôle Financier et au Trésor Public", False),
        (2, 4, "PV d'ouverture des plis non signé par les candidats présents", "Code des marchés publics, art. 45", "Moyen", "Faire signer le PV par les candidats présents et leur en remettre un exemplaire", False),
        (3, 5, "Attribution du marché à un candidat ayant présenté une offre inacceptable", "Code des marchés publics", "Élevé", "Rejeter les offres non conformes lors de l'évaluation", True),
        (3, 7, "Absence de PV de réception technique et provisoire", "CCAP / Code des marchés publics", "Élevé", "Établir les PV de réception avant la réception définitive", False),
        (1, 3, "Spécifications techniques non neutres (mention de marques)", "Code des marchés publics", "Faible", "Utiliser des références à des normes sans préciser de marque", False),
        (7, 2, "Absence de critères de détection des offres anormalement basses", "Code des marchés publics", "Moyen", "Préciser les critères dans le document de mise en concurrence", False),
    ]
    for idx_marche, ordre, desc, texte, risque, reco, impact in irregs:
        ce = etape_ctrl(idx_marche, ordre)
        if ce:
            db.session.add(Irregularite(id_controle_etape=ce.id, description=desc, texte_applicable=texte,
                                         risque=risque, recommandation=reco, impacte_attribution=impact))
    db.session.commit()
    for idx_marche in (3,):
        recalculer_conclusion(controles[idx_marche])  # prend en compte l'irrégularité qui impacte l'attribution

    # ---------- Documents (PDF d'exemple) ----------
    dossier = app.config["UPLOAD_FOLDER"]
    docs = [(0, "Contrat"), (0, "PV d'ouverture des plis"), (1, "Dossier d'Appel d'Offres (DAO)"),
            (1, "Contrat"), (1, "PV d'ouverture des plis"), (1, "Rapport d'évaluation"), (7, "Contrat")]
    for idx_marche, type_libelle in docs:
        nom = f"{type_libelle.split(' (')[0].replace(' ', '_').replace(chr(39), '')}_{marches[idx_marche].reference.replace('/', '-')}.pdf"
        stocke = f"demo_{nom}"
        _pdf_exemple(os.path.join(dossier, stocke), f"{type_libelle} — {marches[idx_marche].reference}")
        db.session.add(Document(id_marche=marches[idx_marche].id, id_type_document=types_doc[type_libelle].id,
                                nom_fichier=nom, chemin_fichier=stocke, taille_ko=2,
                                id_utilisateur=utilisateurs["collecte"].id))
    db.session.commit()

    # ---------- Recommandations ----------
    recos = [
        (1, "Rappeler à la PRMP l'obligation de transmettre le PPM au Contrôle Financier et au Trésor Public.", "EN_COURS"),
        (1, "Élargir les lieux de publication de l'avis d'affichage (CRM, Contrôle Financier, Chambre de Commerce).", "EMISE"),
        (3, "Se conformer aux Instructions aux Candidats et faire diriger l'ouverture des plis par la PRMP.", "EMISE"),
        (3, "Préciser dans le document de mise en concurrence les critères de détection des offres anormalement basses.", "APPLIQUEE"),
        (0, "Effectuer un recyclage périodique des connaissances sur l'évolution de la réglementation.", "APPLIQUEE"),
        (4, "Mettre en cohérence les informations de l'avis de consultation et du dossier de consultation.", "NON_APPLIQUEE"),
    ]
    for idx_entite, texte, statut in recos:
        db.session.add(Recommandation(id_entite=entites[idx_entite].id, texte=texte, statut=statut,
                                      date_emission=aujourd_hui - timedelta(days=20)))
    db.session.commit()

    print("Données de démonstration créées.")
    print("Connexion : admin / admin123  (autres comptes : collecte, verif, analyse, pcnm — voir l'en-tête du fichier)")


if __name__ == "__main__":
    application = create_app()
    with application.app_context():
        seed(application)
