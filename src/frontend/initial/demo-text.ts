// Display-only placeholders with NO backend source (see initial/README.md).
// Every value here is demo text from the pasted design. The shippable rebuild
// deletes this file: anything still imported from it has no source of truth.
export const HEADER_TEAM = "Dr. Sara Al-Husseini · Omar Qadi RN";
export const HEADER_DAY = "Wednesday 15 October 2025";
export const CLUSTER = "Riyadh North Cluster";
export const STATION = "STN-RUH-0842 · v4.12-PROD";
export const NAV_COUNTS = { roster: 4, active: 1, inbox: 3, queue: 3 };

// Per-card extras the roster endpoint does not return (no MRN, address, slot,
// or duration exists in Phase 1). Matched by card order, first visit onwards.
export const CARD_EXTRAS = [
  {
    timeChip: "09:00 · Overdue (50m)",
    timeTone: "bg-tertiary-container text-on-tertiary",
    suffix: ", 68M",
    sub: "MRN: 948210 · Al-Malqa District, Street 14",
    windowLabel: "Target Window",
    windowValue: "09:00 – 09:45 AST",
    windowTone: "text-tertiary-container",
  },
  {
    timeChip: "10:30 AST",
    timeTone: "bg-surface-container-high text-on-surface",
    suffix: ", 72F",
    sub: "MRN: 881294 · Al-Nakheel, Residence Complex 3",
    windowLabel: "Target Window",
    windowValue: "10:30 – 11:30 AST",
    windowTone: "text-on-surface",
  },
  {
    timeChip: "Active Encounter",
    timeTone: "bg-primary text-on-primary",
    suffix: ", 59M",
    sub: "MRN: 712034 · Al-Sahafa District",
    windowLabel: "Scheduled Slot",
    windowValue: "11:45 AST",
    windowTone: "text-on-surface",
  },
  {
    timeChip: "Completed",
    timeTone: "bg-surface-container-high text-on-surface-variant",
    suffix: ", 64F",
    sub: "MRN: 602391 · Al-Ghadir, Villa 8",
    windowLabel: "Session Duration",
    windowValue: "38 Minutes",
    windowTone: "text-on-surface",
  },
];

export const FALLBACK_EXTRA = {
  timeChip: "Demo slot",
  timeTone: "bg-surface-container-high text-on-surface-variant",
  suffix: "",
  sub: "Demo details pending — no source in Phase 1",
  windowLabel: "Target Window",
  windowValue: "—",
  windowTone: "text-on-surface-variant",
};

// Pre-Visit Brief placeholders with NO backend source. The Brief endpoint owns
// trends, last_visit, previous_plan, due and blind_spots; everything below is
// demo text from the pasted design.
export const BRIEF_BANNER = {
  suffix: ", 68M",
  mrn: "MRN 948210",
  citizenLine1: "Citizen ID: 1048829103",
  citizenLine2: "National Unified Medical Record Linked",
  language: "Arabic (Native)",
  diagnosisLine1: "- Type 2 DM",
  diagnosisLine2: "- Essential HTN",
  mobility: "Independent Ambulatory",
  acuity: "Tier 1 Stable Chronic",
  assignedTo: "Dr. Sara Al-Husseini · Omar Qadi RN",
};

export const BRIEF_HISTORY = [
  { date: "14 Jul 2025", time: "10:14 AST", type: "Routine Visit", status: "Completed", tone: "bg-surface-container text-on-surface" },
  { date: "12 Apr 2025", time: "11:30 AST", type: "Routine Visit", status: "Completed", tone: "bg-surface-container text-on-surface" },
  { date: "18 Jan 2025", time: "09:45 AST", type: "Emergency Protocol (Resolved)", status: "Ended Early", tone: "bg-secondary-container text-on-secondary-container" },
  { date: "15 Oct 2024", time: "14:00 AST", type: "Routine Visit", status: "Completed", tone: "bg-surface-container text-on-surface" },
  { date: "02 Jul 2024", time: "10:00 AST", type: "Baseline Visit", status: "Completed", tone: "bg-surface-container text-on-surface" },
];

export const BRIEF_GOAL_BP = {
  value: "130–135 / 80–85 mmHg",
  note: "ACC/AHA & Saudi Hypertension Guidelines 2023 · Prevents orthostatic drop while preserving renal perfusion",
};

export const BRIEF_GOAL_GLYCAEMIC = {
  value: "7.0% – 7.5% HbA1c",
  note: "Target relaxed for autonomic neuropathy and hypoglycemia avoidance",
};

