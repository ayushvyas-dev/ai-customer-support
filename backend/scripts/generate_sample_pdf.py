"""Generates a comprehensive multi-page PDF document for Nexa Mobile smartphones.

Used to test the PDF upload feature and hybrid RAG retrieval.
"""

from pathlib import Path
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject


def add_text_page(writer: PdfWriter, title: str, sections: list[tuple[str, list[str]]]):
    """Adds a page with formatted headers and body paragraphs."""
    page = writer.add_blank_page(width=612, height=792)

    stream_lines = [
        "BT",
        "/F1 16 Tf",
        "22 TL",
        "50 730 Td",
        f"({title}) Tj",
        "/F1 10 Tf",
        "14 TL",
        "T*",
        "() Tj",
    ]

    for section_heading, body_lines in sections:
        stream_lines.append("T*")
        stream_lines.append("/F1 12 Tf")
        clean_heading = section_heading.replace("(", "").replace(")", "")
        stream_lines.append(f"({clean_heading}) Tj")
        stream_lines.append("/F1 10 Tf")
        stream_lines.append("14 TL")

        for line in body_lines:
            clean_line = line.replace("(", "").replace(")", "")
            stream_lines.append("T*")
            stream_lines.append(f"({clean_line}) Tj")

        stream_lines.append("T*")
        stream_lines.append("() Tj")

    stream_lines.append("ET")

    content_stream = "\n".join(stream_lines).encode("latin1")
    stream_obj = DecodedStreamObject()
    stream_obj.set_data(content_stream)
    page[NameObject("/Contents")] = stream_obj

    font_dict = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"),
        NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({
            NameObject("/F1"): font_dict,
        })
    })


