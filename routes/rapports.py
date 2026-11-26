"""
Génération du rapport de contrôle (PDF ou Word) pour un marché donné, au format
« Liste des irrégularités et anomalies constatées et les procédures applicables »,
et du rapport global Word.

Le rapport ne liste que les irrégularités des constats (champ « Irrégularité »), avec l'article applicable.
La colonne « Observations » reste vide : elle est complétée par la PRMP.
"""
from datetime import datetime
from flask import Blueprint, send_file, request, abort, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from xml.sax.saxutils import escape
import io
from securite import peut_voir_entite
from models import Marche, Controle, ControleEtape, Irregularite
from routes.objets import compte_marche
from extensions import db
from models import Utilisateur
rapports_bp = Blueprint("rapports", __name__)

TITRE = "LISTE DES IRRÉGULARITÉS ET ANOMALIES CONSTATÉES ET LES PROCÉDURES APPLICABLES"
EN_TETES = ["Irrégularités et Anomalies constatées", "Procédures applicables", "Observations"]


# ---------------------------------------------------------------------------
# Données communes au PDF et au Word
# ---------------------------------------------------------------------------
def _controle_du_rapport(id_marche):
    """Contrôle validé le plus récent s'il existe, sinon le dernier contrôle."""
    base = Controle.query.filter_by(id_marche=id_marche)
    return (base.filter(Controle.date_validation.isnot(None)).order_by(Controle.id.desc()).first()
            or base.order_by(Controle.id.desc()).first())


def _donnees_rapport(id_marche):
    """Retourne (marche, groupes, conclusion).
    groupes : [(titre_étape, [(irrégularité, article applicable, None), ...]), ...]
    Seules les irrégularités des constats sont listées. La colonne « Observations » reste vide :
    elle est complétée par la PRMP.
    conclusion : « Procédure conforme » / « Procédure non conforme » / None (pas de contrôle)."""
    marche = Marche.query.get_or_404(id_marche)
    if not peut_voir_entite(marche.id_entite):
        abort(403)
    controle = _controle_du_rapport(id_marche)
    groupes, conclusion = [], None

    if controle is not None:
        valeur = str(getattr(controle.conclusion, "value", controle.conclusion)).split(".")[-1].upper()
        conclusion = {"CONFORME": "Procédure conforme", "NON_CONFORME": "Procédure non conforme"}.get(
            valeur, "Contrôle en cours (conclusion non définitive)")
        etapes = sorted(ControleEtape.query.filter_by(id_controle=controle.id).all(), key=lambda e: e.etape.ordre)
        for e in etapes:
            irregularites = Irregularite.query.filter_by(id_controle_etape=e.id).order_by(Irregularite.id).all()
            lignes = [(i.irregularite or i.description, i.texte_applicable, None) for i in irregularites]
            if lignes:
                groupes.append((e.etape.libelle, lignes))

    return marche, groupes, conclusion


def _nom_prmp(marche):
    import models
    Prmp = getattr(models, "Prmp", None)
    if Prmp is not None and getattr(marche, "id_prmp", None):
        p = Prmp.query.get(marche.id_prmp)
        return p.nom if p else None
    return None


def _noms_controleurs(marche):
    controle = _controle_du_rapport(marche.id)
    if controle is None:
        return None
    ids = {e.id_utilisateur for e in ControleEtape.query.filter_by(id_controle=controle.id).all() if e.id_utilisateur}
    noms = []
    for i in sorted(ids):
        u = db.session.get(Utilisateur, i)
        if u:
            noms.append(" ".join(x for x in [u.prenom, u.nom] if x))
    return ", ".join(noms) or None


def _en_tete(marche):
    prmp = _nom_prmp(marche)
    return [
        ("Objet du contrat", marche.objet),
        ("Référence du marché", marche.reference),
        ("Entité", marche.entite.nom),
        ("Personne Responsable de la conduite de la procédure", prmp),
        ("Qualité de la Personne Responsable de la conduite de la procédure", "PRMP" if prmp else None),
        ("Nom des contrôleurs", _noms_controleurs(marche)),
    ], marche.annee_exercice, compte_marche(marche)


def _nom_fichier(marche):
    return marche.reference or f"marche_{marche.id}"


# ---------------------------------------------------------------------------
# PDF
# ---------------------------------------------------------------------------
F, FB, FBI = "Times-Roman", "Times-Bold", "Times-BoldItalic"
S_TITRE = ParagraphStyle("t", fontName=F, fontSize=12, leading=16, alignment=TA_CENTER)
S_INFO = ParagraphStyle("i", fontName=F, fontSize=11, leading=15)
S_ETAPE = ParagraphStyle("e", fontName=FB, fontSize=10.5, leading=13, alignment=TA_CENTER)
S_G = ParagraphStyle("g", fontName=F, fontSize=9.5, leading=12, alignment=TA_LEFT)
S_J = ParagraphStyle("j", fontName=F, fontSize=9.5, leading=12, alignment=TA_JUSTIFY)
S_HEAD = ParagraphStyle("h", fontName=FB, fontSize=10, leading=13, alignment=TA_CENTER)
S_CONCL = ParagraphStyle("k", fontName=FB, fontSize=12, leading=16, spaceBefore=14)


