"use client";

// Pre-Visit Brief — initial throwaway (see initial/README.md). Same process as
// the roster: the pasted design verbatim, the fields the backend owns wired to
// GET /api/visits/{id}/brief and GET /api/roster, demo text for the rest.
// Two requested fixes are applied here (brief.html keeps the pasted original):
// FIX 1 — text aligned left, not right (staging header, banner groups, table
// Action column). FIX 2 — the boxes under the graphs sit at the columns' top
// (justify-start), not pushed to the bottom (justify-between).
import { Suspense, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  BRIEF_BANNER,
  BRIEF_GOAL_BP,
  BRIEF_GOAL_GLYCAEMIC,
  BRIEF_HISTORY,
} from "../../../../initial/demo-text";
import { TAILWIND_CONFIG } from "../../../../initial/tailwind-config";
import {
  CLUSTER,
  HEADER_DAY,
  HEADER_TEAM,
  NAV_COUNTS,
  STATION,
} from "../../../../initial/demo-text";

type DatumValue =
  | string
  | {
      titration: { axis: string; comparison: string; value: number; action: string }[];
      schedule: { axis: string; times_per_week: number }[];
      stop_rules: { axis: string; comparison: string; value: number; action: string }[];
    }
  | null;
type BriefDatum = { state: string; value: DatumValue; as_of: string | null };
type Trend = {
  measurement: string;
  label: string;
  unit: string;
  points: { on: string; value: string }[];
};
type Due = {
  item: string;
  label: string;
  last_done: { state: string; value: string | null; as_of: string | null };
};
type Brief = {
  patient_id: string;
  trends: Trend[];
  last_visit: {
    on: string;
    state: string;
    reason: { row_id: string; free_text: string | null } | null;
  } | null;
  previous_plan: BriefDatum;
  due: Due[];
  blind_spots: string[];
};
type RosterRow = {
  visit_id: string;
  patient_id: string;
  patient_name: string;
  reason: string;
  state: string;
  planning: string;
};

const STATE_WORD: Record<string, string> = {
  scheduled: "Scheduled",
  in_progress: "In Progress",
  emergency: "Emergency",
  completed: "Completed",
  cancelled: "Cancelled",
  ended_early: "Ended Early",
};

function lastVisitLine(
  last: Brief["last_visit"],
): string {
  if (last === null) return "No completed history — this read is the first.";
  const reason =
    last.reason === null
      ? ""
      : ` — ${last.reason.free_text ?? last.reason.row_id}`;
  return `Last Visit concluded ${last.on} · ${STATE_WORD[last.state] ?? last.state}${reason}`;
}

function dueChip(lastDone: Due["last_done"]): { text: string; tone: string } {
  if (lastDone.state === "present")
    return {
      text: `Due — last ${lastDone.value}`,
      tone: "bg-secondary-container text-on-secondary-container",
    };
  return { text: "Due — never recorded", tone: "bg-error-container text-on-error-container" };
}

function dueBenchmark(lastDone: Due["last_done"]): string {
  if (lastDone.state === "present")
    return `Last recorded ${lastDone.value}${lastDone.as_of ? ` · read ${lastDone.as_of}` : ""}`;
  return "No record in Noor.";
}

export default function BriefView() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <BriefBody />
    </Suspense>
  );
}

