"""
Routes API REST pour les marchés — appelées par React.

Répartition des champs :
  - CC / administrateur : crée, modifie et supprime les marchés, mais ne saisit que l'objet (donc le compte) et l'entité ;
  - membre (chef de service) : ne modifie pas les marchés (entité, objet et compte grisés) ;
  - CV : remplit toutes les autres informations (référence, nature, mode de passation, montant, année, …)
    des marchés que son membre (chef de service) lui a envoyés. Il ne peut pas toucher à l'objet, au compte ni à l'entité.
Un marché est « renseigné » quand la référence, la nature, le mode de passation, le montant et l'année sont remplis.
"""
from flask import Blueprint, request, jsonify, g
from extensions import db
from models import Marche, Entite, ObjetMarche
from collections import defaultdict
from models import Controle, Utilisateur, Service
from services import detecter_anomalies, calculer_score_risque
from routes.prmp import infos_prmp
from routes.objets import infos_objet
from anomalies_detaillees import detecter_detaille
from securite import peut_voir_entite, connexion_requise, role_requis
import champs_marche
marches_bp = Blueprint("marches", __name__)

# champs réservés au CV (en plus de ceux gérés par champs_marche : n° de saisie, dates, montants min/max, …)
CHAMPS_CV = ["reference", "id_prmp", "id_nature", "id_mode_passation", "montant", "titulaire",
             "annee_exercice", "hors_ppm", "marche_regularisation"]
CHAMPS_CC = ("objet", "id_objet", "id_entite")


def _role(u):
    return getattr(u.role, "value", u.role)


def _renseigne(m):
    """Les informations obligatoires du marché ont-elles été remplies par le CV ?"""
    return all(v not in (None, "") for v in
               (m.reference, m.id_nature, m.id_mode_passation, m.montant, m.annee_exercice))


def _ids_marches_visibles(u):
    """None = tous les marchés (CC / admin et rôles historiques). Un membre (chef de service) ne voit que les
    marchés notifiés à son service ; un CV que ceux que son membre lui a envoyés."""
    role = _role(u)
    if role == "CHEF_SERVICE":
        q = Controle.query.filter(Controle.id_service == u.id_service)
    elif role == "CV":
        q = Controle.query.filter(Controle.id_utilisateur_assigne == u.id)
    else:
        return None
    return {c.id_marche for c in q.all()}


def _marche_visible(marche, u):
    ids = _ids_marches_visibles(u)
    return ids is None or marche.id in ids


def _refus_gestion(message):
    return jsonify({"erreur": message}), 403


def _objet_choisi(data):
    """(id_objet, libellé) du catalogue d'objets choisi, ou None s'il est absent ou inconnu."""
    try:
        o = db.session.get(ObjetMarche, int(data.get("id_objet") or 0))
    except (TypeError, ValueError):
        o = None
    return (o.id, o.libelle) if o else None


@marches_bp.route("", methods=["GET"])
@connexion_requise
def lister_marches():
    ids = _ids_marches_visibles(g.utilisateur)
    marches = [m for m in Marche.query.all()
               if peut_voir_entite(m.id_entite) and (ids is None or m.id in ids)]
    return jsonify([_marche_en_dict(m) for m in marches])


@marches_bp.route("/risques", methods=["GET"])
@role_requis("ADMIN")
def marches_a_risque():
    """
    Module de détection automatique : pour chaque marché, anomalies détectées par les règles métier
    et score de risque (0 à 7). Sert à prioriser les marchés à contrôler.
    Les marchés pas encore renseignés par le CV sont ignorés.
    """
    bilan = defaultdict(lambda: [0, 0])  # entité -> [contrôles validés, non conformes]
    dernier_controle = {}
    for c in Controle.query.order_by(Controle.id).all():
        dernier_controle[c.id_marche] = c
        if c.date_validation:
            bilan[c.marche.id_entite][0] += 1
            bilan[c.marche.id_entite][1] += 1 if c.conclusion != "CONFORME" else 0

    resultats = []
    for m in Marche.query.all():
        if not peut_voir_entite(m.id_entite) or not _renseigne(m):
            continue
        total, non_conformes = bilan[m.id_entite]
        anomalies = detecter_anomalies(m)
        score = calculer_score_risque(m, (non_conformes / total) if total else 0)
        points = score + len(anomalies)
        niveau = "Élevé" if points >= 5 else "Moyen" if points >= 3 else "Faible" if points >= 1 else "Aucun"
        c = dernier_controle.get(m.id)
        resultats.append({
            "id": m.id, "reference": m.reference, "objet": m.objet, "entite": m.entite.nom, "montant": float(m.montant),
            "score": score, "anomalies": anomalies, "niveau": niveau, "points": points,
            "id_controle": c.id if c else None, "controle_valide": bool(c and c.date_validation),
        })
    resultats.sort(key=lambda r: (-r["points"], -r["montant"]))
    return jsonify(resultats)


@marches_bp.route("/<int:id_marche>", methods=["GET"])
@connexion_requise
def obtenir_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    if not peut_voir_entite(marche.id_entite) or not _marche_visible(marche, g.utilisateur):
        return jsonify({"erreur": "Accès refusé."}), 403
    return jsonify(_marche_en_dict(marche))


