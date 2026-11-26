"""
Circuit de validation d'un contrôle : COLLECTE -> VERIFICATION -> ANALYSE -> VALIDATION.
Chaque transfert (ou renvoi pour correction) est enregistré avec son auteur, sa date et son motif.
Le niveau actuel d'un contrôle est celui de son dernier transfert (COLLECTE s'il n'y en a aucun).

Rôles (CC / directeur = ADMIN, membres A-B-C = CHEF_SERVICE, CV) :
  - COLLECTE et VERIFICATION : le CV auquel le contrôle est assigné ;
  - ANALYSE : le membre (CHEF_SERVICE) du service du contrôle ;
  - VALIDATION : ADMIN / PCNM.
L'ADMIN ne transfère pas : il peut seulement renvoyer (VALIDATION -> ANALYSE) ou valider.
À chaque TRANSFERT (« avancer »), la fiche d'exploitation Excel du contrôle est générée automatiquement,
enregistrée et rattachée au transfert : le destinataire la retrouve dans l'historique du circuit.
"""
import os
from datetime import datetime

from flask import Blueprint, request, jsonify, g, send_file

from extensions import db
from models import Controle, ControleEtape, Utilisateur
from securite import connexion_requise

transferts_bp = Blueprint("transferts", __name__)

NIVEAUX = ["COLLECTE", "VERIFICATION", "ANALYSE", "VALIDATION"]
# rôles autorisés à agir quand le contrôle se trouve à un niveau donné (ADMIN peut toujours agir)
# (les anciens rôles COLLECTE / VERIFICATION / ANALYSE sont conservés pour les comptes existants)
ROLES_PAR_NIVEAU = {"COLLECTE": ["CV", "COLLECTE"],
                    "VERIFICATION": ["CV", "VERIFICATION"],
                    "ANALYSE": ["CHEF_SERVICE", "ANALYSE"],
                    "VALIDATION": ["VALIDATION", "PCNM"]}
NB_ETAPES = 7
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


class Transfert(db.Model):
    __tablename__ = "transferts"
    id = db.Column(db.Integer, primary_key=True)
    id_controle = db.Column(db.Integer, db.ForeignKey("controles.id", ondelete="CASCADE"), nullable=False)
    niveau_depart = db.Column(db.String(20), nullable=False)
    niveau_arrivee = db.Column(db.String(20), nullable=False)
    action = db.Column(db.String(10), nullable=False)          # TRANSFERT ou RENVOI
    motif = db.Column(db.Text)
    id_utilisateur = db.Column(db.Integer, db.ForeignKey("utilisateurs.id"))
    date_transfert = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


def _role(u):
    return getattr(u.role, "value", u.role)


def _nom(u):
    return " ".join(x for x in [u.prenom, u.nom] if x) if u else None


def _niveau_actuel(id_controle):
    dernier = Transfert.query.filter_by(id_controle=id_controle).order_by(Transfert.id.desc()).first()
    return dernier.niveau_arrivee if dernier else NIVEAUX[0]


def _peut_agir(utilisateur, niveau, controle=None):
    """ADMIN peut toujours agir. Le CV n'agit que sur les contrôles qui lui sont assignés, le membre
    (CHEF_SERVICE) que sur ceux de son service, et chacun seulement aux niveaux qui le concernent."""
    role = _role(utilisateur)
    if role == "ADMIN":
        return True
    if role not in ROLES_PAR_NIVEAU[niveau]:
        return False
    if controle is not None:
        if role == "CV":
            return controle.id_utilisateur_assigne == utilisateur.id
        if role == "CHEF_SERVICE":
            return controle.id_service is not None and controle.id_service == utilisateur.id_service
    return True


def _peut_voir(utilisateur, controle):
    role = _role(utilisateur)
    if role == "CV":
        return controle.id_utilisateur_assigne == utilisateur.id
    if role == "CHEF_SERVICE":
        return controle.id_service == utilisateur.id_service
    return True


