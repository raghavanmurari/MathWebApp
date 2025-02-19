from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from datetime import datetime

def generate_pdf_report(
    student_name,
    days_practiced,
    total_days,
    focus_needed,
    strength,
    table_data
):
    """
    Creates a professionally styled PDF progress report
    
    Args:
        student_name (str): Name of the student
        days_practiced (int): Number of days practiced
        total_days (int): Total possible days
        focus_needed (str): Area needing focus
        strength (str): Area of strength
        table_data (list): List of assignment data rows
    
    Returns:
        bytes: PDF file content
    """
    # Create the document
    doc = SimpleDocTemplate(
        "progress_report.pdf",
        pagesize=A4,
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30
    )
    
    # Styles
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=colors.HexColor('#1a75ff')  # Professional blue
    ))
    styles.add(ParagraphStyle(
        name='SubHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#666666'),
        spaceAfter=12,
        alignment=TA_LEFT
    ))
    
    # Content elements
    elements = []
    
    # Title
    elements.append(Paragraph("Weekly Progress Summary", styles['CustomTitle']))
    
    # Student Info Table
    student_info = [
        ["Student Information", ""],
        ["Student Name:", student_name],
        ["Days Practiced:", f"{days_practiced}"],
        ["Focus Area Needed:", focus_needed],
        ["Area of Strength:", strength]
    ]
    
    info_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f0f7ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a75ff')),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        # Content styling
        ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#333333')),
        ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 1), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 12),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('CELLPADDING', (0, 0), (-1, -1), 8),
        # Highlight days practiced
        ('BACKGROUND', (1, 2), (1, 2), colors.HexColor('#fff7e6')),
    ])
    
    student_table = Table(student_info, colWidths=[200, 300])
    student_table.setStyle(info_style)
    elements.append(student_table)
    elements.append(Spacer(1, 20))
    
    # Assignments Table
    elements.append(Paragraph("Assignment Progress", styles['SubHeading']))
    
    # Headers for the assignments table
    headers = ["Topic", "Sub-Topic", "Created", "Deadline", "Days\nPracticed", "Easy %", "Med %", "Hard %"]
    
    # Prepare table data
    assignment_data = [headers]  # Start with headers
    for row in table_data:
        # Clean and format the data
        created_date = str(row[2]).split(" ")[0]
        deadline_date = str(row[3]).split(" ")[0] if row[3] else ""
        
        formatted_row = [
            str(row[0]),  # Topic
            str(row[1]),  # Sub-Topic
            created_date,
            deadline_date,
            str(row[4]),  # Days Practiced
            str(row[5]).replace('🟢', '').replace('🟡', '').replace('🔴', '').strip(),  # Easy
            str(row[6]).replace('🟢', '').replace('🟡', '').replace('🔴', '').strip(),  # Med
            str(row[7]).replace('🟢', '').replace('🟡', '').replace('🔴', '').strip()   # Hard
        ]
        assignment_data.append(formatted_row)
    
    # Create and style the assignments table
    col_widths = [80, 140, 70, 70, 60, 50, 50, 50]
    assignment_table = Table(assignment_data, colWidths=col_widths, repeatRows=1)
    
    assignment_style = TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a75ff')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        # Content styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),  # Center-align dates and numbers
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ('CELLPADDING', (0, 0), (-1, -1), 8),
        # Alternate row colors
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f8f9fa')]),
        # Highlight days practiced column
        ('BACKGROUND', (4, 1), (4, -1), colors.HexColor('#fff7e6')),
    ])
    
    assignment_table.setStyle(assignment_style)
    elements.append(assignment_table)
    
    # Footer
    elements.append(Spacer(1, 30))
    footer_text = f"""
    Thank you for your continued support!<br/>
    <font size=9>Report generated on {datetime.now().strftime('%B %d, %Y')}</font>
    """
    elements.append(Paragraph(footer_text, ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        alignment=TA_CENTER,
        textColor=colors.HexColor('#666666')
    )))
    
    # Build the PDF
    doc.build(elements)
    
    # Read the generated PDF and return its contents
    with open("progress_report.pdf", "rb") as f:
        pdf_content = f.read()
    
    return pdf_content