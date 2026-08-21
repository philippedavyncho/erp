from io import BytesIO
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
try:
    from reportlab.lib.pagesizes import A6
    from reportlab.pdfgen.canvas import Canvas
except ImportError:
    A6 = Canvas = None
from chutes.models import Chute
@login_required
def etiquette(request, pk):
    c=Chute.objects.select_related("type_verre","epaisseur","teinte","emplacement").get(pk=pk)
    if Canvas is None:
        return HttpResponse("Installez reportlab (pip install -r requirements.txt) pour générer les PDF.", status=503)
    stream=BytesIO(); pdf=Canvas(stream,pagesize=A6)
    pdf.setFont("Helvetica-Bold",16); pdf.drawString(18,280,f"Chute {c.numero}"); pdf.setFont("Helvetica",10)
    for i,line in enumerate([f"Dimensions : {c.longueur} x {c.largeur} mm",f"Surface : {c.surface} m2",f"Type : {c.type_verre}",f"Epaisseur : {c.epaisseur}",f"Teinte : {c.teinte}",f"Emplacement : {c.emplacement}",f"QR : {c.code_qr}"]): pdf.drawString(18,250-i*25,line)
    pdf.save(); response=HttpResponse(stream.getvalue(),content_type="application/pdf"); response["Content-Disposition"]=f'inline; filename="{c.numero}.pdf"'; return response