def _destinataire(controle, niveau):
    """Personne qui reçoit le contrôle quand il arrive à ce niveau."""
    if niveau in ("COLLECTE", "VERIFICATION"):
        return db.session.get(Utilisateur, controle.id_utilisateur_assigne) if controle.id_utilisateur_assigne else None
    if niveau == "ANALYSE":
        if not controle.id_service:
            return None
        return Utilisateur.query.filter_by(role="CHEF_SERVICE", id_service=controle.id_service, actif=True).first()
    return Utilisateur.query.filter_by(role="ADMIN", actif=True).first()


def _modele_fiche():
    try:
        from models import FicheExcel
        return FicheExcel
    except ImportError:
        return None


def _fiche_dict(f):
    return {"id": f.id, "nom_fichier": f.nom_fichier, "taille_ko": f.taille_ko,
            "niveau_origine": f.niveau_origine, "niveau_destination": f.niveau_destination,
            "expediteur": _nom(db.session.get(Utilisateur, f.id_expediteur)) if f.id_expediteur else None,
            "destinataire": _nom(db.session.get(Utilisateur, f.id_destinataire)) if f.id_destinataire else None,
            "id_transfert": f.id_transfert,
            "date_creation": f.date_creation.isoformat() if f.date_creation else None}


def _nb_etapes_notees(id_controle):
    return ControleEtape.query.filter(
        ControleEtape.id_controle == id_controle, ControleEtape.note.isnot(None)).count()


def _circuit(controle):
    niveau = _niveau_actuel(controle.id)
    verrouille = controle.date_validation is not None
    agit = _peut_agir(g.utilisateur, niveau, controle)
    est_admin = _role(g.utilisateur) == "ADMIN"
    Fiche = _modele_fiche()
    fiches = {}
    if Fiche is not None:
        for f in Fiche.query.filter_by(id_controle=controle.id).all():
            if f.id_transfert:
                fiches[f.id_transfert] = {"id": f.id, "nom_fichier": f.nom_fichier}
    historique = []
    for t in Transfert.query.filter_by(id_controle=controle.id).order_by(Transfert.id.desc()).all():
        u = db.session.get(Utilisateur, t.id_utilisateur) if t.id_utilisateur else None
        historique.append({
            "id": t.id, "action": t.action, "de": t.niveau_depart, "vers": t.niveau_arrivee, "motif": t.motif,
            "utilisateur": _nom(u), "fiche": fiches.get(t.id),
            "date": t.date_transfert.isoformat() if t.date_transfert else None})

    # Transfert vers VALIDATION bloqué tant que les 7 étapes ne sont pas notées
    bloque = None
    if niveau == NIVEAUX[-2]:
        nb = _nb_etapes_notees(controle.id)
        if nb < NB_ETAPES:
            bloque = f"Les {NB_ETAPES} étapes doivent être notées ({nb}/{NB_ETAPES})."

    return {"niveau": niveau, "niveaux": NIVEAUX, "valide": verrouille,
            "peut_avancer": agit and not est_admin and not verrouille and niveau != NIVEAUX[-1],
            "peut_renvoyer": agit and not verrouille and niveau != NIVEAUX[0]
                             and (not est_admin or niveau == "VALIDATION"),
            "avancer_bloque": bloque,
            "historique": historique}


def _enregistrer(controle, vers, action, motif=None):
    """Ajoute la ligne de transfert (sans commit) et la renvoie avec le niveau de départ."""
    depart = _niveau_actuel(controle.id)
    t = Transfert(id_controle=controle.id, niveau_depart=depart, niveau_arrivee=vers,
                  action=action, motif=motif, id_utilisateur=g.utilisateur.id)
    db.session.add(t)
    db.session.flush()
    return t, depart


@transferts_bp.route("/transferts/controle/<int:id_controle>", methods=["GET"])
@connexion_requise
def lire_circuit(id_controle):
    return jsonify(_circuit(db.get_or_404(Controle, id_controle)))