@marches_bp.route("", methods=["POST"])
@connexion_requise
def creer_marche():
    """Création par le CC : seulement l'entité et l'objet (le compte découle de l'objet)."""
    if _role(g.utilisateur) in ("CHEF_SERVICE", "CV"):
        return _refus_gestion("Accès refusé : seul le CC / administrateur peut créer un marché.")
    data = request.get_json() or {}
    if not data.get("id_entite") or db.session.get(Entite, int(data["id_entite"])) is None:
        return jsonify({"erreur": "Choisis l'entité du marché."}), 400
    choix = _objet_choisi(data)
    if choix is None:
        return jsonify({"erreur": "Choisis l'objet du marché."}), 400
    marche = Marche(objet=choix[1], id_objet=choix[0], id_entite=int(data["id_entite"]),
                    statut_controle="A_CONTROLER")  # un nouveau marché commence toujours « À contrôler »
    db.session.add(marche)
    db.session.commit()
    return jsonify(_marche_en_dict(marche)), 201


@marches_bp.route("/<int:id_marche>", methods=["PUT"])
@connexion_requise
def modifier_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    u = g.utilisateur
    if _role(u) == "CHEF_SERVICE" or not _marche_visible(marche, u):
        return _refus_gestion("Accès refusé : ce marché ne t'a pas été envoyé pour être renseigné.")
    data = request.get_json() or {}
    # statut_controle n'est volontairement pas modifiable ici : il change uniquement via /envois
    if _role(u) == "CV":
        return _modifier_par_cv(marche, data)
    return _modifier_par_cc(marche, data)


def _appliquer_infos(marche, data):
    """Applique les informations du CV (référence, nature, montant, …). Retourne une réponse d'erreur ou None."""
    data = {k: v for k, v in data.items() if k not in CHAMPS_CC}
    if "reference" in data and not str(data["reference"] or "").strip():
        return jsonify({"erreur": "La référence est obligatoire."}), 400
    erreur = _valider(data, partiel=True)
    if erreur:
        return jsonify({"erreur": erreur}), 400
    if data.get("reference"):
        autre = Marche.query.filter_by(reference=data["reference"]).first()
        if autre and autre.id != marche.id:
            return jsonify({"erreur": "Un marché avec cette référence existe déjà."}), 409
    for champ in CHAMPS_CV:
        if champ in data:
            setattr(marche, champ, data[champ])
    champs_marche.appliquer(marche, data)
    return None


def _modifier_par_cc(marche, data):
    """Le CC ne modifie que l'objet (donc le compte) et l'entité ; les autres informations sont celles du CV."""
    if data.get("id_objet"):
        choix = _objet_choisi(data)
        if choix is None:
            return jsonify({"erreur": "Objet inconnu."}), 400
        marche.id_objet, marche.objet = choix
    if data.get("id_entite"):
        if db.session.get(Entite, int(data["id_entite"])) is None:
            return jsonify({"erreur": "Entité inconnue."}), 400
        if marche.id_entite != int(data["id_entite"]):
            marche.id_entite = int(data["id_entite"])
            marche.id_prmp = None  # la PRMP appartenait à l'ancienne entité
    db.session.commit()
    return jsonify(_marche_en_dict(marche))


def _modifier_par_cv(marche, data):
    """Le CV remplit tout sauf l'objet, le compte et l'entité."""
    refus = _appliquer_infos(marche, data)
    if refus:
        db.session.rollback()
        return refus
    db.session.commit()
    return jsonify(_marche_en_dict(marche))


@marches_bp.route("/<int:id_marche>", methods=["DELETE"])
@connexion_requise
def supprimer_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    if _role(g.utilisateur) in ("CHEF_SERVICE", "CV"):
        return _refus_gestion("Accès refusé : seul le CC / administrateur peut supprimer un marché.")
    db.session.delete(marche)
    db.session.commit()
    return "", 204


@marches_bp.route("/<int:id_marche>/anomalies", methods=["GET"])
def detecter_anomalies_marche(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    suggestions = detecter_anomalies(marche)
    return jsonify({"id_marche": id_marche, "suggestions": suggestions})


@marches_bp.route("/<int:id_marche>/anomalies-detaillees", methods=["GET"])
def anomalies_detaillees(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    return jsonify({"suggestions": detecter_detaille(marche)})


def _valider(data, partiel=False):
    """Retourne un message d'erreur si les données saisies par le CV sont invalides, sinon None."""
    if "montant" in data and data["montant"] not in (None, "") and float(data["montant"]) <= 0:
        return "Le montant doit être strictement positif."
    if "annee_exercice" in data and data["annee_exercice"] not in (None, "") \
            and not (2000 <= int(data["annee_exercice"]) <= 2100):
        return "L'année d'exercice n'est pas valide."
    return champs_marche.valider(data)


def _marche_en_dict(m):
    c = Controle.query.filter_by(id_marche=m.id).order_by(Controle.id.desc()).first()
    service = db.session.get(Service, c.id_service) if c and c.id_service else None
    assigne = db.session.get(Utilisateur, c.id_utilisateur_assigne) if c and c.id_utilisateur_assigne else None
    return {
        "id": m.id, "reference": m.reference, "objet": m.objet,
        "montant": float(m.montant) if m.montant is not None else None,
        "titulaire": m.titulaire, "annee_exercice": m.annee_exercice, "hors_ppm": m.hors_ppm,
        "marche_regularisation": m.marche_regularisation,
        "nature": m.nature.libelle if m.nature else None,
        "mode_passation": m.mode_passation.libelle if m.mode_passation else None,
        "entite": m.entite.nom,
        "id_entite": m.id_entite, "id_nature": m.id_nature, "id_mode_passation": m.id_mode_passation,
        "renseigne": _renseigne(m),
        "statut_controle": m.statut_controle or "A_CONTROLER",
        "id_service": c.id_service if c else None,
        "service": service.nom if service else None,
        "id_assigne": c.id_utilisateur_assigne if c else None,
        "assigne_a": " ".join(x for x in [assigne.prenom, assigne.nom] if x) if assigne else None,
        **infos_prmp(m), **infos_objet(m), **champs_marche.infos_generales(m),
    }