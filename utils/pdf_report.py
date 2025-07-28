from fpdf import FPDF
import os
import tempfile
import cv2

class PDFReport(FPDF):
    def header(self):
        self.set_font("Arial", "B", 10)
        self.cell(0, 10, "Tracking Report", ln=True, align="C")
        self.ln(10)

def generate_pdf_report(df_counts, preview_frame, graph_path, video_filename):
    from datetime import datetime
    pdf = PDFReport()
    pdf.add_page()
    # Add date/time and video length metadata in small font at the top right
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # Estimate video duration (if actual duration not passed)
    duration_sec = int(preview_frame.shape[1] / 30)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 10, f"Created: {timestamp}     Video Length: ~{duration_sec} sec", ln=True, align="R")
    pdf.cell(0, 10, f"Video File: {video_filename}", ln=True, align="R")
    pdf.ln(5)

    # Subheader: Video Tracking Preview
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Video Tracking Preview", ln=True)

    # Add image preview
    frame_path = os.path.join(tempfile.gettempdir(), "preview_frame.jpg")
    cv2.imwrite(frame_path, cv2.cvtColor(preview_frame, cv2.COLOR_RGB2BGR))
    pdf.image(frame_path, x=10, y=None, w=180)

    pdf.add_page()
    pdf.ln(10)
    # Subheader: Detection Count Plot
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Detection Count Plot", ln=True)

    # Add graph
    pdf.image(graph_path, x=10, y=None, w=180)


    pdf.add_page()
    pdf.ln(10)
    # Subheader: Detection Counts Table
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Detection Counts Table", ln=True)

    # Add detection count table, cleaner formatting
    col_widths = [45, 45]
    row_height = 8
    pdf.set_font("Arial", "B", 12)
    pdf.cell(col_widths[0], row_height, "Second", border=1, align="C")
    pdf.cell(col_widths[1], row_height, "Unique IDs", border=1, ln=True, align="C")

    pdf.set_font("Arial", "", 12)
    for _, row in df_counts.iterrows():
        pdf.cell(col_widths[0], row_height, str(row["Second"]), border=1, align="C")
        pdf.cell(col_widths[1], row_height, str(row["Unique IDs"]), border=1, ln=True, align="C")

    # Save PDF
    pdf_path = os.path.join(tempfile.gettempdir(), "tracking_report.pdf")
    pdf.output(pdf_path)
    return pdf_path