// Clinical Verification placeholders with NO backend source. Statuses, gate,
// emergencies, and plan presence are wired; everything below is demo text.
// Phase 1 has no producer, so the recommendation cards are demo by necessity.
export const VERIFY_SECTIONS = [
  { key: "VISIT_REASON", num: "01", title: "Visit Reason", summary: "Scheduled review — Type 2 Diabetes & Primary Hypertension" },
  { key: "CONCERNS_AND_INTERVAL_HISTORY", num: "02", title: "Concerns & Interval History", summary: "Hypoglycaemic episode reported: “Mild symptomatic dip last Tuesday, resolved with dates”. Attributed concern from Caregiver Reem: “Complains of burning sensation in soles of feet at night.”" },
  { key: "MEDICATION_RECONCILIATION", num: "03", title: "Medication Reconciliation", summary: "Physical items in house: Metformin 1000mg (48 left), Amlodipine 5mg (14 left), Glimepiride 2mg (28 left). Unreachable reference list declared. Bedside verbal & blister pack cross-checked." },
  { key: "VITALS", num: "04", title: "Vitals & Home Readings", summary: "BP 136/84 mmHg, HR 72 bpm regular, SpO2 98%, Accu-Chek Guide sync 138 mg/dL 7-day fasting mean." },
  { key: "PHYSICAL_EXAMINATION", num: "05", title: "Physical Examination", summary: "Diabetic foot screening completed (Monofilament 10g sensory map intact 8/10 points, Pedal pulses 2+ bilateral)." },
  { key: "SELF_CARE_CHECK", num: "06", title: "Self-Care Check", summary: "" },
  { key: "NOTES", num: "07", title: "Attending Clinical Notes", summary: "Attending clinical evaluation summary by Dr. Sara Al-Husseini recorded and signed bedside." },
  { key: "CARE_PLAN", num: "08", title: "Care Plan & Between-Visit Mandate", summary: "Metformin BD, Amlodipine OD, Blood pressure stop rule (>180 or <100 mmHg). 3 machine-testable lines emitted." },
];

export const VERIFY_SELF_CARE_COPY =
  "Required bedside observation for Insulin Cold-Chain & Storage or Oral Regimen Verification not captured. Section must have verified observation or structured non-resolution reason before visit completion (§5.8, N6).";

export const VERIFY_TRANSMISSION = {
  target: "RUH-Central EMR",
  sub: "Payload: 38.4 KB (Encrypted) · Awaiting completion",
};

export const VERIFY_VITALS = [
  { label: "BLOOD PRESSURE", value: "136/84", unit: "mmHg" },
  { label: "HEART RATE", value: "72", unit: "bpm · regular" },
  { label: "SPO₂", value: "98%", unit: "room air" },
  { label: "FASTING GLUCOSE", value: "138", unit: "mg/dL · 7-day mean" },
];

export const VERIFY_RECS = [
  {
    tag: "Rec #1 · Tier 1",
    badge: "Accepted",
    title: "Dilated Eye Exam Referral",
    tierLine: "Tier 1 · Supervisor Review within 72 Hours",
    modalTitle: "Referral for Comprehensive Dilated Eye Exam",
    body: "Surveillance overdue by 42 days. Confirmed bedside by Dr. Sara Al-Husseini with patient consent. Queued directly to Optometry Triage at Riyadh North Sector.",
    facts: [
      "Provenance Guideline: ADA 2024 Standards of Care, Section 12 (Retinopathy Screening)",
      "Routing Action: Transmission queued for RUH-Optometry Referral Outbox",
      "Attending Action: Accepted bedside without modification",
    ],
  },
  {
    tag: "Rec #2 · Tier 0",
    badge: "Overridden",
    title: "Gabapentin 100 mg nocte",
    tierLine: "Tier 0 · Field Team Acts Bedside",
    modalTitle: "Prescribe Gabapentin 100mg nocte or topical agent",
    body: "Triggered by caregiver report of burning sensations in bilateral soles of feet. Overridden bedside with structured two-level clinical justification (§5.10).",
    facts: [
      "Level 1 Category: Right guideline, not executable today",
      "Level 2 Clinical Reason: Patient requests non-pharmacological foot cooling trial before adding new oral neuroactive medication",
      "Override authorized by: Dr. Sara Al-Husseini (Junior Physician, License #48102)",
      "Provenance: ADA Neuropathy Care Guidelines & Saudi MoH Type 2 DM Pathway",
    ],
  },
  {
    tag: "Rec #3 · Engine",
    badge: "Filed (Suppressed)",
    title: "Atorvastatin 40 mg Optimization",
    tierLine: "Tier 0 · Background Engine",
    modalTitle: "Statin Dosage Optimization (Atorvastatin 20mg to 40mg)",
    body: "Filed (unshown under N3 cap of 3 active bedside prompts). Stored in write-back audit data with deferral count 1. Will reappear automatically upon next routine surveillance cycle or following new lipid panel ingest.",
    facts: [
      "Provenance Guideline: ACC/AHA & Saudi Hypertension/Dyslipidemia Guidelines",
      "Engine Action: Filed to local database; no immediate clinician action required today",
    ],
  },
];

export const VERIFY_ATTEST = {
  quote:
    "“I hereby certify that the clinical observations, degraded reconciliation declarations, and decision overrides recorded during this residence visit accurately reflect the patient state and bedside findings.”",
  role: "Attending Junior Physician · Saudi Commission for Health Specialties #48102",
  timestamp: "15 Oct 2025 · 14:41 AST",
};