@transferts_bp.route("/transferts/controle/<int:id_controle>/avancer", methods=["POST"])
@connexion_requise
def avancer(id_controle):
    controle = db.get_or_404(Controle, id_controle)
    niveau = _niveau_actuel(id_controle)
    if controle.date_validation is not None:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus transférable."}), 409
    if _role(g.utilisateur) == "ADMIN":
        return jsonify({"erreur": "L'administrateur ne peut pas transférer : il peut seulement renvoyer pour correction."}), 403
    if niveau == NIVEAUX[-1]:
        return jsonify({"erreur": "Ce contrôle est déjà au dernier niveau."}), 400
    if not _peut_agir(g.utilisateur, niveau, controle):
        return jsonify({"erreur": "Accès refusé : ce contrôle n'est pas à ton niveau."}), 403
    suivant = NIVEAUX[NIVEAUX.index(niveau) + 1]
    if suivant == NIVEAUX[-1]:
        nb = _nb_etapes_notees(id_controle)
        if nb < NB_ETAPES:
            return jsonify({"erreur": f"Les {NB_ETAPES} étapes doivent être notées avant la validation ({nb}/{NB_ETAPES})."}), 400

    transfert, depart = _enregistrer(controle, suivant, "TRANSFERT")

    # Fiche d'exploitation Excel générée automatiquement et rattachée au transfert.
    # Une erreur d'Excel ne doit jamais empêcher le transfert : le savepoint isole cette partie.
    fiche, erreur_fiche = None, None
    try:
        from routes import fiche_excel
        destinataire = _destinataire(controle, suivant)
        with db.session.begin_nested():
            fiche = fiche_excel.archiver_fiche(
                controle, id_expediteur=g.utilisateur.id,
                id_destinataire=destinataire.id if destinataire else None,
                niveau_origine=depart, niveau_destination=suivant, id_transfert=transfert.id)
    except Exception as e:  # noqa: BLE001
        erreur_fiche = str(e)
    db.session.commit()

    reponse = _circuit(controle)
    reponse["fiche"] = _fiche_dict(fiche) if fiche else None
    reponse["fiche_erreur"] = erreur_fiche
    return jsonify(reponse)


@transferts_bp.route("/transferts/controle/<int:id_controle>/renvoyer", methods=["POST"])
@connexion_requise
def renvoyer(id_controle):
    controle = db.get_or_404(Controle, id_controle)
    niveau = _niveau_actuel(id_controle)
    motif = ((request.get_json() or {}).get("motif") or "").strip()
    if controle.date_validation is not None:
        return jsonify({"erreur": "Ce contrôle est validé : il n'est plus modifiable."}), 409
    if niveau == NIVEAUX[0]:
        return jsonify({"erreur": "Ce contrôle est déjà au premier niveau."}), 400
    if not _peut_agir(g.utilisateur, niveau, controle):
        return jsonify({"erreur": "Accès refusé : ce contrôle n'est pas à ton niveau."}), 403
    if _role(g.utilisateur) == "ADMIN" and niveau != "VALIDATION":
        return jsonify({"erreur": "L'administrateur ne peut renvoyer que depuis le niveau VALIDATION."}), 403
    if not motif:
        return jsonify({"erreur": "Indique le motif du renvoi."}), 400
    _enregistrer(controle, NIVEAUX[NIVEAUX.index(niveau) - 1], "RENVOI", motif)
    db.session.commit()
    return jsonify(_circuit(controle))


@transferts_bp.route("/transferts/a-traiter", methods=["GET"])
@connexion_requise
def a_traiter():
    """Identifiants des contrôles non validés qui se trouvent au niveau de l'utilisateur connecté."""
    ids = [c.id for c in Controle.query.filter(Controle.date_validation.is_(None)).all()
           if _peut_agir(g.utilisateur, _niveau_actuel(c.id), c)]
    return jsonify({"ids": ids})


