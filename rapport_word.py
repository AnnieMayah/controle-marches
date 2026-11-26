"""
Rapport global de mission de contrôle a posteriori (Word), au format du rapport de la CRM.
generer(annee, debut, fin, region) -> (BytesIO, exercice)
"""
import io
from collections import OrderedDict, defaultdict
from datetime import date

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_COLOR_INDEX, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt, Mm, Cm

from extensions import db
from models import (Controle, ControleEtape, Irregularite, Marche,
                    Recommandation, Utilisateur)

A_COMPLETER = "[À compléter]"
MOIS = ["Janvier", "Février", "Mars", "Avril", "Mai", "Juin", "Juillet", "Août",
        "Septembre", "Octobre", "Novembre", "Décembre"]
NOMBRES = {0: "ZÉRO", 1: "UN", 2: "DEUX", 3: "TROIS", 4: "QUATRE", 5: "CINQ",
           6: "SIX", 7: "SEPT", 8: "HUIT", 9: "NEUF", 10: "DIX"}


# ------------------------------------------------------------------ utilitaires
def _val(x):
    return str(getattr(x, "value", x)).split(".")[-1].upper()


def _montant(v):
    v = float(v or 0)
    s = f"{v:,.2f}".replace(",", " ").replace(".", ",")
    return s[:-3] if s.endswith(",00") else s


def _nb(n):
    return f"{n:02d}"


def _lettres(n):
    return f"{NOMBRES.get(n, str(n))} ({_nb(n)})"


def _taux(a, b):
    return (f"{(100 * a / b):.2f}".replace(".", ",") + " %") if b else "0 %"


def _champ(par, instr, texte=""):
    """Insère un champ Word (TOC, SEQ, PAGE...) mis à jour à l'ouverture."""
    def fc(t):
        r = par.add_run()
        e = OxmlElement("w:fldChar")
        e.set(qn("w:fldCharType"), t)
        if t == "begin":
            e.set(qn("w:dirty"), "true")
        r._r.append(e)
    fc("begin")
    r = par.add_run()
    it = OxmlElement("w:instrText")
    it.set(qn("xml:space"), "preserve")
    it.text = " " + instr + " "
    r._r.append(it)
    fc("separate")
    par.add_run(texte)
    fc("end")


def _ecrire(par, texte, bold=False, italic=False, underline=False, size=None):
    """Ajoute du texte ; '[À compléter]' est surligné en jaune."""
    morceaux = str(texte).split(A_COMPLETER)
    for i, m in enumerate(morceaux):
        if m:
            r = par.add_run(m)
            r.bold, r.italic, r.underline = bold, italic, underline
            if size:
                r.font.size = Pt(size)
        if i < len(morceaux) - 1:
            r = par.add_run(A_COMPLETER)
            r.font.highlight_color = WD_COLOR_INDEX.YELLOW
            r.bold = bold
            if size:
                r.font.size = Pt(size)


def _para(doc, texte="", align=WD_ALIGN_PARAGRAPH.JUSTIFY, **kw):
    p = doc.add_paragraph()
    p.alignment = align
    p.paragraph_format.space_after = Pt(6)
    if texte:
        _ecrire(p, texte, **kw)
    return p


def _puces(doc, items):
    for it in items:
        p = doc.add_paragraph(style="List Bullet")
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        _ecrire(p, it)


def _titre(doc, texte, niveau=1):
    h = doc.add_heading(level=niveau)
    r = h.add_run(texte)
    r.font.name = "Times New Roman"
    r.bold = True
    r.font.size = Pt({1: 14, 2: 13, 3: 12}[niveau])
    return h


def _legende(doc, genre, texte):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run(genre + " ")
    r.bold = r.italic = True
    _champ(p, "SEQ " + genre + " \\* ARABIC", "1")
    r = p.add_run(" " + texte)
    r.bold = r.italic = True
    return p


def _saut_page(doc):
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def _ombrer(cell, couleur="D9D9D9"):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), couleur)
    tcPr.append(shd)


def _cell(cell, texte, bold=False, align=WD_ALIGN_PARAGRAPH.LEFT, size=10, underline=False):
    cell.text = ""
    p = cell.paragraphs[0]
    p.alignment = align
    _ecrire(p, texte, bold=bold, size=size, underline=underline)


def _tableau(doc, entetes, largeurs_mm=None):
    t = doc.add_table(rows=1, cols=len(entetes))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, h in enumerate(entetes):
        _cell(t.rows[0].cells[i], h, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=9.5)
        _ombrer(t.rows[0].cells[i], "E7E6E6")
    trPr = t.rows[0]._tr.get_or_add_trPr()
    th = OxmlElement("w:tblHeader")
    th.set(qn("w:val"), "true")
    trPr.append(th)
    t._largeurs = largeurs_mm
    return t


