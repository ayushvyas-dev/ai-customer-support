"""Generates a professional, human-readable multi-page PDF document for Nexa Mobile smartphones.

Uses ReportLab to produce a standard, beautifully formatted PDF document that opens cleanly
in any PDF viewer (Adobe Acrobat, Chrome, Firefox, Evince, Preview, VS Code).
"""

from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import (
    HRFlowable,
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page count and footer."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, total_pages: int):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748B"))

        # Header (pages after page 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "NEXA HORIZON ULTRA (2026 EDITION) — USER GUIDE & SPECIFICATIONS")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.5)
            self.line(54, 744, 558, 744)

        # Footer (all pages)
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.5)
        self.line(54, 45, 558, 45)

        footer_left = "Nexa Mobile Technologies Pvt. Ltd. | Confidential & Proprietary"
        footer_right = f"Page {self._pageNumber} of {total_pages}"
        self.drawString(54, 32, footer_left)
        self.drawRightString(558, 32, footer_right)

        self.restoreState()


def build_pdf(output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=54,
        rightMargin=54,
        topMargin=54,
        bottomMargin=54,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=colors.HexColor("#0F172A"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "DocSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#2563EB"),
        spaceAfter=14,
    )

    h1_style = ParagraphStyle(
        "SectionH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=17,
        textColor=colors.HexColor("#1E293B"),
        spaceBefore=12,
        spaceAfter=6,
    )

    body_style = ParagraphStyle(
        "BodyDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9.5,
        leading=14,
        textColor=colors.HexColor("#334155"),
        spaceAfter=8,
    )

    bullet_style = ParagraphStyle(
        "BulletDark",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13.5,
        textColor=colors.HexColor("#334155"),
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=4,
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
    )

    table_cell_bold = ParagraphStyle(
        "TableCellBold",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#0F172A"),
    )

    table_cell_body = ParagraphStyle(
        "TableCellBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#334155"),
    )

    story = []

    # ================= PAGE 1 =================
    story.append(Paragraph("NEXA HORIZON ULTRA (2026 EDITION)", title_style))
    story.append(Paragraph("Official Flagship User Guide, System Documentation & Technical Specifications", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2563EB"), spaceAfter=14))

    story.append(Paragraph("1. Product Overview and Pre-installed Operating System", h1_style))
    story.append(Paragraph(
        "The Nexa Horizon Ultra (2026 Edition) represents the pinnacle of next-generation mobile engineering. "
        "It arrives pre-configured with certified <b>Android 16</b> out of the box, running the lightweight <b>NexaOS 4.0</b> "
        "user environment with full Google Mobile Services (GMS) certification.",
        body_style,
    ))
    story.append(Paragraph("&bull; <b>Pre-installed Android 16 & GMS:</b> Certified out of the box with the full Google Mobile Services suite, including Google Play Store, Chrome, Google Maps, Google Photos, and Google Gemini Nano on-device AI integration.", bullet_style))
    story.append(Paragraph("&bull; <b>Extended Software Commitment:</b> Guaranteed 5 major Android OS version upgrades (Android 16 through Android 21) and 7 years of bi-monthly security patches delivered over-the-air (OTA).", bullet_style))
    story.append(Paragraph("&bull; <b>Zero Bloatware Guarantee:</b> Pure clean OS build with zero third-party pre-installed trialware, adware, or intrusive telemetry services.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("2. Core Hardware Architecture and Computational Engine", h1_style))

    spec_data_p1 = [
        [Paragraph("Specification Component", table_header_style), Paragraph("Hardware Configuration & Details", table_header_style)],
        [Paragraph("Processor / SoC", table_cell_bold), Paragraph("Qualcomm Snapdragon 8 Gen 5 Extreme Edition (TSMC 3nm foundry process, octa-core architecture up to 4.4 GHz)", table_cell_body)],
        [Paragraph("AI Engine (NPU)", table_cell_bold), Paragraph("Dual-Core Nexa Neural Core v4 with 65 TOPS on-device INT4/FP16 neural inference acceleration", table_cell_body)],
        [Paragraph("System Memory (RAM)", table_cell_bold), Paragraph("16 GB or 24 GB high-speed quad-channel LPDDR5X (8,533 Mbps transfer rate)", table_cell_body)],
        [Paragraph("Internal Storage", table_cell_bold), Paragraph("512 GB or 1 TB ultra-fast UFS 4.1 dual-lane non-volatile flash storage", table_cell_body)],
        [Paragraph("Chassis Materials", table_cell_bold), Paragraph("Aerospace-grade Grade 5 Titanium perimeter frame with matte anti-glare ceramic back panel", table_cell_body)],
        [Paragraph("Available Colorways", table_cell_bold), Paragraph("Cosmic Titanium, Stellar Nebula Blue, and Obsidian Satin Black", table_cell_body)],
    ]

    t1 = Table(spec_data_p1, colWidths=[1.8 * inch, 5.2 * inch])
    t1.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t1)

    story.append(PageBreak())

    # ================= PAGE 2 =================
    story.append(Paragraph("3. ProXDR LTPO 4.0 Display Technology", h1_style))
    story.append(Paragraph(
        "The Horizon Ultra introduces the revolutionary 6.82-inch micro-curved ProXDR AMOLED display, "
        "designed for uncompromising outdoor sunlight legibility and color accuracy for content creators.",
        body_style,
    ))
    story.append(Paragraph("&bull; <b>Resolution and Density:</b> 3168 &times; 1440 pixels (Quad HD+ resolution) at an ultra-sharp 510 pixels per inch (PPI).", bullet_style))
    story.append(Paragraph("&bull; <b>Adaptive 1Hz–144Hz LTPO:</b> Dynamic LTPO 4.0 backplane switches seamlessly from 1Hz for static Always-On Display (AOD) up to 144Hz for extreme high-frame gaming.", bullet_style))
    story.append(Paragraph("&bull; <b>Luminance & HDR:</b> Industry-leading 4,500 nits local peak HDR luminance, 1,800 nits High Brightness Mode (HBM), with Dolby Vision and HDR10+ certification.", bullet_style))
    story.append(Paragraph("&bull; <b>Eye Safety & Glass:</b> 2,160Hz PWM high-frequency dimming with TUV Rheinland flicker-free certification. Protected by scratch-resistant Corning Gorilla Glass Armor with 75% surface reflection reduction.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("4. 3D Ultrasonic Biometrics, Security & Acoustic Architecture", h1_style))

    spec_data_p2 = [
        [Paragraph("Security & Audio Subsystem", table_header_style), Paragraph("Engineering Architecture & Capabilities", table_header_style)],
        [Paragraph("Fingerprint Scanner", table_cell_bold), Paragraph("Qualcomm 3D Sonic Max Gen 3 ultrasonic in-display scanner; recognizes dry, damp, wet, and oily fingers in 0.12 seconds", table_cell_body)],
        [Paragraph("Facial Recognition", table_cell_bold), Paragraph("Sub-surface 3D structured light infrared face scanner providing zero-light biometric authentication", table_cell_body)],
        [Paragraph("Security Enclave", table_cell_bold), Paragraph("Dedicated Nexa Vault hardware chip providing isolated key management and Android StrongBox cryptographic storage", table_cell_body)],
        [Paragraph("Stereo Acoustic Sound", table_cell_bold), Paragraph("Dual symmetrical 1216 box speakers with 1.2cc equivalent sound chambers and Dolby Atmos spatial audio profile", table_cell_body)],
        [Paragraph("Wireless Audio Codecs", table_cell_bold), Paragraph("Certified Hi-Res Wireless Audio support for Sony LDAC, Qualcomm aptX Lossless, and Bluetooth LE Audio LC3", table_cell_body)],
    ]

    t2 = Table(spec_data_p2, colWidths=[1.8 * inch, 5.2 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t2)

    story.append(PageBreak())

    # ================= PAGE 3 =================
    story.append(Paragraph("5. Professional Imaging & Optical Camera System", h1_style))
    story.append(Paragraph(
        "Co-engineered with elite optical specialists, the Horizon Ultra imaging array delivers true studio-grade "
        "photography across all focal lengths from 14mm macro up to 240mm telephoto.",
        body_style,
    ))

    cam_data = [
        [Paragraph("Camera Module", table_header_style), Paragraph("Hardware Specifications & Optical Capabilities", table_header_style)],
        [Paragraph("Primary Wide (24mm)", table_cell_bold), Paragraph("200MP Samsung ISOCELL HP9, large 1/1.14\" sensor, f/1.68 aperture, 8P glass lens with 2nd-gen Sensor-Shift OIS", table_cell_body)],
        [Paragraph("Periscope Telephoto (120mm)", table_cell_bold), Paragraph("50MP Sony IMX858, 10x true optical zoom, 100x Space Zoom, f/3.0 aperture, prism Dual-OIS image stabilization", table_cell_body)],
        [Paragraph("Ultra-Wide & Macro (14mm)", table_cell_bold), Paragraph("50MP sensor, 122&deg; ultra-wide field of view, f/2.0 aperture, active laser autofocus with 2.5cm macro focus distance", table_cell_body)],
        [Paragraph("Front Selfie Camera", table_cell_bold), Paragraph("50MP autofocus lens with 4K 60fps HDR video capture, f/2.2 aperture, and 90&deg; group-selfie field of view", table_cell_body)],
    ]

    t3 = Table(cam_data, colWidths=[1.8 * inch, 5.2 * inch])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t3)

    story.append(Spacer(1, 10))
    story.append(Paragraph("6. Cinematic Videography and Computational Features", h1_style))
    story.append(Paragraph("&bull; <b>8K 60fps HDR Video:</b> Full 10-bit LOG video capture across both wide and periscope lenses with real-time LUT monitoring.", bullet_style))
    story.append(Paragraph("&bull; <b>Active Gyroscopic Action Stabilization:</b> Hardware gyroscope combined with AI horizon-leveling stabilizes video during vigorous sports or running.", bullet_style))
    story.append(Paragraph("&bull; <b>Nexa Nightography Ultra:</b> Multi-exposure neural fusion synthesizes 12 raw exposures into pristine night photographs under 0.05 lux candle-light conditions.", bullet_style))

    story.append(PageBreak())

    # ================= PAGE 4 =================
    story.append(Paragraph("7. 6,000mAh Silicon-Carbon Battery & 120W HyperCharge", h1_style))
    story.append(Paragraph(
        "Utilizing aerospace-grade Silicon-Carbon (Si-C) negative electrodes, the battery achieves an energy density of 795 Wh/L, "
        "providing exceptional 2-day battery endurance in a thin 8.2mm chassis.",
        body_style,
    ))

    batt_data = [
        [Paragraph("Power Subsystem", table_header_style), Paragraph("Technical Metrics and Charging Profiles", table_header_style)],
        [Paragraph("Nominal Battery Capacity", table_cell_bold), Paragraph("6,000 mAh (typical) / 5,880 mAh (rated) Silicon-Carbon high-density dual-cell architecture", table_cell_body)],
        [Paragraph("120W HyperCharge (Wired)", table_cell_bold), Paragraph("Reaches 0 to 50% in 8 minutes; 0 to 100% in 19 minutes using official Nexa GaN charger", table_cell_body)],
        [Paragraph("50W Wireless Charging", table_cell_bold), Paragraph("Supports Qi2 magnetic alignment wireless charging (0 to 100% in 48 minutes)", table_cell_body)],
        [Paragraph("10W Reverse Wireless", table_cell_bold), Paragraph("Enables charging Qi-compatible smartwatches, earbuds, and accessories on device rear panel", table_cell_body)],
        [Paragraph("Battery Longevity Rating", table_cell_bold), Paragraph("Guaranteed &gt;85% health retention after 1,600 full charge cycles (equivalent to 4+ years of daily use)", table_cell_body)],
        [Paragraph("Bypass Gaming Power", table_cell_bold), Paragraph("Powers CPU/GPU directly without routing power through battery cells, eliminating gaming heat buildup", table_cell_body)],
    ]

    t4 = Table(batt_data, colWidths=[1.8 * inch, 5.2 * inch])
    t4.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t4)

    story.append(Spacer(1, 10))
    story.append(Paragraph("8. Ingress Protection (IP68 & IP69) and Thermal Architecture", h1_style))
    story.append(Paragraph("&bull; <b>IP68 Submersion Resistance:</b> Certified for continuous freshwater immersion up to 2.0 meters for 30 minutes without seal degradation.", bullet_style))
    story.append(Paragraph("&bull; <b>IP69 Steam & Jet Protection:</b> High-pressure thermal jet water resistance tested up to 100 bar pressure at 80&deg;C.", bullet_style))
    story.append(Paragraph("&bull; <b>10,000 sq mm Ice-Loop Cooling:</b> Dual-channel 3D vapor chamber dissipates up to 14 Watts of thermal power, keeping frame temperature below 41&deg;C.", bullet_style))

    story.append(PageBreak())

    # ================= PAGE 5 =================
    story.append(Paragraph("9. On-Device Nexa AI Suite & NexaOS 4.0 Productivity", h1_style))
    story.append(Paragraph(
        "NexaOS 4.0 integrates deep machine learning into daily workflows, processing sensitive user data entirely "
        "on the local device without sending private data to cloud servers.",
        body_style,
    ))
    story.append(Paragraph("&bull; <b>Offline Live Call Translation:</b> Real-time two-way voice-to-voice translation in phone calls across 35 languages without network connectivity.", bullet_style))
    story.append(Paragraph("&bull; <b>Circle to Search:</b> Instant contextual visual lookup powered by Google Gemini Nano integration.", bullet_style))
    story.append(Paragraph("&bull; <b>AI Magic Eraser Pro & Scene Expand:</b> Intelligently eliminates unwanted background persons, shadows, and reflections from photos with one tap.", bullet_style))
    story.append(Paragraph("&bull; <b>Nexa Desktop Link:</b> Connect to external displays via USB-C 3.2 Gen 2 (10 Gbps) for an instant multi-window 4K 60Hz desktop computing interface.", bullet_style))

    story.append(Spacer(1, 10))
    story.append(Paragraph("10. Global Connectivity, Wi-Fi 7 & Satellite Emergency SOS", h1_style))

    comm_data = [
        [Paragraph("Connectivity Feature", table_header_style), Paragraph("Standard & Operational Protocols", table_header_style)],
        [Paragraph("Satellite Emergency SOS", table_cell_bold), Paragraph("Two-way direct-to-satellite messaging via L-band satellite constellations when outside cell coverage", table_cell_body)],
        [Paragraph("Wi-Fi 7 (802.11be)", table_cell_bold), Paragraph("Tri-band 2.4 / 5 / 6 GHz with 320 MHz channels, 4096-QAM modulation, and peak speeds up to 5.8 Gbps", table_cell_body)],
        [Paragraph("Bluetooth 5.4", table_cell_bold), Paragraph("Dual-mode Bluetooth 5.4 with Auracast broadcast audio sharing and low-energy sub-band channels", table_cell_body)],
        [Paragraph("Global Satellite GNSS", table_cell_bold), Paragraph("Dual-frequency GNSS (GPS L1+L5, GLONASS, Galileo E1+E5a, BeiDou B1I+B2a, and NavIC)", table_cell_body)],
        [Paragraph("Ultra-Wideband (UWB)", table_cell_bold), Paragraph("FiRa-certified UWB chip for centimeter-precise digital car key unlocking and smart tag tracking", table_cell_body)],
    ]

    t5 = Table(comm_data, colWidths=[1.8 * inch, 5.2 * inch])
    t5.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1E293B")),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t5)

    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Successfully generated human-readable PDF: {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    kb_pdf = Path(__file__).resolve().parents[1] / "knowledge_base" / "Nexa_Mobile_Smartphone_User_Guide.pdf"
    root_pdf = Path(__file__).resolve().parents[2] / "Nexa_Mobile_Smartphone_User_Guide.pdf"

    build_pdf(kb_pdf)
    build_pdf(root_pdf)