# ---------------------------------------------------------------------------
# Historique des fiches Excel d'un contrôle
# ---------------------------------------------------------------------------
@transferts_bp.route("/transferts/controle/<int:id_controle>/fiches", methods=["GET"])
@connexion_requise
def lister_fiches(id_controle):
    controle = db.get_or_404(Controle, id_controle)
    if not _peut_voir(g.utilisateur, controle):
        return jsonify({"erreur": "Accès refusé."}), 403
    Fiche = _modele_fiche()
    if Fiche is None:
        return jsonify([])
    fiches = Fiche.query.filter_by(id_controle=id_controle).order_by(Fiche.id.desc()).all()
    return jsonify([_fiche_dict(f) for f in fiches])


@transferts_bp.route("/transferts/fiches/<int:id_fiche>/telecharger", methods=["GET"])
@connexion_requise
def telecharger_fiche(id_fiche):
    Fiche = _modele_fiche()
    if Fiche is None:
        return jsonify({"erreur": "Table des fiches non installée."}), 404
    f = db.get_or_404(Fiche, id_fiche)
    controle = db.get_or_404(Controle, f.id_controle)
    if not _peut_voir(g.utilisateur, controle):
        return jsonify({"erreur": "Accès refusé."}), 403
    if not os.path.exists(f.chemin_fichier):
        return jsonify({"erreur": "Fichier introuvable sur le serveur."}), 404
    return send_file(f.chemin_fichier, as_attachment=True, download_name=f.nom_fichier, mimetype=XLSX)

@transferts_bp.route("/transferts/controle/<int:id_controle>/excel", methods=["GET"])
@connexion_requise
def generer_excel(id_controle):
    controle = db.get_or_404(Controle, id_controle)
    if not _peut_voir(g.utilisateur, controle):
        return jsonify({"erreur": "Accès refusé."}), 403
    try:
        import fiche_excel
        niveau = _niveau_actuel(id_controle)
        fiche = fiche_excel.archiver_fiche(
            controle, id_expediteur=g.utilisateur.id, id_destinataire=None,
            niveau_origine=niveau, niveau_destination=niveau, id_transfert=None)
        db.session.commit()
    except Exception as e:  # noqa: BLE001
        return jsonify({"erreur": f"Génération Excel impossible : {e}"}), 500
    return send_file(fiche.chemin_fichier, as_attachment=True,
                     download_name=fiche.nom_fichier, mimetype=XLSX)
                     
@transferts_bp.route("/transferts/export-excel", methods=["GET"])
@connexion_requise
def exporter_excel():
    """Fiche d'exploitation Excel de tous les contrôles validés (filtres : date_debut, date_fin, type)."""
    if _role(g.utilisateur) not in ("ADMIN", "CHEF_SERVICE"):
        return jsonify({"erreur": "Accès refusé."}), 403
    q = Controle.query.filter(Controle.date_validation.isnot(None))
    debut = request.args.get("date_debut")
    fin = request.args.get("date_fin")
    if debut:
        q = q.filter(Controle.date_validation >= datetime.fromisoformat(debut))
    if fin:
        q = q.filter(Controle.date_validation < datetime.fromisoformat(fin).replace(hour=23, minute=59, second=59))
    controles = [c for c in q.order_by(Controle.id).all() if _peut_voir(g.utilisateur, c)]
    type_ = request.args.get("type")
    if type_:
        controles = [c for c in controles if c.marche.nature and c.marche.nature.libelle == type_]
    if not controles:
        return jsonify({"erreur": "Aucun contrôle validé à exporter."}), 404
    try:
        import fiche_excel
        buf = fiche_excel.construire_fiche_excel(controles)
    except Exception as e:  # noqa: BLE001
        return jsonify({"erreur": f"Export Excel impossible : {e}"}), 500
    nom = f"Fiche_exploitation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return send_file(buf, as_attachment=True, download_name=nom, mimetype=XLSX)