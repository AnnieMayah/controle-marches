"""
Génération du rapport de contrôle au format PDF pour un marché donné.
"""
from datetime import date, datetime
from flask import Blueprint, send_file, request, jsonify
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
import io

from models import Marche, Controle, ControleEtape, Irregularite

rapports_bp = Blueprint("rapports", __name__)


@rapports_bp.route("/marche/<int:id_marche>/pdf", methods=["GET"])
def rapport_marche_pdf(id_marche):
    marche = Marche.query.get_or_404(id_marche)
    controle = Controle.query.filter_by(id_marche=id_marche).order_by(Controle.id.desc()).first()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    titre_style = ParagraphStyle("TitrePerso", parent=styles["Heading1"], textColor=colors.HexColor("#1B4332"))
    soustitre_style = ParagraphStyle("SousTitrePerso", parent=styles["Heading2"], textColor=colors.HexColor("#1B4332"), fontSize=13)

    elements = [
        Paragraph("Rapport de contrôle a posteriori", titre_style),
        Paragraph(f"Marché {marche.reference}", styles["Normal"]),
        Spacer(1, 10 * mm),

        Paragraph("Informations générales", soustitre_style),
        Table([
            ["Référence", marche.reference],
            ["Objet", marche.objet],
            ["Entité", marche.entite.nom],
            ["Nature", marche.nature.libelle],
            ["Mode de passation", marche.mode_passation.libelle],
            ["Montant", f"{marche.montant:,.0f} Ar".replace(",", " ")],
            ["Titulaire", marche.titulaire or "—"],
            ["Année d'exercice", str(marche.annee_exercice)],
            ["Hors PPM", "Oui" if marche.hors_ppm else "Non"],
        ], colWidths=[50 * mm, 110 * mm], style=TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DAD4C0")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#EAE6D6")),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])),
        Spacer(1, 8 * mm),
    ]

    if controle is None:
        elements.append(Paragraph("Aucun contrôle n'a encore été réalisé pour ce marché.", styles["Normal"]))
    else:
        couleur_conclusion = colors.HexColor("#2D6A4F") if controle.conclusion == "CONFORME" else colors.HexColor("#A5423A")
        elements.append(Paragraph("Résultat du contrôle", soustitre_style))
        elements.append(Paragraph(
            f"Note globale : <b>{controle.note_globale or '—'}</b> / 4 — "
            f"Conclusion : <font color='{couleur_conclusion.hexval()}'><b>{controle.conclusion}</b></font>",
            styles["Normal"]
        ))
        elements.append(Spacer(1, 6 * mm))

        etapes = ControleEtape.query.filter_by(id_controle=controle.id).all()
        donnees_etapes = [["Étape", "Note", "Observations"]]
        for e in etapes:
            donnees_etapes.append([e.etape.libelle, str(e.note) if e.note is not None else "—", e.observations or "—"])

        elements.append(Table(donnees_etapes, colWidths=[55 * mm, 20 * mm, 85 * mm], style=TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DAD4C0")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1B4332")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ])))
        elements.append(Spacer(1, 8 * mm))

        toutes_irregularites = []
        for e in etapes:
            for irr in Irregularite.query.filter_by(id_controle_etape=e.id).all():
                toutes_irregularites.append([e.etape.libelle, irr.description, irr.texte_applicable or "—"])

        elements.append(Paragraph("Irrégularités constatées", soustitre_style))
        if toutes_irregularites:
            donnees_irr = [["Étape", "Description", "Texte applicable"]] + toutes_irregularites
            elements.append(Table(donnees_irr, colWidths=[40 * mm, 80 * mm, 40 * mm], style=TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DAD4C0")),
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#B8860B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
            ])))
        else:
            elements.append(Paragraph("Aucune irrégularité constatée.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return send_file(buffer, mimetype="application/pdf", as_attachment=True,
                      download_name=f"rapport_{marche.reference}.pdf")


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
