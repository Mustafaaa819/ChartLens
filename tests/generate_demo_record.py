"""
Generate a realistic fake US personal injury medical record PDF for demo purposes.
Patient: Maria Rodriguez — Tampa, FL auto accident case.
"""

from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

OUTPUT_PATH = Path(__file__).parent / "sample_records" / "demo_us_case.pdf"

# ── Patient demographics ───────────────────────────────────────────────────────
PATIENT = {
    "name": "Maria Rodriguez",
    "dob":  "04/12/1988",
    "address": "4521 Bay Shore Blvd, Tampa, FL 33611",
    "phone": "(813) 555-0192",
    "ssn_last4": "****",
    "doa": "01/08/2025",          # date of accident
}


def _styles():
    base = getSampleStyleSheet()
    styles = {
        "provider_header": ParagraphStyle(
            "provider_header",
            fontSize=13,
            fontName="Helvetica-Bold",
            spaceAfter=2,
            textColor=colors.HexColor("#1a3a5c"),
        ),
        "provider_sub": ParagraphStyle(
            "provider_sub",
            fontSize=9,
            fontName="Helvetica",
            spaceAfter=1,
            textColor=colors.HexColor("#444444"),
        ),
        "section_title": ParagraphStyle(
            "section_title",
            fontSize=11,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=4,
            textColor=colors.HexColor("#1a3a5c"),
        ),
        "body": ParagraphStyle(
            "body",
            fontSize=9,
            fontName="Helvetica",
            leading=14,
            spaceAfter=2,
        ),
        "body_bold": ParagraphStyle(
            "body_bold",
            fontSize=9,
            fontName="Helvetica-Bold",
            leading=14,
            spaceAfter=2,
        ),
        "small": ParagraphStyle(
            "small",
            fontSize=8,
            fontName="Helvetica",
            leading=12,
            textColor=colors.HexColor("#555555"),
        ),
        "label": ParagraphStyle(
            "label",
            fontSize=9,
            fontName="Helvetica-Bold",
            leading=13,
        ),
        "centered": ParagraphStyle(
            "centered",
            fontSize=9,
            fontName="Helvetica",
            alignment=TA_CENTER,
        ),
        "disclaimer": ParagraphStyle(
            "disclaimer",
            fontSize=7,
            fontName="Helvetica-Oblique",
            textColor=colors.HexColor("#888888"),
            alignment=TA_CENTER,
            spaceBefore=4,
        ),
    }
    return styles


def _hr():
    return HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#cccccc"), spaceAfter=6, spaceBefore=6)


def _thick_hr():
    return HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1a3a5c"), spaceAfter=8, spaceBefore=4)


def _patient_block(s):
    """Standard patient info block used at top of every section."""
    data = [
        ["Patient Name:", PATIENT["name"], "Date of Birth:", PATIENT["dob"]],
        ["Address:", PATIENT["address"], "Phone:", PATIENT["phone"]],
        ["Date of Accident:", PATIENT["doa"], "Account #:", "TGH-2025-00847"],
    ]
    tbl = Table(data, colWidths=[1.2*inch, 2.5*inch, 1.2*inch, 1.6*inch])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#222222")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f7fb")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d9e8")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f4f7fb"), colors.HexColor("#eef2f9")]),
    ]))
    return tbl


# ══════════════════════════════════════════════════════════════════════════════
# PAGE BUILDERS
# ══════════════════════════════════════════════════════════════════════════════

