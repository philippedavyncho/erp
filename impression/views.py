from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.urls import reverse
try:
    from reportlab.lib.pagesizes import A6
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen.canvas import Canvas
except ImportError:
    A6 = Canvas = ImageReader = None
from chutes.models import Chute
from production.models import PieceProduction
@login_required
def etiquette(request, pk):
    c=Chute.objects.select_related("type_verre","epaisseur","teinte","emplacement").get(pk=pk)
    if Canvas is None:
        return HttpResponse("Installez reportlab (pip install -r requirements.txt) pour générer les PDF.", status=503)
    stream=BytesIO(); pdf=Canvas(stream,pagesize=A6)
    pdf.setFont("Helvetica-Bold",16); pdf.drawString(18,280,f"Chute {c.numero}"); pdf.setFont("Helvetica",10)
    for i,line in enumerate([f"Dimensions : {c.longueur} x {c.largeur} mm",f"Surface : {c.surface} m2",f"Type : {c.type_verre}",f"Epaisseur : {c.epaisseur}",f"Teinte : {c.teinte}",f"Emplacement : {c.emplacement}",f"QR : {c.code_qr}"]): pdf.drawString(18,250-i*25,line)
    pdf.save(); response=HttpResponse(stream.getvalue(),content_type="application/pdf"); response["Content-Disposition"]=f'inline; filename="{c.numero}.pdf"'; return response


@login_required
def etiquette_piece(request, pk):
    if not request.user.has_perm("production.view_ficheproduction"):
        return HttpResponse(status=403)
    piece = get_object_or_404(
        PieceProduction.objects.select_related(
            "fiche__commande__client", "ligne_commande__type_verre", "ligne_commande__epaisseur"
        ), pk=pk,
    )
    if Canvas is None:
        return HttpResponse("Installez reportlab (pip install -r requirements.txt) pour générer les PDF.", status=503)
    try:
        import qrcode
    except ImportError:
        return HttpResponse("Installez qrcode (pip install -r requirements.txt) pour générer les étiquettes QR.", status=503)

    piece_url = request.build_absolute_uri(reverse("production:piece", args=[piece.pk]))
    qr_buffer = BytesIO()
    qrcode.make(piece_url).save(qr_buffer, format="PNG")
    qr_buffer.seek(0)
    qr_image = ImageReader(qr_buffer)
    stream = BytesIO()
    pdf = Canvas(stream, pagesize=A6)
    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(18, 280, f"Pièce {piece.reference}")
    pdf.setFont("Helvetica", 10)
    line = piece.ligne_commande
    lines = [
        f"Commande : {piece.fiche.commande.reference}",
        f"Client : {piece.fiche.commande.client.nom}",
        f"Dimensions : {line.longueur or '—'} x {line.largeur or '—'} mm",
        f"Matière : {line.type_verre or '—'} · ép. {line.epaisseur or '—'}",
        f"Quantité : {piece.quantite}",
    ]
    for index, value in enumerate(lines):
        pdf.drawString(18, 252 - index * 20, value)
    pdf.drawImage(qr_image, 168, 45, width=110, height=110, mask="auto")
    pdf.setFont("Helvetica", 7)
    pdf.drawString(18, 25, "Scannez ce code pour confirmer les opérations de cette pièce.")
    pdf.save()
    response = HttpResponse(stream.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="{piece.reference}.pdf"'
    return response
