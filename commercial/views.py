from io import BytesIO

from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from commandes.services import transformer_devis
from .forms import DemandeDevisForm, DevisForm, LigneDevisForm
from .models import DemandeDevis, Devis
from .services import changer_statut_devis


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
    form = DevisForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        devis = form.save(commit=False)
        devis.cree_par = request.user
        devis.save()
        return redirect("commercial:detail", pk=devis.pk)
    return render(request, "commercial/devis_form.html", {"form": form})


@permission_required("commercial.view_devis", raise_exception=True)
def detail(request, pk):
    devis = get_object_or_404(Devis.objects.select_related("client"), pk=pk)
    return render(request, "commercial/detail.html", {"devis": devis, "ligne_form": LigneDevisForm()})


@permission_required("commercial.change_devis", raise_exception=True)
def ajouter_ligne(request, pk):
    devis = get_object_or_404(Devis, pk=pk)
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
            changer_statut_devis(devis, statut, request.user, request.POST.get("commentaire", ""))
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
    devis = get_object_or_404(Devis.objects.select_related("client"), pk=pk)
    from reportlab.pdfgen.canvas import Canvas

    stream = BytesIO()
    canvas = Canvas(stream)
    canvas.setFont("Helvetica-Bold", 16)
    canvas.drawString(50, 800, f"DEVIS {devis.reference}")
    canvas.setFont("Helvetica", 10)
    canvas.drawString(50, 775, devis.client.nom)
    y = 730
    for line in devis.lignes.all():
        detail = f"{line.description} - {line.quantite} x {line.surface_unitaire_m2} m2 x {line.prix_unitaire} FCFA/m2 = {line.montant} FCFA"
        canvas.drawString(50, y, detail[:110])
        y -= 20
    canvas.drawString(50, y - 20, f"Total TTC : {devis.total_ttc} FCFA")
    canvas.save()
    response = HttpResponse(stream.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{devis.reference}.pdf"'
    return response
