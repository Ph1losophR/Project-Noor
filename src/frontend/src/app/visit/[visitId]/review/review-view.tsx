"use client";

// Clinical Verification — initial throwaway (see initial/README.md). The Field
// Team reviews what was registered before closing: section statuses, the
// emergency record, the emitted plan, and the recommendation dispositions.
// Wired where the backend owns it (detail + complete endpoints); demo where
// Phase 1 has no source — most visibly the recommendation cards, since Phase 1
// has no producer. Taste pass vs the paste is logged in the README.
import { Suspense, useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { TAILWIND_CONFIG } from "../../../../../initial/tailwind-config";
import {
  BRIEF_BANNER,
  VERIFY_ATTEST,
  VERIFY_RECS,
  VERIFY_SECTIONS,
  VERIFY_SELF_CARE_COPY,
  VERIFY_TRANSMISSION,
  VERIFY_VITALS,
} from "../../../../../initial/demo-text";
import {
  CLUSTER,
  HEADER_DAY,
  HEADER_TEAM,
  NAV_COUNTS,
  STATION,
} from "../../../../../initial/demo-text";

type Reason = { row_id: string; free_text: string | null };
type Resolution = { content: unknown; reason: Reason | null };
type TimelineEntry = { kind: string; text: string; at: string };
type Emergency = { started_at: string; ended_at: string | null; entries: TimelineEntry[] };
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
  emergencies: Emergency[];
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

const SECTION_LABEL: Record<string, string> = {
  VISIT_REASON: "Visit Reason",
  CONCERNS_AND_INTERVAL_HISTORY: "Concerns & Interval History",
  MEDICATION_RECONCILIATION: "Medication Reconciliation",
  VITALS: "Vitals",
  PHYSICAL_EXAMINATION: "Physical Examination",
  SELF_CARE_CHECK: "Self-Care Check",
  CARE_PLAN: "Care Plan",
  NOTES: "Notes",
};

function planLineCount(plan: unknown): number | null {
  if (typeof plan !== "object" || plan === null) return null;
  const p = plan as { titration?: unknown; schedule?: unknown; stop_rules?: unknown };
  if (!Array.isArray(p.titration) || !Array.isArray(p.schedule) || !Array.isArray(p.stop_rules))
    return null;
  return p.titration.length + p.schedule.length + p.stop_rules.length;
}

export default function ReviewView() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <ReviewBody />
    </Suspense>
  );
}

function ReviewBody() {
  const params = useParams<{ visitId: string }>();
  const search = useSearchParams();
  const visitId = params.visitId;
  const day = search.get("day") ?? "2026-08-28";

  const [detail, setDetail] = useState<VisitDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionDone, setActionDone] = useState<string | null>(null);
  const [openRec, setOpenRec] = useState<number | null>(null);

  const refresh = useCallback(async () => {
    const r = await fetch(`/api/visits/${visitId}`);
    if (!r.ok) throw new Error(`visit HTTP ${r.status}`);
    setDetail((await r.json()) as VisitDetail);
  }, [visitId]);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    refresh().catch(() => {
      if (live) {
        setDetail(null);
        setLoadError("The Visit could not be read.");
      }
    });
    return () => {
      live = false;
    };
  }, [refresh]);

  useEffect(() => {
    if (openRec === null) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpenRec(null);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [openRec ]);

  async function completeVisit() {
    setActionError(null);
    setActionDone(null);
    const r = await fetch(`/api/visits/${visitId}/complete`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ by: detail?.junior_physician ?? "Field Team", at: new Date().toISOString() }),
    });
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The Visit was refused.");
      return;
    }
    setActionDone("Visit Completed — the Write-Back is queued.");
    await refresh().catch(() => setLoadError("The Visit could not be re-read."));
  }

  const resolutions = detail?.resolutions ?? {};
  const missing = VERIFY_SECTIONS.filter((s) => !(s.key in resolutions)).map((s) => s.key);
  const openEmergencies = (detail?.emergencies ?? []).filter(
    (e) => e.ended_at === null || e.entries.length === 0,
  );
  const lines = detail === null || detail === undefined ? null : planLineCount(detail.plan);
  const blockers = [
    ...missing.map((m) => `${SECTION_LABEL[m] ?? m} unresolved`),
    ...(openEmergencies.length > 0
      ? [`${openEmergencies.length} Emergency record(s) open`]
      : []),
    ...(lines === null ? ["No Between-Visit Plan emitted"] : []),
  ];
  const ready = detail !== null && blockers.length === 0;
  const stateWord = detail === null ? "…" : (STATE_WORD[detail.state] ?? detail.state);
  const emergencies = detail?.emergencies ?? [];
  const closer = detail?.junior_physician ?? "—";

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
      <style>{`@layer base { html, body { margin: 0; padding: 0; } body { overscroll-behavior: none; } main > :first-child { margin-top: 0 !important; } main > :last-child { margin-bottom: 0 !important; } } ::-webkit-scrollbar { display: none; } .tabular-nums { font-variant-numeric: tabular-nums; }`}</style>
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
            <div className="w-full space-y-space-xl pb-28">
              <section className="flex flex-col gap-space-md">
                <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight">
                  Clinical Verification
                </h1>
                <div className="grid grid-cols-1 md:grid-cols-12 gap-space-md items-stretch">
                  <div className="md:col-span-7 p-space-lg rounded-xl bg-surface-container-lowest shadow-sm flex flex-col justify-between border border-outline-variant/40">
                    <div>
                      <div className="flex items-baseline justify-between gap-space-sm">
                        <span className="font-headline-md text-headline-md font-bold text-primary">
                          {detail?.patient_name ?? "…"}
                          {BRIEF_BANNER.suffix}
                        </span>
                        <span className="px-2.5 py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider bg-surface-container-high text-on-surface font-semibold shrink-0">
                          {stateWord}
                        </span>
                      </div>
                      <div className="mt-1 font-body-sm text-body-sm text-on-surface-variant">
                        <span className="font-semibold text-primary">{BRIEF_BANNER.mrn}</span>
                        <div>
                          <b>Citizen ID:</b> <span className="tabular-nums">1048829103</span>&nbsp;
                          <div className="">National Unified Medical Record Linked</div>
                        </div>
                      </div>
                    </div>
                    <div className="mt-space-md pt-space-sm border-t border-outline-variant/30 grid grid-cols-2 gap-x-space-md gap-y-space-xs text-body-sm text-on-surface-variant">
                      <div className="">
                        <span className="font-label-sm uppercase tracking-wider text-on-surface block text-[10px]">
                          Language
                        </span>
                        {BRIEF_BANNER.language}
                      </div>
                      <div className="">
                        <span className="font-label-sm uppercase tracking-wider text-on-surface block text-[10px]">
                          Mobility
                        </span>
                        {BRIEF_BANNER.mobility}
                      </div>
                      <div className="">
                        <span className="font-label-sm uppercase tracking-wider text-on-surface block text-[10px]">
                          Primary Diagnosis
                        </span>
                        Type 2 DM &amp; Essential HTN
                      </div>
                      <div className="">
                        <span className="font-label-sm uppercase tracking-wider text-on-surface block text-[10px]">
                          Clinical Acuity
                        </span>
                        {BRIEF_BANNER.acuity}
                      </div>
                    </div>
                  </div>
                  <div className="md:col-span-5 flex flex-col gap-space-md justify-between">
                    <div
                      className={`p-space-lg rounded-xl shadow-sm flex flex-col justify-between flex-1 border ${
                        ready
                          ? "bg-surface-container-lowest border-outline-variant/40"
                          : "bg-[#FDF2F1] border-status-now/40"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <span
                          className={`font-label-sm text-label-sm uppercase tracking-widest font-bold ${
                            ready ? "text-status-clear" : "text-status-now"
                          }`}
                        >
                          Gate Status
                        </span>
                        <span
                          className={`px-2 py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider font-bold ${
                            ready ? "bg-status-clear text-on-primary" : "bg-status-now text-on-primary"
                          }`}
                        >
                          {ready
                            ? "Ready"
                            : `${blockers.length} Missing Required Field${blockers.length === 1 ? "" : "s"}`}
                        </span>
                      </div>
                      <div className="mt-space-sm">
                        <span
                          className={`font-data-display text-data-display font-bold ${
                            ready ? "text-status-clear" : "text-status-now"
                          }`}
                        >
                          {ready ? "Ready" : "Not Ready"}
                        </span>
                        <span className="block font-body-sm text-body-sm text-on-surface-variant mt-0.5 tabular-nums">
                          {ready
                            ? "Every verification gate satisfied — the Visit may close."
                            : `${8 - missing.length} of 8 sections resolved${
                                blockers.length > 0 ? ` (${blockers[0]})` : ""
                              }`}
                        </span>
                      </div>
                    </div>
                    <div className="p-space-lg rounded-xl bg-surface-container-lowest shadow-sm flex flex-col justify-between border border-outline-variant/40 flex-1">
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                        Transmission Target
                      </span>
                      <div className="mt-space-sm">
                        <span className="font-data-metric text-data-metric text-primary font-semibold">
                          {VERIFY_TRANSMISSION.target}
                        </span>
                        <span className="block font-body-sm text-body-sm text-on-surface-variant mt-0.5 tabular-nums">
                          {VERIFY_TRANSMISSION.sub}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
              {loadError !== null && (
                <div className="w-full bg-surface-container-low p-space-md rounded-lg">
                  <span className="font-body-md text-body-md text-on-surface">{loadError}</span>
                </div>
              )}
              {actionError !== null && (
                <div className="w-full bg-error-container p-space-md rounded-lg">
                  <span className="font-body-md text-body-md text-on-error-container">
                    {actionError}
                  </span>
                </div>
              )}
              {actionDone !== null && (
                <div className="w-full bg-surface-container-low p-space-md rounded-lg">
                  <span className="font-body-md text-body-md text-on-surface">{actionDone}</span>
                </div>
              )}
              <section className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm space-y-space-lg border border-outline-variant/30">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pb-space-sm border-b border-outline-variant/30">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant block">
                      Requirement 1
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Recorded Visit Info
                    </h2>
                  </div>
                  <a
                    className="min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider text-on-primary bg-primary hover:bg-primary-container transition-colors inline-flex items-center justify-center font-semibold shadow-sm self-start sm:self-auto"
                    href={`/visit/${visitId}?day=${day}`}
                  >
                    Edit Visit
                  </a>
                </div>
                <div className="space-y-space-sm">
                  {VERIFY_SECTIONS.map((s) => {
                    const resolution = resolutions[s.key];
                    if (resolution === undefined) {
                      const specific = s.key === "SELF_CARE_CHECK";
                      return (
                        <div
                          key={s.key}
                          className="p-space-lg rounded-xl bg-[#FDF2F1] border-2 border-status-now space-y-space-sm"
                        >
                          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                            <div className="flex items-center gap-space-md">
                              <span className="font-label-md text-label-md text-status-now font-bold w-5 tabular-nums">
                                {s.num}
                              </span>
                              <span className="font-body-md text-body-md font-bold text-status-now">
                                {s.title}
                              </span>
                            </div>
                            <span className="px-3 py-1 rounded-full font-label-sm text-label-sm uppercase tracking-wider bg-status-now text-on-primary font-bold shrink-0 self-start sm:self-auto">
                              Missing Required Field
                            </span>
                          </div>
                          <p className="font-body-sm text-body-sm text-[#1B1C1A] pl-0 sm:pl-9 leading-relaxed">
                            {specific
                              ? VERIFY_SELF_CARE_COPY
                              : "Not yet resolved — record content or a structured reason for having none before visit completion (§5.8)."}
                          </p>
                          <div className="pt-space-xs pl-0 sm:pl-9 flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                            <a
                              className="inline-flex items-center font-label-md text-label-md font-bold text-status-now hover:underline underline-offset-4"
                              href={`/visit/${visitId}?day=${day}`}
                            >
                              Resolve {s.title} Now →
                            </a>
                          </div>
                        </div>
                      );
                    }
                    const byReason = resolution.reason !== null;
                    return (
                      <div
                        key={s.key}
                        className={`p-space-md rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-space-md ${
                          s.key === "MEDICATION_RECONCILIATION"
                            ? "bg-surface-container-high"
                            : "bg-surface-container-low"
                        }`}
                      >
                        <div className="flex items-start gap-space-md">
                          <span className="font-label-md text-label-md text-on-surface-variant w-5 pt-0.5 tabular-nums">
                            {s.num}
                          </span>
                          <div>
                            <div className="flex items-center gap-space-sm flex-wrap">
                              <span className="font-body-md text-body-md font-semibold text-primary">
                                {s.title}
                              </span>
                              {s.key === "MEDICATION_RECONCILIATION" && (
                                <span className="font-label-sm text-label-sm px-2 py-0.5 rounded bg-surface-container-highest text-on-surface-variant font-semibold">
                                  Degraded Mode
                                </span>
                              )}
                            </div>
                            <span className="font-body-sm text-body-sm text-on-surface-variant">
                              {s.summary}
                            </span>
                          </div>
                        </div>
                        <span
                          className={`px-3 py-1 rounded-full font-label-sm text-label-sm uppercase tracking-wider font-semibold shrink-0 self-start sm:self-auto ${
                            byReason
                              ? "bg-surface-container-highest text-on-surface-variant"
                              : s.key === "MEDICATION_RECONCILIATION"
                                ? "bg-secondary-container text-on-secondary-container"
                                : "bg-surface-container-highest text-primary"
                          }`}
                        >
                          {byReason ? "Resolved with reason" : "Examined · Complete"}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </section>
              <section className="space-y-space-sm pt-space-xs">
                <div className="pb-1 flex items-baseline justify-between">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold block">
                      CLINICAL SNAPSHOT
                    </span>
                    <h2 className="font-headline-md text-headline-md text-primary font-medium">
                      Vitals at a glance
                    </h2>
                  </div>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                    SYNCHRONIZED AT 14:32
                  </span>
                </div>
                <div className="grid grid-cols-2 md:grid-cols-4 rounded-2xl bg-surface-container-lowest border border-outline-variant/40 divide-y md:divide-y-0 md:divide-x divide-outline-variant/30 shadow-sm overflow-hidden">
                  {VERIFY_VITALS.map((v) => (
                    <div key={v.label} className="p-space-lg flex flex-col justify-between min-h-[120px]">
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                        {v.label}
                      </span>
                      <div className="mt-space-sm">
                        <div className="font-data-display text-[32px] leading-none font-bold text-primary tabular-nums tracking-tight">
                          {v.value}
                        </div>
                        <span className="font-label-sm text-[12px] uppercase font-semibold text-on-surface-variant mt-1.5 block tracking-wider">
                          {v.unit}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </section>
              <section className="grid grid-cols-1 md:grid-cols-2 gap-space-lg">
                <div className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm space-y-space-md flex flex-col justify-between border border-outline-variant/30">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant block">
                      Requirement 2
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary mt-1">
                      Emergency Record Check
                    </h2>
                    <p className="font-body-md text-body-md text-on-surface-variant mt-space-sm">
                      {emergencies.length === 0
                        ? "No Emergency entered during this visit. (Condition satisfied)"
                        : `${emergencies.length} Emergency record(s) — ${
                            openEmergencies.length > 0
                              ? `${openEmergencies.length} still open`
                              : "all documented"
                          }.`}
                    </p>
                  </div>
                  <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between">
                    <span className="font-label-md text-label-md text-on-surface font-semibold">
                      Tier 3 Red Escalation
                    </span>
                    <span
                      className={`font-label-sm text-label-sm uppercase tracking-wider font-semibold ${
                        openEmergencies.length > 0 ? "text-status-now" : "text-status-clear"
                      }`}
                    >
                      {openEmergencies.length > 0 ? "Open Record" : "Zero Occurrences"}
                    </span>
                  </div>
                </div>
                <div className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm space-y-space-md flex flex-col justify-between border border-outline-variant/30">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant block">
                      Requirement 3
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary mt-1">
                      Final Section Verification
                    </h2>
                    <p className="font-body-md text-body-md text-on-surface-variant mt-space-sm">
                      {lines === null
                        ? "No Between-Visit Plan emitted yet."
                        : `Care Plan assembled; Between-Visit Plan emitted with ${lines} machine-testable line${lines === 1 ? "" : "s"}.`}
                    </p>
                  </div>
                  <div className="p-space-md rounded-lg bg-surface-container-low flex items-center justify-between">
                    <span className="font-label-md text-label-md text-on-surface font-semibold">
                      Parser Verification
                    </span>
                    <span
                      className={`font-label-sm text-label-sm uppercase tracking-wider font-semibold tabular-nums ${
                        lines === null ? "text-status-now" : "text-status-clear"
                      }`}
                    >
                      {lines === null ? "Nothing Compiled" : `${lines} Rules Compiled`}
                    </span>
                  </div>
                </div>
              </section>
              <section className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm space-y-space-lg border border-outline-variant/30">
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-xs pb-space-sm border-b border-outline-variant/30">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant block font-semibold">
                      Requirement 4
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Recommendation Disposition (§5.8 &amp; §4.7)
                    </h2>
                  </div>
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                    3 Active Records
                  </span>
                </div>
                {/* Demo: Phase 1 has no producer, so no Recommendation exists to
                    disposition. These three cards hold the layout until Phase 1.5. */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md items-stretch">
                  {VERIFY_RECS.map((rec, i) => (
                    <button
                      key={rec.title}
                      className="w-full text-left p-space-xl rounded-xl bg-surface-container-low hover:bg-surface-container transition-all flex flex-col justify-between border border-outline-variant/40 min-h-[170px] focus:outline-none focus:ring-2 focus:ring-primary group"
                      onClick={() => setOpenRec(i)}
                      type="button"
                    >
                      <div className="space-y-space-sm">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                            {rec.tag}
                          </span>
                          <span
                            className={`px-2.5 py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider font-bold ${
                              rec.badge === "Accepted"
                                ? "bg-primary text-on-primary"
                                : rec.badge === "Overridden"
                                  ? "bg-secondary-container text-on-secondary-container"
                                  : "bg-surface-container-highest text-on-surface-variant"
                            }`}
                          >
                            {rec.badge}
                          </span>
                        </div>
                        <h3 className="font-headline-md text-[22px] leading-snug text-primary transition-colors font-medium">
                          {rec.title}
                        </h3>
                      </div>
                      <div className="pt-space-md flex items-center justify-between text-on-surface-variant font-label-sm text-[11px] uppercase tracking-wider border-t border-outline-variant/20 mt-space-md">
                        <span className="underline underline-offset-4 group-hover:text-primary font-semibold">
                          View Details →
                        </span>
                      </div>
                    </button>
                  ))}
                </div>
              </section>
              <section className="p-space-xl rounded-xl bg-surface-container-high space-y-space-md border border-outline-variant/40">
                <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold block">
                  Clinician Attestation
                </span>
                <p className="font-headline-sm text-headline-sm text-primary italic">
                  {VERIFY_ATTEST.quote}
                </p>
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm pt-space-xs border-t border-outline-variant/30">
                  <div>
                    <span className="font-data-metric text-data-metric text-primary block font-semibold">
                      {closer}
                    </span>
                    <span className="font-body-sm text-body-sm text-on-surface-variant">
                      {VERIFY_ATTEST.role}
                    </span>
                  </div>
                  <div className="text-left sm:text-right">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant block font-semibold">
                      Device Timestamp
                    </span>
                    <span className="font-data-metric text-data-metric text-primary tabular-nums">
                      {VERIFY_ATTEST.timestamp}
                    </span>
                  </div>
                </div>
              </section>
            </div>
            <div className="fixed bottom-0 left-0 right-0 z-40 bg-surface/95 shadow-[0_-4px_20px_rgba(40,35,28,0.06)] border-t border-outline-variant/40">
              <div className="max-w-[768px] mx-auto px-margin py-space-md flex flex-col sm:flex-row items-center justify-between gap-space-sm">
                <div className="flex items-center gap-2 self-start sm:self-center">
                  <span
                    className={`w-2.5 h-2.5 rounded-full shrink-0 ${
                      ready ? "bg-status-clear" : "bg-status-now"
                    }`}
                  ></span>
                  <div className="flex flex-col">
                    <span
                      className={`font-label-sm text-label-sm uppercase tracking-wider font-bold ${
                        ready ? "text-status-clear" : "text-status-now"
                      }`}
                    >
                      {ready
                        ? "Gate Status: Ready"
                        : `Gate Status: ${blockers.length} Unresolved Requirement${blockers.length === 1 ? "" : "s"}`}
                    </span>
                    <span className="font-body-sm text-[12px] text-on-surface-variant">
                      {ready ? "Every gate satisfied — the Visit may close." : (blockers[0] ?? "")}
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-space-sm w-full sm:w-auto justify-end">
                  <a
                    className="min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider text-primary bg-surface-container-high hover:bg-surface-container-highest transition-colors font-semibold inline-flex items-center"
                    href={`/visit/${visitId}?day=${day}`}
                  >
                    Return to Workspace
                  </a>
                  <button
                    className={`min-h-[48px] px-space-xl rounded-full font-label-md text-label-md uppercase tracking-wider font-semibold transition-colors ${
                      ready
                        ? "text-on-primary bg-primary hover:bg-primary-container shadow-sm"
                        : "text-on-primary bg-primary/40 cursor-not-allowed shadow-none"
                    }`}
                    disabled={!ready}
                    title={ready ? "Close the Visit" : blockers[0] ?? "Resolve everything first"}
                    type="button"
                    onClick={() => void completeVisit()}
                  >
                    {ready ? "Complete Visit" : "Complete Visit (Locked)"}
                  </button>
                </div>
              </div>
            </div>
            {openRec !== null && (
              <div
                className="fixed inset-0 z-50 bg-primary/40 flex items-center justify-center p-margin"
                onClick={() => setOpenRec(null)}
              >
                <div
                  className="bg-surface-container-lowest w-full max-w-[560px] rounded-xl p-space-xl shadow-2xl"
                  onClick={(e) => e.stopPropagation()}
                  role="dialog"
                  aria-modal="true"
                  aria-label={VERIFY_RECS[openRec].title}
                >
                  <div className="p-space-xl space-y-space-md">
                    <div className="flex items-center justify-between gap-space-sm pb-space-sm border-b border-outline-variant/40">
                      <div className="flex items-center gap-space-sm">
                        <span
                          className={`px-2.5 py-0.5 rounded font-label-sm text-label-sm uppercase tracking-wider font-bold ${
                            VERIFY_RECS[openRec].badge === "Accepted"
                              ? "bg-primary text-on-primary"
                              : VERIFY_RECS[openRec].badge === "Overridden"
                                ? "bg-secondary-container text-on-secondary-container"
                                : "bg-surface-container-highest text-on-surface-variant"
                          }`}
                        >
                          {VERIFY_RECS[openRec].badge}
                        </span>
                        <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                          Recommendation {openRec + 1} of 3
                        </span>
                      </div>
                      <button
                        className="min-h-[48px] px-3 font-label-md text-label-md uppercase tracking-wider text-on-surface-variant hover:text-primary"
                        onClick={() => setOpenRec(null)}
                        type="button"
                      >
                        Close [Esc]
                      </button>
                    </div>
                    <div>
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold block mb-1">
                        {VERIFY_RECS[openRec].tierLine}
                      </span>
                      <h3 className="font-headline-md text-headline-md text-primary">
                        {VERIFY_RECS[openRec].modalTitle}
                      </h3>
                      <p className="font-body-md text-body-md text-on-surface-variant mt-space-sm">
                        {VERIFY_RECS[openRec].body}
                      </p>
                    </div>
                    <div className="p-space-md rounded-lg bg-surface-container-low space-y-1 text-body-sm text-on-surface-variant">
                      {VERIFY_RECS[openRec].facts.map((fact) => (
                        <div key={fact} className="">
                          {fact}
                        </div>
                      ))}
                    </div>
                    <div className="pt-space-sm flex justify-end">
                      <button
                        className="min-h-[48px] px-space-xl rounded-full font-label-md text-label-md uppercase tracking-wider bg-primary text-on-primary font-semibold"
                        onClick={() => setOpenRec(null)}
                        type="button"
                      >
                        Done
                      </button>
                    </div>
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