function BriefBody() {
  const params = useParams<{ visitId: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const visitId = params.visitId;
  const day = search.get("day") ?? "2026-08-28";

  const [brief, setBrief] = useState<Brief | null>(null);
  const [rosterRow, setRosterRow] = useState<RosterRow | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    Promise.all([
      fetch(`/api/visits/${visitId}/brief?as_of=${day}`).then((r) => {
        if (!r.ok) throw new Error(`brief HTTP ${r.status}`);
        return r.json();
      }),
      fetch(`/api/roster?day=${day}`).then((r) => {
        if (!r.ok) throw new Error(`roster HTTP ${r.status}`);
        return r.json();
      }),
    ])
      .then(([briefBody, rosterBody]) => {
        if (!live) return;
        setBrief(briefBody as Brief);
        const rows = rosterBody.visits as RosterRow[];
        setRosterRow(rows.find((r) => r.visit_id === visitId) ?? null);
      })
      .catch(() => {
        if (live) {
          setBrief(null);
          setLoadError("The Brief could not be read.");
        }
      });
    return () => {
      live = false;
    };
  }, [visitId, day]);

  const planningWord =
    rosterRow === null
      ? "—"
      : rosterRow.planning === "baseline"
        ? "Baseline Visit"
        : "Routine Visit";
  const patientName = rosterRow?.patient_name ?? brief?.patient_id ?? "…";

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center">
      <script src="https://cdn.tailwindcss.com" />
      <script id="tailwind-config" dangerouslySetInnerHTML={{ __html: TAILWIND_CONFIG }} />
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
        rel="stylesheet"
      />
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,100..1000;1,9..40,100..1000&family=EB+Garamond:ital,wght@0,400..800;1,400..800&display=swap"
        rel="stylesheet"
      />
      <style>{`@layer base { html, body { margin: 0; padding: 0; } body { overscroll-behavior: none; } main > :first-child { margin-top: 0 !important; } main > :last-child { margin-bottom: 0 !important; } } ::-webkit-scrollbar { display: none; }`}</style>
      <div className="w-full max-w-[768px] min-h-screen flex flex-col bg-surface shadow-[0_4px_20px_rgba(40,35,28,0.04)]">
        <header className="fixed top-0 w-full max-w-[768px] z-50 bg-surface/95 shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
          <div className="h-16 px-margin flex items-center justify-between">
            <div className="flex items-baseline gap-space-sm">
              <span className="font-headline-md text-headline-md tracking-tight text-primary">NOOR</span>
              <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                Home Clinical Care
              </span>
            </div>
            <div className="flex items-center gap-space-md">
              <div className="hidden sm:flex flex-col items-end">
                <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                  GOOD MORNING
                </span>
                <span className="font-label-md text-label-md text-on-surface font-semibold">
                  {HEADER_TEAM}
                </span>
              </div>
              <div className="h-6 w-px bg-outline-variant hidden sm:block"></div>
              <div className="flex items-center bg-surface-container-high rounded-full p-0.5">
                <button
                  aria-label="Day Mode"
                  className="w-7 h-7 rounded-full bg-surface-container-lowest text-primary flex items-center justify-center shadow-sm"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[16px]">light_mode</span>
                </button>
                <button
                  aria-label="Night Mode"
                  className="w-7 h-7 rounded-full text-on-surface-variant flex items-center justify-center"
                  type="button"
                >
                  <span className="material-symbols-outlined text-[16px]">dark_mode</span>
                </button>
              </div>
              <div className="w-8 h-8 rounded-full bg-primary flex items-center justify-center">
                <span className="material-symbols-outlined text-on-primary text-[18px]">person</span>
              </div>
            </div>
          </div>
          <div className="px-margin py-1.5 bg-surface-container-low flex items-center justify-between text-on-surface-variant font-label-sm text-label-sm">
            <div className="flex items-center gap-space-md">
              <span className="font-semibold uppercase tracking-wider text-on-surface">
                {HEADER_DAY}
              </span>
              <span className="text-outline-variant">|</span>
              <span className="">Sync Status: Local DB Ready</span>
            </div>
            <div className="font-semibold uppercase tracking-wider text-on-surface">{CLUSTER}</div>
          </div>
          <nav
            className="px-margin py-2 bg-surface flex items-center gap-space-sm overflow-x-auto"
            data-active-classes="bg-primary text-on-primary font-semibold rounded-full"
          >
            <a
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors whitespace-nowrap"
              data-path="roster"
              href="/initial"
            >
              <span className="">ROSTER</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface-variant font-semibold">
                {NAV_COUNTS.roster}
              </span>
            </a>
            <a
              aria-current="page"
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm uppercase tracking-wider transition-colors whitespace-nowrap bg-primary text-on-primary font-semibold rounded-full font-label-md text-label-md"
              data-path="active-visit"
              href="#"
            >
              <span className="">ACTIVE VISIT</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-highest text-on-surface font-semibold">
                {NAV_COUNTS.active}
              </span>
            </a>
            <a
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors whitespace-nowrap"
              data-path="supervisor-inbox"
              href="/inbox"
            >
              <span className="">SUPERVISOR INBOX</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface-variant font-semibold">
                {NAV_COUNTS.inbox}
              </span>
            </a>
            <a
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors whitespace-nowrap"
              data-path="write-back-queue"
              href="/queue"
            >
              <span className="">WRITE-BACK QUEUE</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface-variant font-semibold">
                {NAV_COUNTS.queue}
              </span>
            </a>
          </nav>
        </header>
        <main className="w-full pt-36 px-margin pb-space-xl flex-1 bg-surface">
          <div className="flex flex-col w-full">
            <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-sm pb-space-lg">
              <div className="flex flex-col">
                <div className="flex items-center gap-space-sm">
                  <span className="w-1.5 h-1.5 rounded-full bg-secondary"></span>
                </div>
                <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight mt-0.5">
                  Pre-Visit Brief
                </h1>
              </div>
              {/* FIX 1: staging note aligned left, not right */}
              <div className="flex flex-col sm:items-start">
                <span className="font-label-sm text-label-sm text-on-surface-variant tracking-wider uppercase">
                  In-Vehicle Staging
                </span>
              </div>
            </div>
            {loadError !== null && (
              <div className="w-full bg-surface-container-low p-space-md rounded-lg mb-space-lg">
                <span className="font-body-md text-body-md text-on-surface">{loadError}</span>
              </div>
            )}
            <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-md mb-space-xl">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-space-lg pb-space-lg">
                <div className="flex flex-col">
                  <div className="flex items-baseline gap-space-md flex-wrap">
                    <span className="font-headline-md text-headline-md text-primary">
                      {patientName}
                      {BRIEF_BANNER.suffix}
                    </span>
                    <span className="font-data-metric text-data-metric font-mono text-on-surface-variant tracking-tight">
                      {BRIEF_BANNER.mrn}
                    </span>
                  </div>
                  <span className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                    {BRIEF_BANNER.citizenLine1}
                    <br />
                    {BRIEF_BANNER.citizenLine2}
                  </span>
                  {rosterRow !== null && (
                    <span className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                      Scheduled reason: {rosterRow.reason}
                    </span>
                  )}
                </div>
                {/* FIX 1: banner groups aligned left, not right */}
                <div className="flex items-center gap-space-md">
                  <div className="flex flex-col items-start">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Visit Type
                    </span>
                    <span className="font-label-lg text-label-lg font-semibold text-primary">
                      {planningWord}
                    </span>
                  </div>
                  <div className="h-8 w-1 bg-secondary-container rounded-full"></div>
                  <div className="flex flex-col items-start">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                      Assigned TO
                    </span>
                    <span className="font-label-md text-label-md text-on-surface font-medium text-left">
                      {BRIEF_BANNER.assignedTo}
                    </span>
                  </div>
                </div>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-space-md pt-space-lg bg-surface-container-low rounded-lg p-space-md">
                <div>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block">
                    Language
                  </span>
                  <span className="font-body-md text-body-md font-medium text-on-surface">
                    {BRIEF_BANNER.language}
                  </span>
                </div>
                <div>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block">
                    Primary Diagnosis
                  </span>
                  <span className="font-body-md text-body-md font-medium text-on-surface">
                    {BRIEF_BANNER.diagnosisLine1}
                    <br />
                    {BRIEF_BANNER.diagnosisLine2}
                  </span>
                </div>
                <div>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block">
                    Mobility Status
                  </span>
                  <span className="font-body-md text-body-md font-medium text-on-surface">
                    {BRIEF_BANNER.mobility}
                  </span>
                </div>
                <div>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block">
                    Acuity Band
                  </span>
                  <span className="font-body-md text-body-md font-medium text-on-surface">
                    {BRIEF_BANNER.acuity}
                  </span>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-space-xl">
              <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-md">
                <div className="flex items-center justify-between pb-space-sm mb-space-md">
                  <div className="flex flex-col">
                    <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                      Section 1
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Visit History &amp; Longitudinal Attendance
                    </h2>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-surface-container font-label-sm text-label-sm text-on-surface-variant font-medium">
                    Last 5 Recorded Encounters
                  </span>
                </div>
                {brief !== null && (
                  <div className="pb-space-sm">
                    <span className="font-body-sm text-body-sm text-on-surface-variant">
                      {lastVisitLine(brief.last_visit)}
                    </span>
                  </div>
                )}
                <div className="overflow-x-auto">
                  <table className="w-full text-left font-body-md">
                    <thead>
                      <tr className="bg-surface-container-low text-on-surface-variant font-label-sm text-label-sm uppercase tracking-wider">
                        <th className="py-space-md px-space-lg rounded-l">Date &amp; Time</th>
                        <th className="py-space-md px-space-lg">Type</th>
                        <th className="py-space-md px-space-lg">Status</th>
                        {/* FIX 1: Action column aligned left, not right */}
                        <th className="py-space-md px-space-lg rounded-r text-left">Action</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-outline-variant/30 tabular-nums">
                      {BRIEF_HISTORY.map((row) => (
                        <tr key={`${row.date}-${row.type}`} className="hover:bg-surface-container-low/40 transition-colors">
                          <td className="py-space-md px-space-lg">
                            <span className="font-semibold text-primary block">{row.date}</span>
                            <span className="font-label-sm text-label-sm text-on-surface-variant">
                              {row.time}
                            </span>
                          </td>
                          <td className="py-space-md px-space-lg">
                            <span className="font-body-md text-body-md text-on-surface">{row.type}</span>
                          </td>
                          <td className="py-space-md px-space-lg">
                            <span
                              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-label-sm font-semibold ${row.tone}`}
                            >
                              {row.status}
                            </span>
                          </td>
                          <td className="py-space-md px-space-lg text-left">
                            <button
                              className="min-h-[48px] px-space-lg inline-flex items-center justify-center rounded-lg border border-outline-variant/60 bg-surface-container-lowest hover:bg-surface-container hover:border-outline text-primary font-label-md text-label-md uppercase tracking-wider transition-colors"
                              type="button"
                            >
                              View Visit
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
              <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-md">
                <div className="flex items-center justify-between pb-space-sm mb-space-md">
                  <div className="flex flex-col">
                    <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                      Section 2
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Verified In-Person Vitals Trajectory
                    </h2>
                  </div>
                  <span className="font-label-sm text-label-sm text-secondary uppercase tracking-wider font-semibold">
                    EMR Longitudinal Store
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
                  {/* FIX 2: columns start at the top (justify-start) so the boxes
                      below the graphs align to their top border, not the bottom */}
                  <div className="flex flex-col justify-start p-space-lg bg-surface-container-low rounded-lg">
                    <div>
                      <div className="flex items-center justify-between pb-space-sm">
                        <div>
                          <span className="font-headline-sm text-headline-sm text-primary">
                            Blood Pressure
                          </span>
                        </div>
                        <div className="flex items-center gap-space-md text-label-sm font-label-sm">
                          <div className="flex items-center gap-1.5">
                            <span className="w-3 h-0.5 bg-[#282825] inline-block"></span>
                            <span className="text-on-surface">Systolic</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="w-3 border-t-2 border-dashed border-[#66625A] inline-block"></span>
                            <span className="text-on-surface-variant">Diastolic</span>
                          </div>
                        </div>
                      </div>
                      <div className="w-full bg-surface-container-lowest p-space-md rounded-lg mt-space-sm">
                        <svg
                          aria-label="Blood Pressure Line Chart"
                          className="w-full h-44 overflow-visible"
                          preserveAspectRatio="none"
                          viewBox="0 0 320 150"
                        >
                          <line stroke="#E5E2DD" strokeWidth="1" x1="30" x2="310" y1="20" y2="20"></line>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="10" textAnchor="end" x="25" y="23">160</text>
                          <line stroke="#E5E2DD" strokeWidth="1" x1="30" x2="310" y1="60" y2="60"></line>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="10" textAnchor="end" x="25" y="63">120</text>
                          <line stroke="#E5E2DD" strokeWidth="1" x1="30" x2="310" y1="100" y2="100"></line>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="10" textAnchor="end" x="25" y="103">80</text>
                          {/* Systolic Line (148 -> 144 -> 142 -> 136) */}
                          {/* x coordinates: 50, 130, 210, 290 */}
                          {/* y mapping: 160 -> 20, 120 -> 60. scale: 1 mmHg = 1px. y = 20 + (160 - val) */}
                          {/* 148 -> 32, 144 -> 36, 142 -> 38, 136 -> 44 */}
                          <polyline fill="none" points="50,32 130,36 210,38 290,44" stroke="#282825" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5"></polyline>
                          {/* Diastolic Line (92 -> 90 -> 88 -> 84) */}
                          {/* y mapping: 80 -> 100, 120 -> 60. scale: 1 mmHg = 1px. y = 100 - (val - 80) */}
                          {/* 92 -> 88, 90 -> 90, 88 -> 92, 84 -> 96 */}
                          <polyline fill="none" points="50,88 130,90 210,92 290,96" stroke="#665D4C" strokeDasharray="4,4" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></polyline>
                          <circle cx="50" cy="32" fill="#ffffff" r="3.5" stroke="#282825" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="10" fontWeight="600" textAnchor="middle" x="50" y="24">148</text>
                          <circle cx="130" cy="36" fill="#ffffff" r="3.5" stroke="#282825" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="10" fontWeight="600" textAnchor="middle" x="130" y="28">144</text>
                          <circle cx="210" cy="38" fill="#ffffff" r="3.5" stroke="#282825" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="10" fontWeight="600" textAnchor="middle" x="210" y="30">142</text>
                          <circle cx="290" cy="44" fill="#ffffff" r="3.5" stroke="#282825" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="10" fontWeight="600" textAnchor="middle" x="290" y="36">136</text>
                          <circle cx="50" cy="88" fill="#ffffff" r="3" stroke="#665D4C" strokeWidth="2"></circle>
                          <text fill="#665D4C" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="50" y="103">92</text>
                          <circle cx="130" cy="90" fill="#ffffff" r="3" stroke="#665D4C" strokeWidth="2"></circle>
                          <text fill="#665D4C" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="130" y="105">90</text>
                          <circle cx="210" cy="92" fill="#ffffff" r="3" stroke="#665D4C" strokeWidth="2"></circle>
                          <text fill="#665D4C" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="210" y="107">88</text>
                          <circle cx="290" cy="96" fill="#ffffff" r="3" stroke="#665D4C" strokeWidth="2"></circle>
                          <text fill="#665D4C" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="290" y="111">84</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="50" y="132">15 Oct</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="130" y="132">18 Jan</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="210" y="132">12 Apr</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="290" y="132">14 Jul</text>
                        </svg>
                      </div>
                    </div>
                    <div className="mt-space-md p-space-md bg-surface-container-lowest rounded-lg">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block font-semibold">
                        Goal of Care — Blood Pressure
                      </span>
                      <span className="font-data-metric text-data-metric text-primary block mt-0.5">
                        {BRIEF_GOAL_BP.value}
                      </span>
                      <p className="font-body-sm text-body-sm text-on-surface-variant mt-1.5 leading-snug">
                        {BRIEF_GOAL_BP.note}
                      </p>
                    </div>
                  </div>
                  <div className="flex flex-col justify-start p-space-lg bg-surface-container-low rounded-lg">
                    <div>
                      <div className="flex items-center justify-between pb-space-sm">
                        <div>
                          <span className="font-headline-sm text-headline-sm text-primary">
                            Glucose &amp; HbA1c
                          </span>
                        </div>
                        <div className="flex items-center gap-space-md text-label-sm font-label-sm">
                          <div className="flex items-center gap-1.5">
                            <span className="w-3 h-0.5 bg-[#131411] inline-block"></span>
                            <span className="text-on-surface">mg/dL</span>
                          </div>
                          <div className="flex items-center gap-1.5">
                            <span className="w-3 border-t-2 border-[#84231E] inline-block"></span>
                            <span className="text-[#84231E] font-medium">HbA1c %</span>
                          </div>
                        </div>
                      </div>
                      <div className="w-full bg-surface-container-lowest p-space-md rounded-lg mt-space-sm">
                        <svg
                          aria-label="Glucose and HbA1c Chart"
                          className="w-full h-44 overflow-visible"
                          preserveAspectRatio="none"
                          viewBox="0 0 320 150"
                        >
                          <line stroke="#E5E2DD" strokeWidth="1" x1="30" x2="285" y1="25" y2="25"></line>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="end" x="25" y="28">180</text>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9.5" textAnchor="start" x="290" y="28">9.0%</text>
                          <line stroke="#E5E2DD" strokeWidth="1" x1="30" x2="285" y1="65" y2="65"></line>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="end" x="25" y="68">150</text>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9.5" textAnchor="start" x="290" y="68">8.0%</text>
                          <line stroke="#E5E2DD" strokeWidth="1" x1="30" x2="285" y1="105" y2="105"></line>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="end" x="25" y="108">120</text>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9.5" textAnchor="start" x="290" y="108">7.0%</text>
                          {/* Blood Glucose Line (165 -> 152 -> 148 -> 140 mg/dL) */}
                          {/* x: 50, 120, 190, 260 */}
                          {/* y mapping for Glucose: 180 -> 25, 120 -> 105. 60 units = 80px => 1.33px per unit. y = 25 + (180 - val)*1.33 */}
                          {/* 165 -> 45, 152 -> 62, 148 -> 68, 140 -> 78 */}
                          <polyline fill="none" points="50,45 120,62 190,68 260,78" stroke="#131411" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2.5"></polyline>
                          {/* HbA1c Line (8.5% -> 8.2% -> 8.0% -> 7.8%) */}
                          {/* y mapping for HbA1c: 9.0% -> 25, 7.0% -> 105. 2.0% = 80px => 40px per 1%. y = 25 + (9.0 - val)*40 */}
                          {/* 8.5% -> 45, 8.2% -> 57, 8.0% -> 65, 7.8% -> 73 */}
                          <polyline fill="none" points="50,45 120,57 190,65 260,73" stroke="#84231E" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2"></polyline>
                          <circle cx="50" cy="45" fill="#ffffff" r="3.5" stroke="#131411" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="9.5" fontWeight="600" textAnchor="middle" x="50" y="37">165</text>
                          <circle cx="120" cy="62" fill="#ffffff" r="3.5" stroke="#131411" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="9.5" fontWeight="600" textAnchor="middle" x="120" y="54">152</text>
                          <circle cx="190" cy="68" fill="#ffffff" r="3.5" stroke="#131411" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="9.5" fontWeight="600" textAnchor="middle" x="190" y="60">148</text>
                          <circle cx="260" cy="78" fill="#ffffff" r="3.5" stroke="#131411" strokeWidth="2"></circle>
                          <text fill="#131411" fontFamily="DM Sans" fontSize="9.5" fontWeight="600" textAnchor="middle" x="260" y="70">140</text>
                          <circle cx="50" cy="45" fill="#84231E" r="2.5"></circle>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="50" y="58">8.5%</text>
                          <circle cx="120" cy="57" fill="#84231E" r="2.5"></circle>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="120" y="72">8.2%</text>
                          <circle cx="190" cy="65" fill="#84231E" r="2.5"></circle>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="190" y="80">8.0%</text>
                          <circle cx="260" cy="73" fill="#84231E" r="2.5"></circle>
                          <text fill="#84231E" fontFamily="DM Sans" fontSize="9" fontWeight="600" textAnchor="middle" x="260" y="88">7.8%</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="50" y="132">15 Oct</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="120" y="132">18 Jan</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="190" y="132">12 Apr</text>
                          <text fill="#777770" fontFamily="DM Sans" fontSize="9.5" textAnchor="middle" x="260" y="132">14 Jul</text>
                        </svg>
                      </div>
                    </div>
                    <div className="mt-space-md space-y-space-md">
                      <div className="p-space-md bg-surface-container-lowest rounded-lg">
                        <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block font-semibold">
                          Goal of Care — Glycaemic Target
                        </span>
                        <span className="font-data-metric text-data-metric text-primary block mt-0.5">
                          {BRIEF_GOAL_GLYCAEMIC.value}
                        </span>
                        <p className="font-body-sm text-body-sm text-on-surface-variant mt-1 leading-snug">
                          {BRIEF_GOAL_GLYCAEMIC.note}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="mt-space-lg p-space-md bg-surface-container-high rounded-lg flex items-baseline gap-space-sm">
                  <span className="w-2 h-2 rounded-full bg-secondary shrink-0 mt-1"></span>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    <strong className="font-medium text-on-surface">
                      Reconciliation Protocol §4.8:
                    </strong>{" "}
                    Home telemetry readings stored within patient glucose meter and portable cuff memory
                    are verified upon bedside entry. The continuous between-visit longitudinal curve will
                    synthesize automatically following optical/NFC device interrogation.
                  </p>
                </div>
              </div>
              <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-md">
                <div className="flex items-center justify-between pb-space-sm mb-space-md">
                  <div className="flex flex-col">
                    <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                      Section 3
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Surveillance &amp; Screening Due Cadence
                    </h2>
                  </div>
                  <span className="font-label-sm text-label-sm text-on-surface-variant">
                    Computed by Noor Engine
                  </span>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                  {(brief?.due ?? []).map((d) => {
                    const chip = dueChip(d.last_done);
                    return (
                      <div
                        key={d.item}
                        className="p-space-lg bg-surface-container-low rounded-lg flex flex-col justify-between"
                      >
                        <div className="flex items-start justify-between gap-space-sm">
                          <div>
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block">
                              Surveillance Parameter
                            </span>
                            <span className="font-headline-sm text-headline-sm text-primary">
                              {d.label}
                            </span>
                          </div>
                          <span
                            className={`px-2.5 py-1 font-label-sm text-label-sm uppercase tracking-wider rounded font-semibold whitespace-nowrap ${chip.tone}`}
                          >
                            {chip.text}
                          </span>
                        </div>
                        <div className="mt-space-md pt-space-sm bg-surface-container-lowest p-space-md rounded">
                          <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider block">
                            Historical Benchmark
                          </span>
                          <span className="font-body-md text-body-md text-on-surface">
                            {dueBenchmark(d.last_done)}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
              <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-md">
                <div className="flex items-center justify-between pb-space-sm mb-space-md">
                  <div className="flex flex-col">
                    <div className="flex items-center gap-space-sm">
                      <span className="w-2.5 h-2.5 rounded-sm bg-error"></span>
                      <span className="font-label-md text-label-md uppercase tracking-wider text-error font-semibold">
                        Section 4
                      </span>
                    </div>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Explicit Missing Data Declaration
                    </h2>
                  </div>
                  <span className="font-label-sm text-label-sm text-on-surface-variant">
                    EMR Analysis
                  </span>
                </div>
                <div className="p-space-lg bg-surface-container rounded-lg">
                  <div className="flex flex-col gap-space-sm">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Unresolved Clinical Variable
                    </span>
                    {(brief?.blind_spots ?? []).length === 0 && (
                      <p className="font-body-lg text-body-lg text-primary font-medium">
                        No blind spots — every read answered.
                      </p>
                    )}
                    {(brief?.blind_spots ?? []).map((spot) => (
                      <p key={spot} className="font-body-lg text-body-lg text-primary font-medium">
                        {spot}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>
            <div className="mt-space-xl pt-space-lg pb-space-lg flex flex-col gap-space-md">
              <div className="bg-surface-container-low p-space-lg rounded-xl flex flex-col sm:flex-row items-start sm:items-center justify-between gap-space-md">
                <div className="flex flex-col">
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                    State Confirmation Notice
                  </span>
                  <p className="font-body-sm text-body-sm text-on-surface-variant">
                    Starting freezes engine inputs, settles visit category to{" "}
                    <strong className="font-semibold text-primary">{planningWord}</strong>, and registers
                    formal MoH bedside ingress timestamp.
                  </p>
                </div>
                <div className="flex items-center gap-space-md w-full sm:w-auto shrink-0">
                  <a
                    className="min-h-[48px] px-space-xl flex-1 sm:flex-none flex items-center justify-center rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface bg-surface-container-high hover:bg-surface-container-highest transition-colors"
                    data-path="roster"
                    href="/initial"
                  >
                    Back to Roster
                  </a>
                  {/* The deliberate Start (§5.5): the backend settles the kind
                      from history and stamps the standing pair, then the
                      workspace opens on the In Progress Visit. */}
                  <button
                    className="min-h-[48px] px-space-xl flex-1 sm:flex-none flex items-center justify-center rounded-full font-label-md text-label-md uppercase tracking-wider bg-primary text-on-primary hover:bg-primary-container transition-all active:scale-[0.98] shadow-sm disabled:opacity-70"
                    id="start-visit-button"
                    type="button"
                    disabled={starting}
                    onClick={() => {
                      setStarting(true);
                      fetch(`/api/visits/${visitId}/start`, {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify({ at: new Date().toISOString() }),
                      })
                        .then((r) => {
                          if (!r.ok)
                            return r.json().then((b: { detail?: string }) => {
                              throw new Error(b.detail ?? "The Visit could not start.");
                            });
                          router.push(`/visit/${visitId}?day=${day}`);
                        })
                        .catch((e: Error) => {
                          setStarting(false);
                          setLoadError(e.message);
                        });
                    }}
                  >
                    {starting ? "INITIALIZING VISIT..." : "Start Visit"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </main>
        <footer className="w-full bg-surface-container-low px-margin py-space-lg shadow-[0_-1px_8px_rgba(0,0,0,0.02)]">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-space-sm font-label-sm text-label-sm text-on-surface-variant">
            <div className="uppercase tracking-wider">
              Project Noor · Kingdom of Saudi Arabia MoH Clinical Governance
            </div>
            <div className="font-mono">{STATION}</div>
          </div>
        </footer>
      </div>
    </div>
  );
}