def _p(texte, style, vide="—"):
    return Paragraph(escape(str(texte or vide)).replace("\n", "<br/>"), style)


def _info(label, valeur):
    return Paragraph(f"<b><u>{escape(label)}</u></b> : {escape(str(valeur or '—'))}", S_INFO)


def construire_pdf(marche, groupes, conclusion):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, leftMargin=15 * mm, rightMargin=15 * mm,
                            topMargin=15 * mm, bottomMargin=15 * mm)
    infos, annee, compte = _en_tete(marche)
    elements = [
        Paragraph(f"<u>{TITRE}</u>", S_TITRE),
        Spacer(1, 7 * mm),
        Paragraph(f"<b><u>Année</u></b> : {escape(str(annee or '—'))}"
                  f"&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;"
                  f"<b><u>Compte</u></b> : {escape(str(compte or '—'))}", S_INFO),
    ] + [_info(l, v) for l, v in infos] + [Spacer(1, 5 * mm)]

    data = [[_p(t, S_HEAD) for t in EN_TETES]]
    style = [
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]
    for titre, lignes in groupes:
        r = len(data)
        data.append([Paragraph(f"<u>{escape(titre)}</u>", S_ETAPE), "", ""])
        style.append(("SPAN", (0, r), (2, r)))
        for irregularite, article, observation in lignes:
            # 3e colonne laissée vide : elle est complétée par la PRMP
            data.append([_p("- " + str(irregularite), S_G), _p(article, S_J), _p(observation, S_J, "")])

    if len(data) == 1:
        data.append([_p("Aucune irrégularité constatée.", S_G), _p("—", S_J), _p("", S_J, "")])

    elements.append(Table(data, colWidths=[70 * mm, 65 * mm, 45 * mm], repeatRows=1, style=TableStyle(style)))
    if conclusion:
        elements.append(Paragraph(f"<u>Conclusion</u> : {escape(conclusion)}", S_CONCL))
    doc.build(elements)
    buffer.seek(0)
    return buffer


@rapports_bp.route("/marche/<int:id_marche>/pdf", methods=["GET"])
def rapport_marche_pdf(id_marche):
    marche, groupes, conclusion = _donnees_rapport(id_marche)
    buffer = construire_pdf(marche, groupes, conclusion)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True,
                     download_name=f"rapport_{_nom_fichier(marche)}.pdf")


# ---------------------------------------------------------------------------
# Word
# ---------------------------------------------------------------------------
def construire_docx(marche, groupes, conclusion):
    from docx import Document
    from docx.enum.table import WD_TABLE_ALIGNMENT
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml import OxmlElement
    from docx.oxml.ns import qn
    from docx.shared import Pt, Mm

    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Mm(210), Mm(297)
    section.left_margin = section.right_margin = section.top_margin = section.bottom_margin = Mm(15)

    normal = document.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(11)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")

    def run(par, texte, bold=False, underline=False, italic=False, size=None):
        r = par.add_run(texte)
        r.bold, r.underline, r.italic = bold, underline, italic
        if size:
            r.font.size = Pt(size)
        return r

    infos, annee, compte = _en_tete(marche)

    p = document.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run(p, TITRE, underline=True, size=12)
    document.add_paragraph()

    p = document.add_paragraph()
    run(p, "Année", bold=True, underline=True)
    run(p, f" : {annee or '—'}\t\t")
    run(p, "Compte", bold=True, underline=True)
    run(p, f" : {compte or '—'}")
    for label, valeur in infos:
        p = document.add_paragraph()
        run(p, label, bold=True, underline=True)
        run(p, f" : {valeur or '—'}")
    document.add_paragraph()

    table = document.add_table(rows=1, cols=3)
    table.style = "Table Grid"
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    largeurs = [Mm(70), Mm(65), Mm(45)]

    def remplir(cell, texte, align=WD_ALIGN_PARAGRAPH.LEFT, bold=False, underline=False, size=9.5, vide="—"):
        cell.text = ""
        par = cell.paragraphs[0]
        par.alignment = align
        run(par, str(texte or vide), bold=bold, underline=underline, size=size)

    for i, titre in enumerate(EN_TETES):
        remplir(table.rows[0].cells[i], titre, WD_ALIGN_PARAGRAPH.CENTER, bold=True, size=10)
    # répéter la ligne d'en-tête sur chaque page
    trPr = table.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)

    for titre, lignes in groupes:
        row = table.add_row()
        fusion = row.cells[0].merge(row.cells[2])
        remplir(fusion, titre, WD_ALIGN_PARAGRAPH.CENTER, bold=True, underline=True, size=10.5)
        for irregularite, article, observation in lignes:
            row = table.add_row()
            remplir(row.cells[0], "- " + str(irregularite))
            remplir(row.cells[1], article, WD_ALIGN_PARAGRAPH.JUSTIFY)
            remplir(row.cells[2], observation, WD_ALIGN_PARAGRAPH.JUSTIFY, vide="")  # complétée par la PRMP

    if not groupes:
        row = table.add_row()
        remplir(row.cells[0], "Aucune irrégularité constatée.")
        remplir(row.cells[1], "—")
        remplir(row.cells[2], "", vide="")

    for row in table.rows:
        for cell, largeur in zip(row.cells, largeurs):
            cell.width = largeur

    if conclusion:
        document.add_paragraph()
        p = document.add_paragraph()
        run(p, "Conclusion", bold=True, underline=True, size=12)
        run(p, f" : {conclusion}", bold=True, size=12)

    buffer = io.BytesIO()
    document.save(buffer)
    buffer.seek(0)
    return buffer


