from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from commandes.services import transformer_devis
from .forms import DemandeDevisForm, DevisForm, LigneDevisForm
from .models import DemandeDevis, Devis
from .services import changer_statut_devis


def _societe():
    return {
        "nom": settings.ENTREPRISE_NOM,
        "activite": settings.ENTREPRISE_ACTIVITE,
        "adresse": settings.ENTREPRISE_ADRESSE,
        "telephone": settings.ENTREPRISE_TELEPHONE,
        "email": settings.ENTREPRISE_EMAIL,
        "identifiant": settings.ENTREPRISE_IDENTIFIANT,
    }


@permission_required("commercial.view_demandedevis", raise_exception=True)
def demandes(request):
    return render(request, "commercial/demandes.html", {"items": DemandeDevis.objects.select_related("client").all()})


@permission_required("commercial.view_demandedevis", raise_exception=True)
def detail_demande(request, pk):
    demande = get_object_or_404(DemandeDevis.objects.select_related("client", "type_verre", "epaisseur", "cree_par"), pk=pk)
    return render(request, "commercial/demande_detail.html", {"demande": demande})


@permission_required("commercial.add_demandedevis", raise_exception=True)
def creer_demande(request):
    form = DemandeDevisForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.cree_par = request.user
        item.save()
        return redirect("commercial:demandes")
    return render(request, "commercial/demande_form.html", {"form": form})


@permission_required("commercial.view_devis", raise_exception=True)
def liste(request):
    return render(request, "commercial/liste.html", {"items": Devis.objects.select_related("client").all()})


@permission_required("commercial.add_devis", raise_exception=True)
def creer(request):
    initial = {}
    demande_id = request.GET.get("demande")
    if demande_id:
        demande = get_object_or_404(DemandeDevis, pk=demande_id)
        initial = {
            "client": demande.client_id,
            "demande": demande.pk,
            "chantier_adresse": demande.chantier_adresse,
            "chantier_contact": demande.contact_chantier,
            "chantier_telephone": demande.telephone_chantier,
            "pose_incluse": demande.pose_souhaitee,
        }
    form = DevisForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        devis = form.save(commit=False)
        devis.cree_par = request.user
        devis.save()
        return redirect("commercial:detail", pk=devis.pk)
    return render(request, "commercial/devis_form.html", {"form": form})


@permission_required("commercial.view_devis", raise_exception=True)
def detail(request, pk):
    devis = get_object_or_404(Devis.objects.select_related("client"), pk=pk)
    return render(request, "commercial/detail_v3.html", {"devis": devis, "ligne_form": LigneDevisForm(), "societe": _societe()})


@permission_required("commercial.view_devis", raise_exception=True)
def fiche_production(request, pk):
    devis = get_object_or_404(Devis.objects.select_related("client").prefetch_related("lignes__type_verre", "lignes__epaisseur"), pk=pk)
    return render(request, "commercial/fiche_production.html", {"devis": devis})


@permission_required("commercial.view_devis", raise_exception=True)
def fiche_decoupe(request, pk):
    devis = get_object_or_404(Devis.objects.select_related("client").prefetch_related("lignes__panneau_stock", "lignes__chute_stock"), pk=pk)
    return render(request, "commercial/fiche_decoupe.html", {"devis": devis})


