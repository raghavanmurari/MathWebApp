from fpdf import FPDF

def generate_pdf_report(
    student_name,
    days_practiced,
    total_days,
    focus_needed,
    strength,
    table_data
):
    """
    Creates a PDF with the student's weekly progress summary,
    showing each Topic/Sub-Topic in a simple list format.
    
    :param student_name: str - The student's name
    :param days_practiced: int - Total days practiced by the student
    :param total_days: int - Total possible days
    :param focus_needed: str - Difficulty or area needing focus
    :param strength: str - Difficulty or area where the student is strong
    :param table_data: list of rows, each row is:
       [Topic, Sub-Topic, Created Date, Deadline, Days Practiced, EasyAcc, MedAcc, HardAcc]
    :return: PDF data as bytes (so we can download directly in Streamlit)
    """
    pdf = FPDF()
    pdf.add_page()

    # Title
    pdf.set_font("Arial", "B", size=14)
    pdf.cell(200, 10, txt="Weekly Progress Summary", ln=True, align="C")

    pdf.ln(5)

    # Student Info
    pdf.set_font("Arial", "", size=12)
    pdf.cell(200, 8, txt=f"Student Name: {student_name}", ln=True)
    pdf.cell(200, 8, txt=f"Days Practiced: {days_practiced} out of {total_days}", ln=True)
    pdf.cell(200, 8, txt=f"Focus Needed: {focus_needed}", ln=True)
    pdf.cell(200, 8, txt=f"Strength: {strength}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 8, txt="Assignment Details:", ln=True)
    pdf.set_font("Arial", "", size=11)

    # For each row in table_data, print a simple list
    for row in table_data:
        # row structure: [Topic, Sub-Topic, Created, Deadline, Days, EasyAcc, MedAcc, HardAcc]
        topic = str(row[0])
        sub_topic = str(row[1])
        created_date = str(row[2])
        deadline_date = str(row[3])
        days = str(row[4])
        
        pdf.ln(3)  # small spacing before each assignment block
        pdf.cell(200, 6, txt=f"- Topic: {topic}", ln=True)
        pdf.cell(200, 6, txt=f"   Sub-Topic: {sub_topic}", ln=True)
        pdf.cell(200, 6, txt=f"   Created: {created_date}", ln=True)
        pdf.cell(200, 6, txt=f"   Deadline: {deadline_date}", ln=True)
        pdf.cell(200, 6, txt=f"   Days Practiced: {days}", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "", size=12)
    pdf.cell(200, 10, txt="Thank you for your continued support!", ln=True)

    return pdf.output(dest="S").encode("latin-1")