// Supervisor Inbox placeholders with NO backend source. Rows, due times,
// recommendations, flags, dispositions, goal bands and lineage are wired;
// everything below is demo text from the pasted design. The Supervisor's name
// stands in for a sign-in Phase 1 does not have.
export const INBOX_SUPERVISOR = "Dr. Tariq Mansoor";

export const INBOX_DEMO = {
  consultantRole: "Consultant Endocrinologist · Regional Oversight Lead",
  consultantLicence: "MOH-LIC: SA-END-88924 · Cryptographic Key Active",
  contextParagraph:
    "Caregiver daughters (Mona & Reem) actively manage pillbox setup and administration. Automatic home sphygmomanometer validated with adult extra-large cuff (32–42 cm) during the baseline visit. Verified refrigerator temperature log confirms insulin cold-chain integrity.",
  contextChips: [
    "Validated Monitor: Omron M7 Intelli IT",
    "Caregiver Training: Completed 14:05 AST",
    "Living Situation: Residence with 2 Caregivers",
  ],
  auditNote:
    "Sampled under the 10% Silence Audit: this Visit produced no Recommendations, so the Supervisor reads the record itself. A disagreement here is a report about a rule that never fired.",
};

// Write-Back Queue placeholders with NO backend source. Envelopes, refusals,
// owners, due times, and addenda are wired (GET /api/queue, POST dispatches);
// everything below is demo text from the pasted design. Envelope IDs, payload
// sizes, SHA keys, FHIR transaction IDs, endpoint URLs, NFC/export, signature
// verification, and storage-meter figures have no Phase 1 source.
export const QUEUE_DEMO = {
  syncLine: "Local cache synchronized as-of 14:32 AST",
  sizeLine: "Payload Size: sealed on this device",
  endpointLine:
    "Endpoint: https://ruh-central.moh.gov.sa/fhir/Bundle/$process-message · Upstream server refused validation.",
  exportToast:
    "NFC interface armed. Tap supervisor token against top-edge tablet reader.",
  verifyToast:
    "Local database integrity verified. 4 signatures valid against KSA MoH Root Cert.",
  storageLine: "Local Store: 312 KB Used / 16 GB Allocated",
  dispatchedCard: {
    envelope: "WB-2025-1039",
    patient: "Mona Al-Khatib (Routine Visit)",
    sentLine: "Dispatched at 08:52 AST to RUH-Central EMR FHIR endpoint.",
    transaction: "Transaction ID: #FHIR-SA-99482",
  },
};
// Clinical Addendum placeholders with NO backend source. The addendum text,
// author, timestamp, flagged switch, prior addenda list, commit refusals, and
// confirmation state are wired (GET/POST /api/visits/{id}/addenda); everything
// below is demo text from the pasted design. The author name stands in for a
// sign-in Phase 1 does not have, like the inbox's Supervisor name.
export const ADDENDUM_DEMO = {
  suffix: ", 68M",
  mrnLine: "MRN: 948210",
  authorRole: "Junior Physician, Attending Lead",
  timestampLine: "15 Oct 2025 · 15:02 AST",
  ntpLine: "Synchronized via Riyadh KSA Regional NTP",
  supervisorRole: "Standing Assignment Consultant · Lic. SA-MOH-49102",
  supervisorNote: "Automatic default based on geographical sector: Central Region Sector 4.",
  hashLine: "Cryptographic hash will bind upon commitment",
  envelopeLine: "Envelope N6: Independent Addendum Write-Back",
  envelopeSub:
    "Will append to remote master record without reopening clinical status or mutating original vital sign logs.",
  stagedLine:
    "The addendum has been written to the local encrypted SQLite queue. 1 item staged for synchronous uplink to the Central Regional Repository.",
};
// Emergency Protocol placeholders with NO backend source. Patient name,
// timeline entries, allergy line, and the exit gate are wired; everything
// below is demo text from the pasted design (no MRN, dispatch, medication,
// or vitals-trajectory source exists in Phase 1).
export const EMERG_DEMO = {
  suffix: ", 68M",
  mrnLine: "MRN: 948210 · KSA National ID: 1083921441",
  ingressNote: "Red Crescent Dispatch",
  emptyHint: "No lines written yet — one entry is what lets this Visit close.",
  handoverUnit: "Red Crescent Unit 14 Direct Custody",
  handoverOfficers: "Dr. Sara Al-Husseini (Consultant Family Medicine) · Omar Qadi RN",
  handoverMeds: [
    "· Bisoprolol 5mg po OD (Morning dose taken 08:30 AST)",
    "· Sacubitril/Valsartan 24/26mg po BID",
    "· Empagliflozin 10mg po OD",
    "· Furosemide 40mg po PRN",
  ],
  handoverVitals: [
    { label: "13:50 Base", value: "128/78" },
    { label: "14:14 Drop", value: "86/52" },
    { label: "14:18 Post-O2", value: "92/58" },
  ],
};
