"""
Circuit de validation d'un contrôle : COLLECTE -> VERIFICATION -> ANALYSE -> VALIDATION.
Chaque transfert (ou renvoi pour correction) est enregistré avec son auteur, sa date et son motif.
Le niveau actuel d'un contrôle est celui de son dernier transfert (COLLECTE s'il n'y en a aucun).
"""
from datetime import datetime

from flask import Blueprint, request, jsonify, g

from extensions import db
from models import Controle, ControleEtape, Utilisateur
from securite import connexion_requise

transferts_bp = Blueprint("transferts", __name__)

NIVEAUX = ["COLLECTE", "VERIFICATION", "ANALYSE", "VALIDATION"]
# rôles autorisés à agir quand le contrôle se trouve à un niveau donné (ADMIN peut toujours agir)
ROLES_PAR_NIVEAU = {"COLLECTE": ["COLLECTE"], "VERIFICATION": ["VERIFICATION"],
                    "ANALYSE": ["ANALYSE"], "VALIDATION": ["VALIDATION", "PCNM"]}
NB_ETAPES = 7


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


def _niveau_actuel(id_controle):
    dernier = Transfert.query.filter_by(id_controle=id_controle).order_by(Transfert.id.desc()).first()
    return dernier.niveau_arrivee if dernier else NIVEAUX[0]


def _peut_agir(utilisateur, niveau):
    return _role(utilisateur) == "ADMIN" or _role(utilisateur) in ROLES_PAR_NIVEAU[niveau]


def _circuit(controle):
    niveau = _niveau_actuel(controle.id)
    verrouille = controle.date_validation is not None
    agit = _peut_agir(g.utilisateur, niveau)
    historique = []
    for t in Transfert.query.filter_by(id_controle=controle.id).order_by(Transfert.id.desc()).all():
        u = db.session.get(Utilisateur, t.id_utilisateur) if t.id_utilisateur else None
        historique.append({
            "id": t.id, "action": t.action, "de": t.niveau_depart, "vers": t.niveau_arrivee, "motif": t.motif,
            "utilisateur": " ".join(x for x in [u.prenom, u.nom] if x) if u else None,
            "date": t.date_transfert.isoformat() if t.date_transfert else None})
    return {"niveau": niveau, "niveaux": NIVEAUX, "valide": verrouille,
            "peut_avancer": agit and not verrouille and niveau != NIVEAUX[-1],
            "peut_renvoyer": agit and not verrouille and niveau != NIVEAUX[0],
            "historique": historique}


def _enregistrer(controle, vers, action, motif=None):
    depart = _niveau_actuel(controle.id)
    db.session.add(Transfert(id_controle=controle.id, niveau_depart=depart, niveau_arrivee=vers,
                             action=action, motif=motif, id_utilisateur=g.utilisateur.id))
    db.session.commit()


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
    if niveau == NIVEAUX[-1]:
        return jsonify({"erreur": "Ce contrôle est déjà au dernier niveau."}), 400
    if not _peut_agir(g.utilisateur, niveau):
        return jsonify({"erreur": "Accès refusé : ce contrôle n'est pas à ton niveau."}), 403
    suivant = NIVEAUX[NIVEAUX.index(niveau) + 1]
    if suivant == NIVEAUX[-1]:
        nb = ControleEtape.query.filter(ControleEtape.id_controle == id_controle, ControleEtape.note.isnot(None)).count()
        if nb < NB_ETAPES:
            return jsonify({"erreur": f"Les {NB_ETAPES} étapes doivent être notées avant la validation ({nb}/{NB_ETAPES})."}), 400
    _enregistrer(controle, suivant, "TRANSFERT")
    return jsonify(_circuit(controle))


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
    if not _peut_agir(g.utilisateur, niveau):
        return jsonify({"erreur": "Accès refusé : ce contrôle n'est pas à ton niveau."}), 403
    if not motif:
        return jsonify({"erreur": "Indique le motif du renvoi."}), 400
    _enregistrer(controle, NIVEAUX[NIVEAUX.index(niveau) - 1], "RENVOI", motif)
    return jsonify(_circuit(controle))