@permission_required("commercial.change_devis", raise_exception=True)
def ajouter_ligne(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    if devis.statut != Devis.Statut.BROUILLON:
        messages.error(request, "Les lignes et les matières ne peuvent plus être modifiées après l'émission du devis.")
        return redirect("commercial:detail", pk=pk)
    form = LigneDevisForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        ligne = form.save(commit=False)
        ligne.devis = devis
        ligne.save()
        devis.recalculer_totaux()
    return redirect("commercial:detail", pk=pk)


def statut(request, pk, statut):
    devis = get_object_or_404(Devis, pk=pk)
    if request.method == "POST":
        try:
            devis = changer_statut_devis(devis, statut, request.user, request.POST.get("commentaire", ""))
            messages.success(request, "Statut du devis mis à jour.")
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("commercial:detail", pk=pk)


@permission_required("commercial.transform_devis", raise_exception=True)
def transformer(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
    if request.method == "POST":
        try:
            commande = transformer_devis(devis, request.user)
            messages.success(request, f"Commande {commande.reference} créée.")
            return redirect("commandes:detail", pk=commande.pk)
        except ValueError as exc:
            messages.error(request, str(exc))
    return redirect("commercial:detail", pk=pk)


@permission_required("commercial.view_devis", raise_exception=True)
def pdf(request, pk):
    devis = get_object_or_404(Devis.objects.select_related("client").prefetch_related("lignes__type_verre", "lignes__epaisseur"), pk=pk)
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT, TA_RIGHT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import mm
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    def money(value):
        return f"{value:,.0f}".replace(",", " ") + " FCFA"

    societe = _societe()
    styles = getSampleStyleSheet()
    normal = ParagraphStyle("QuoteNormal", parent=styles["BodyText"], fontName="Helvetica", fontSize=8.5, leading=11, textColor=colors.HexColor("#334155"))
    small = ParagraphStyle("QuoteSmall", parent=normal, fontSize=7.5, leading=9, textColor=colors.HexColor("#64748b"))
    heading = ParagraphStyle("QuoteHeading", parent=styles["Heading1"], fontName="Helvetica-Bold", fontSize=19, leading=23, textColor=colors.white)
    right = ParagraphStyle("QuoteRight", parent=normal, alignment=TA_RIGHT)
    stream = BytesIO()
    document = SimpleDocTemplate(stream, pagesize=A4, leftMargin=16 * mm, rightMargin=16 * mm, topMargin=15 * mm, bottomMargin=18 * mm, title=f"Devis {devis.reference}", author="VerreStock")
    story = []
    header = Table([[Paragraph(f"<b>{societe['nom'].upper()}</b><br/><font size='8'>{societe['activite']}</font>", ParagraphStyle("Brand", parent=normal, textColor=colors.white, leading=12)), Paragraph(f"<b>DEVIS</b><br/><font size='12'>{devis.reference}</font><br/><font size='8'>Émis le {devis.date.strftime('%d/%m/%Y')}</font>", ParagraphStyle("HeaderRight", parent=normal, textColor=colors.white, alignment=TA_RIGHT, leading=12))]], colWidths=[105 * mm, 73 * mm])
    header.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#102653")), ("BOX", (0, 0), (-1, -1), 0, colors.HexColor("#102653")), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 12), ("BOTTOMPADDING", (0, 0), (-1, -1), 12)]))
    story += [header, Spacer(1, 7 * mm)]
    client_text = f"<b>DESTINATAIRE</b><br/><br/><b>{devis.client.nom}</b><br/>{devis.client.contact or ''}<br/>{(devis.client.adresse or '').replace(chr(10), '<br/>')}<br/>{devis.client.ville or ''}"
    chantier = devis.chantier_adresse or devis.client.adresse or "À confirmer"
    conditions_text = f"<b>CHANTIER & CONDITIONS</b><br/><br/>Chantier : <b>{chantier}</b><br/>Délai : <b>{devis.delai_fabrication or 'À confirmer'}</b><br/>Acompte : <b>{devis.acompte_taux} %</b><br/>TVA : <b>{devis.tva_taux} %</b>"
    meta = Table([[Paragraph(client_text, normal), Paragraph(conditions_text, normal)]], colWidths=[105 * mm, 73 * mm])
    meta.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f8fc")), ("BOX", (0, 0), (-1, -1), .5, colors.HexColor("#dbe5f0")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12), ("TOPPADDING", (0, 0), (-1, -1), 11), ("BOTTOMPADDING", (0, 0), (-1, -1), 11)]))
    story += [meta, Spacer(1, 7 * mm)]
    rows = [["Désignation", "Verre / ép.", "Dimensions", "Qté", "Prix / m²", "Montant HT"]]
    for line in devis.lignes.all():
        services = " · ".join(label for enabled, label in [(line.decoupe, "Découpe"), (line.rabotage, "Rabotage"), (line.percage, "Perçage"), (line.trempe, "Trempe")] if enabled)
        if line.autres_prestations:
            services = f"{services} · {line.autres_prestations}" if services else line.autres_prestations
        rows.append([Paragraph(f"<b>{line.description}</b><br/><font size='7'>{services or '—'}</font>", normal), Paragraph(f"{line.type_verre or '—'}<br/>{line.epaisseur or '—'}", small), Paragraph(f"{line.longueur or '—'} × {line.largeur or '—'} mm<br/><font size='7'>{line.surface_unitaire_m2:.4f} m² / pièce</font>", normal), Paragraph(str(line.quantite), right), Paragraph(money(line.prix_unitaire), right), Paragraph(f"<b>{money(line.montant)}</b>", right)])
    table = Table(rows, colWidths=[47 * mm, 30 * mm, 34 * mm, 12 * mm, 27 * mm, 28 * mm], repeatRows=1)
    table.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf1f8")), ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#334155")), ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"), ("FONTSIZE", (0, 0), (-1, 0), 8), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#dbe5f0")), ("VALIGN", (0, 0), (-1, -1), "TOP"), ("LEFTPADDING", (0, 0), (-1, -1), 6), ("RIGHTPADDING", (0, 0), (-1, -1), 6), ("TOPPADDING", (0, 1), (-1, -1), 7), ("BOTTOMPADDING", (0, 1), (-1, -1), 7)]))
    story += [table, Spacer(1, 7 * mm)]
    notes = Paragraph(f"<b>OBSERVATIONS, POSE ET RÈGLEMENT</b><br/><br/>{devis.observations or 'Prix établi sous réserve de validation des dimensions et spécifications techniques.'}<br/><br/>Pose : <b>{'incluse' if devis.pose_incluse else 'non incluse'}</b> · Dimensions sur site : <b>{'validées' if devis.prise_mesures_validee else 'à confirmer'}</b><br/>Règlement : {devis.conditions_paiement}<br/><br/><font size='7'>Bon pour accord : signature précédée de la mention « Lu et approuvé ».</font>", normal)
    totals = Table([["Sous-total HT", money(devis.sous_total)], ["Remise", f"− {money(devis.remise)}"], ["Total HT", money(devis.total_ht)], ["TOTAL TTC", money(devis.total_ttc)]], colWidths=[38 * mm, 43 * mm])
    totals.setStyle(TableStyle([("FONTNAME", (0, 0), (-1, -2), "Helvetica"), ("ALIGN", (1, 0), (1, -1), "RIGHT"), ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#102653")), ("TEXTCOLOR", (0, -1), (-1, -1), colors.white), ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"), ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#dbe5f0")), ("LEFTPADDING", (0, 0), (-1, -1), 8), ("RIGHTPADDING", (0, 0), (-1, -1), 8), ("TOPPADDING", (0, 0), (-1, -1), 7), ("BOTTOMPADDING", (0, 0), (-1, -1), 7)]))
    bottom = Table([[notes, totals]], colWidths=[97 * mm, 81 * mm])
    bottom.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("RIGHTPADDING", (0, 0), (0, 0), 15)]))
    story.append(bottom)
    def footer(canvas, document):
        canvas.saveState(); canvas.setStrokeColor(colors.HexColor("#dbe5f0")); canvas.line(16 * mm, 12 * mm, A4[0] - 16 * mm, 12 * mm); canvas.setFont("Helvetica", 7); canvas.setFillColor(colors.HexColor("#64748b")); canvas.drawString(16 * mm, 8 * mm, f"{societe['nom']} · Devis {devis.reference}"); canvas.drawRightString(A4[0] - 16 * mm, 8 * mm, f"Page {document.page}"); canvas.restoreState()
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    response = HttpResponse(stream.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{devis.reference}.pdf"'
    return response