def page_er_admission(s, story):
    """Pages 1-2: Tampa General Hospital Emergency — admission."""
    # Letterhead
    story.append(Paragraph("TAMPA GENERAL HOSPITAL", s["provider_header"]))
    story.append(Paragraph("1 Tampa General Circle  •  Tampa, FL 33606", s["provider_sub"]))
    story.append(Paragraph("Main: (813) 844-7000  •  Emergency Department: (813) 844-7550", s["provider_sub"]))
    story.append(Paragraph("NPI: 1487623059  •  Tax ID: 59-0624081", s["provider_sub"]))
    story.append(_thick_hr())

    story.append(Paragraph("EMERGENCY DEPARTMENT — MEDICAL RECORD", s["section_title"]))
    story.append(_patient_block(s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("VISIT INFORMATION", s["section_title"]))
    story.append(_hr())
    visit_data = [
        ["Date of Service:", "January 8, 2025", "Time of Arrival:", "14:37"],
        ["Visit Type:", "Emergency", "Discharge Time:", "19:52"],
        ["Chief Complaint:", "Motor vehicle accident — neck and back pain, headache", "", ""],
        ["Attending Physician:", "James Whitfield, MD", "ED Nurse:", "R. Nguyen, RN"],
        ["MRN:", "TGH-MRN-88412", "Claim #:", "INS-FL-2025-009134"],
    ]
    vt = Table(visit_data, colWidths=[1.4*inch, 2.4*inch, 1.4*inch, 1.3*inch])
    vt.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (1, 2), (3, 2)),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d9e8")),
    ]))
    story.append(vt)
    story.append(Spacer(1, 8))

    story.append(Paragraph("HISTORY OF PRESENT ILLNESS", s["section_title"]))
    story.append(_hr())
    hpi = (
        "Ms. Rodriguez is a 36-year-old female who presents to the emergency department following a "
        "motor vehicle accident that occurred today, January 8, 2025, at approximately 13:15. Patient "
        "reports she was a restrained driver traveling southbound on I-275 when her vehicle was struck "
        "from behind by another vehicle at highway speed. Patient was transported via EMS (Sunstar "
        "Paramedics, Unit 47). She complains of significant neck pain and stiffness, low back pain, "
        "and headache beginning shortly after impact. Patient denies loss of consciousness. "
        "<b>Patient denies any prior history of neck or back pain. Patient denies prior treatment "
        "for musculoskeletal complaints.</b> No prior motor vehicle accidents. No known allergies. "
        "Current medications: oral contraceptive (Sprintec), multivitamin."
    )
    story.append(Paragraph(hpi, s["body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("PHYSICAL EXAMINATION", s["section_title"]))
    story.append(_hr())
    exam_items = [
        ("General:", "Alert and oriented x3. Moderate distress secondary to pain. GCS 15."),
        ("Vital Signs:", "BP 138/84  |  HR 96  |  RR 18  |  Temp 98.6°F  |  O₂ Sat 99% RA"),
        ("HEENT:", "Normocephalic. No scalp lacerations. PERRL 4mm bilaterally. No hemotympanum."),
        ("Cervical Spine:",
         "Significant tenderness to palpation at C4-C5 level. Range of motion markedly limited in "
         "flexion and extension. Paraspinal muscle spasm noted bilaterally. No midline bony tenderness."),
        ("Lumbar Spine:",
         "Tenderness to palpation L4-L5. Paraspinal muscle guarding. Straight leg raise negative bilaterally."),
        ("Neurological:",
         "Cranial nerves II-XII intact. Motor strength 5/5 upper and lower extremities. Sensation intact. "
         "DTRs 2+ and symmetric. No focal deficits."),
        ("Extremities:", "No obvious deformity. Peripheral pulses intact. No edema."),
    ]
    for label, text in exam_items:
        story.append(Paragraph(f"<b>{label}</b> {text}", s["body"]))

    story.append(Spacer(1, 6))
    story.append(Paragraph("DIAGNOSTIC STUDIES", s["section_title"]))
    story.append(_hr())
    diag_data = [
        ["Study", "Result", "Ordered By"],
        ["CT Head (non-contrast)", "No intracranial hemorrhage. No acute bony injury.", "J. Whitfield, MD"],
        ["CT Cervical Spine", "No fracture or malalignment. Soft tissue swelling anterior C4-C5.", "J. Whitfield, MD"],
        ["X-Ray Lumbar Spine (2-view)", "No acute fracture. Mild disc space narrowing L4-L5.", "J. Whitfield, MD"],
        ["CBC, CMP, Coagulation Panel", "Within normal limits.", "J. Whitfield, MD"],
    ]
    dt = Table(diag_data, colWidths=[2.0*inch, 3.2*inch, 1.4*inch])
    dt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fb")]),
    ]))
    story.append(dt)
    story.append(Spacer(1, 8))

    story.append(Paragraph("ASSESSMENT & PLAN", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "1. <b>Cervical sprain/strain (ICD-10: S13.4XXA)</b> — secondary to motor vehicle accident. "
        "Applied rigid cervical collar. Patient instructed to wear x 72 hours.", s["body"]))
    story.append(Paragraph(
        "2. <b>Lumbar contusion (ICD-10: S30.01XA)</b> — paraspinal muscle guarding and point tenderness. "
        "Ice/heat alternating, activity restriction.", s["body"]))
    story.append(Paragraph(
        "3. <b>Mild concussion without loss of consciousness (ICD-10: S09.90XA)</b> — postconcussive "
        "headache. Concussion return-to-activity protocol discussed. Head CT negative for hemorrhage.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Medications Prescribed at Discharge:</b>", s["body_bold"]))
    rx_data = [
        ["Medication", "Dose", "Frequency", "Quantity", "Duration"],
        ["Ibuprofen 800mg", "800mg", "TID with food", "#42 tabs", "14 days"],
        ["Cyclobenzaprine 10mg", "10mg", "TID PRN spasm", "#21 tabs", "7 days"],
    ]
    rx_t = Table(rx_data, colWidths=[1.8*inch, 0.8*inch, 1.4*inch, 1.0*inch, 1.2*inch])
    rx_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2a5080")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story.append(rx_t)
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Discharge Instructions:</b> Return to ED immediately for worsening headache, vision changes, "
        "numbness/tingling, or weakness in arms or legs. Follow up with primary care physician within "
        "3-5 days. Recommend orthopedic spine consultation given mechanism of injury.", s["body"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("BILLING & CHARGES", s["section_title"]))
    story.append(_hr())
    bill_data = [
        ["Service Description", "CPT Code", "Billed", "Insurance Paid", "Balance"],
        ["Emergency Department Level 4 Visit", "99284", "$3,200.00", "$1,280.00", "$1,920.00"],
        ["CT Head w/o contrast", "70450", "$1,450.00", "$540.00", "$910.00"],
        ["CT Cervical Spine w/o contrast", "72125", "$1,650.00", "$780.00", "$870.00"],
        ["X-Ray Lumbar Spine 2 views", "72100", "$420.00", "$280.00", "$140.00"],
        ["Laboratory Panel (CBC, CMP)", "80053", "$480.00", "$180.00", "$300.00"],
        ["Cervical Collar Application", "A4570", "$250.00", "$140.00", "$110.00"],
        ["TOTAL", "", "$8,450.00", "$3,200.00", "$4,250.00"],
    ]
    bt = Table(bill_data, colWidths=[2.4*inch, 0.9*inch, 0.9*inch, 1.0*inch, 0.9*inch])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fb")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f7fb")]),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(bt)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Electronically signed by: James Whitfield, MD  •  Emergency Medicine  •  "
        "NPI: 1679340218  •  Date: 01/08/2025 20:14",
        s["small"]))
    story.append(Paragraph(
        "This document is a confidential medical record. Unauthorized disclosure is prohibited by federal "
        "and state law (HIPAA 45 CFR §164.502). FOR LEGAL PROCEEDINGS USE ONLY.",
        s["disclaimer"]))