@rapports_bp.route("/marche/<int:id_marche>/docx", methods=["GET"])
def rapport_marche_docx(id_marche):
    marche, groupes, conclusion = _donnees_rapport(id_marche)
    buffer = construire_docx(marche, groupes, conclusion)
    return send_file(buffer, as_attachment=True, download_name=f"rapport_{_nom_fichier(marche)}.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")


# ---------------------------------------------------------------------------
# Fiche d'exploitation Excel + historique des fiches transmises dans le circuit
# ---------------------------------------------------------------------------
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@rapports_bp.route("/marche/<int:id_marche>/excel", methods=["GET"])
def rapport_marche_excel(id_marche):
    """Fiche d'exploitation Excel du contrôle du marché (même format que le modèle de la CRM)."""
    marche = Marche.query.get_or_404(id_marche)
    if not peut_voir_entite(marche.id_entite):
        abort(403)
    controle = _controle_du_rapport(id_marche)
    if controle is None:
        abort(404, "Aucun contrôle pour ce marché.")
    import fiche_excel
    buffer = fiche_excel.construire_fiche_excel([controle])
    return send_file(buffer, as_attachment=True, mimetype=XLSX,
                     download_name=f"fiche_exploitation_{_nom_fichier(marche)}.xlsx")


@rapports_bp.route("/controle/<int:id_controle>/fiches", methods=["GET"])
def fiches_controle(id_controle):
    """Historique des fiches Excel envoyées lors des transferts du circuit (plus récentes d'abord)."""
    from models import FicheExcel
    controle = Controle.query.get_or_404(id_controle)
    if not peut_voir_entite(controle.marche.id_entite):
        abort(403)

    def nom(uid):
        u = db.session.get(Utilisateur, uid) if uid else None
        return " ".join(x for x in [u.prenom, u.nom] if x) if u else None

    fiches = FicheExcel.query.filter_by(id_controle=id_controle).order_by(FicheExcel.id.desc()).all()
    return jsonify([{
        "id": f.id, "nom_fichier": f.nom_fichier, "taille_ko": f.taille_ko,
        "niveau_origine": f.niveau_origine, "niveau_destination": f.niveau_destination,
        "expediteur": nom(f.id_expediteur), "destinataire": nom(f.id_destinataire),
        "date_creation": f.date_creation.isoformat() if f.date_creation else None,
    } for f in fiches])


@rapports_bp.route("/fiches/<int:id_fiche>/telecharger", methods=["GET"])
def telecharger_fiche(id_fiche):
    from models import FicheExcel
    import os
    f = FicheExcel.query.get_or_404(id_fiche)
    if not peut_voir_entite(Controle.query.get_or_404(f.id_controle).marche.id_entite):
        abort(403)
    if not os.path.exists(f.chemin_fichier):
        abort(404, "Fichier introuvable sur le serveur.")
    return send_file(f.chemin_fichier, as_attachment=True, download_name=f.nom_fichier, mimetype=XLSX)


# ---------------------------------------------------------------------------
# Rapport global Word
# ---------------------------------------------------------------------------
@rapports_bp.route("/global/docx", methods=["GET"])
def rapport_global_docx():
    """Grand rapport de mission (Word) : ?annee=2024&debut=2024-01-01&fin=2024-12-31&region=Haute Matsiatra"""
    import rapport_word

    def _date(v):
        try:
            return datetime.strptime(v, "%Y-%m-%d").date() if v else None
        except ValueError:
            return None

    annee = request.args.get("annee", type=int)
    fichier, exercice = rapport_word.generer(annee=annee, debut=_date(request.args.get("debut")),
                                             fin=_date(request.args.get("fin")), region=(request.args.get("region") or "").strip() or None)
    return send_file(fichier, as_attachment=True, download_name=f"Rapport_global_controles_{exercice}.docx",
                     mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")