def _largeurs(t):
    if t._largeurs:
        for row in t.rows:
            for c, w in zip(row.cells, t._largeurs):
                c.width = Mm(w)


def _ligne_fusionnee(t, texte):
    row = t.add_row()
    c = row.cells[0].merge(row.cells[-1])
    _cell(c, texte, bold=True, align=WD_ALIGN_PARAGRAPH.CENTER, size=10)
    return row


# ------------------------------------------------------------------ graphiques
def _png_camembert(labels, valeurs):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    pairs = [(l, v) for l, v in zip(labels, valeurs) if v]
    if not pairs:
        return None
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.pie([v for _, v in pairs], autopct="%1.2f%%", startangle=90, textprops={"fontsize": 9})
    total = sum(v for _, v in pairs)
    ax.legend(["%s — %.2f%% (%s)" % (l, 100 * v / total, v) for l, v in pairs],
              loc="upper center", bbox_to_anchor=(0.5, 0.0), fontsize=8, frameon=False)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _png_histo(noms, conformes, non_conformes):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return None
    if not noms:
        return None
    fig, ax = plt.subplots(figsize=(7, 4))
    x = list(range(len(noms)))
    ax.bar([i - 0.2 for i in x], conformes, 0.4, label="Conforme")
    ax.bar([i + 0.2 for i in x], non_conformes, 0.4, label="Non conforme")
    ax.set_ylim(0, 100)
    ax.set_yticks(range(0, 101, 10))
    ax.set_yticklabels([str(v) + "%" for v in range(0, 101, 10)], fontsize=8)
    ax.set_xticks(x)
    ax.set_xticklabels([n if len(n) < 28 else n[:26] + "…" for n in noms], fontsize=7)
    ax.legend(fontsize=8)
    ax.grid(axis="y", alpha=.3)
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf


def _image(doc, buf, largeur_cm=13):
    if buf is None:
        _para(doc, A_COMPLETER + " (figure à insérer)", align=WD_ALIGN_PARAGRAPH.CENTER)
        return
    doc.add_picture(buf, width=Cm(largeur_cm))
    doc.paragraphs[-1].alignment = WD_ALIGN_PARAGRAPH.CENTER


# ------------------------------------------------------------------ données
def _charger(annee, debut, fin):
    q = (db.session.query(Controle)
         .join(Marche, Controle.id_marche == Marche.id)
         .filter(Controle.date_validation.isnot(None)))
    if annee:
        q = q.filter(Marche.annee_exercice == annee)
    if debut:
        q = q.filter(Controle.date_controle >= debut)
    if fin:
        q = q.filter(Controle.date_controle <= fin)
    vus, controles = set(), []
    for c in q.order_by(Controle.id.desc()).all():   # un seul contrôle validé (le plus récent) par marché
        if c.id_marche not in vus:
            vus.add(c.id_marche)
            controles.append(c)
    controles.sort(key=lambda c: (c.marche.entite.nom, c.id))
    return controles


def _libelle_fonction(u):
    r = _val(u.role)
    if r == "ADMIN":
        return "Chef de la Commission Régionale des Marchés"
    if r == "CHEF_SERVICE":
        return "Membre de la Commission (Chef de service)"
    if r == "CV":
        return "Contrôleur Vérificateur"
    return r.replace("_", " ").capitalize()


def _periode(dates):
    a, b = min(dates), max(dates)
    m1, m2 = MOIS[a.month - 1].lower(), MOIS[b.month - 1].lower()
    if a == b:
        return "%d %s %d" % (a.day, m1, a.year)
    if (a.month, a.year) == (b.month, b.year):
        return "%d au %d %s %d" % (a.day, b.day, m1, a.year)
    return "%d %s %d au %d %s %d" % (a.day, m1, a.year, b.day, m2, b.year)


