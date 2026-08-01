"""
students/utils.py

PDF generation for the applicant's own application summary -- a
simple one-page confirmation they can download anytime while their
application is pending (or after a decision), showing what was
submitted and the current status.
"""

from io import BytesIO
from django.conf import settings
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors


def generate_application_summary_pdf(application):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle("Title", parent=styles["Title"], alignment=TA_CENTER, fontSize=16)
    sub_style = ParagraphStyle("Sub", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11)
    elements.append(Paragraph(settings.SCHOOL_NAME, title_style))
    elements.append(Paragraph(settings.SCHOOL_ADDRESS, sub_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("Admission Application Summary", ParagraphStyle("H2", parent=styles["Heading2"], alignment=TA_CENTER)))
    elements.append(Spacer(1, 14))

    grade_line = f"Grade {application.applying_for_grade}" if application.applying_for_grade else "Not yet specified"
    if application.applying_for_track:
        grade_line += f" - {application.get_applying_for_track_display()}"

    rows = [
        ["Reference Number:", f"#{application.id}"],
        ["Full Name:", f"{application.first_name} {application.last_name}"],
        ["Date of Birth:", str(application.date_of_birth) if application.date_of_birth else "Not yet specified"],
        ["Gender:", application.get_gender_display()],
        ["Applying for:", grade_line],
        ["Guardian:", f"{application.guardian_name or '-'} ({application.guardian_phone or '-'})"],
        ["Previous School:", application.previous_school or "-"],
        ["Submitted On:", application.submitted_on.strftime("%d %B %Y")],
        ["Status:", application.get_status_display()],
    ]
    table = Table(rows, colWidths=[130, 320])
    table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.lightgrey),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 24))

    if application.status == application.Status.ACCEPTED and hasattr(application, "student_record"):
        elements.append(Paragraph(
            f"<b>Congratulations!</b> This application has been accepted. Student ID: "
            f"<b>{application.student_record.student_id}</b>.",
            styles["Normal"]
        ))
    elif application.status == application.Status.PENDING:
        elements.append(Paragraph("This application is still under review. Check back on the portal for updates.", styles["Normal"]))
    else:
        elements.append(Paragraph("This application was not successful.", styles["Normal"]))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph("This is a system-generated document and is valid without a signature.", styles["Italic"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer
