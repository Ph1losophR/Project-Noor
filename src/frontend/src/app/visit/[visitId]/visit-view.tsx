"use client";

// Clinical Encounter Workspace — initial throwaway (see initial/README.md).
// Same process as roster + brief: the pasted design verbatim, the fields the
// backend owns wired to the visit endpoints, demo content for the rest. The
// header chrome is identical to the previous two pages (ACTIVE VISIT active),
// and the working copy carries the alignment fixes (text left, not right).
import { Suspense, useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { TAILWIND_CONFIG } from "../../../../initial/tailwind-config";
import {
  CLUSTER,
  HEADER_DAY,
  HEADER_TEAM,
  NAV_COUNTS,
  STATION,
} from "../../../../initial/demo-text";

type Reason = { row_id: string; free_text: string | null };
type Resolution = { content: unknown; reason: Reason | null };
type VisitDetail = {
  visit_id: string;
  patient_id: string;
  patient_name: string;
  scheduled_for: string;
  scheduled_reason: string;
  state: string;
  kind: string | null;
  junior_physician: string | null;
  nurse: string | null;
  started_at: string | null;
  closed_at: string | null;
  closed_by: string | null;
  closing_reason: Reason | null;
  resolutions: Record<string, Resolution>;
  plan: unknown;
};

const STATE_WORD: Record<string, string> = {
  scheduled: "Scheduled",
  in_progress: "In Progress",
  emergency: "Emergency",
  completed: "Completed",
  cancelled: "Cancelled",
  ended_early: "Ended Early",
};

function nowIso(): string {
  return new Date().toISOString();
}

function reasonText(detail: VisitDetail | null): string {
  const content = detail?.resolutions?.VISIT_REASON?.content;
  if (
    typeof content === "object" &&
    content !== null &&
    typeof (content as Record<string, unknown>).reason === "string"
  )
    return (content as Record<string, string>).reason;
  return detail?.scheduled_reason ?? "";
}

export default function VisitView() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <VisitBody />
    </Suspense>
  );
}

function VisitBody() {
  const params = useParams<{ visitId: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const visitId = params.visitId;
  const day = search.get("day") ?? "2026-08-28";

  const [detail, setDetail] = useState<VisitDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionDone, setActionDone] = useState<string | null>(null);
  const [reason, setReason] = useState("");
  const [reasonDirty, setReasonDirty] = useState(false);
  const [saveNote, setSaveNote] = useState<string | null>(null);
  const [showEndEarly, setShowEndEarly] = useState(false);
  const [showEmergency, setShowEmergency] = useState(false);

  const refresh = useCallback(async () => {
    const r = await fetch(`/api/visits/${visitId}`);
    if (!r.ok) throw new Error(`visit HTTP ${r.status}`);
    const body = (await r.json()) as VisitDetail;
    setDetail(body);
    return body;
  }, [visitId]);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    refresh()
      .then((body) => {
        if (live) setReason(reasonText({ ...body, resolutions: body.resolutions }));
      })
      .catch(() => {
        if (live) {
          setDetail(null);
          setLoadError("The Visit could not be read.");
        }
      });
    return () => {
      live = false;
    };
  }, [refresh]);

  async function saveReason() {
    if (!reasonDirty) return;
    setReasonDirty(false);
    setSaveNote(null);
    const r = await fetch(`/api/visits/${visitId}/sections/visit_reason`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ content: { reason } }),
    });
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setSaveNote(body.detail ?? "The reason was refused.");
      return;
    }
    setSaveNote("Saved.");
    try {
      await refresh();
    } catch {
      setSaveNote("Saved, but the Visit could not be re-read.");
    }
  }

  async function enterEmergency() {
    setActionError(null);
    const r = await fetch(`/api/visits/${visitId}/emergency`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ at: nowIso() }),
    });
    setShowEmergency(false);
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The Emergency was refused.");
      return;
    }
    setActionDone("Emergency entered — the Visit Protocol is suspended.");
    router.push(`/visit/${visitId}/emergency?day=${day}`);
  }

  const stateWord = detail === null ? "…" : (STATE_WORD[detail.state] ?? detail.state);
  const kindWord =
    detail?.kind === null || detail?.kind === undefined
      ? "Unstarted"
      : detail.kind === "baseline"
        ? "Baseline Visit"
        : "Routine Visit";

  return (
    <div className="min-h-screen bg-surface flex flex-col items-center">
      <script src="https://cdn.tailwindcss.com" />
      <script id="tailwind-config" dangerouslySetInnerHTML={{ __html: TAILWIND_CONFIG }} />
      <link
        href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"
        rel="stylesheet"
      />
      <link
        href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@100..900&family=EB+Garamond:wght@100..900&display=swap"
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
            <div className="flex flex-col sm:flex-row sm:items-end justify-between pb-space-lg mb-space-lg gap-space-md">
              <div>
                <div className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                  Bedside Record §4.2–4.5 · {stateWord} · {kindWord}
                </div>
                <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight">
                  Clinical Encounter Workspace
                </h1>
                {detail !== null && (
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    {detail.patient_name} · {detail.scheduled_reason}
                  </span>
                )}
              </div>
              <div className="flex items-center gap-space-sm">
                <button
                  className="min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface bg-surface-container-highest hover:bg-surface-dim transition-colors"
                  onClick={() => setShowEndEarly(true)}
                  type="button"
                >
                  End Early
                </button>
                {detail?.state === "emergency" ? (
                  <a
                    className="min-h-[48px] px-space-lg rounded-lg font-label-md text-label-md uppercase tracking-wider text-on-error bg-error hover:bg-tertiary-container transition-colors shadow-sm flex items-center"
                    href={`/visit/${visitId}/emergency?day=${day}`}
                  >
                    Return to Emergency Protocol
                  </a>
                ) : (
                  <button
                    className="min-h-[48px] px-space-lg rounded-lg font-label-md text-label-md uppercase tracking-wider text-on-error bg-error hover:bg-tertiary-container transition-colors shadow-sm"
                    onClick={() => setShowEmergency(true)}
                    type="button"
                  >
                    Escalate
                  </button>
                )}
              </div>
            </div>
            {loadError !== null && (
              <div className="w-full bg-surface-container-low p-space-md rounded-lg mb-space-lg">
                <span className="font-body-md text-body-md text-on-surface">{loadError}</span>
              </div>
            )}
            {actionError !== null && (
              <div className="w-full bg-error-container p-space-md rounded-lg mb-space-lg">
                <span className="font-body-md text-body-md text-on-error-container">
                  {actionError}
                </span>
              </div>
            )}
            {actionDone !== null && (
              <div className="w-full bg-surface-container-low p-space-md rounded-lg mb-space-lg">
                <span className="font-body-md text-body-md text-on-surface">{actionDone}</span>
              </div>
            )}
            <div className="flex flex-col gap-space-xl">
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    01 · Clinical Indication
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Visit Reason
                </h2>
                <div className="bg-surface-container-low rounded-lg p-space-md">
                  <label
                    className="block font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant mb-space-xs font-semibold"
                    htmlFor="visit-reason-input"
                  >
                    Primary Focus (Editable Dispatch Directive)
                  </label>
                  <input
                    className="w-full bg-surface text-on-surface font-body-lg text-body-lg px-space-md py-3 rounded-lg border-0 focus:outline-none focus:bg-surface-bright shadow-inner"
                    id="visit-reason-input"
                    type="text"
                    value={reason}
                    onChange={(e) => {
                      setReason(e.target.value);
                      setReasonDirty(true);
                    }}
                    onBlur={() => void saveReason()}
                  />
                  {saveNote !== null && (
                    <span className="font-label-sm text-label-sm text-on-surface-variant block mt-space-xs">
                      {saveNote}
                    </span>
                  )}
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    02 · Interval Surveillance
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Concerns &amp; Interval Events
                </h2>
                <div className="space-y-space-md">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                    <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col justify-between min-h-[96px]">
                      <div className="flex items-start justify-between gap-space-sm">
                        <span className="font-label-md text-label-md uppercase tracking-wide text-primary font-semibold">
                          Hypoglycaemic Episode
                        </span>
                        <span className="font-label-sm text-label-sm uppercase px-2 py-0.5 rounded bg-tertiary-container text-on-tertiary font-semibold">
                          Reported
                        </span>
                      </div>
                      <div className="mt-space-sm bg-surface rounded p-space-sm text-on-surface font-body-sm text-body-sm">
                        “Mild symptomatic dip last Tuesday, resolved with dates.”
                      </div>
                    </div>
                    <div className="bg-surface-container-low rounded-lg p-space-md flex items-center justify-between min-h-[48px]">
                      <span className="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant font-semibold">
                        Fall Event
                      </span>
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                        None Observed
                      </span>
                    </div>
                    <div className="bg-surface-container-low rounded-lg p-space-md flex items-center justify-between min-h-[48px]">
                      <span className="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant font-semibold">
                        Hospital Admission
                      </span>
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                        None Reported
                      </span>
                    </div>
                    <div className="bg-surface-container-low rounded-lg p-space-md flex items-center justify-between min-h-[48px]">
                      <span className="font-label-md text-label-md uppercase tracking-wide text-on-surface-variant font-semibold">
                        Medication Changed Elsewhere
                      </span>
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                        Zero Discrepancy
                      </span>
                    </div>
                  </div>
                  <div className="bg-surface-container-high rounded-lg p-space-md mt-space-md">
                    <div className="flex items-baseline justify-between mb-space-xs">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold">
                        Attributed Bedside Concern
                      </span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant">
                        Attribution: Primary Household Caregiver
                      </span>
                    </div>
                    <div className="font-body-md text-body-md text-on-surface bg-surface-container-lowest p-space-md rounded-md">
                      <span className="font-semibold text-primary">Caregiver (daughter Reem):</span>{" "}
                      “Complains of burning sensation in soles of feet at night.”
                    </div>
                  </div>
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    03 · Pharmacotherapy Ledger
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Medication Reconciliation
                </h2>
                <div className="bg-surface-container-high rounded-lg p-space-lg mb-space-lg">
                  <div className="font-label-md text-label-md uppercase tracking-wider text-primary font-semibold mb-1">
                    State Paradigm: Unreachable Reference Node (§4.10)
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface">
                    The prescribed medication list could not be read from EMR (Unreachable).
                    Discrepancies against prescribed list are not shown. Recording physical items in
                    household below:
                  </p>
                </div>
                <div className="space-y-space-sm">
                  <div className="text-label-sm font-label-sm uppercase tracking-wider text-on-surface-variant px-space-sm pb-1 flex justify-between">
                    <span className="">Physical Household Items Identified</span>
                    <span className="">Verified Stock</span>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                    <div className="flex flex-col">
                      <span className="font-data-metric text-data-metric text-on-surface">
                        Metformin 1000mg
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Oral Tablet · Intact blister pack
                      </span>
                    </div>
                    <div className="flex items-center gap-space-lg">
                      <div className="text-left">
                        <span className="font-data-metric text-data-metric text-on-surface">48</span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant ml-1">
                          remaining
                        </span>
                      </div>
                      <span className="font-label-sm text-label-sm uppercase tracking-wide bg-surface-container-highest px-space-sm py-1 rounded text-on-surface font-semibold">
                        Exp: 11/2026
                      </span>
                    </div>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                    <div className="flex flex-col">
                      <span className="font-data-metric text-data-metric text-on-surface">
                        Amlodipine 5mg
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Oral Tablet · Original hospital carton
                      </span>
                    </div>
                    <div className="flex items-center gap-space-lg">
                      <div className="text-left">
                        <span className="font-data-metric text-data-metric text-on-surface">14</span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant ml-1">
                          remaining
                        </span>
                      </div>
                      <span className="font-label-sm text-label-sm uppercase tracking-wide bg-surface-container-highest px-space-sm py-1 rounded text-on-surface font-semibold">
                        Exp: 08/2026
                      </span>
                    </div>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                    <div className="flex flex-col">
                      <span className="font-data-metric text-data-metric text-on-surface">
                        Glimepiride 2mg
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Oral Tablet · Dispensed blister
                      </span>
                    </div>
                    <div className="flex items-center gap-space-lg">
                      <div className="text-left">
                        <span className="font-data-metric text-data-metric text-on-surface">28</span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant ml-1">
                          remaining
                        </span>
                      </div>
                      <span className="font-label-sm text-label-sm uppercase tracking-wide bg-surface-container-highest px-space-sm py-1 rounded text-on-surface font-semibold">
                        Exp: 03/2027
                      </span>
                    </div>
                  </div>
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    04 · Physiological Telemetry
                  </span>
                  <span className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                    Bedside Measurement
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Physiological Parameters
                </h2>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-space-md mb-space-lg">
                  <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col justify-between min-h-[96px]">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Blood Pressure
                    </span>
                    <div>
                      <span className="font-data-display text-data-display text-primary">136/84</span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant ml-1 font-semibold">
                        mmHg
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm text-secondary">
                      Manual Sphygmomanometer
                    </span>
                  </div>
                  <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col justify-between min-h-[96px]">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Heart Rate
                    </span>
                    <div>
                      <span className="font-data-display text-data-display text-primary">72</span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant ml-1 font-semibold">
                        bpm
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm text-secondary">Regular Rhythm</span>
                  </div>
                  <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col justify-between min-h-[96px]">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Oxygen Saturation
                    </span>
                    <div>
                      <span className="font-data-display text-data-display text-primary">98</span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant ml-1 font-semibold">
                        %
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm text-secondary">
                      Ambient Room Air
                    </span>
                  </div>
                  <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col justify-between min-h-[96px]">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Random Glucose
                    </span>
                    <div>
                      <span className="font-data-display text-data-display text-primary">148</span>
                      <span className="font-label-sm text-label-sm text-on-surface-variant ml-1 font-semibold">
                        mg/dL
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm text-secondary">
                      Capillary Bedside Draw
                    </span>
                  </div>
                </div>
                <div className="bg-surface-container-high rounded-lg p-space-md flex flex-col sm:flex-row items-start sm:items-center justify-between gap-space-md">
                  <div className="flex flex-col">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold">
                      Household Meter Memory Readout (§4.8)
                    </span>
                    <span className="font-body-sm text-body-sm text-on-surface-variant">
                      Accu-Chek Guide · Serial SN-883109 · Verified device memory extraction
                    </span>
                  </div>
                  <div className="flex items-baseline gap-space-md self-start sm:self-auto">
                    <div className="text-left">
                      <span className="font-data-metric text-data-metric text-primary">
                        138 mg/dL
                      </span>
                      <span className="block font-label-sm text-label-sm text-secondary font-semibold">
                        7-Day Fasting Mean
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm bg-surface-container-lowest text-on-surface px-space-sm py-1 rounded font-mono">
                      14:15 AST
                    </span>
                  </div>
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    05 · Objective Exam
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Physical Examination Findings
                </h2>
                <div className="space-y-space-md">
                  <div className="bg-surface-container-low rounded-lg p-space-md">
                    <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold mb-1">
                      Lower Extremity &amp; Neurological Assessment
                    </div>
                    <div className="font-body-md text-body-md text-on-surface">
                      Bilateral monofilament 10g Semmes-Weinstein foot sensation diminished over 1st
                      and 5th metatarsal heads bilaterally. Plantar skin dry without calluses or
                      ulcerations.
                    </div>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-space-md flex items-center justify-between">
                    <div>
                      <div className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                        Vascular Status
                      </div>
                      <div className="font-body-md text-body-md text-on-surface">
                        Pedal pulses present and symmetrical bilaterally (Dorsalis Pedis 2+, Posterior
                        Tibial 2+).
                      </div>
                    </div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-primary px-space-sm py-1 rounded bg-surface-container-highest font-semibold shrink-0">
                      Intact
                    </span>
                  </div>
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    06 · Environmental &amp; Regimen Audit
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Self-Care Verification (§4.5)
                </h2>
                <div className="space-y-space-md">
                  <div className="bg-surface-container-low rounded-lg p-space-md flex items-center justify-between">
                    <div className="flex flex-col">
                      <span className="font-label-md text-label-md uppercase tracking-wide text-on-surface font-semibold">
                        Insulin Cold-Chain &amp; Storage
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Patient prescribed oral hypoglycaemics exclusively. No injectable peptides
                        present in household.
                      </span>
                    </div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest bg-surface-container-highest text-on-surface-variant px-space-sm py-1 rounded font-semibold shrink-0">
                      Not Applicable
                    </span>
                  </div>
                  <div className="bg-surface-container-high rounded-lg p-space-md">
                    <div className="flex items-baseline justify-between mb-space-xs">
                      <span className="font-label-md text-label-md uppercase tracking-wide text-primary font-semibold">
                        Medication Administration Observation
                      </span>
                      <span className="font-label-sm text-label-sm text-secondary font-semibold">
                        Performer: Caregiver (Reem)
                      </span>
                    </div>
                    <div className="font-body-md text-body-md text-on-surface bg-surface-container-lowest p-space-md rounded-md">
                      “Pill organizer loaded weekly; morning dose taken with water; no skipped doses
                      observed during inspection.”
                    </div>
                  </div>
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    07 · Provider Assessment Notes
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Attending Clinical Evaluation
                </h2>
                <div className="bg-surface-container-low rounded-lg p-space-md">
                  <div className="flex items-center justify-between mb-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Clinical Synthesis · Dr. Sara Al-Husseini
                    </span>
                    <span className="font-label-sm text-label-sm text-secondary font-mono">
                      14:40 AST
                    </span>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface leading-relaxed">
                    Glycaemic control remains within acceptable bounds with mild peripheral neuropathy
                    emerging (burning feet in evening + distal sensory blunting). No active trophic
                    foot lesions or cellulitis. Amlodipine regimen successfully maintaining target MAP
                    below 100. Household safety audit satisfactory; daughter Reem shows disciplined
                    oversight of oral medications.
                  </p>
                </div>
              </section>
              <section className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm">
                <div className="flex items-baseline justify-between mb-space-sm">
                  <span className="font-label-md text-label-md uppercase tracking-wider text-on-surface-variant font-semibold">
                    08 · Inter-Visit Directive
                  </span>
                </div>
                <h2 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                  Care Plan &amp; Between-Visit Mandate
                </h2>
                <div className="space-y-space-md">
                  <div className="bg-surface-container-low rounded-lg p-space-md">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold block mb-space-xs">
                      Pharmacotherapy Continuations
                    </span>
                    <ul className="space-y-space-xs font-body-md text-body-md text-on-surface">
                      <li className="flex items-center justify-between py-1">
                        <span className="">Metformin Hydrochloride 1000mg</span>
                        <span className="font-semibold text-primary">
                          Continue BD (Twice Daily) with meals
                        </span>
                      </li>
                      <li className="flex items-center justify-between py-1">
                        <span className="">Amlodipine Besylate 5mg</span>
                        <span className="font-semibold text-primary">
                          Continue OD (Once Daily) in morning
                        </span>
                      </li>
                    </ul>
                  </div>
                  <div className="bg-surface-container-high rounded-lg p-space-md">
                    <div className="flex items-baseline justify-between mb-space-xs">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-primary font-semibold">
                        Home Surveillance &amp; Stop Rule Thresholds
                      </span>
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-tertiary-container font-semibold">
                        Enforced Rule
                      </span>
                    </div>
                    <div className="font-body-md text-body-md text-on-surface bg-surface-container-lowest p-space-md rounded-md">
                      Execute blood pressure check twice weekly.{" "}
                      <span className="font-semibold text-primary">Stop rule:</span> If Systolic BP
                      &gt; 180 mmHg or &lt; 100 mmHg, immediately halt autonomous adjustments and
                      notify clinical response dispatch.
                    </div>
                  </div>
                </div>
              </section>
            </div>
            <div className="sticky bottom-0 z-40 bg-surface/95 pt-space-md pb-space-lg mt-space-xl shadow-[0_-4px_20px_rgba(40,35,28,0.06)]">
              <div className="flex flex-col sm:flex-row items-center justify-between gap-space-md">
                <div className="flex items-center gap-space-md">
                  <div className="w-3 h-3 rounded-full bg-primary shrink-0"></div>
                  <div className="flex flex-col">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold">
                      All 8 Sections Synchronized
                    </span>
                    <span className="font-body-sm text-body-sm text-on-surface-variant">
                      Validated by Attending Pair · Offline Ledger Sealed
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-space-sm w-full sm:w-auto">
                  <a
                    className="min-h-[48px] px-space-lg flex items-center justify-center rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface-variant hover:text-on-surface transition-colors"
                    href={`/initial`}
                  >
                    Back to Roster
                  </a>
                  <a
                    className="min-h-[48px] px-8 flex items-center justify-center rounded-full font-label-md text-label-md uppercase tracking-wider text-on-primary bg-primary hover:bg-primary-container transition-colors text-center font-semibold"
                    data-path="review-complete"
                    href={`/visit/${visitId}/review?day=${day}`}
                  >
                    Review &amp; Complete Visit
                  </a>
                  {(detail?.state === "completed" ||
                    detail?.state === "cancelled" ||
                    detail?.state === "ended_early") && (
                    <a
                      className="min-h-[48px] px-8 flex items-center justify-center rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface bg-surface-container-high hover:bg-surface-container-highest transition-colors text-center font-semibold"
                      data-path="write-addendum"
                      href={`/visit/${visitId}/addendum?day=${day}`}
                    >
                      Write Addendum
                    </a>
                  )}
                </div>
              </div>
            </div>
            {showEndEarly && (
              <div className="fixed inset-0 z-50 bg-primary/40 flex items-center justify-center p-margin">
                <div className="bg-surface-container-lowest w-full max-w-[520px] rounded-xl p-space-xl shadow-2xl">
                  <div className="flex items-baseline justify-between mb-space-sm">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                      Protocol Exception §5.10
                    </span>
                    <button
                      className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant hover:text-primary"
                      onClick={() => setShowEndEarly(false)}
                      type="button"
                    >
                      Close
                    </button>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-primary mb-space-md">
                    Terminate Bedside Encounter Early
                  </h3>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mb-space-md">
                    Select the governing rationale for premature discharge. This disposition will log
                    into the regional clinical write-back ledger.
                  </p>
                  {/* THROWAWAY: front-end only, like the roster Cancel popover. The
                      four demo rows are not the eight real `ended_early` rows in
                      docs/clinical-content/reason-lists.md, which POST
                      /api/visits/{id}/end-early validates against. */}
                  <div className="space-y-space-sm mb-space-lg">
                    {[
                      "Patient or Household Declined Continuation",
                      "Patient Absent from Residence at Arrival",
                      "Environmental / Practitioner Safety Risk Identified",
                      "Re-routed to Secondary Immediate Emergency",
                    ].map((label) => (
                      <button
                        key={label}
                        className="w-full min-h-[48px] p-space-md rounded-lg text-left bg-surface-container-low hover:bg-surface-container-high transition-colors font-body-md text-body-md text-on-surface flex justify-between items-center"
                        onClick={() => setShowEndEarly(false)}
                        type="button"
                      >
                        <span className="">{label}</span>
                        <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary">
                          Select
                        </span>
                      </button>
                    ))}
                  </div>
                  <div className="flex justify-end">
                    <button
                      className="min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider bg-surface-container text-on-surface"
                      onClick={() => setShowEndEarly(false)}
                      type="button"
                    >
                      Cancel &amp; Retain Workspace
                    </button>
                  </div>
                </div>
              </div>
            )}
            {showEmergency && (
              <div className="fixed inset-0 z-50 bg-tertiary/60 flex items-center justify-center p-margin">
                <div className="bg-surface-container-lowest w-full max-w-[520px] rounded-xl p-space-xl shadow-2xl">
                  <div className="flex items-baseline justify-between mb-space-sm">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-error font-semibold">
                      triggering emergency protocol
                    </span>
                    <button
                      className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant hover:text-primary"
                      onClick={() => setShowEmergency(false)}
                      type="button"
                    >
                      Dismiss
                    </button>
                  </div>
                  <h3 className="font-headline-sm text-headline-sm text-error mb-space-md">
                    Initiate 997 Emergency Dispatch
                  </h3>
                  <p className="font-body-md text-body-md text-on-surface mb-space-lg">
                    This bedside encounter will transition immediately to{" "}
                    <strong className="text-error">Critical Transfer Mode</strong>. Saudi Red
                    Crescent (997) telemetry and Central Regional Supervisor channels will be opened
                    automatically.
                  </p>
                  <div className="space-y-space-sm mb-space-xl">
                    <div className="p-space-md rounded-lg bg-error-container text-on-error-container font-body-sm text-body-sm">
                      Patient coordinates (Riyadh, Al-Malqa District) and latest physiological
                      telemetry (BP 136/84, HR 72, SPO2 98%) are ready for one-tap dispatch payload.
                    </div>
                  </div>
                  <div className="flex flex-col sm:flex-row items-center justify-end gap-space-sm">
                    <button
                      className="w-full sm:w-auto min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider bg-surface-container text-on-surface"
                      onClick={() => setShowEmergency(false)}
                      type="button"
                    >
                      Cancel &amp; Return
                    </button>
                    <button
                      className="w-full sm:w-auto min-h-[48px] px-space-xl rounded-lg font-label-md text-label-md uppercase tracking-wider bg-error text-on-error font-semibold shadow-md"
                      onClick={() => void enterEmergency()}
                      type="button"
                    >
                      Confirm 997 Callout
                    </button>
                  </div>
                </div>
              </div>
            )}
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
