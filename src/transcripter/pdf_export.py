"""
PDF Export Module

Generates structured PDF reports from meeting summaries.
Uses reportlab for PDF generation (lightweight alternative to fpdf).
"""

from typing import List, Optional
from pathlib import Path


def export_to_pdf(
    summary: str,
    action_items: List[str],
    highlights: List[str],
    topics: List[str],
    output_path: Optional[str] = None
) -> bytes:
    """
    Export meeting summary to PDF.
    
    Creates a structured PDF with sections for:
    - Summary
    - Action Items
    - Highlights
    - Topics
    
    Args:
        summary: Meeting summary text
        action_items: List of action items
        highlights: List of highlights
        topics: List of topics/keywords
        output_path: Optional path to save PDF file. If None, returns bytes.
        
    Returns:
        PDF file as bytes (if output_path is None)
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from io import BytesIO
    except ImportError:
        # Fallback to fpdf if reportlab is not available
        return _export_to_pdf_fpdf(summary, action_items, highlights, topics, output_path)
    
    # Create buffer or file
    if output_path:
        doc = SimpleDocTemplate(output_path, pagesize=letter)
        buffer = None
    else:
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
    
    # Container for PDF content
    story = []
    
    # Styles
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor='#1f77b4',
        spaceAfter=30,
        alignment=TA_CENTER
    )
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor='#2c3e50',
        spaceAfter=12,
        spaceBefore=20
    )
    normal_style = styles['Normal']
    bullet_style = ParagraphStyle(
        'Bullet',
        parent=styles['Normal'],
        leftIndent=20,
        spaceAfter=8
    )
    
    # Title
    story.append(Paragraph("Meeting Summary", title_style))
    story.append(Spacer(1, 0.3 * inch))
    
    # Summary Section
    if summary:
        story.append(Paragraph("Summary", heading_style))
        # Split summary into paragraphs
        summary_paragraphs = summary.split('\n')
        for para in summary_paragraphs:
            if para.strip():
                story.append(Paragraph(para.strip(), normal_style))
                story.append(Spacer(1, 0.1 * inch))
        story.append(Spacer(1, 0.2 * inch))
    
    # Action Items Section
    if action_items:
        story.append(Paragraph("Action Items", heading_style))
        for item in action_items:
            # Remove leading "- " if present
            clean_item = item.lstrip("- ").strip()
            story.append(Paragraph(f"• {clean_item}", bullet_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Highlights Section
    if highlights:
        story.append(Paragraph("Highlights", heading_style))
        for highlight in highlights:
            # Remove leading "- " if present
            clean_highlight = highlight.lstrip("- ").strip()
            story.append(Paragraph(f"• {clean_highlight}", bullet_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Topics Section
    if topics:
        story.append(Paragraph("Topics", heading_style))
        topics_text = ", ".join(topics)
        story.append(Paragraph(topics_text, normal_style))
        story.append(Spacer(1, 0.2 * inch))
    
    # Build PDF
    doc.build(story)
    
    # Return bytes if buffer was used
    if buffer:
        buffer.seek(0)
        return buffer.getvalue()
    
    # If file was saved, read and return bytes
    if output_path:
        with open(output_path, 'rb') as f:
            return f.read()
    
    return b''


def _export_to_pdf_fpdf(
    summary: str,
    action_items: List[str],
    highlights: List[str],
    topics: List[str],
    output_path: Optional[str] = None
) -> bytes:
    """
    Fallback PDF export using fpdf (lighter weight than reportlab).
    """
    try:
        try:
            from fpdf import FPDF
        except ImportError:
            from fpdf2 import FPDF
        from io import BytesIO
    except ImportError:
        raise ImportError(
            "Either reportlab or fpdf2 is required for PDF export. "
            "Install with: pip install reportlab or pip install fpdf2"
        )
    
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Title
    pdf.set_font("Arial", "B", 20)
    pdf.set_text_color(31, 119, 180)  # Blue color
    pdf.cell(0, 10, "Meeting Summary", ln=True, align="C")
    pdf.ln(10)
    
    # Summary
    if summary:
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(44, 62, 80)  # Dark gray
        pdf.cell(0, 10, "Summary", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)  # Black
        # Split summary into lines that fit
        summary_lines = summary.split('\n')
        for line in summary_lines:
            if line.strip():
                pdf.multi_cell(0, 7, line.strip())
                pdf.ln(3)
        pdf.ln(5)
    
    # Action Items
    if action_items:
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, "Action Items", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        for item in action_items:
            clean_item = item.lstrip("- ").strip()
            pdf.cell(10, 7, "•", ln=False)
            pdf.multi_cell(0, 7, clean_item)
            pdf.ln(2)
        pdf.ln(5)
    
    # Highlights
    if highlights:
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, "Highlights", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        for highlight in highlights:
            clean_highlight = highlight.lstrip("- ").strip()
            pdf.cell(10, 7, "•", ln=False)
            pdf.multi_cell(0, 7, clean_highlight)
            pdf.ln(2)
        pdf.ln(5)
    
    # Topics
    if topics:
        pdf.set_font("Arial", "B", 14)
        pdf.set_text_color(44, 62, 80)
        pdf.cell(0, 10, "Topics", ln=True)
        pdf.ln(5)
        pdf.set_font("Arial", "", 11)
        pdf.set_text_color(0, 0, 0)
        topics_text = ", ".join(topics)
        pdf.multi_cell(0, 7, topics_text)
    
    # Output
    if output_path:
        pdf.output(output_path)
        with open(output_path, 'rb') as f:
            return f.read()
    else:
        # For fpdf, output to string and encode
        try:
            # fpdf2 uses output(dest='S') which returns string
            pdf_string = pdf.output(dest='S')
            return pdf_string.encode('latin-1')
        except TypeError:
            # Some versions might need different approach
            buffer = BytesIO()
            pdf.output(buffer)
            buffer.seek(0)
            return buffer.getvalue()