# ------------------------------------------------------------------ génération
def generer(annee=None, debut=None, fin=None, region=None):
    controles = _charger(annee, debut, fin)
    exercice = annee or max((c.marche.annee_exercice for c in controles if c.marche.annee_exercice),
                            default=date.today().year)
    region = region or A_COMPLETER

    par_entite = OrderedDict()
    for c in controles:
        par_entite.setdefault(c.marche.entite, []).append(c)
    entites = list(par_entite.keys())
    n_ent = len(entites)
    types = defaultdict(int)
    for e in entites:
        types[_val(e.type)] += 1

    def nat(c):
        return c.marche.nature.libelle if c.marche.nature else "Non renseigné"

    def mod(c):
        return c.marche.mode_passation.libelle if c.marche.mode_passation else "Non renseigné"

    natures = sorted({nat(c) for c in controles})
    modes = sorted({mod(c) for c in controles})
    total = len(controles)
    conformes = sum(1 for c in controles if _val(c.conclusion) == "CONFORME")

    # ---------------- document
    doc = Document()
    s = doc.sections[0]
    s.page_width, s.page_height = Mm(210), Mm(297)
    s.left_margin = s.right_margin = Mm(25)
    s.top_margin = s.bottom_margin = Mm(25)
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), "Times New Roman")
    for st in ("Heading 1", "Heading 2", "Heading 3"):
        doc.styles[st].font.name = "Times New Roman"
        doc.styles[st].font.color.rgb = None
    upd = OxmlElement("w:updateFields")
    upd.set(qn("w:val"), "true")
    doc.settings.element.append(upd)

    fp = s.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _champ(fp, "PAGE", "1")

    # ---------------- couverture
    for ligne, gras in [("MINISTERE DE L’ECONOMIE ET DES FINANCES", True), ("……………………………", False),
                        ("COMMISSION NATIONALE DES MARCHES", True), ("………………………", False),
                        ("COMMISSION REGIONALE DES MARCHES", True),
                        (region.upper() if region != A_COMPLETER else region, True), ("…………………….", False)]:
        _para(doc, ligne, align=WD_ALIGN_PARAGRAPH.CENTER, bold=gras, size=11)
    for _ in range(6):
        doc.add_paragraph()
    boite = doc.add_paragraph()
    boite.alignment = WD_ALIGN_PARAGRAPH.CENTER
    pPr = boite._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr")
    for cote in ("top", "left", "bottom", "right"):
        e = OxmlElement("w:" + cote)
        e.set(qn("w:val"), "double")
        e.set(qn("w:sz"), "12")
        e.set(qn("w:space"), "10")
        e.set(qn("w:color"), "4E9A2F")
        bd.append(e)
    pPr.append(bd)
    _ecrire(boite, "Rapport de mission de contrôle a posteriori des marchés passés au titre de l’exercice "
                   "budgétaire %s auprès de %s (%s) entités publiques dont :"
            % (exercice, NOMBRES.get(n_ent, str(n_ent)).lower(), _nb(n_ent)), bold=True, size=15)
    for t_, lib in (("STD", "STD"), ("CTD", "CTD"), ("EPN", "Etablissements Publics")):
        if types.get(t_):
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Cm(3)
            _ecrire(p, "▪ %s %s" % (_lettres(types[t_]), lib), bold=True, size=14)
    for _ in range(6):
        doc.add_paragraph()
    _para(doc, "%s %d" % (MOIS[date.today().month - 1], date.today().year),
          align=WD_ALIGN_PARAGRAPH.CENTER, bold=True, underline=True)
    _saut_page(doc)

    # ---------------- sommaire
    _para(doc, "TABLE DES MATIERES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    _champ(doc.add_paragraph(), 'TOC \\o "1-3" \\h \\z \\u',
           "Clic droit › Mettre à jour le champ pour afficher le sommaire.")
    _para(doc, "LISTE DES TABLEAUX", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    _champ(doc.add_paragraph(), 'TOC \\h \\z \\c "Tableau"', "")
    _para(doc, "LISTE DES FIGURES", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    _champ(doc.add_paragraph(), 'TOC \\h \\z \\c "Figure"', "")
    _saut_page(doc)

    _para(doc, "LISTE DES SIGLES ET ABREVIATIONS", align=WD_ALIGN_PARAGRAPH.CENTER, bold=True)
    for sg, df in [("CRM", "Commission Régionale des Marchés Publics"), ("STD", "Services Techniques Déconcentrés"),
                   ("CTD", "Collectivité Territoriale Décentralisée"), ("EPN", "Etablissement Public National"),
                   ("SIGMP", "Système Informatisé de Gestion des Marchés Publics"),
                   ("SIIGFP", "Système Intégré Informatisé de Gestion des Finances Publiques"),
                   ("PRMP", "Personne Responsable des Marchés Publics"),
                   ("MEF", "Ministère de l’Economie et des Finances"), ("PV", "Procès-Verbal"),
                   ("AOR", "Appel d’Offres Restreint"), ("MGG", "Marché de Gré à Gré"),
                   ("PPM", "Plan de Passation des Marchés Publics"),
                   ("AGPM", "Avis Général de Passation des Marchés Publics"),
                   ("DAO", "Dossier d’Appel d’Offres"), ("CAO", "Commission d’Appel d’Offre"),
                   ("CCAP", "Cahier de Clause Administrative Particulière"),
                   ("CNM", "Commission Nationale des Marchés"),
                   ("UGPM", "Unité de Gestion des Passations des Marchés"),
                   ("NIF", "Numéro d’Identification Fiscale"), ("STAT", "Statistique")]:
        p = doc.add_paragraph()
        _ecrire(p, sg + " : ", bold=True)
        _ecrire(p, df)
        p.paragraph_format.space_after = Pt(0)
    _saut_page(doc)

    # ---------------- 1. Introduction
    _titre(doc, "1. INTRODUCTION")
    _para(doc, "Dans un contexte de renforcement de la bonne gouvernance et de transparence dans la gestion des "
               "finances publiques, le contrôle des marchés publics occupe une place stratégique dans le dispositif "
               "national de régulation des dépenses publiques. À Madagascar, cette dynamique est encadrée par la "
               "Loi n°2016-055 du 25 janvier 2017 portant Code des marchés publics. Le contrôle a posteriori, "
               "instrument essentiel de maîtrise, permet de vérifier, après exécution, la conformité des procédures "
               "avec les dispositions en vigueur.")
    _para(doc, "Pour la Commission Régionale des Marchés (CRM) de la région %s, cette mission s’inscrit dans une "
               "double logique : accompagner les entités dans l’application correcte des procédures, et évaluer la "
               "régularité, la transparence et l’efficience de la commande publique régionale, dans un esprit de "
               "redevabilité." % region)
    det = ", ".join("%s %s" % (_lettres(types[t]), t) for t in ("STD", "CTD", "EPN") if types.get(t)) or A_COMPLETER
    _para(doc, "Le présent rapport présente les résultats de la mission de contrôle a posteriori des marchés passés "
               "en %s auprès de %s entités (%s), dans la limite de sa compétence territoriale. %s "
               "(justification du nombre d’entités contrôlées)." % (exercice, _lettres(n_ent), det, A_COMPLETER))
    _para(doc, "L’objectif général du contrôle consiste à garantir la conformité des pratiques contractuelles avec "
               "les normes en vigueur, renforcer la transparence et promouvoir la bonne gouvernance. Les objectifs "
               "spécifiques sont :")
    _puces(doc, ["Vérifier la régularité des procédures de passation et d’exécution des marchés ;",
                 "Identifier les bonnes pratiques et les éventuelles irrégularités ou défaillances ;",
                 "Formuler des recommandations visant à améliorer la qualité et la conformité des procédures ;",
                 "Renforcer les capacités des entités régionales dans l’application des règles de la commande "
                 "publique."])

    # ---------------- 2. Méthodologie
    _titre(doc, "2. APPROCHE METHODOLOGIQUE")
    _para(doc, "La méthodologie adoptée repose sur trois étapes :")
    _puces(doc, ["Définition de la liste des entités et des contrats à contrôler, à partir du SIGMP, des fiches "
                 "centralisées des engagements du SIIGFP et de la liste fournie par l’entité contrôlée ;",
                 "Analyse de la conformité d’une procédure de passation, de la planification à l’établissement du "
                 "contrat, sur la base d’un échantillon de contrats ;",
                 "Restitution des résultats du contrôle auprès de chaque entité, l’informant des irrégularités "
                 "constatées et des procédures applicables."])
    _titre(doc, "2.1. Définition des entités et des contrats à contrôler", 2)
    _para(doc, "a) Méthode de sélection des entités à contrôler", bold=True)
    _para(doc, "La sélection des entités a été fondée sur une combinaison de critères institutionnels et de critères "
               "de risque : volume et valeur des marchés enregistrés auprès de la CRM, diversité institutionnelle, "
               "couverture des entités n’ayant pas subi de contrôle a posteriori antérieur, marchés touchant la vie "
               "quotidienne de la population, évolution des pratiques contractuelles, risque de réapparition de "
               "pratiques non conformes, suspicion de manipulation contractuelle, historique de litiges et "
               "couverture géographique équilibrée.")
    _para(doc, "b) Méthode de sélection des marchés à contrôler", bold=True)
    _para(doc, "Le contrôle a posteriori cible exclusivement les marchés non soumis au contrôle a priori de la CRM, "
               "conformément à l’arrêté n° 20442/2019/MEF du 17/09/2019. Les marchés ont été sélectionnés selon la "
               "nature (travaux, fournitures, services, avec priorité aux travaux), le mode de passation, le montant "
               "et les aspects techniques et réglementaires couverts (planification, publicité, passation, "
               "exécution, réception, archivage).")
    _titre(doc, "2.2. Analyse de conformité des procédures", 2)
    _para(doc, "La conformité est appréciée au regard des principes de l’article 5 de la loi n°2016-055 : liberté "
               "d’accès à la commande publique, égalité de traitement des candidats et transparence des procédures. "
               "Chaque étape est notée de 0 à 4 :")
    _puces(doc, ["0 : existence d’importantes irrégularités ou anomalies (en nombre)",
                 "1 : existence d’irrégularités ou anomalies", "2 : généralement acceptable",
                 "3 : acceptable", "4 : excellente maîtrise"])
    _para(doc, "Une procédure est jugée conforme en tendance si la moyenne des notes des étapes est supérieure ou "
               "égale à 2, non conforme en tendance dans le cas contraire. Toutefois, la passation hors PPM, "
               "l’existence d’une irrégularité impactant l’attribution du marché ou les marchés de régularisation "
               "rendent la procédure définitivement non conforme. L’indisponibilité de pièces essentielles fait "
               "l’objet d’un PV de carence signé par les deux parties.")
    for titre, pts in [
        ("2.2.1. Cas des mises en concurrence ouverte",
         ["Publication des avis spécifiques de mise en concurrence", "PV d’ouverture des plis",
          "Documents d’évaluation valides (date, signature, pluralité d’évaluateurs)",
          "Information relative au résultat de la mise en concurrence (affichage et lettre d’information)"]),
        ("2.2.2. Cas des Appels d’offres restreint (AOR)",
         ["Lettre d’invitation adressée aux candidats de la liste restreinte et preuve de réception",
          "PV d’ouverture des plis", "Documents d’évaluation valides",
          "Information relative au résultat de la mise en concurrence"]),
        ("2.2.3. Cas des marchés de prestations intellectuelles",
         ["Publication de l’appel à manifestations d’intérêts", "Décision autorisant la liste restreinte",
          "PV d’ouverture des plis", "Documents d’évaluation valides",
          "Information relative au résultat de la mise en concurrence"]),
        ("2.2.4. Cas des marchés de gré à gré (MGG)",
         ["Rapport justificatif signé par la PRMP",
          "Décision autorisant le gré à gré signée par l’autorité contractante",
          "PV de validation du choix du titulaire et du montant par la CAO", "Document de marché"]),
        ("2.2.5. Cas des achats directs",
         ["Disponibilité d’une copie de l’acte d’engagement",
          "Attribution du contrat : contrat recevable, acceptable, etc."]),
        ("2.2.6. Autres points de vérification",
         ["Existence du marché dans le PPM, transmission et publication des PPM et AGPM",
          "Conformité des documents de mise en concurrence avec les modèles-types",
          "Respect du délai de remise des offres, de l’évaluation et du délai de recours",
          "Disponibilité, conformité et validité du contrat ; cohérence avec le DAO et l’offre de l’attributaire",
          "Notification, ordre de service de commencer, avenants",
          "Respect des délais de livraison et d’exécution, des clauses du CCAP",
          "Réception dans les formes requises, cohérence avec le contrat, effectivité des prestations"])]:
        _titre(doc, titre, 3)
        _puces(doc, pts)
    _titre(doc, "2.3. Analyse du système d’archivage", 2)
    _para(doc, "Le système d’archivage fait l’objet d’une appréciation générale par entité et de recommandations "
               "appropriées.")
    _titre(doc, "2.4. Descentes auprès des organismes publics", 2)
    _para(doc, A_COMPLETER + " (visites de courtoisie, réunions préparatoires, organisation des équipes de contrôle).")
    _titre(doc, "2.5. Déroulement de la mission", 2)
    _para(doc, A_COMPLETER + " (déroulement général, accès aux archives, information des entités).")
    _titre(doc, "2.6. Restitution des résultats et rapport de contrôle", 2)
    _para(doc, "Une séance de restitution est réalisée par organisme contrôlé. À l’issue de la mission, deux "
               "documents sont établis : une fiche de restitution par entité, signée par les parties et remise à "
               "l’entité, et le présent rapport, compilé au niveau central en vue du rapport de contrôle a "
               "posteriori de la CNM à transmettre au Ministre de l’Economie et des Finances.")

    # ---------------- 3. Données générales
    _titre(doc, "3. DONNEES GENERALES")
    _titre(doc, "3.1. Entités contrôlées", 2)
    _para(doc, "%s entités ont fait l’objet de contrôle pour les marchés passés au titre de l’exercice budgétaire "
               "%s (Tableau 1)." % (_lettres(n_ent), exercice))
    _legende(doc, "Tableau", "Liste des entités contrôlées")
    t = _tableau(doc, ["N°", "Entité", "Type"], [15, 120, 25])
    for i, e in enumerate(entites, 1):
        r = t.add_row()
        _cell(r.cells[0], str(i), align=WD_ALIGN_PARAGRAPH.CENTER)
        _cell(r.cells[1], e.nom)
        _cell(r.cells[2], _val(e.type), align=WD_ALIGN_PARAGRAPH.CENTER)
    _largeurs(t)

    _titre(doc, "3.2. Statistique sur les contrats contrôlés", 2)
    _para(doc, "Les contrôleurs ont examiné %s échantillons de contrats." % _lettres(total))

    def tableau_croise(titre_legende, colonnes, cle, valeur, est_nombre):
        _legende(doc, "Tableau", titre_legende)
        tb = _tableau(doc, ["Années"] + colonnes + ["Total"])
        tot = [0] * (len(colonnes) + 1)
        fmt = _nb if est_nombre else _montant
        for e, cs in par_entite.items():
            _ligne_fusionnee(tb, e.nom)
            r = tb.add_row()
            _cell(r.cells[0], str(exercice), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
            vals = [sum(valeur(c) for c in cs if cle(c) == col) for col in colonnes]
            vals.append(sum(vals))
            for k, v in enumerate(vals):
                tot[k] += v
                _cell(r.cells[k + 1], fmt(v), align=WD_ALIGN_PARAGRAPH.RIGHT)
        r = tb.add_row()
        _cell(r.cells[0], "TOTAL GENERAL", bold=True)
        for k, v in enumerate(tot):
            _cell(r.cells[k + 1], fmt(v), bold=True, align=WD_ALIGN_PARAGRAPH.RIGHT)

    if controles:
        _titre(doc, "3.2.1. Nombre de contrats contrôlés par nature", 3)
        tableau_croise("Nombre de contrats contrôlés par nature", natures, nat, lambda c: 1, True)
        _para(doc)
        _image(doc, _png_camembert(natures, [sum(1 for c in controles if nat(c) == n) for n in natures]))
        _legende(doc, "Figure", "Proportion des contrats contrôlés par nature")

        _titre(doc, "3.2.2. Nombre de contrats contrôlés par mode de passation", 3)
        tableau_croise("Nombre de contrats contrôlés par mode de passation", modes, mod, lambda c: 1, True)
        _para(doc)
        _image(doc, _png_camembert(modes, [sum(1 for c in controles if mod(c) == m) for m in modes]))
        _legende(doc, "Figure", "Proportion des contrats contrôlés par mode de passation")

        _titre(doc, "3.2.3. Montant des contrats contrôlés par nature", 3)
        tableau_croise("Montant des contrats contrôlés par nature (Ar)", natures, nat,
                       lambda c: float(c.marche.montant or 0), False)
        _titre(doc, "3.2.4. Montant des contrats contrôlés par mode de passation", 3)
        tableau_croise("Montant des contrats contrôlés par mode de passation (Ar)", modes, mod,
                       lambda c: float(c.marche.montant or 0), False)
    else:
        _para(doc, "Aucun contrôle validé pour les critères choisis.")

    # ---------------- 4. Résultats
    _titre(doc, "4. RESULTATS DU CONTROLE")
    _titre(doc, "4.1. Taux de conformité", 2)
    _para(doc, "Sur un total de %s échantillons de contrats contrôlés, %s dossiers sont jugés conformes à la "
               "réglementation, soit un taux de conformité de %s (Tableau 6)."
          % (_lettres(total), _lettres(conformes), _taux(conformes, total)))
    _legende(doc, "Tableau", "Nombre de dossiers conformes / non conformes")
    t = _tableau(doc, ["Entité", "Dossiers contrôlés", "Conforme", "Non conforme", "PV de carence"],
                 [70, 25, 22, 25, 22])
    noms_h, c_h, n_h = [], [], []
    for e, cs in par_entite.items():
        ok = sum(1 for c in cs if _val(c.conclusion) == "CONFORME")
        r = t.add_row()
        _cell(r.cells[0], e.nom)
        for k, v in enumerate([len(cs), ok, len(cs) - ok, 0]):
            _cell(r.cells[k + 1], str(v), align=WD_ALIGN_PARAGRAPH.CENTER)
        noms_h.append(e.nom)
        c_h.append(round(100 * ok / len(cs)))
        n_h.append(100 - round(100 * ok / len(cs)))
    r = t.add_row()
    for k, v in enumerate(["TOTAL", total, conformes, total - conformes, 0]):
        _cell(r.cells[k], str(v), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER if k else WD_ALIGN_PARAGRAPH.LEFT)
    r = t.add_row()
    _cell(r.cells[0], "TAUX", bold=True)
    _cell(r.cells[1], "")
    _cell(r.cells[2], _taux(conformes, total), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    _cell(r.cells[3], _taux(total - conformes, total), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
    _cell(r.cells[4], "")
    _largeurs(t)
    _para(doc)
    _para(doc, "Les taux de conformité varient d’une entité à l’autre (Figure 3). %s (analyse des écarts et des "
               "facteurs explicatifs)." % A_COMPLETER)
    _image(doc, _png_histo(noms_h, c_h, n_h), 15)
    _legende(doc, "Figure", "Taux de conformité des procédures par entité")

    _titre(doc, "4.2. Principales irrégularités", 2)
    _para(doc, "Les principales irrégularités et anomalies constatées sont présentées par étape de procédure de "
               "passation de marchés (Tableau 7).")
    groupes = {}
    for c in controles:
        for ce in ControleEtape.query.filter_by(id_controle=c.id).all():
            for ir in Irregularite.query.filter_by(id_controle_etape=ce.id).order_by(Irregularite.id).all():
                txt = (ir.irregularite or ir.description or "").strip()
                if txt:
                    groupes.setdefault((ce.etape.ordre, ce.etape.libelle), OrderedDict()) \
                           .setdefault(txt, set()).add(c.marche.entite.nom)
    _legende(doc, "Tableau", "Principales irrégularités")
    t = _tableau(doc, ["Points de vérification", "Irrégularités et anomalies constatées", "Entités concernées"],
                 [35, 85, 50])
    if not groupes:
        r = t.add_row()
        _cell(r.cells[0], "—")
        _cell(r.cells[1], "Aucune irrégularité constatée.")
        _cell(r.cells[2], "—")
    for (_, lib), irs in sorted(groupes.items(), key=lambda kv: kv[0]):
        debut_i = len(t.rows)
        for txt, ents in irs.items():
            r = t.add_row()
            _cell(r.cells[1], "- " + txt, size=9.5)
            _cell(r.cells[2], ", ".join(sorted(ents)), size=9.5)
        fin_i = len(t.rows) - 1
        c0 = t.cell(debut_i, 0).merge(t.cell(fin_i, 0)) if fin_i > debut_i else t.cell(debut_i, 0)
        _cell(c0, lib, bold=True)
        _ombrer(c0, "E7E6E6")
    _largeurs(t)

    _titre(doc, "4.3. Causes de non-conformité", 2)
    _para(doc, "La conformité de chaque procédure est appréciée à partir de la moyenne des notes des étapes "
               "(≥ 2 : conforme en tendance ; < 2 : non conforme en tendance). La passation hors PPM, "
               "l’irrégularité impactant l’attribution et les marchés de régularisation rendent la procédure "
               "définitivement non conforme.")
    hors_ppm = sum(1 for c in controles if c.marche.hors_ppm)
    regul = sum(1 for c in controles if c.marche.marche_regularisation)
    impact = 0
    for c in controles:
        for ce in ControleEtape.query.filter_by(id_controle=c.id).all():
            if Irregularite.query.filter_by(id_controle_etape=ce.id, impacte_attribution=True).first():
                impact += 1
    _para(doc, "Dans l’échantillon : %s marché(s) hors PPM, %s marché(s) de régularisation et %s étape(s) "
               "comportant une irrégularité impactant l’attribution." % (_nb(hors_ppm), _nb(regul), _nb(impact)))
    _para(doc, "Les principales causes de non-conformité constatées sont les suivantes : " + A_COMPLETER)
    _para(doc, "Selon les réponses des PRMP aux lettres d’information, la majorité des irrégularités s’expliquent "
               "par : " + A_COMPLETER)

    # ---------------- 5. Recommandations
    _titre(doc, "5. PRINCIPALES RECOMMANDATIONS ET PROPOSITIONS D’AMELIORATION")
    _para(doc, "Compte tenu de ces résultats, des recommandations et suggestions sont formulées à l’endroit des "
               "autorités contractantes et des responsables concernés (Tableau 8).")
    _legende(doc, "Tableau", "Principales recommandations et/ou propositions d’amélioration")
    t = _tableau(doc, ["Entités contrôlées", "Principales recommandations et/ou propositions d’amélioration"],
                 [50, 120])
    for e, cs in par_entite.items():
        ids = [c.id for c in cs]
        recos = OrderedDict()
        for rc in Recommandation.query.filter(Recommandation.id_controle.in_(ids)).order_by(Recommandation.id).all():
            recos[rc.texte.strip()] = 1
        for c in cs:
            for ce in ControleEtape.query.filter_by(id_controle=c.id).all():
                for ir in Irregularite.query.filter_by(id_controle_etape=ce.id).all():
                    if ir.recommandation and ir.recommandation.strip():
                        recos[ir.recommandation.strip()] = 1
        r = t.add_row()
        _cell(r.cells[0], e.nom.upper(), bold=True, align=WD_ALIGN_PARAGRAPH.CENTER)
        c1 = r.cells[1]
        c1.text = ""
        if not recos:
            _ecrire(c1.paragraphs[0], A_COMPLETER, size=10)
        for k, txt in enumerate(recos):
            par = c1.paragraphs[0] if k == 0 else c1.add_paragraph()
            par.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            _ecrire(par, "- " + txt, size=10)
    _largeurs(t)

    # ---------------- 6. Conclusion
    _titre(doc, "6. CONCLUSION")
    _para(doc, "Le contrôle a posteriori des marchés publics réalisé dans la Région %s sur l’exercice %s enregistre "
               "un taux de conformité de %s (%d dossiers conformes sur %d). %s (comparaison avec les exercices "
               "antérieurs)." % (region, exercice, _taux(conformes, total), conformes, total, A_COMPLETER))
    _para(doc, A_COMPLETER + " (synthèse des irrégularités par phase : planification, mise en concurrence, "
                             "ouverture des plis, évaluation et attribution, gestion contractuelle, réception ; "
                             "causes profondes).")
    _para(doc, A_COMPLETER + " (recommandations stratégiques : renforcement du contrôle, suivi semestriel, "
                             "sanctions, formation, amélioration des documents types).")
    _saut_page(doc)

    # ---------------- Annexes
    _titre(doc, "ANNEXE 1 - Fiches d’exploitation (par entité contrôlée)")
    for e, cs in par_entite.items():
        _para(doc, e.nom, bold=True, align=WD_ALIGN_PARAGRAPH.LEFT)
        t = _tableau(doc, ["Référence", "Objet", "Nature", "Mode", "Montant (Ar)", "Note", "Conclusion"],
                     [24, 50, 20, 20, 24, 12, 22])
        for c in cs:
            r = t.add_row()
            vals = [c.marche.reference or "—", c.marche.objet, nat(c), mod(c), _montant(c.marche.montant),
                    str(c.note_globale if c.note_globale is not None else "—"),
                    {"CONFORME": "Conforme", "NON_CONFORME": "Non conforme"}.get(_val(c.conclusion), "En cours")]
            for k, v in enumerate(vals):
                _cell(r.cells[k], v, size=8.5)
        _largeurs(t)
        _para(doc)
    _saut_page(doc)

    _titre(doc, "ANNEXE 2 - Liste des contrôleurs")
    ids = set()
    for c in controles:
        for ce in ControleEtape.query.filter_by(id_controle=c.id).all():
            if ce.id_utilisateur:
                ids.add(ce.id_utilisateur)
        for uid in (c.id_utilisateur_assigne, c.id_utilisateur_validateur):
            if uid:
                ids.add(uid)
    agents = Utilisateur.query.filter(Utilisateur.id.in_(ids)).order_by(Utilisateur.nom).all() if ids else []
    t = _tableau(doc, ["NOMS", "FONCTIONS"], [85, 85])
    if not agents:
        r = t.add_row()
        _cell(r.cells[0], A_COMPLETER)
        _cell(r.cells[1], A_COMPLETER)
    for u in agents:
        r = t.add_row()
        _cell(r.cells[0], " ".join(x for x in [u.nom, u.prenom] if x))
        _cell(r.cells[1], _libelle_fonction(u))
    _largeurs(t)
    _para(doc)

    _titre(doc, "ANNEXE 3 - Calendriers de contrôle")
    t = _tableau(doc, ["Entités contrôlées", "Date des opérations"], [100, 70])
    for e, cs in par_entite.items():
        d = [c.date_controle for c in cs if c.date_controle]
        r = t.add_row()
        _cell(r.cells[0], e.nom)
        _cell(r.cells[1], _periode(d) if d else A_COMPLETER)
    _largeurs(t)

    buf = io.BytesIO()
    doc.save(buf)
    buf.seek(0)
    return buf, exercice