"""
Generator Script for Enterprise Architecture Diagram (PDF & PNG)
Uses Matplotlib & ReportLab to produce high-resolution, vector-quality architecture deliverables.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from reportlab.lib.pagesizes import letter, landscape
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

ROOT = Path(__file__).resolve().parents[1]
ARCH_DIR = ROOT / "architecture"
ARCH_DIR.mkdir(parents=True, exist_ok=True)
PNG_PATH = ARCH_DIR / "Architecture_Diagram.png"
PDF_PATH = ARCH_DIR / "Architecture_Diagram.pdf"


def generate_architecture_image():
    fig, ax = plt.subplots(figsize=(14, 8), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Background
    fig.patch.set_facecolor('#F8FAFC')
    ax.set_facecolor('#F8FAFC')

    # Header
    ax.text(50, 95, "HEALTHCARE PATIENT MANAGEMENT SYSTEM", fontsize=18, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 91.5, "Enterprise Microservice & Distributed Relational Architecture", fontsize=11, ha='center', color='#0D9488')

    # Box styles
    def draw_box(x, y, w, h, title, subtitle, items, bg_color, border_color):
        rect = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.5", linewidth=1.5, edgecolor=border_color, facecolor=bg_color)
        ax.add_patch(rect)
        ax.text(x + w/2, y + h - 4, title, fontsize=12, fontweight='bold', ha='center', color='#0F172A')
        ax.text(x + w/2, y + h - 8, subtitle, fontsize=9, fontstyle='italic', ha='center', color='#64748B')
        for idx, item in enumerate(items):
            ax.text(x + 3, y + h - 14 - (idx * 4), f"• {item}", fontsize=9, color='#1E293B')

    # Layer 1: Data Ingestion
    draw_box(
        4, 25, 20, 58,
        "DATA INGESTION (ETL)",
        "Raw & Ingestion Layer",
        [
            "UCI 130-US Hospitals",
            "100K+ Inpatient Records",
            "Pandas Cleaning Engine",
            "Deduplication Filter",
            "Missing Value Imputer",
            "ICD-9 Normalizer",
            "Incremental Loader (CDC)"
        ],
        '#FFFFFF', '#0D9488'
    )

    # Layer 2: Storage
    draw_box(
        27, 25, 21, 58,
        "STORAGE LAYER",
        "Relational Core",
        [
            "Dual-Engine Connector",
            "MySQL (Production)",
            "SQLite (Zero-Friction)",
            "3NF Relational Model",
            "patients (Master)",
            "encounters (Fact)",
            "encounter_diagnoses",
            "encounter_medications",
            "audit_logs (Compliance)"
        ],
        '#FFFFFF', '#2563EB'
    )

    # Layer 3: REST API
    draw_box(
        51, 25, 21, 58,
        "MICROSERVICE (API)",
        "FastAPI Service Layer",
        [
            "OAuth2 + JWT Auth",
            "Argon2 Security",
            "Role-Based Access (RBAC)",
            "Admin / Staff / Analyst",
            "Patient & Encounter CRUD",
            "Aggregation Engine",
            "CSV / Excel Exporters",
            "Audit Interceptor"
        ],
        '#FFFFFF', '#7C3AED'
    )

    # Layer 4: Presentation
    draw_box(
        75, 25, 21, 58,
        "PRESENTATION LAYER",
        "Streamlit Clinical UI",
        [
            "Deep Navy & Teal Theme",
            "Role-Gated Navigation",
            "KPI Performance Cards",
            "Readmission Analytics",
            "Length of Stay Histograms",
            "Patient Timeline Viewer",
            "Admission Operations",
            "Audit Compliance Log"
        ],
        '#FFFFFF', '#0D9488'
    )

    # Arrows connecting boxes
    arrow_props = dict(arrowstyle="->", lw=2, color="#0F172A")
    ax.annotate("", xy=(26, 54), xytext=(24.5, 54), arrowprops=arrow_props)
    ax.annotate("", xy=(50, 54), xytext=(48.5, 54), arrowprops=arrow_props)
    ax.annotate("", xy=(74, 54), xytext=(72.5, 54), arrowprops=arrow_props)

    # Security Footnote Banner
    banner = patches.FancyBboxPatch((4, 6), 92, 12, boxstyle="round,pad=1", linewidth=1, edgecolor='#CBD5E1', facecolor='#F1F5F9')
    ax.add_patch(banner)
    ax.text(50, 14, "ENTERPRISE SECURITY & AUDIT TRAIL ARCHITECTURE", fontsize=10, fontweight='bold', ha='center', color='#0F172A')
    ax.text(50, 9.5, "Strict Role Enforcement: Admin (User Admin, Audits) | Healthcare Staff (Patient CRUD, Admissions) | Analyst (Aggregations, CSV/Excel Reports)", fontsize=8.5, ha='center', color='#475569')

    plt.tight_layout()
    plt.savefig(PNG_PATH, dpi=300)
    plt.close()
    print(f"Generated {PNG_PATH}")


def generate_architecture_pdf():
    c = canvas.Canvas(str(PDF_PATH), pagesize=landscape(letter))
    c.drawImage(str(PNG_PATH), 20, 30, width=750, height=540)
    c.save()
    print(f"Generated {PDF_PATH}")


if __name__ == "__main__":
    generate_architecture_image()
    generate_architecture_pdf()