def page_imaging(s, story):
    """Pages 3-4: Advanced Imaging of Tampa — MRI reports."""
    story.append(Paragraph("ADVANCED IMAGING OF TAMPA", s["provider_header"]))
    story.append(Paragraph("8901 N. Dale Mabry Hwy, Suite 210  •  Tampa, FL 33614", s["provider_sub"]))
    story.append(Paragraph("Tel: (813) 961-4400  •  Fax: (813) 961-4401  •  NPI: 1932847561", s["provider_sub"]))
    story.append(Paragraph("ACR-Accredited Diagnostic Imaging Center  •  Tax ID: 46-2813940", s["provider_sub"]))
    story.append(_thick_hr())

    story.append(Paragraph("RADIOLOGY REPORT", s["section_title"]))
    story.append(_patient_block(s))
    story.append(Spacer(1, 8))

    # ── MRI Cervical ──
    story.append(Paragraph("EXAMINATION 1: MRI CERVICAL SPINE WITHOUT CONTRAST", s["section_title"]))
    story.append(_hr())
    c_data = [
        ["Date of Service:", "January 15, 2025", "Accession #:", "AIT-2025-C-00293"],
        ["Ordering Provider:", "James Whitfield, MD — TGH-ED", "Referring Dx:", "S13.4XXA"],
        ["Radiologist:", "Sarah Chen, MD, FRCR", "Report Date:", "01/15/2025 — 16:42"],
        ["Modality:", "3.0 Tesla MRI (Siemens Prisma)", "Sequences:", "Sag T1, Sag T2, Axial T2, STIR"],
    ]
    story.append(_info_table(c_data))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CLINICAL INDICATION:</b> Motor vehicle accident 01/08/2025. "
                           "Cervical pain and radiculopathy. Evaluate for disc pathology.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>TECHNIQUE:</b> Multiplanar, multisequence MRI of the cervical spine performed "
                           "on a 3.0 Tesla magnet without intravenous contrast administration.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>FINDINGS:</b>", s["body_bold"]))
    findings_c = [
        "Vertebral body heights and alignment are maintained throughout.",
        "No fracture or dislocation identified.",
        "C3-C4: Disc space preserved. No significant disc herniation. Mild uncovertebral joint hypertrophy.",
        "<b>C4-C5: Posterior disc herniation measuring 4.2mm with moderate right-sided foraminal stenosis. "
        "Mild mass effect on the right ventral thecal sac. Contact but no compression of the right C5 "
        "nerve root sleeve.</b>",
        "C5-C6: Disc space preserved. Mild bilateral facet arthropathy.",
        "C6-C7: Minimal disc bulge without significant stenosis.",
        "Spinal cord: Normal cord signal and caliber throughout. No myelopathy.",
        "Paravertebral soft tissues: Increased T2 signal in bilateral paraspinal musculature at C4-C6 "
        "level, consistent with acute muscle strain/edema.",
        "No epidural hematoma or abscess.",
    ]
    for f in findings_c:
        story.append(Paragraph(f"• {f}", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>IMPRESSION:</b>", s["body_bold"]))
    story.append(Paragraph(
        "1. Posterior disc herniation at C4-C5 with moderate right foraminal stenosis and contact "
        "of the right C5 nerve root sleeve. Clinical correlation recommended.", s["body"]))
    story.append(Paragraph(
        "2. Bilateral paraspinal muscle edema C4-C6, consistent with acute traumatic strain.", s["body"]))
    story.append(Paragraph(
        "3. Mild degenerative changes at C5-C6. No acute fracture or cord signal abnormality.", s["body"]))
    story.append(Spacer(1, 8))

    # ── MRI Lumbar ──
    story.append(Paragraph("EXAMINATION 2: MRI LUMBAR SPINE WITHOUT CONTRAST", s["section_title"]))
    story.append(_hr())
    l_data = [
        ["Date of Service:", "January 15, 2025", "Accession #:", "AIT-2025-L-00294"],
        ["Ordering Provider:", "James Whitfield, MD — TGH-ED", "Referring Dx:", "S30.01XA"],
        ["Radiologist:", "Sarah Chen, MD, FRCR", "Report Date:", "01/15/2025 — 17:08"],
        ["Modality:", "3.0 Tesla MRI (Siemens Prisma)", "Sequences:", "Sag T1, Sag T2, Axial T2, STIR"],
    ]
    story.append(_info_table(l_data))
    story.append(Spacer(1, 6))

    story.append(Paragraph("<b>CLINICAL INDICATION:</b> Motor vehicle accident 01/08/2025. "
                           "Lumbar pain. Evaluate for disc pathology.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>FINDINGS:</b>", s["body_bold"]))
    findings_l = [
        "Vertebral body heights maintained L1-S1. Normal lumbar lordosis.",
        "No compression fracture or acute bony injury.",
        "L1-L2, L2-L3, L3-L4: Discs preserved. No significant pathology.",
        "<b>L4-L5: Broad-based disc bulge with mild bilateral foraminal narrowing. "
        "Minimal flattening of the ventral thecal sac. No nerve root compression.</b>",
        "L5-S1: Disc space preserved. No herniation.",
        "Conus medullaris at L1-L2 level, normal signal.",
        "Paraspinal musculature: Mild increased T2 signal L4-S1, consistent with strain.",
        "No spondylolysis or spondylolisthesis.",
    ]
    for f in findings_l:
        story.append(Paragraph(f"• {f}", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>IMPRESSION:</b>", s["body_bold"]))
    story.append(Paragraph(
        "1. L4-L5 broad-based disc bulge with mild bilateral foraminal narrowing, without frank "
        "nerve root compression. Findings are consistent with post-traumatic exacerbation in the "
        "setting of recent MVA.", s["body"]))
    story.append(Paragraph(
        "2. Mild paraspinal muscle strain L4-S1.", s["body"]))
    story.append(Paragraph(
        "3. No acute fracture, cord signal abnormality, or surgical emergency.", s["body"]))
    story.append(Spacer(1, 10))

    # Billing
    story.append(Paragraph("BILLING SUMMARY", s["section_title"]))
    story.append(_hr())
    bill_data = [
        ["Service", "CPT", "Billed", "Insurance Paid", "Balance"],
        ["MRI Cervical Spine w/o contrast", "72141", "$2,100.00", "$840.00", "$1,260.00"],
        ["MRI Lumbar Spine w/o contrast", "72148", "$2,100.00", "$840.00", "$1,260.00"],
        ["TOTAL", "", "$4,200.00", "$1,680.00", "$2,520.00"],
    ]
    story.append(_bill_table(bill_data))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Electronically signed by: Sarah Chen, MD, FRCR  •  Diagnostic Radiology  •  "
        "NPI: 1204837165  •  Date: 01/15/2025",
        s["small"]))
    story.append(Paragraph(
        "This report is a confidential medical document. Reproduction or distribution without "
        "patient authorization is prohibited. HIPAA compliant.",
        s["disclaimer"]))


def page_ortho(s, story):
    """Pages 5-6: Tampa Bay Orthopedic Specialists."""
    story.append(Paragraph("TAMPA BAY ORTHOPEDIC SPECIALISTS", s["provider_header"]))
    story.append(Paragraph("4902 Ehrlich Road, Suite 300  •  Tampa, FL 33624", s["provider_sub"]))
    story.append(Paragraph("Tel: (813) 882-5100  •  Fax: (813) 882-5101  •  NPI: 1720394856", s["provider_sub"]))
    story.append(Paragraph("Board Certified Orthopedic Surgery & Spine  •  Tax ID: 59-3847102", s["provider_sub"]))
    story.append(_thick_hr())

    story.append(Paragraph("ORTHOPEDIC SPINE CONSULTATION & FOLLOW-UP NOTES", s["section_title"]))
    story.append(_patient_block(s))
    story.append(Spacer(1, 8))

    # Visit 1
    story.append(Paragraph("VISIT 1 — INITIAL CONSULTATION", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph("<b>Date of Service:</b> January 22, 2025  |  "
                           "<b>Provider:</b> Michael Torres, MD, FAAOS  |  "
                           "<b>Visit Type:</b> New Patient / Consultation", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Patient is a 36-year-old female referred from Tampa General Hospital ED following motor "
        "vehicle accident on 01/08/2025. She presents with persistent cervical and lumbar pain "
        "rated 7/10 at rest, 9/10 with movement. She reports radiating pain into the right upper "
        "extremity with numbness in the right thumb and index finger. Lumbar pain radiates to the "
        "left buttock. Sleep is significantly disrupted. Unable to return to work (medical "
        "transcriptionist, sedentary).", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>MRI Review (01/15/2025):</b> C4-C5 disc herniation with right foraminal "
                           "stenosis confirmed. L4-L5 disc bulge with bilateral foraminal narrowing.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>DIAGNOSES:</b>", s["body_bold"]))
    story.append(Paragraph("• Cervical disc herniation C4-C5 with right C5 radiculopathy (ICD-10: M50.122)", s["body"]))
    story.append(Paragraph("• Lumbar disc displacement with radiculopathy (ICD-10: M51.16)", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>PLAN:</b>", s["body_bold"]))
    story.append(Paragraph(
        "1. Physical therapy prescribed: 3x/week for 8 weeks. Focus on cervical and lumbar "
        "stabilization, traction, and myofascial release. PT order attached.", s["body"]))
    story.append(Paragraph(
        "2. Medrol dose pack (methylprednisolone) x 6-day taper for acute inflammation.", s["body"]))
    story.append(Paragraph(
        "3. Referral to pain management (Florida Pain & Spine Institute) for consideration of "
        "cervical epidural steroid injection if symptoms do not improve with conservative care.", s["body"]))
    story.append(Paragraph(
        "4. Restrict heavy lifting (>10 lbs), prolonged sitting >30 minutes without break, "
        "no overhead activities.", s["body"]))
    story.append(Paragraph("5. Return to clinic in 2 weeks for reassessment.", s["body"]))
    story.append(Spacer(1, 8))

    # Visit 2
    story.append(Paragraph("VISIT 2 — FOLLOW-UP", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph("<b>Date of Service:</b> February 5, 2025  |  "
                           "<b>Provider:</b> Michael Torres, MD, FAAOS  |  "
                           "<b>Visit Type:</b> Follow-Up", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Patient has completed 6 PT sessions. Reports mild improvement in lumbar symptoms "
        "(pain 5/10 at rest) but continued significant cervical pain with radiculopathy unchanged. "
        "Right hand grip strength mildly reduced. Paresthesias in right thumb and index finger "
        "persist. Sleeping better with body pillow support.", s["body"]))
    story.append(Paragraph(
        "<b>Physical Exam:</b> Spurling's test positive right side. Motor strength right hand "
        "grip 4/5. Reflexes intact. Cervical range of motion remains limited — flexion 30°, "
        "extension 20° (normal 45°/45°). Pain management consult appointment scheduled "
        "03/10/2025.", s["body"]))
    story.append(Paragraph(
        "<b>Plan:</b> Continue PT. Pain management referral confirmed. "
        "Patient remains off work pending further evaluation.", s["body"]))
    story.append(Spacer(1, 8))

    # Visit 3
    story.append(Paragraph("VISIT 3 — FOLLOW-UP", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph("<b>Date of Service:</b> February 19, 2025  |  "
                           "<b>Provider:</b> Michael Torres, MD, FAAOS  |  "
                           "<b>Visit Type:</b> Follow-Up", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Patient has now completed 13 of 16 prescribed PT sessions. Lumbar pain improved to "
        "3/10. Cervical symptoms partially improved. Right upper extremity paresthesias mildly "
        "improved. Patient to proceed with cervical ESI at Florida Pain & Spine Institute "
        "on 03/10/2025. Follow up post-procedure.", s["body"]))
    story.append(Paragraph(
        "<b>Work Status:</b> Patient remains temporarily disabled. Light duty work restrictions "
        "in place. Anticipated MMI at 6 months post-accident (July 2025) pending response to "
        "interventional treatment.", s["body"]))
    story.append(Spacer(1, 10))

    # Billing
    story.append(Paragraph("BILLING SUMMARY — ALL VISITS", s["section_title"]))
    story.append(_hr())
    bill_data = [
        ["Service", "Date", "CPT", "Billed", "Ins. Paid", "Balance"],
        ["New Patient Consultation (Level 4)", "01/22/2025", "99204", "$850.00", "$340.00", "$510.00"],
        ["Office Visit Follow-Up (Level 3)", "02/05/2025", "99213", "$425.00", "$170.00", "$255.00"],
        ["Office Visit Follow-Up (Level 3)", "02/19/2025", "99213", "$425.00", "$170.00", "$255.00"],
        ["X-Ray Review / Image Interpretation", "01/22/2025", "72141-26", "$400.00", "$160.00", "$240.00"],
        ["TOTAL", "", "", "$2,100.00", "$840.00", "$1,260.00"],
    ]
    bt = Table(bill_data, colWidths=[2.1*inch, 0.9*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fb")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f7fb")]),
        ("ALIGN", (3, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(bt)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Electronically signed by: Michael Torres, MD, FAAOS  •  Orthopedic Surgery & Spine  •  "
        "NPI: 1538271049  •  Documents generated: 02/19/2025",
        s["small"]))
    story.append(Paragraph(
        "Confidential Medical Record — Personal Injury Case Documentation. HIPAA Protected.",
        s["disclaimer"]))


def page_pain_mgmt(s, story):
    """Pages 7-8: Florida Pain & Spine Institute — epidural steroid injection."""
    story.append(Paragraph("FLORIDA PAIN & SPINE INSTITUTE", s["provider_header"]))
    story.append(Paragraph("3001 W. Cypress Creek Rd, Suite 400  •  Tampa, FL 33619", s["provider_sub"]))
    story.append(Paragraph("Tel: (813) 740-2200  •  Fax: (813) 740-2201  •  NPI: 1847293056", s["provider_sub"]))
    story.append(Paragraph("ABPM Board Certified Pain Management  •  AAPM Member  •  Tax ID: 65-0928471", s["provider_sub"]))
    story.append(_thick_hr())

    story.append(Paragraph("INTERVENTIONAL PAIN PROCEDURE NOTE", s["section_title"]))
    story.append(_patient_block(s))
    story.append(Spacer(1, 8))

    p_data = [
        ["Date of Service:", "March 10, 2025", "Start Time:", "10:15"],
        ["Procedure:", "Cervical Epidural Steroid Injection", "End Time:", "10:42"],
        ["Location:", "C4-C5 interlaminar approach", "ASA Class:", "II"],
        ["Attending Provider:", "Amanda Patel, MD", "Anesthesia:", "Conscious Sedation"],
        ["Anesthesiologist:", "Robert Kim, MD", "Facility:", "FPSI Procedure Suite"],
    ]
    story.append(_info_table(p_data))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PRE-PROCEDURE ASSESSMENT", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "Patient is a 36-year-old female with C4-C5 disc herniation and right C5 radiculopathy "
        "following MVA on 01/08/2025. Conservative management including physical therapy (completed "
        "13 of 16 sessions) and oral medications has provided only partial relief. Patient continues "
        "to experience cervical pain 6/10 with right upper extremity radiation and paresthesias "
        "affecting right thumb and index finger. Patient and risks/benefits of the procedure discussed "
        "at length. Informed consent obtained.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph("<b>Contraindications reviewed:</b> No active infection, no anticoagulation, "
                           "no known contrast allergy, INR within normal limits, NPO x 6 hours. "
                           "Consent signed. Time-out completed.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PROCEDURE DETAILS", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "Patient was positioned prone on the fluoroscopy table. Conscious sedation administered by "
        "Dr. Kim (Midazolam 2mg IV, Fentanyl 50mcg IV). Vital signs monitored continuously "
        "throughout the procedure. The posterior neck was prepped and draped in a sterile fashion.", s["body"]))
    story.append(Paragraph(
        "Under continuous fluoroscopic guidance (GE OEC Elite C-arm), the C4-C5 interlaminar "
        "epidural space was accessed using a 17-gauge Tuohy needle via loss-of-resistance technique. "
        "Epidurogram with 2mL Omnipaque 240 contrast confirmed epidural flow pattern with "
        "appropriate bilateral spread and no intravascular uptake.", s["body"]))
    story.append(Paragraph(
        "<b>Injectate:</b> Betamethasone 12mg (2mL) + Bupivacaine 0.25% (2mL) + Normal Saline "
        "(1mL) = 5mL total volume injected incrementally without complication.", s["body"]))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "Patient tolerated the procedure well. No immediate complications. Recovered in PACU for "
        "45 minutes. Vital signs stable upon discharge. Patient escorted home by designated driver "
        "per sedation protocol.", s["body"]))
    story.append(Spacer(1, 6))

    story.append(Paragraph("POST-PROCEDURE INSTRUCTIONS", s["section_title"]))
    story.append(_hr())
    story.append(Paragraph(
        "No driving or operating machinery for 24 hours. Ice to injection site PRN. Resume "
        "physical therapy in 48 hours. Avoid NSAIDS for 48 hours post-injection. Blood sugar "
        "monitoring advised for 3-5 days (corticosteroid effect). Follow up 4 weeks or sooner "
        "if increased pain, fever, or neurological changes.", s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("BILLING SUMMARY", s["section_title"]))
    story.append(_hr())
    bill_data = [
        ["Service Description", "CPT Code", "Billed", "Insurance Paid", "Balance"],
        ["Cervical Epidural Steroid Injection", "62321", "$3,200.00", "$1,280.00", "$1,920.00"],
        ["Fluoroscopic Guidance", "77003", "$800.00", "$320.00", "$480.00"],
        ["Conscious Sedation (first 30 min)", "99152", "$1,400.00", "$560.00", "$840.00"],
        ["Conscious Sedation (each add. 15 min)", "99153", "$600.00", "$240.00", "$360.00"],
        ["Procedure Facility Fee", "ASC", "$800.00", "$320.00", "$480.00"],
        ["TOTAL", "", "$6,800.00", "$2,720.00", "$4,080.00"],
    ]
    story.append(_bill_table(bill_data))
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Electronically signed by: Amanda Patel, MD  •  Pain Management  •  "
        "NPI: 1629384710  •  Date: 03/10/2025 11:30",
        s["small"]))
    story.append(Paragraph(
        "Confidential Procedure Record — Personal Injury Documentation. HIPAA Protected. "
        "Florida Pain & Spine Institute, LLC.",
        s["disclaimer"]))


def page_physical_therapy(s, story):
    """Page 9: ProActive Physical Therapy records."""
    story.append(Paragraph("PROACTIVE PHYSICAL THERAPY", s["provider_header"]))
    story.append(Paragraph("7821 N. Armenia Ave, Suite 105  •  Tampa, FL 33604", s["provider_sub"]))
    story.append(Paragraph("Tel: (813) 933-7700  •  Fax: (813) 933-7701  •  NPI: 1748302916", s["provider_sub"]))
    story.append(Paragraph("APTA Member  •  Florida Licensed Physical Therapy  •  Tax ID: 47-2039481", s["provider_sub"]))
    story.append(_thick_hr())

    story.append(Paragraph("PHYSICAL THERAPY — TREATMENT SUMMARY & BILLING", s["section_title"]))
    story.append(_patient_block(s))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PLAN OF CARE", s["section_title"]))
    story.append(_hr())
    poc_data = [
        ["Referring Provider:", "Michael Torres, MD", "Date of Referral:", "01/22/2025"],
        ["Treating Therapist:", "Kevin Marshall, DPT", "Plan Start Date:", "02/01/2025"],
        ["Plan End Date:", "03/28/2025", "Frequency:", "3x/week x 8 weeks"],
        ["Total Authorized Sessions:", "24", "Sessions Completed:", "16"],
        ["Diagnosis:", "C4-C5 disc herniation (M50.122), L4-L5 disc bulge (M51.16)", "", ""],
    ]
    pot = Table(poc_data, colWidths=[1.4*inch, 2.5*inch, 1.4*inch, 1.6*inch])
    pot.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("SPAN", (1, 4), (3, 4)),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d9e8")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f4f7fb"), colors.HexColor("#eef2f9")]),
    ]))
    story.append(pot)
    story.append(Spacer(1, 8))

    story.append(Paragraph("SESSION LOG", s["section_title"]))
    story.append(_hr())
    sessions = [
        ("02/01/2025", "1", "Initial eval. Baseline measurements. Cervical AROM: F30°/E20°. Manual therapy cervical, lumbar. Therapeutic exercise program initiated."),
        ("02/03/2025", "2", "Cervical traction 15 lbs x 12 min. TENS. Hot pack. HEP reviewed."),
        ("02/05/2025", "3", "Lumbar stabilization exercises. Core strengthening. Myofascial release lumbar paraspinals."),
        ("02/08/2025", "4", "Cervical AROM improving: F38°/E27°. Neural gliding exercises. TENS bilateral upper extremities."),
        ("02/10/2025", "5", "Therapeutic exercise progression. Balance/proprioception. Patient reports improved sleep."),
        ("02/12/2025", "6", "Manual therapy cervical and thoracic. Joint mobilization grade III. Patient tolerating well."),
        ("02/15/2025", "7", "Cervical traction 18 lbs. Right UE strengthening. Paresthesias mildly improved."),
        ("02/19/2025", "8", "Lumbar stabilization. Resistance band exercises. Pain 5/10 (from 7/10 initial)."),
        ("02/22/2025", "9", "Aquatic therapy introduction. Buoyancy-assisted cervical AROM."),
        ("02/26/2025", "10", "Progress note. Patient at 60% functional capacity. Continue plan."),
        ("03/01/2025", "11", "Therapeutic exercise advancement. Core endurance training."),
        ("03/05/2025", "12", "Cervical traction 20 lbs. Manual therapy. Myofascial release."),
        ("03/08/2025", "13", "Pre-injection session. Gentle mobilization only per MD instruction."),
        ("03/15/2025", "14", "Post-injection (03/10/25) session. Gentle ROM. Patient reports 40% improvement cervical symptoms."),
        ("03/22/2025", "15", "Strengthening progression. Scapular stabilization. Postural re-education."),
        ("03/28/2025", "16", "Discharge assessment. Final AROM: F52°/E41°. Significant functional improvement. Discharged to HEP."),
    ]
    session_data = [["Date", "#", "Treatment Note"]]
    for date, num, note in sessions:
        session_data.append([date, num, note])
    st = Table(session_data, colWidths=[0.9*inch, 0.3*inch, 5.4*inch])
    st.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fb")]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(st)
    story.append(Spacer(1, 8))

    story.append(Paragraph("BILLING SUMMARY", s["section_title"]))
    story.append(_hr())
    bill_data = [
        ["Service", "CPT", "Units", "Unit Rate", "Total Billed", "Ins. Paid"],
        ["Physical Therapy Evaluation", "97161", "1", "$275.00", "$275.00", "$110.00"],
        ["Therapeutic Exercise", "97110", "48", "$42.00", "$2,016.00", "$806.40"],
        ["Manual Therapy Techniques", "97140", "32", "$48.00", "$1,536.00", "$614.40"],
        ["Mechanical Traction", "97012", "10", "$35.00", "$350.00", "$140.00"],
        ["TENS / E-Stim", "97032", "12", "$32.00", "$384.00", "$153.60"],
        ["Hot/Cold Pack", "97010", "16", "$15.00", "$240.00", "$96.00"],
        ["TOTAL", "", "", "", "$4,801.00", "$1,920.40"],
    ]
    bt = Table(bill_data, colWidths=[1.8*inch, 0.6*inch, 0.4*inch, 0.7*inch, 0.9*inch, 0.9*inch])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fb")),
        ("FONTSIZE", (0, 0), (-1, -1), 7.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f7fb")]),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(bt)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Electronically signed by: Kevin Marshall, DPT  •  Licensed Physical Therapist  •  "
        "FL License: PT39847  •  Date: 03/28/2025",
        s["small"]))
    story.append(Paragraph(
        "Confidential Medical Record — Physical Therapy Documentation. HIPAA Protected.",
        s["disclaimer"]))


def page_pharmacy(s, story):
    """Page 10: CVS Pharmacy records — contains the embedded inconsistency."""
    story.append(Paragraph("CVS PHARMACY #4821", s["provider_header"]))
    story.append(Paragraph("6001 S. Dale Mabry Hwy  •  Tampa, FL 33611", s["provider_sub"]))
    story.append(Paragraph("Tel: (813) 835-4821  •  Pharmacy Fax: (813) 835-4822  •  NCPDP: 4821048", s["provider_sub"]))
    story.append(Paragraph("FL Board of Pharmacy License: PH29841  •  DEA: AC4821093", s["provider_sub"]))
    story.append(_thick_hr())

    story.append(Paragraph("PHARMACY RECORDS — PRESCRIPTION HISTORY", s["section_title"]))
    story.append(_patient_block(s))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "<b>Record Request:</b> All prescriptions filled at this location for patient Maria Rodriguez "
        "(DOB 04/12/1988) for the period November 1, 2024 through April 30, 2025. "
        "Records provided pursuant to valid HIPAA authorization dated 04/15/2025.",
        s["body"]))
    story.append(Spacer(1, 8))

    story.append(Paragraph("PRESCRIPTION FILL HISTORY", s["section_title"]))
    story.append(_hr())

    rx_data = [
        ["Rx #", "Fill Date", "Medication", "Strength", "Qty", "Days", "Prescriber", "Billed"],
        # ─── INCONSISTENCY: Gabapentin filled Nov 2024 — BEFORE the accident ───
        ["RX-7741092", "11/14/2024", "Gabapentin", "300mg capsules", "90", "30",
         "Dr. Elena Vasquez, MD\n(Internal Medicine)", "$38.00"],
        ["RX-7741093", "12/12/2024", "Gabapentin", "300mg capsules", "90", "30",
         "Dr. Elena Vasquez, MD\n(Internal Medicine)", "$38.00"],
        # ─── Post-accident medications ───
        ["RX-7748291", "01/09/2025", "Cyclobenzaprine", "10mg tablets", "21", "7",
         "Dr. James Whitfield, MD\n(TGH Emergency)", "$22.00"],
        ["RX-7748292", "01/09/2025", "Ibuprofen", "800mg tablets", "42", "14",
         "Dr. James Whitfield, MD\n(TGH Emergency)", "$19.00"],
        ["RX-7749104", "01/23/2025", "Methylprednisolone", "4mg dose pack", "21", "6",
         "Dr. Michael Torres, MD\n(TBOS)", "$45.00"],
        ["RX-7749105", "01/23/2025", "Gabapentin", "300mg capsules", "90", "30",
         "Dr. Michael Torres, MD\n(TBOS)", "$38.00"],
        ["RX-7751837", "02/10/2025", "Gabapentin", "300mg capsules", "90", "30",
         "Dr. Michael Torres, MD\n(TBOS)", "$38.00"],
        ["RX-7753201", "02/10/2025", "Omeprazole", "20mg capsules", "30", "30",
         "Dr. Michael Torres, MD\n(TBOS)", "$28.00"],
        ["RX-7756482", "03/10/2025", "Ibuprofen", "800mg tablets", "30", "30",
         "Dr. Amanda Patel, MD\n(FPSI)", "$19.00"],
        ["RX-7758034", "03/12/2025", "Gabapentin", "300mg capsules", "90", "30",
         "Dr. Amanda Patel, MD\n(FPSI)", "$38.00"],
        ["RX-7759841", "04/01/2025", "Gabapentin", "300mg capsules", "90", "30",
         "Dr. Amanda Patel, MD\n(FPSI)", "$38.00"],
        ["RX-7760192", "04/01/2025", "Omeprazole", "20mg capsules", "30", "30",
         "Dr. Amanda Patel, MD\n(FPSI)", "$28.00"],
    ]

    col_widths = [0.85*inch, 0.75*inch, 1.1*inch, 0.9*inch, 0.35*inch, 0.35*inch, 1.45*inch, 0.6*inch]
    rt = Table(rx_data, colWidths=col_widths)
    rt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, 0), 7.5),
        ("FONTSIZE", (0, 1), (-1, -1), 7),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fb")]),
        # Highlight the pre-accident Gabapentin rows in amber to draw attention (for demo)
        ("BACKGROUND", (0, 1), (-1, 2), colors.HexColor("#fffbeb")),
        ("TEXTCOLOR", (0, 1), (-1, 2), colors.HexColor("#92400e")),
        ("FONTNAME", (0, 1), (-1, 2), "Helvetica"),
        ("ALIGN", (7, 0), (7, -1), "RIGHT"),
    ]))
    story.append(rt)
    story.append(Spacer(1, 8))

    # Billing summary
    story.append(Paragraph("BILLING SUMMARY", s["section_title"]))
    story.append(_hr())
    bill_sum = [
        ["Category", "Rx Count", "Total Billed"],
        ["Pre-accident prescriptions (Nov–Dec 2024)", "2", "$76.00"],
        ["Post-accident prescriptions (Jan–Apr 2025)", "10", "$771.00"],
        ["TOTAL (All prescriptions this period)", "12", "$847.00"],
    ]
    bst = Table(bill_sum, colWidths=[3.2*inch, 1.2*inch, 1.2*inch])
    bst.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fb")),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
    ]))
    story.append(bst)
    story.append(Spacer(1, 8))

    story.append(Paragraph(
        "<b>Note:</b> Prescriptions filled 11/14/2024 and 12/12/2024 (highlighted above) were "
        "filled prior to the reported date of accident (01/08/2025) and were prescribed by "
        "Dr. Elena Vasquez (Internal Medicine). Gabapentin (300mg) is indicated for neuropathic "
        "pain and nerve-related conditions. These fills are included in this record at the "
        "request of the authorized requesting party.",
        s["body"]))
    story.append(Spacer(1, 8))

    # Grand total damages box
    story.append(Paragraph("TOTAL DAMAGES SUMMARY — ALL PROVIDERS", s["section_title"]))
    story.append(_hr())
    grand_data = [
        ["Provider", "Date(s)", "Total Billed", "Total Paid", "Outstanding"],
        ["Tampa General Hospital — ED", "01/08/2025", "$8,450.00", "$3,200.00", "$5,250.00"],
        ["Advanced Imaging of Tampa — MRI", "01/15/2025", "$4,200.00", "$1,680.00", "$2,520.00"],
        ["Tampa Bay Orthopedic Specialists", "01/22–02/19/2025", "$2,100.00", "$840.00", "$1,260.00"],
        ["Florida Pain & Spine Institute", "03/10/2025", "$6,800.00", "$2,720.00", "$4,080.00"],
        ["ProActive Physical Therapy", "02/01–03/28/2025", "$4,801.00", "$1,920.40", "$2,880.60"],
        ["CVS Pharmacy #4821", "01/09–04/01/2025", "$847.00", "$0.00", "$847.00"],
        ["GRAND TOTAL", "", "$27,198.00", "$10,360.40", "$16,837.60"],
    ]
    gt = Table(grand_data, colWidths=[1.9*inch, 1.3*inch, 1.0*inch, 1.0*inch, 1.0*inch])
    gt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, -1), (-1, -1), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f7fb")]),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]))
    story.append(gt)
    story.append(Spacer(1, 10))
    story.append(Paragraph(
        "Pharmacy records certified by: Patricia Okonkwo, PharmD  •  CVS Pharmacy #4821  •  "
        "FL Pharmacist License: PS28471  •  Records generated: 04/20/2025",
        s["small"]))
    story.append(Paragraph(
        "CONFIDENTIAL — These pharmacy records contain protected health information (PHI) "
        "and are produced pursuant to a valid HIPAA authorization. Unauthorized use or "
        "disclosure is strictly prohibited. FOR LEGAL PROCEEDINGS USE ONLY.",
        s["disclaimer"]))


# ── Helper table builders ──────────────────────────────────────────────────────

def _info_table(data):
    tbl = Table(data, colWidths=[1.3*inch, 2.5*inch, 1.3*inch, 1.5*inch])
    tbl.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d9e8")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f4f7fb"), colors.HexColor("#eef2f9")]),
    ]))
    return tbl


def _bill_table(data):
    bt = Table(data, colWidths=[2.4*inch, 0.9*inch, 0.9*inch, 1.0*inch, 0.9*inch])
    bt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -2), "Helvetica"),
        ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f0fb")),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f4f7fb")]),
        ("ALIGN", (2, 0), (-1, -1), "RIGHT"),
    ]))
    return bt


# ══════════════════════════════════════════════════════════════════════════════
# MAIN — assemble and build PDF
# ══════════════════════════════════════════════════════════════════════════════

def build_pdf():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    s = _styles()

    # PageBreak between sections
    from reportlab.platypus import PageBreak

    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        leftMargin=0.75*inch,
        rightMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch,
    )

    story = []

    # Cover page — brief index
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph("MEDICAL RECORDS COMPILATION", ParagraphStyle(
        "cover_title", fontSize=18, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3a5c"), alignment=TA_CENTER, spaceAfter=6)))
    story.append(Paragraph("Personal Injury Case — For Legal Proceedings", ParagraphStyle(
        "cover_sub", fontSize=11, fontName="Helvetica",
        textColor=colors.HexColor("#555555"), alignment=TA_CENTER, spaceAfter=30)))
    story.append(_thick_hr())
    story.append(Spacer(1, 0.2*inch))

    cover_data = [
        ["Patient:", "Maria Rodriguez"],
        ["Date of Birth:", "April 12, 1988"],
        ["Address:", "4521 Bay Shore Blvd, Tampa, FL 33611"],
        ["Date of Accident:", "January 8, 2025"],
        ["Type of Accident:", "Motor Vehicle Accident (Rear-end collision, I-275 Tampa)"],
        ["Records Period:", "January 8, 2025 — April 30, 2025"],
        ["Compiled:", "April 20, 2025"],
        ["Total Pages:", "10"],
    ]
    ct = Table(cover_data, colWidths=[1.8*inch, 4.8*inch])
    ct.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#d0d9e8")),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#f4f7fb")]),
        ("LEFTPADDING", (0, 0), (-1, -1), 10),
    ]))
    story.append(ct)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("TABLE OF CONTENTS", ParagraphStyle(
        "toc_h", fontSize=12, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1a3a5c"), spaceBefore=10, spaceAfter=6)))
    toc_data = [
        ["Pages", "Provider", "Service Type", "Date(s)"],
        ["1–2", "Tampa General Hospital — Emergency Dept.", "Emergency Visit + CT Scans", "01/08/2025"],
        ["3–4", "Advanced Imaging of Tampa", "MRI Cervical + Lumbar Spine", "01/15/2025"],
        ["5–6", "Tampa Bay Orthopedic Specialists", "Orthopedic Consult + 2 Follow-ups", "01/22 – 02/19/2025"],
        ["7–8", "Florida Pain & Spine Institute", "Cervical Epidural Steroid Injection", "03/10/2025"],
        ["9", "ProActive Physical Therapy", "16 PT Sessions — Treatment Summary", "02/01 – 03/28/2025"],
        ["10", "CVS Pharmacy #4821", "Prescription Fill History", "11/2024 – 04/2025"],
    ]
    toc_t = Table(toc_data, colWidths=[0.5*inch, 2.2*inch, 2.0*inch, 1.6*inch])
    toc_t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3a5c")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f7fb")]),
    ]))
    story.append(toc_t)
    story.append(Spacer(1, 0.4*inch))
    story.append(Paragraph(
        "CONFIDENTIALITY NOTICE: This document contains protected health information (PHI) as defined "
        "under the Health Insurance Portability and Accountability Act of 1996 (HIPAA), 45 CFR §164 et seq. "
        "This compilation is produced for use in a personal injury legal proceeding pursuant to valid patient "
        "authorization. Any unauthorized disclosure, copying, or use of this information is strictly "
        "prohibited and may be subject to civil and criminal penalties. If you have received this document "
        "in error, please contact the originating provider immediately and destroy all copies.",
        ParagraphStyle("disclaimer_cover", fontSize=7.5, fontName="Helvetica-Oblique",
                       textColor=colors.HexColor("#666666"), leading=11)))

    story.append(PageBreak())

    # Section 1 — ER (pages 1-2)
    page_er_admission(s, story)
    story.append(PageBreak())

    # Section 2 — Imaging (pages 3-4)
    page_imaging(s, story)
    story.append(PageBreak())

    # Section 3 — Ortho (pages 5-6)
    page_ortho(s, story)
    story.append(PageBreak())

    # Section 4 — Pain Mgmt (pages 7-8)
    page_pain_mgmt(s, story)
    story.append(PageBreak())

    # Section 5 — PT (page 9)
    page_physical_therapy(s, story)
    story.append(PageBreak())

    # Section 6 — Pharmacy (page 10, with inconsistency)
    page_pharmacy(s, story)

    doc.build(story)
    print(f"PDF generated: {OUTPUT_PATH}")
    print(f"File size: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    build_pdf()
