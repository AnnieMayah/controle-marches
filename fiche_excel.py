"""
Fiche d'exploitation Excel (format CRM « FICHE D'EXPLOITATION ») pour un ou plusieurs contrôles,
et archivage de la fiche lors d'un transfert du circuit de validation.

  construire_fiche_excel([controle, ...]) -> BytesIO   (un bloc par marché, comme dans le modèle fourni)
  archiver_fiche(controle, ...)           -> FicheExcel (fichier enregistré + ligne en base, sans commit)
"""
import io
import math
import os
import re
from datetime import datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side

ORANGE = "FFFFC000"
POLICE = "Agency FB"
FIN = Side(style="thin")
BORDURE = Border(left=FIN, right=FIN, top=FIN, bottom=FIN)

# (colonne, titre, largeur)
COLONNES = [
    ("A", "", 4),
    ("B", "AUTORITE CONTRACTANTE", 24),
    ("C", "REFERENCE DU DOSSIER", 20),
    ("D", "Exercices ", 10),
    ("E", "PRMP", 24),
    ("F", "Objet du marché", 38),
    ("G", "Mode de passation", 26),
    ("H", "Irrégularités constatées", 22),       # H:I fusionnées
    ("I", None, 42),
    ("J", "Observations", 42),
    ("K", "Observations générales", 34),
    ("L", "Risques", 42),
    ("M", "Textes applicables", 52),
    ("N", "Recommandations", 46),
    ("O", "Note par étape (0 à 4)", 12),
    ("P", "Note de la procédure de passation (moyenne des notes par étape ou pénalisation )", 22),
    ("Q", "Conclusion (conforme/non-conforme)", 24),
    ("R", "Nom des Contrôleurs", 26),
    ("S", "Réponse de l'entité après restitution", 42),
]
LARGEURS = {c: w for c, _, w in COLONNES}
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


# ------------------------------------------------------------------ utilitaires
def _txt(v):
    return "" if v is None else str(v).strip()


def _val(x):
    return str(getattr(x, "value", x)).split(".")[-1].upper()


def _liste(items):
    """Un seul élément : texte brut ; plusieurs : une puce « - » par ligne."""
    items = [i for i in (_txt(x) for x in items) if i]
    if not items:
        return ""
    return items[0] if len(items) == 1 else "\n".join("- " + i for i in items)


def _risque(ir):
    desc = _txt(getattr(ir, "description_risque", None))
    niveau = _txt(ir.risque)
    if desc and niveau:
        return f"{desc} (niveau : {niveau})"
    return desc or (f"Niveau de risque : {niveau}" if niveau else "")


def _hauteur(cellules):
    """Hauteur de ligne estimée d'après le texte et la largeur de chaque colonne (max Excel : 409,5)."""
    n_max = 1
    for texte, largeur in cellules:
        n = 0
        for seg in str(texte).split("\n"):
            n += max(1, math.ceil(len(seg) / max(1.0, largeur * 0.95)))
        n_max = max(n_max, n)
    return min(409.5, max(30.0, n_max * 13.5 + 6))


def _nom_personne(p):
    """Nom lisible d'un objet (prénom + nom, ou nom/libelle), ou '' s'il n'y en a pas."""
    if p is None:
        return ""
    if isinstance(p, str):
        return p.strip()
    prenom = _txt(getattr(p, "prenom", None))
    nom = _txt(getattr(p, "nom", None)) or _txt(getattr(p, "nom_complet", None)) or _txt(getattr(p, "libelle", None))
    return " ".join(x for x in [prenom, nom] if x)

def _prmp(marche):
    """PRMP du marché : même règle que l'écran (routes/prmp.py)."""
    from routes.prmp import nom_prmp_marche
    return nom_prmp_marche(marche) or ""