def generate_nexa_smartphone_guide(output_path: Path):
    writer = PdfWriter()

    # --- Page 1: Brand Overview & Flagship Lineup ---
    add_text_page(
        writer,
        title="NEXA MOBILE - OFFICIAL SMARTPHONE USER GUIDE (2026)",
        sections=[
            (
                "1. Brand Mission and Product Portfolio",
                [
                    "Nexa Mobile designs smartphones built for sustained performance, battery endurance,",
                    "and intuitive software experiences for Indian and global consumers.",
                    "The 2026 lineup introduces three distinct models engineered for diverse user needs:",
                    "- Nexa One: The balanced everyday flagship. Features a 6.5-inch FHD+ AMOLED 90Hz display,",
                    "  50MP Sony OIS main camera, 5000mAh battery, 33W Fast Charging, and 8GB RAM + 128GB storage.",
                    "  Official Price: Rs. 24,999 on Amazon India.",
                    "- Nexa One Pro: Engineered for power users and creators. Features a 6.7-inch Quad HD+ AMOLED",
                    "  120Hz dynamic refresh display, 50MP Sony flagship sensor with Night Mode 3.0, 5000mAh cell,",
                    "  67W Turbo Charge, and 12GB LPDDR5 RAM + 256GB UFS 3.1 storage. Price: Rs. 39,999.",
                    "- Nexa Lite: Essential reliability. Features a 6.5-inch 90Hz display, 50MP AI dual camera,",
                    "  5000mAh battery, 18W charging, and 6GB RAM + 128GB storage. Price: Rs. 14,999.",
                ],
            ),
            (
                "2. Standard In-The-Box Contents and Eco Policy",
                [
                    "Every retail box contains: Handset with pre-applied screen protector, 1-meter USB-C to USB-C cable,",
                    "SIM tray ejector tool, Quick Start Guide, and Safety Warranty Card.",
                    "Important Eco Notice: In alignment with electronic waste reduction initiatives, dedicated wall",
                    "chargers are sold separately. We recommend official Nexa 33W or 67W USB-PD power adapters.",
                ],
            ),
        ],
    )

    # --- Page 2: Battery Technology, Fast Charging & Thermal Safety ---
    add_text_page(
        writer,
        title="NEXA MOBILE - BATTERY CARE AND CHARGING GUIDE",
        sections=[
            (
                "3. Battery Specifications and Fast Charging Profiles",
                [
                    "All models feature a 5000mAh high-density lithium-ion battery with smart cell protection.",
                    "Charging inputs: Nexa Lite up to 18W, Nexa One up to 33W (0 to 50 percent in 28 minutes),",
                    "and Nexa One Pro up to 67W Turbo Charge (0 to 100 percent in 42 minutes).",
                    "Charging Curve: Charging speed automatically tapers above 80 percent to safeguard battery chemistry.",
                    "Slow Charging Troubleshooting:",
                    "1. Verify that the cable is firmly connected to both the device and the wall adapter.",
                    "2. Inspect the USB-C port for pocket lint or debris using a dry, soft non-conductive brush.",
                    "3. Test with an alternate certified USB Type-C cable and a USB-PD compliant power source.",
                    "4. Avoid charging in direct sunlight or environments above 35 degrees Celsius.",
                ],
            ),
            (
                "4. Critical Safety Warnings - Battery Hazard Protocol",
                [
                    "If a device exhibits a swollen back cover, excessive heat, smoke, popping sounds, or chemical odor:",
                    "- Disconnect the charger immediately if it is safe to do so.",
                    "- Stop using the device and move it onto a non-flammable surface (tile, concrete, or stone).",
                    "- Keep away from beds, sofas, curtains, and children.",
                    "- Do not attempt to puncture, press, or pry open the battery compartment.",
                    "- Contact Nexa Mobile Safety Support immediately for emergency hazardous exchange.",
                ],
            ),
        ],
    )

    # --- Page 3: Display, Camera and Hardware Diagnostics ---
    add_text_page(
        writer,
        title="NEXA MOBILE - HARDWARE AND DISPLAY DIAGNOSTICS",
        sections=[
            (
                "5. Display Settings and Touchscreen Calibration",
                [
                    "Nexa One Pro supports dynamic refresh rates from 60Hz up to 120Hz for fluid scrolling.",
                    "To enable 120Hz: Navigate to Settings > Display > Screen Refresh Rate > Dynamic 120Hz.",
                    "If experiencing touch unresponsiveness or frozen screens:",
                    "- Perform a hardware force reboot: Press and hold Power + Volume Down together for 10 seconds.",
                    "- If display shows colored vertical lines or black blotches, this indicates physical panel trauma.",
                    "- Remove thick non-certified tempered glass screen protectors that may impair touch sensitivity.",
                ],
            ),
            (
                "6. 50MP Camera Optimization and Lens Care",
                [
                    "The primary 50MP Sony sensor utilizes Optical Image Stabilization (OIS) to eliminate motion blur.",
                    "Best practices for clear photos:",
                    "- Clean the camera lens glass using a lint-free microfiber cloth.",
                    "- If the camera app crashes, go to Settings > Apps > Camera > Storage > Clear Cache.",
                    "- Close other active applications that may be accessing the camera hardware in the background.",
                    "- Ensure imaging firmware is up to date under Settings > System > System Update.",
                ],
            ),
        ],
    )

    # --- Page 4: Connectivity, SIM and System Performance ---
    add_text_page(
        writer,
        title="NEXA MOBILE - CONNECTIVITY AND SYSTEM PERFORMANCE",
        sections=[
            (
                "7. 5G Dual SIM Setup and Network Troubleshooting",
                [
                    "All Nexa devices support Dual SIM Dual Standby (DSDV) on sub-6GHz 5G bands (n28, n77, n78).",
                    "If cellular data or mobile reception drops:",
                    "1. Toggle Airplane Mode on for 10 seconds, then toggle off to re-register with cell towers.",
                    "2. Verify carrier APN settings under Settings > Network and Internet > SIMs > Access Point Names.",
                    "3. Eject the SIM tray using the bundled pin, inspect contacts for scratches, and re-seat firmly.",
                    "4. Test the SIM in another phone to rule out carrier-level network outages or deactivated accounts.",
                ],
            ),
            (
                "8. System Performance, Safe Mode, and Data Backup",
                [
                    "To resolve system sluggishness or app freezing:",
                    "- Keep at least 15 percent free internal storage under Settings > Storage.",
                    "- Test in Safe Mode: Press and hold Power button, then touch and hold Power Off on screen until",
                    "  'Reboot to safe mode' appears. Safe mode disables third-party apps to isolate issues.",
                    "- Always back up photos, contacts, and WhatsApp data to Google Drive before system maintenance.",
                ],
            ),
        ],
    )

    # --- Page 5: Warranty Terms, Amazon Returns and Support Contact ---
    add_text_page(
        writer,
        title="NEXA MOBILE - WARRANTY AND RETURN POLICIES",
        sections=[
            (
                "9. 1-Year Limited Manufacturer Warranty Coverage",
                [
                    "Handsets: 1-Year limited manufacturer warranty against internal component defects and motherboard failure.",
                    "In-Box Accessories: 6-Month warranty coverage for official USB-C cables and SIM ejector pins.",
                    "Warranty Exclusions:",
                    "- Accidental damage, water immersion (IP54 is splash resistant only, not waterproof), dropped screens.",
                    "- Unofficial rooting, bootloader unlocking, or unauthorized repair shop disassembly.",
                    "- Normal cosmetic wear, battery capacity decline over 300 charge cycles, and surface scratches.",
                ],
            ),
            (
                "10. Amazon 30-Day Return Window and RMA Procedures",
                [
                    "Purchases on Amazon.in qualify for a 30-day return or replacement window from delivery date.",
                    "Items must be returned with all original box accessories, manuals, and undamaged packaging.",
                    "To generate a prepaid return label (RMA): Log in to Amazon > Your Orders > Return or Replace Items.",
                    "Nexa Support Email: support@nexamobile.com | Customer Service Hotline: 1800-NEXA-CARE",
                    "Corporate Address: Nexa Mobile Technologies Pvt Ltd, Cyber City, Gurugram, India.",
                ],
            ),
        ],
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        writer.write(f)

    print(f"Successfully generated 5-page PDF: {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    kb_pdf = Path(__file__).resolve().parents[1] / "knowledge_base" / "Nexa_Mobile_Smartphone_User_Guide.pdf"
    root_pdf = Path(__file__).resolve().parents[2] / "Nexa_Mobile_Smartphone_User_Guide.pdf"

    generate_nexa_smartphone_guide(kb_pdf)
    generate_nexa_smartphone_guide(root_pdf)

