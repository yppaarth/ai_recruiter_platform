import io
import csv
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Campaign, Contact, Email


def export_campaign_csv(campaign_id: str, db: Session) -> bytes:
    """Export campaign contacts and stats as CSV."""
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError("Campaign not found")

    contacts = db.query(Contact).filter(Contact.campaign_id == campaign_id).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Name", "Email", "Company", "Title", "Status",
        "Open Count", "Click Count", "Replied", "Reply At",
    ])

    for contact in contacts:
        writer.writerow([
            contact.name,
            contact.email,
            contact.company or "",
            contact.title or "",
            contact.status,
            contact.open_count,
            contact.click_count,
            "Yes" if contact.has_replied else "No",
            contact.reply_at.isoformat() if contact.reply_at else "",
        ])

    return output.getvalue().encode("utf-8")


def export_campaign_excel(campaign_id: str, db: Session) -> bytes:
    """Export campaign data as Excel file."""
    try:
        import xlsxwriter
    except ImportError:
        raise ValueError("xlsxwriter not installed")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError("Campaign not found")

    contacts = db.query(Contact).filter(Contact.campaign_id == campaign_id).all()

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # Formats
    header_fmt = workbook.add_format({
        "bold": True, "bg_color": "#2563EB", "font_color": "white",
        "border": 1, "align": "center",
    })
    cell_fmt = workbook.add_format({"border": 1})
    percent_fmt = workbook.add_format({"border": 1, "num_format": "0.0%"})

    # Contacts sheet
    ws = workbook.add_worksheet("Contacts")
    headers = ["Name", "Email", "Company", "Title", "Status", "Opens", "Clicks", "Replied"]
    for col, h in enumerate(headers):
        ws.write(0, col, h, header_fmt)
        ws.set_column(col, col, 20)

    for row, contact in enumerate(contacts, 1):
        ws.write(row, 0, contact.name, cell_fmt)
        ws.write(row, 1, contact.email, cell_fmt)
        ws.write(row, 2, contact.company or "", cell_fmt)
        ws.write(row, 3, contact.title or "", cell_fmt)
        ws.write(row, 4, contact.status, cell_fmt)
        ws.write(row, 5, contact.open_count, cell_fmt)
        ws.write(row, 6, contact.click_count, cell_fmt)
        ws.write(row, 7, "Yes" if contact.has_replied else "No", cell_fmt)

    # Summary sheet
    ws2 = workbook.add_worksheet("Summary")
    total = len(contacts)
    sent = sum(1 for c in contacts if c.status not in ("pending", "failed"))
    opened = sum(1 for c in contacts if c.open_count > 0)
    clicked = sum(1 for c in contacts if c.click_count > 0)
    replied = sum(1 for c in contacts if c.has_replied)

    summary_data = [
        ["Campaign", campaign.name],
        ["Status", campaign.status],
        ["Created", campaign.created_at.strftime("%Y-%m-%d")],
        ["Total Contacts", total],
        ["Sent", sent],
        ["Opened", opened],
        ["Clicked", clicked],
        ["Replied", replied],
        ["Open Rate", opened / max(sent, 1)],
        ["Click Rate", clicked / max(sent, 1)],
        ["Reply Rate", replied / max(sent, 1)],
    ]
    for row, (label, value) in enumerate(summary_data):
        ws2.write(row, 0, label, header_fmt)
        if isinstance(value, float):
            ws2.write(row, 1, value, percent_fmt)
        else:
            ws2.write(row, 1, value, cell_fmt)

    workbook.close()
    return output.getvalue()


def export_campaign_pdf(campaign_id: str, db: Session) -> bytes:
    """Export campaign analytics report as PDF."""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.units import inch
    except ImportError:
        raise ValueError("reportlab not installed")

    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise ValueError("Campaign not found")

    contacts = db.query(Contact).filter(Contact.campaign_id == campaign_id).all()

    output = io.BytesIO()
    doc = SimpleDocTemplate(output, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = ParagraphStyle("Title", parent=styles["Title"], textColor=colors.HexColor("#2563EB"))
    story.append(Paragraph(f"Campaign Report: {campaign.name}", title_style))
    story.append(Spacer(1, 0.25 * inch))

    # Meta
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles["Normal"]))
    story.append(Paragraph(f"Status: {campaign.status}", styles["Normal"]))
    story.append(Spacer(1, 0.25 * inch))

    # Stats table
    total = len(contacts)
    sent = sum(1 for c in contacts if c.status not in ("pending", "failed"))
    opened = sum(1 for c in contacts if c.open_count > 0)
    clicked = sum(1 for c in contacts if c.click_count > 0)
    replied = sum(1 for c in contacts if c.has_replied)

    stats_data = [
        ["Metric", "Value", "Rate"],
        ["Total Contacts", str(total), "-"],
        ["Sent", str(sent), "100%"],
        ["Opened", str(opened), f"{opened/max(sent,1)*100:.1f}%"],
        ["Clicked", str(clicked), f"{clicked/max(sent,1)*100:.1f}%"],
        ["Replied", str(replied), f"{replied/max(sent,1)*100:.1f}%"],
    ]

    table = Table(stats_data, colWidths=[2.5 * inch, 1.5 * inch, 1.5 * inch])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2563EB")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F3F4F6")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(table)

    if campaign.ai_summary:
        story.append(Spacer(1, 0.25 * inch))
        story.append(Paragraph("AI Insights", styles["Heading2"]))
        story.append(Paragraph(campaign.ai_summary, styles["Normal"]))

    doc.build(story)
    return output.getvalue()