# ------------------------------------------------------------------ collecte des données (base)
def _bloc(controle):
    """Transforme un contrôle en dictionnaire simple (un bloc de la fiche)."""
    from models import ControleEtape, Etape, Irregularite, Utilisateur
    from extensions import db

    marche = controle.marche
    notees = {ce.id_etape: ce for ce in ControleEtape.query.filter_by(id_controle=controle.id).all()}
    ids_agents = {ce.id_utilisateur for ce in notees.values() if ce.id_utilisateur}
    if controle.id_utilisateur_assigne:
        ids_agents.add(controle.id_utilisateur_assigne)

    impacte, lignes = False, []
    for et in Etape.query.order_by(Etape.ordre).all():
        ce = notees.get(et.id)
        irs = (Irregularite.query.filter_by(id_controle_etape=ce.id).order_by(Irregularite.id).all()
               if ce else [])
        impacte = impacte or any(ir.impacte_attribution for ir in irs)
        if ce is None:                                   # étape pas encore notée
            lignes.append(dict(etape=et.libelle, i="", j="", k="", l="", m="", n="", note=None))
        elif irs:
            lignes.append(dict(
                etape=et.libelle,
                # I : irrégularité choisie dans la liste des observations de l'étape
                i=_liste([ir.irregularite for ir in irs]),
                # J « Observations » : champ Observation (à défaut, la description du constat)
                j=_liste([getattr(ir, "observation", None) or ir.description for ir in irs]),
                k=_liste([getattr(ir, "observations_generales", None) for ir in irs]),
                l=_liste([_risque(ir) for ir in irs]),
                m=_liste([ir.texte_applicable for ir in irs]),
                n=_liste([ir.recommandation for ir in irs]),
                note=ce.note))
        else:                                            # étape notée sans irrégularité
            lignes.append(dict(etape=et.libelle, i="", j="Conforme", k="", l="Néant", m="Néant", n="Néant",
                               note=ce.note))

    notes = [ce.note for ce in notees.values() if ce.note is not None]
    moyenne = round(sum(notes) / len(notes), 2) if notes else None
    note = float(controle.note_globale) if controle.note_globale is not None else moyenne
    penalise = bool(marche.hors_ppm or marche.marche_regularisation or impacte)
    if note is None:
        note_proc = ""
    elif penalise and note >= 2:
        note_proc = f"{note:g} mais pénalisé"
    else:
        note_proc = note

    concl = _val(controle.conclusion)
    if concl == "CONFORME":
        conclusion = "Tendance conforme"
    elif concl == "NON_CONFORME":
        conclusion = "Non conforme" + (" (pénalisation)" if penalise else "")
    else:
        conclusion = "En cours"

    agents = []
    for uid in sorted(ids_agents):
        u = db.session.get(Utilisateur, uid)
        if u:
            agents.append(" ".join(x for x in [u.prenom, u.nom] if x))

    return dict(
        entite=marche.entite.nom, reference=marche.reference or "", exercice=marche.annee_exercice,
        prmp=_prmp(marche), objet=marche.objet or "",
        mode=marche.mode_passation.libelle if marche.mode_passation else "",
        lignes=lignes, note_proc=note_proc, conclusion=conclusion, controleurs="\n".join(agents))


# ------------------------------------------------------------------ mise en page (sans base de données)
def _style(cell, taille=10, gras=False, couleur="FF000000", fond=None, h="center", police=POLICE, wrap=True):
    cell.font = Font(name=police, size=taille, bold=gras, color=couleur)
    cell.alignment = Alignment(horizontal=h, vertical="center", wrap_text=wrap)
    cell.border = BORDURE
    if fond:
        cell.fill = PatternFill("solid", fgColor=fond)


def _ecrire_classeur(blocs):
    wb = Workbook()
    ws = wb.active
    ws.title = "Feuil1"
    for col, _, larg in COLONNES:
        ws.column_dimensions[col].width = larg

    # titre (lignes 1-2) : « X » en colonne A comme dans le modèle
    ws.merge_cells("B1:S2")
    ws["B1"] = "FICHE D'EXPLOITATION"
    _style(ws["B1"], taille=26, gras=True, police="Calibri")
    for r in (1, 2):
        ws.row_dimensions[r].height = 33.75
        ws.cell(r, 1, "X")
        _style(ws.cell(r, 1), taille=11, couleur="FFFFFFFF", fond=ORANGE, wrap=False)

    ligne = 3
    for b in blocs:
        # ---- en-tête du bloc (« Y » en colonne A)
        ws.row_dimensions[ligne].height = 99.75
        for col, titre, _ in COLONNES:
            c = ws[f"{col}{ligne}"]
            c.value = "Y" if col == "A" else titre
            if col == "A":
                _style(c, taille=11, couleur="FFFFFFFF", fond=ORANGE, wrap=False)
            else:
                _style(c, gras=True, fond=ORANGE)
        ws.merge_cells(f"H{ligne}:I{ligne}")
        ligne += 1

        # ---- une ligne par étape
        for k, lg in enumerate(b["lignes"]):
            premiere = k == 0
            valeurs = {
                "A": "x",
                "B": b["entite"] if premiere else None, "C": b["reference"] if premiere else None,
                "D": b["exercice"] if premiere else None, "E": b["prmp"] if premiere else None,
                "F": b["objet"] if premiere else None, "G": b["mode"] if premiere else None,
                "H": lg["etape"], "I": lg["i"], "J": lg["j"], "K": lg["k"], "L": lg["l"],
                "M": lg["m"], "N": lg["n"], "O": lg["note"],
                "P": b["note_proc"] if premiere else None, "Q": b["conclusion"] if premiere else None,
                "R": b["controleurs"] if premiere else None, "S": None,   # réponse de l'entité : à compléter après restitution
            }
            for col, _, _ in COLONNES:
                c = ws[f"{col}{ligne}"]
                v = valeurs.get(col)
                c.value = v if v not in ("", None) else None
                if col == "A":
                    _style(c, taille=11, couleur="FFFFFFFF", fond=ORANGE, wrap=False)
                else:
                    _style(c, gras=col in "BCDEFGPQR", h="left" if col == "S" else "center")
            ws.row_dimensions[ligne].height = _hauteur(
                [(valeurs[c] or "", LARGEURS[c]) for c in "BEFGIJKLMNQR" if valeurs.get(c)])
            ligne += 1

    ws.page_setup.orientation = "landscape"
    ws.page_setup.fitToWidth = 1
    ws.page_setup.fitToHeight = 0
    ws.sheet_properties.pageSetUpPr.fitToPage = True

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


# ------------------------------------------------------------------ API publique
def construire_fiche_excel(controles):
    """Fiche d'exploitation (un bloc par contrôle) -> BytesIO du fichier .xlsx."""
    return _ecrire_classeur([_bloc(c) for c in controles])


def archiver_fiche(controle, id_expediteur=None, id_destinataire=None,
                   niveau_origine=None, niveau_destination=None, id_transfert=None):
    """Génère la fiche Excel du contrôle, l'enregistre sur disque et crée la ligne FicheExcel
    (historique du circuit). Ne fait PAS le commit : c'est l'appelant (route de transfert) qui le fait."""
    from flask import current_app
    from extensions import db
    from models import FicheExcel

    dossier = os.path.join(current_app.root_path, "uploads", "fiches_excel")
    os.makedirs(dossier, exist_ok=True)
    ref = re.sub(r"[^A-Za-z0-9_-]+", "_", controle.marche.reference or f"marche_{controle.marche.id}").strip("_")
    etapes = "_".join(x for x in [niveau_origine, niveau_destination] if x)
    nom = "_".join(x for x in ["Fiche", ref, etapes, datetime.now().strftime("%Y%m%d_%H%M%S")] if x) + ".xlsx"
    contenu = construire_fiche_excel([controle]).getvalue()
    chemin = os.path.join(dossier, nom)
    with open(chemin, "wb") as f:
        f.write(contenu)

    fiche = FicheExcel(id_controle=controle.id, id_transfert=id_transfert,
                       niveau_origine=niveau_origine, niveau_destination=niveau_destination,
                       id_expediteur=id_expediteur, id_destinataire=id_destinataire,
                       nom_fichier=nom, chemin_fichier=chemin, taille_ko=max(1, round(len(contenu) / 1024)))
    db.session.add(fiche)
    db.session.flush()
    return fiche