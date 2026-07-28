"""
assessment/utils.py

PDF generation for report cards and transcripts, using ReportLab
(pure-Python, no system dependencies -- important for free-tier
hosts like Render where installing wkhtmltopdf/WeasyPrint's native
libs is extra hassle).
"""

from io import BytesIO
from django.conf import settings
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER

from .models import Result


def _header(elements, styles, subtitle):
    title_style = ParagraphStyle("SchoolTitle", parent=styles["Title"], alignment=TA_CENTER, fontSize=16)
    sub_style = ParagraphStyle("Subtitle", parent=styles["Normal"], alignment=TA_CENTER, fontSize=11)
    elements.append(Paragraph(settings.SCHOOL_NAME, title_style))
    elements.append(Paragraph(settings.SCHOOL_ADDRESS, sub_style))
    elements.append(Spacer(1, 6))
    elements.append(Paragraph(subtitle, ParagraphStyle("H2", parent=styles["Heading2"], alignment=TA_CENTER)))
    elements.append(Spacer(1, 10))


def generate_report_card_pdf(report_card):
    """Returns a BytesIO PDF buffer for one student's single-term report card."""
    student = report_card.student
    term = report_card.term
    results = Result.objects.filter(student=student, term=term).select_related("subject")

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements = []

    _header(elements, styles, f"Termly Report Card &mdash; {term}")

    info_data = [
        ["Student Name:", f"{student.first_name} {student.last_name}", "Student ID:", student.student_id],
        ["Class:", str(student.current_class or "-"), "Term:", str(term)],
    ]
    info_table = Table(info_data, colWidths=[80, 170, 80, 170])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    table_data = [["Subject", "CA (40)", "Exam (60)", "Total (100)", "Grade", "Remark"]]
    for r in results:
        table_data.append([
            r.subject.name, str(r.ca_score), str(r.exam_score),
            str(r.total_score), r.grade, r.remark
        ])

    results_table = Table(table_data, colWidths=[150, 60, 65, 70, 50, 90], repeatRows=1)
    results_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3d5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(results_table)
    elements.append(Spacer(1, 14))

    summary_data = [
        ["Average Score:", str(report_card.average_score or "-"), "Class Position:", str(report_card.class_position or "-")],
        ["Attendance:", f"{report_card.attendance_present_days or 0} / {report_card.attendance_total_days or 0} days", "", ""],
    ]
    summary_table = Table(summary_data, colWidths=[90, 160, 90, 90])
    summary_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 14))

    if report_card.class_teacher_comment:
        elements.append(Paragraph(f"<b>Class Teacher's Comment:</b> {report_card.class_teacher_comment}", styles["Normal"]))
        elements.append(Spacer(1, 6))
    if report_card.principal_comment:
        elements.append(Paragraph(f"<b>Principal's Comment:</b> {report_card.principal_comment}", styles["Normal"]))

    elements.append(Spacer(1, 30))
    elements.append(Paragraph("This is a system-generated report card and is valid without a signature.", styles["Italic"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer


def generate_transcript_pdf(student):
    """
    Full academic history across every term the student has results
    for. This is the document restricted to admin-permission staff
    only (see assessment/views.py).
    """
    results = Result.objects.filter(student=student).select_related("subject", "term", "term__session").order_by(
        "term__session", "term__name", "subject__name"
    )

    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20 * mm, bottomMargin=20 * mm)
    styles = getSampleStyleSheet()
    elements = []

    _header(elements, styles, "Official Academic Transcript")

    info_data = [
        ["Student Name:", f"{student.first_name} {student.last_name}", "Student ID:", student.student_id],
        ["Date of Birth:", str(student.date_of_birth), "Date Admitted:", str(student.date_admitted)],
    ]
    info_table = Table(info_data, colWidths=[85, 165, 85, 165])
    info_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(info_table)
    elements.append(Spacer(1, 14))

    current_term = None
    table_data = [["Term", "Subject", "CA", "Exam", "Total", "Grade"]]
    for r in results:
        table_data.append([str(r.term), r.subject.name, str(r.ca_score), str(r.exam_score), str(r.total_score), r.grade])

    transcript_table = Table(table_data, colWidths=[85, 155, 45, 45, 50, 55], repeatRows=1)
    transcript_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f3d5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f2f2")]),
        ("ALIGN", (2, 0), (-1, -1), "CENTER"),
    ]))
    elements.append(transcript_table)
    elements.append(Spacer(1, 30))
    elements.append(Paragraph(
        "This transcript is an official school document. Issued by staff with administrative "
        "permission and valid for institutional/employment verification purposes.",
        styles["Italic"]
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer
