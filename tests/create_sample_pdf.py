"""Generate a realistic multi-page test medical record PDF for Week 3 E2E testing."""
import sys
from pathlib import Path

# Allow running from any directory
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors

OUTPUT = PROJECT_ROOT / "tests" / "sample_records" / "test_medical_record.pdf"

RECORDS = [
    {
        "page_title": "EMERGENCY DEPARTMENT — DISCHARGE SUMMARY",
        "date": "March 14, 2023",
        "provider": "Tampa General Hospital — Dr. Maria Santos, MD",
        "body": [
            "PATIENT: John Anderson  |  DOB: 07/12/1978  |  MRN: 00234567",
            "DATE OF SERVICE: 03/14/2023  |  ADMIT: 2:41 PM  |  DISCHARGE: 8:15 PM",
            "",
            "CHIEF COMPLAINT: Acute lower back pain and cervical pain following MVA.",
            "",
            "HISTORY OF PRESENT ILLNESS:",
            "Mr. Anderson is a 44-year-old male presenting via EMS following a rear-end",
            "motor vehicle collision on I-275 southbound. Patient was restrained driver.",
            "Airbags did not deploy. Vehicle was struck at approximately 45 mph.",
            "Patient denies any prior history of back pain or neck injury.",
            "",
            "PHYSICAL EXAMINATION:",
            "Vitals: BP 138/88, HR 94, RR 18, Temp 98.6F, SpO2 99%",
            "Musculoskeletal: Midline lumbar tenderness at L4-L5. Cervical paraspinal",
            "muscle spasm. ROM limited in all planes. No radiculopathy noted.",
            "Neurological: Intact sensation bilateral lower extremities. DTRs 2+ symmetric.",
            "",
            "ASSESSMENT & PLAN:",
            "1. Acute lumbar strain (M54.5)",
            "2. Cervical sprain (S13.4XXA)",
            "MRI lumbar spine ordered. MRI cervical spine ordered.",
            "Ibuprofen 800mg TID with food. Cyclobenzaprine 5mg TID PRN.",
            "Physical therapy referral placed. Follow up orthopedics in 1 week.",
            "",
            "BILLING: Total charges $4,200.00  |  Insurance paid $1,890.00",
            "Patient responsibility $2,310.00",
        ],
    },
    {
        "page_title": "RADIOLOGY REPORT — MRI LUMBAR SPINE",
        "date": "March 16, 2023",
        "provider": "Tampa Bay Radiology Associates — Dr. Kevin Park, MD",
        "body": [
            "PATIENT: John Anderson  |  MRN: 00234567  |  Ordering Physician: Dr. Santos",
            "EXAM DATE: 03/16/2023  |  EXAM: MRI Lumbar Spine without contrast",
            "",
            "CLINICAL INDICATION: MVA 03/14/2023, acute back pain, r/o disc herniation",
            "",
            "TECHNIQUE: Sagittal T1, T2, STIR; Axial T2 sequences. 3T scanner.",
            "",
            "FINDINGS:",
            "L3-L4: Mild posterior disc bulge. Moderate bilateral facet arthrosis.",
            "No significant foraminal narrowing.",
            "",
            "L4-L5: Broad-based posterior disc protrusion measuring 6mm AP displacement.",
            "Mild bilateral lateral recess narrowing. Mild left foraminal narrowing.",
            "Mild compression of the traversing left L5 nerve root is suspected.",
            "",
            "L5-S1: Disc desiccation with mild disc height loss. Mild posterior bulge.",
            "No significant neural compromise.",
            "",
            "IMPRESSION:",
            "1. L4-L5 disc protrusion with possible mild left L5 nerve root compression.",
            "   Clinical correlation and EMG/NCV recommended.",
            "2. Multilevel degenerative disc disease, most prominent L4-L5 and L5-S1.",
            "3. No fracture, spondylolisthesis, or cord compression.",
            "",
            "BILLING: Total charges $2,800.00  |  Insurance paid $1,260.00",
        ],
    },
    {
        "page_title": "ORTHOPEDIC CONSULTATION — INITIAL VISIT",
        "date": "March 21, 2023",
        "provider": "Florida Spine & Orthopedic — Dr. James Ortega, MD",
        "body": [
            "PATIENT: John Anderson  |  DOB: 07/12/1978  |  MRN: 00456789",
            "DATE OF SERVICE: 03/21/2023  |  VISIT TYPE: New Patient Consultation",
            "",
            "REFERRING PHYSICIAN: Dr. Maria Santos, Tampa General Hospital",
            "REASON FOR REFERRAL: MVA 03/14/2023, lumbar disc protrusion at L4-L5",
            "",
            "HISTORY:",
            "Mr. Anderson presents one week post-MVA with worsening left-sided leg pain",
            "radiating from the lower back into the left buttock and posterolateral thigh.",
            "Numerical Pain Rating: 7/10 at rest, 9/10 with activity. Unable to sit",
            "for more than 20 minutes. Sleeping poorly secondary to pain.",
            "Denies bowel or bladder dysfunction.",
            "",
            "REVIEW OF IMAGING: MRI 03/16/2023 reviewed. L4-L5 disc protrusion with",
            "left foraminal involvement consistent with left L5 radiculopathy.",
            "",
            "EXAMINATION:",
            "Antalgic gait favoring right side. Positive straight leg raise at 45 degrees",
            "left side. Diminished sensation lateral left foot (L5 dermatomal distribution).",
            "Left EHL strength 4/5 compared to 5/5 right.",
            "",
            "PLAN:",
            "1. Left L4-L5 transforaminal epidural steroid injection (TFESI) — scheduled",
            "2. EMG/NCV bilateral lower extremities ordered",
            "3. Formal physical therapy: lumbar stabilization program, 3x/week x 6 weeks",
            "4. Gabapentin 300mg TID added to regimen",
            "5. Continue Ibuprofen and Cyclobenzaprine as prescribed by ER",
            "6. Return in 3 weeks for re-evaluation post-injection",
            "",
            "BILLING: Office visit $425.00  |  Insurance paid $191.25",
        ],
    },
    {
        "page_title": "PHYSICAL THERAPY — INITIAL EVALUATION",
        "date": "March 28, 2023",
        "provider": "Advanced Physical Therapy of Tampa — Sarah Kim, DPT",
        "body": [
            "PATIENT: John Anderson  |  DOB: 07/12/1978",
            "DATE OF SERVICE: 03/28/2023  |  REFERRING MD: Dr. J. Ortega",
            "DIAGNOSIS: Lumbar disc protrusion L4-L5 (M51.16), Left L5 radiculopathy",
            "",
            "SUBJECTIVE:",
            "Patient reports constant dull aching in lumbar spine rated 6/10, sharp",
            "left leg pain with prolonged sitting rated 8/10. Functional limitations:",
            "unable to perform job duties (delivery driver), cannot exercise, difficulty",
            "performing ADLs including prolonged standing while cooking.",
            "",
            "OBJECTIVE:",
            "Posture: Forward head posture, reduced lumbar lordosis.",
            "ROM: Lumbar flexion 45 deg (WNL 90), extension 10 deg (WNL 25),",
            "lateral flexion R 15/L 10 deg.",
            "Strength: Hip abductors 4/5 bilateral, multifidus 3+/5 bilateral.",
            "Special tests: Positive SLR 40 degrees left, FABER positive left.",
            "",
            "PLAN: 18 visits over 6 weeks.",
            "Goals: Reduce pain NRS by 50%, restore functional ROM,",
            "return to modified work duties within 6 weeks.",
            "",
            "Modalities: Moist heat, TENS, manual therapy, therapeutic exercise.",
            "",
            "BILLING: Initial evaluation $350.00  |  Insurance paid $157.50",
        ],
    },
    {
        "page_title": "PAIN MANAGEMENT — EPIDURAL STEROID INJECTION NOTE",
        "date": "April 4, 2023",
        "provider": "Florida Spine & Orthopedic — Dr. James Ortega, MD",
        "body": [
            "PATIENT: John Anderson  |  MRN: 00456789",
            "DATE OF PROCEDURE: 04/04/2023",
            "PROCEDURE: Left L4-L5 Transforaminal Epidural Steroid Injection",
            "FACILITY: Florida Spine Ambulatory Surgery Center",
            "",
            "PRE-PROCEDURE HISTORY:",
            "Patient presents for planned TFESI for left L5 radiculopathy secondary",
            "to MVA-related L4-L5 disc protrusion. Pain continues at 7/10 with",
            "significant functional limitation. Conservative management including PT",
            "and oral medications have provided only 20% relief.",
            "",
            "PROCEDURE NOTE:",
            "Patient was positioned prone on fluoroscopy table. Left L4-L5 foramen",
            "identified under fluoroscopic guidance. 22-gauge spinal needle advanced",
            "to target position. Contrast injected to confirm epidural spread.",
            "Injectate: 40mg triamcinolone acetonide + 3mL 0.5% bupivacaine.",
            "Procedure tolerated well. No complications. Post-procedure vitals stable.",
            "",
            "POST-PROCEDURE INSTRUCTIONS:",
            "Ice to injection site PRN. Avoid NSAIDs 48 hours. Resume PT in 4 days.",
            "Follow up in 3 weeks to assess response.",
            "",
            "BILLING: Procedure $1,850.00  |  Facility $1,200.00",
            "Insurance paid $1,387.50 (procedure) + $540.00 (facility)",
        ],
    },
    {
        "page_title": "PHYSICAL THERAPY — PROGRESS NOTE (Visit 8 of 18)",
        "date": "April 18, 2023",
        "provider": "Advanced Physical Therapy of Tampa — Sarah Kim, DPT",
        "body": [
            "PATIENT: John Anderson  |  DATE: 04/18/2023",
            "",
            "SUBJECTIVE: Patient reports improvement since TFESI on 04/04/2023.",
            "Lumbar pain NRS 4/10 at rest (improved from 6/10), 6/10 with activity",
            "(improved from 8/10). Left leg radicular symptoms reduced significantly.",
            "Patient able to sit up to 45 minutes (improved from 20 minutes).",
            "Sleeping 6-7 hours per night (improved from 4-5 hours).",
            "",
            "OBJECTIVE:",
            "ROM: Lumbar flexion 65 deg (improved from 45), extension 18 deg.",
            "Strength: Hip abductors 4+/5 bilateral (improved), multifidus 4/5.",
            "SLR: Negative bilateral at this visit.",
            "",
            "ASSESSMENT: Good progress toward goals. Patient responding well to",
            "combined PT and injection therapy.",
            "",
            "PLAN: Continue per plan of care. Advance home exercise program.",
            "Goal: 12 visits remaining over 5 weeks.",
            "",
            "BILLING: PT visit $175.00  |  Insurance paid $78.75",
        ],
    },
    {
        "page_title": "ORTHOPEDIC FOLLOW-UP — 6-WEEK RE-EVALUATION",
        "date": "May 2, 2023",
        "provider": "Florida Spine & Orthopedic — Dr. James Ortega, MD",
        "body": [
            "PATIENT: John Anderson  |  MRN: 00456789",
            "DATE OF SERVICE: 05/02/2023  |  VISIT TYPE: Follow-up",
            "",
            "INTERVAL HISTORY:",
            "Patient notes approximately 50% overall improvement since initial visit.",
            "Left leg radiculopathy has resolved. Lumbar pain persists at 4/10.",
            "Physical therapy ongoing, 8 of 18 sessions completed.",
            "Epidural injection provided sustained relief.",
            "",
            "EMG/NCV RESULTS REVIEWED (ordered 03/21/2023, completed 04/10/2023):",
            "Findings consistent with mild left L5 radiculopathy, chronic active.",
            "No evidence of axonal loss. Prognosis favorable with conservative care.",
            "",
            "EXAMINATION:",
            "Ambulation normal. SLR negative bilateral.",
            "Lumbar ROM improved but still limited: flexion 65 deg, extension 20 deg.",
            "No focal neurological deficits.",
            "",
            "PLAN:",
            "1. Continue physical therapy — 10 visits remaining",
            "2. Consider second TFESI if pain plateaus",
            "3. Continue Gabapentin, wean Cyclobenzaprine",
            "4. Disability paperwork completed — patient unable to return to",
            "   delivery driving duties pending further improvement",
            "5. Return in 6 weeks",
            "",
            "BILLING: Office visit $425.00  |  Insurance paid $191.25",
        ],
    },
    {
        "page_title": "BILLING SUMMARY — ACCOUNT STATEMENT",
        "date": "June 1, 2023",
        "provider": "Multiple Providers — Statement Date 06/01/2023",
        "body": [
            "PATIENT: John Anderson  |  Date of Injury: 03/14/2023",
            "",
            "SUMMARY OF CHARGES TO DATE:",
            "",
            "03/14/2023  Tampa General Hospital ER        $4,200.00   Paid $1,890.00",
            "03/16/2023  Tampa Bay Radiology (MRI-LS)     $2,800.00   Paid $1,260.00",
            "03/21/2023  Florida Spine Ortho (consult)    $  425.00   Paid $  191.25",
            "03/28/2023  Advanced PT (eval)               $  350.00   Paid $  157.50",
            "04/04/2023  Florida Spine (TFESI procedure)  $1,850.00   Paid $1,387.50",
            "04/04/2023  FL Spine ASC (facility fee)      $1,200.00   Paid $  540.00",
            "04/07/2023  Advanced PT x3 sessions          $  525.00   Paid $  236.25",
            "04/11/2023  Advanced PT x2 sessions          $  350.00   Paid $  157.50",
            "04/18/2023  Advanced PT (visit 8)            $  175.00   Paid $   78.75",
            "04/25/2023  Advanced PT x2 sessions          $  350.00   Paid $  157.50",
            "05/02/2023  Florida Spine Ortho (F/U)        $  425.00   Paid $  191.25",
            "05/09/2023  Advanced PT x2 sessions          $  350.00   Paid $  157.50",
            "05/16/2023  Advanced PT x2 sessions          $  350.00   Paid $  157.50",
            "",
            "SUBTOTAL BILLED:    $13,350.00",
            "SUBTOTAL PAID:       $6,413.50",
            "OUTSTANDING BALANCE: $6,936.50",
            "",
            "Note: Additional treatment anticipated. Lien on file with PI attorney.",
        ],
    },
]


def build_pdf() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.9 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=13, spaceAfter=6)
    h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=11, spaceAfter=4)
    body = ParagraphStyle("Body", parent=styles["Normal"], fontSize=9, leading=13)
    label = ParagraphStyle("Label", parent=styles["Normal"], fontSize=9, textColor=colors.grey)

    story = []
    for rec in RECORDS:
        story.append(Paragraph(rec["page_title"], h1))
        story.append(Paragraph(f"Date: {rec['date']}  |  Provider: {rec['provider']}", label))
        story.append(Spacer(1, 0.15 * inch))
        for line in rec["body"]:
            if line == "":
                story.append(Spacer(1, 0.08 * inch))
            else:
                story.append(Paragraph(line, body))
        from reportlab.platypus import PageBreak
        story.append(PageBreak())

    doc.build(story)
    print(f"Created: {OUTPUT}")
    import fitz
    doc2 = fitz.open(str(OUTPUT))
    print(f"Pages: {len(doc2)} | Extractable text: {bool(doc2[0].get_text('text').strip())}")
    doc2.close()


if __name__ == "__main__":
    build_pdf()
