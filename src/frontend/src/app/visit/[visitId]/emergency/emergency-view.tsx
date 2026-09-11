"use client";

// Emergency Protocol — initial throwaway (see initial/README.md). The screen
// the Field Team works while the Visit is suspended: the live record (banner
// clock, retrospective timeline, handover slip) and the binary exit (resume
// the Protocol, or end early with a §5.10 reason). Wired where the backend
// owns it (detail, timeline entries, resume, reasons, end-early endpoints);
// demo where Phase 1 has no source — the dossier extras, handover meds and
// vitals trajectory, and the invented timeline authorship the paste shows.
import { Suspense, useCallback, useEffect, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { TAILWIND_CONFIG } from "../../../../../initial/tailwind-config";
import {
  CLUSTER,
  EMERG_DEMO,
  HEADER_DAY,
  HEADER_TEAM,
  NAV_COUNTS,
  STATION,
} from "../../../../../initial/demo-text";

type Reason = { row_id: string; free_text: string | null };
type TimelineEntry = { kind: string; text: string; at: string };
type EmergencyRecord = { started_at: string; ended_at: string | null; entries: TimelineEntry[] };
type Datum = { state: string; value: unknown; as_of: string | null };
type ReasonRow = { id: string; label: string };
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
  resolutions: Record<string, unknown>;
  emergencies: EmergencyRecord[];
  allergies: Datum;
  plan: unknown;
};

function nowIso(): string {
  return new Date().toISOString();
}

function clockTime(iso: string): string {
  return `${iso.slice(11, 16)} AST`;
}

function elapsedSince(iso: string, nowMs: number): string {
  const secs = Math.max(0, Math.floor((nowMs - new Date(iso).getTime()) / 1000));
  const h = Math.floor(secs / 3600);
  const m = Math.floor((secs % 3600) / 60);
  const s = secs % 60;
  const tail = `${m}m ${s < 10 ? "0" : ""}${s}s`;
  return h > 0 ? `${h}h ${tail}` : tail;
}

function allergyLine(allergies: Datum | undefined): string {
  if (allergies === undefined) return "…";
  if (allergies.state === "present" && Array.isArray(allergies.value)) {
    const joined = (allergies.value as unknown[]).map(String).join(" · ");
    return joined === "" ? "No allergies recorded on the cached read" : joined;
  }
  if (allergies.state === "absent") return "No allergies recorded on the cached read";
  return "Allergy read unavailable — confirm with the household before giving anything";
}

export default function EmergencyView() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <EmergencyBody />
    </Suspense>
  );
}

function EmergencyBody() {
  const params = useParams<{ visitId: string }>();
  const search = useSearchParams();
  const router = useRouter();
  const visitId = params.visitId;
  const day = search.get("day") ?? "2026-08-28";

  const [detail, setDetail] = useState<VisitDetail | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [tag, setTag] = useState<"done" | "observed">("done");
  const [draft, setDraft] = useState("");
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [reasonRows, setReasonRows] = useState<ReasonRow[] | null>(null);
  const [reasonsError, setReasonsError] = useState<string | null>(null);
  const [chosenRow, setChosenRow] = useState<string | null>(null);
  const [otherText, setOtherText] = useState("");
  const [nowMs, setNowMs] = useState(() => Date.now());

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
    const tick = window.setInterval(() => setNowMs(Date.now()), 1000);
    return () => window.clearInterval(tick);
  }, []);

  const record = detail === null || detail.emergencies.length === 0
    ? null
    : detail.emergencies[detail.emergencies.length - 1];
  const active = detail?.state === "emergency";
  const documented = (record?.entries.length ?? 0) > 0;
  const showExit = active;
  const showAppend = record !== null && !(record.ended_at !== null && documented);

  async function commitEntry() {
    const text = draft.trim();
    if (text === "" || record === null) return;
    setActionError(null);
    const r = await fetch(`/api/visits/${visitId}/emergency/entries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ kind: tag, text, at: nowIso() }),
    });
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The timeline entry was refused.");
      return;
    }
    setDraft("");
    await refresh().catch(() => setLoadError("The Visit could not be re-read."));
  }

  async function resumeProtocol() {
    setActionError(null);
    const r = await fetch(`/api/visits/${visitId}/emergency/resume`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ at: nowIso() }),
    });
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The resume was refused.");
      return;
    }
    router.push(`/visit/${visitId}?day=${day}`);
  }

  async function openDrawer() {
    const next = !drawerOpen;
    setDrawerOpen(next);
    if (next && reasonRows === null && reasonsError === null) {
      try {
        const r = await fetch("/api/reasons/ended_early");
        if (!r.ok) throw new Error(`reasons HTTP ${r.status}`);
        const body = (await r.json()) as { rows: ReasonRow[] };
        setReasonRows(body.rows);
      } catch {
        setReasonsError("The reason list could not be read.");
      }
    }
  }

  async function finalizeTransfer() {
    if (chosenRow === null) return;
    setActionError(null);
    const r = await fetch(`/api/visits/${visitId}/end-early`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        row_id: chosenRow,
        free_text: otherText,
        by: detail?.junior_physician ?? "Field Team",
        at: nowIso(),
      }),
    });
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The transfer was refused.");
      return;
    }
    router.push(`/initial?day=${day}`);
  }

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
              href={`/initial?day=${day}`}
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
          <div className="flex flex-col w-full gap-space-lg">
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
            {detail !== null && record === null && (
              <div className="w-full bg-surface-container-lowest p-space-xl rounded-xl shadow-md flex flex-col gap-space-sm">
                <h1 className="font-headline-md text-headline-md text-primary">
                  No Emergency on this Visit
                </h1>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  The Emergency Protocol was never entered here. The workspace holds the
                  Visit Protocol.
                </p>
                <a
                  className="min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider bg-primary text-on-primary font-semibold flex items-center justify-center self-start"
                  href={`/visit/${visitId}?day=${day}`}
                >
                  Back to Workspace
                </a>
              </div>
            )}
            {detail !== null && record !== null && (
              <>
                <section className="bg-surface-container-lowest p-space-lg md:p-space-xl rounded-xl shadow-md border-l-4 border-status-now flex flex-col gap-space-md">
                  <div className="flex flex-wrap items-center justify-between gap-y-2 gap-x-space-md pb-space-xs border-b border-black/10">
                    <div className="flex items-center gap-space-sm flex-wrap">
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full bg-status-now/10 text-status-now font-label-sm text-label-sm font-bold tracking-widest uppercase">
                        Escalation Protocol active
                      </span>
                      <span className="text-outline-variant hidden sm:inline">|</span>
                      <h1 className="font-headline-md text-headline-md text-primary font-medium tracking-tight">
                        SUSPENDED VISIT PROTOCOL
                      </h1>
                    </div>
                    <div className="flex items-center gap-space-sm bg-surface-container-low px-space-md py-1 rounded-full border border-black/5">
                      <span className="w-2 h-2 rounded-full bg-status-now animate-pulse"></span>
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                        Live Protocol Clock
                      </span>
                      <span className="font-data-metric text-data-metric text-tertiary-container font-bold tabular-nums">
                        {elapsedSince(record.started_at, nowMs)}
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-12 gap-space-md items-center pt-space-xs">
                    <div className="lg:col-span-6 flex flex-col">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                        Subject / Dossier Identifier
                      </span>
                      <span className="font-headline-sm text-headline-sm text-primary font-medium">
                        {detail.patient_name}
                        {EMERG_DEMO.suffix}
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        {EMERG_DEMO.mrnLine}
                      </span>
                    </div>
                    <div className="lg:col-span-3 flex flex-col sm:border-l sm:border-black/10 sm:pl-space-md">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                        Emergency Ingress
                      </span>
                      <span className="font-data-metric text-data-metric text-primary">
                        {clockTime(record.started_at)}
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        {EMERG_DEMO.ingressNote}
                      </span>
                    </div>
                    <div className="lg:col-span-3 flex flex-col sm:border-l sm:border-black/10 sm:pl-space-md">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                        Required Fields At Entry
                      </span>
                      <span className="font-data-metric text-data-metric text-primary">
                        0 (Immediate Bypass)
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Zero Validation Halt
                      </span>
                    </div>
                  </div>
                </section>
                <div className="grid grid-cols-1 md:grid-cols-12 gap-space-lg items-start">
                  <section className="md:col-span-7 flex flex-col gap-space-lg">
                    <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-md flex flex-col gap-space-lg">
                      <div className="flex items-center justify-between pb-space-xs border-b border-black/10">
                        <div className="flex flex-col">
                          <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                            Section 5.7 Audit Trail
                          </span>
                          <h2 className="font-headline-sm text-headline-sm text-primary">
                            Retrospective Emergency Timeline
                          </h2>
                        </div>
                      </div>
                      <div className="relative pl-6 flex flex-col gap-space-lg before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-3 before:w-0.5 before:bg-outline-variant/50">
                        {record.entries.length === 0 && (
                          <p className="font-body-md text-body-md text-on-surface-variant">
                            {EMERG_DEMO.emptyHint}
                          </p>
                        )}
                        {record.entries.map((entry, index) => (
                          <div className="relative flex flex-col gap-space-xs" key={index}>
                            <div
                              className={
                                entry.kind === "done"
                                  ? "absolute -left-[27px] top-1 w-3 h-3 rounded-full bg-primary ring-4 ring-surface-container-lowest"
                                  : "absolute -left-[27px] top-1 w-3 h-3 rounded-full bg-surface-container-highest ring-4 ring-surface-container-lowest border-2 border-outline"
                              }
                            ></div>
                            <div className="flex items-center justify-between">
                              <div className="flex items-center gap-space-sm">
                                <span className="font-label-sm text-label-sm font-bold tracking-wider text-primary uppercase">
                                  {clockTime(entry.at)}
                                </span>
                                <span
                                  className={
                                    entry.kind === "done"
                                      ? "px-space-sm py-0.5 bg-primary text-on-primary font-label-sm text-label-sm rounded uppercase font-semibold"
                                      : "px-space-sm py-0.5 bg-surface-container-highest text-on-surface font-label-sm text-label-sm rounded uppercase font-semibold"
                                  }
                                >
                                  {entry.kind}
                                </span>
                              </div>
                              <span className="font-body-sm text-body-sm text-on-surface-variant">
                                Field Team
                              </span>
                            </div>
                            <p
                              className="font-body-md text-body-md text-on-surface pt-space-xs"
                              dir="auto"
                            >
                              {entry.text}
                            </p>
                          </div>
                        ))}
                      </div>
                      {showAppend && (
                        <div className="border-t border-black/10 pt-space-md flex flex-col gap-space-sm">
                          <div className="flex items-center justify-between">
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                              Append Retrospective Entry
                            </span>
                          </div>
                          <div className="flex flex-col gap-space-sm">
                            <div className="flex items-center gap-space-sm">
                              <button
                                className={
                                  tag === "done"
                                    ? "h-8 px-space-md rounded-full bg-primary text-on-primary font-label-sm text-label-sm uppercase font-semibold"
                                    : "h-8 px-space-md rounded-full bg-surface-container-high text-on-surface font-label-sm text-label-sm uppercase font-semibold"
                                }
                                onClick={() => setTag("done")}
                                type="button"
                              >
                                Tag: DONE
                              </button>
                              <button
                                className={
                                  tag === "observed"
                                    ? "h-8 px-space-md rounded-full bg-primary text-on-primary font-label-sm text-label-sm uppercase font-semibold"
                                    : "h-8 px-space-md rounded-full bg-surface-container-high text-on-surface font-label-sm text-label-sm uppercase font-semibold"
                                }
                                onClick={() => setTag("observed")}
                                type="button"
                              >
                                Tag: OBSERVED
                              </button>
                            </div>
                            <textarea
                              className="w-full p-space-md bg-surface-container-low rounded-lg font-body-md text-body-md text-on-surface focus:outline-none focus:bg-surface-container-lowest placeholder:text-on-surface-variant/60 resize-none"
                              dir="auto"
                              onChange={(e) => setDraft(e.target.value)}
                              placeholder="Document critical clinical event, intervention, or measurement..."
                              rows={2}
                              value={draft}
                            ></textarea>
                            <div className="flex justify-end">
                              <button
                                className="min-h-[48px] px-space-xl rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase font-semibold hover:bg-primary-container transition-colors"
                                onClick={() => void commitEntry()}
                                type="button"
                              >
                                Commit Entry to Audit Stream
                              </button>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                  <section className="md:col-span-5 flex flex-col gap-space-lg">
                    <div className="bg-surface-container-lowest p-space-xl rounded-xl shadow-md flex flex-col gap-space-md">
                      <div className="flex items-center justify-between pb-space-xs border-b border-black/10">
                        <div className="flex flex-col">
                          <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                            Section 10 Offline Protocol
                          </span>
                          <h2 className="font-headline-sm text-headline-sm text-primary">
                            Paramedic Handover
                          </h2>
                        </div>
                      </div>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Direct bedside transfer dossier compiled instantly from the SQLite
                        encrypted local ledger. Prepared for physical rotation or direct
                        thermal printing.
                      </p>
                      <button
                        className="min-h-[48px] w-full px-space-lg bg-primary text-on-primary rounded-full font-label-md text-label-md uppercase font-semibold flex items-center justify-center gap-space-sm hover:bg-primary-container transition-colors"
                        onClick={() => window.print()}
                        type="button"
                      >
                        PRINT HANDOVER
                      </button>
                      <div className="bg-white text-black p-space-lg rounded-lg border border-black/10 shadow-sm flex flex-col gap-space-md select-none transition-all">
                        <div className="flex items-center justify-between pb-space-xs border-b border-black/10">
                          <div className="flex flex-col">
                            <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-black">
                              MOH Emergency Transfer Handover
                            </span>
                            <span className="font-body-sm text-body-sm font-medium">
                              {EMERG_DEMO.handoverUnit}
                            </span>
                          </div>
                          <span className="font-label-sm text-label-sm font-bold text-black uppercase">
                            {STATION.split(" · ")[0]}
                          </span>
                        </div>
                        <div className="flex flex-col gap-space-xs">
                          <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-black/70">
                            Attending Field Officers
                          </span>
                          <span className="font-body-md text-body-md text-black font-medium">
                            {EMERG_DEMO.handoverOfficers}
                          </span>
                        </div>
                        <div className="flex flex-col gap-space-xs p-space-sm rounded bg-red-50/70 border-l-2 border-status-now">
                          <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-status-now">
                            Verified Critical Allergies
                          </span>
                          <span
                            className="font-body-md text-body-md text-black font-semibold"
                            dir="auto"
                          >
                            {allergyLine(detail.allergies)}
                          </span>
                        </div>
                        <div className="flex flex-col gap-space-xs">
                          <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-black/70">
                            Active Pharmacotherapy in Residence
                          </span>
                          <div className="font-body-sm text-body-sm text-black flex flex-col space-y-0.5">
                            {EMERG_DEMO.handoverMeds.map((line) => (
                              <span className="" key={line}>
                                {line}
                              </span>
                            ))}
                          </div>
                        </div>
                        <div className="flex flex-col gap-space-xs">
                          <span className="font-label-sm text-label-sm font-bold uppercase tracking-wider text-black/70">
                            Vital Trajectory Sequence
                          </span>
                          <div className="grid grid-cols-3 gap-space-xs text-center">
                            {EMERG_DEMO.handoverVitals.map((cell) => (
                              <div className="p-space-xs bg-black/5 rounded" key={cell.label}>
                                <span className="font-label-sm text-label-sm uppercase text-black/60 block">
                                  {cell.label}
                                </span>
                                <span className="font-data-metric text-data-metric text-black font-semibold">
                                  {cell.value}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    </div>
                  </section>
                </div>
                {showExit ? (
                  <section className="bg-surface-container-lowest p-space-xl rounded-xl shadow-md flex flex-col gap-space-md">
                    <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-xs pb-space-xs border-b border-black/10">
                      <div className="flex flex-col">
                        <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                          Section 5.7 Directive
                        </span>
                        <h2 className="font-headline-sm text-headline-sm text-primary">
                          Emergency Exit Binary Gate
                        </h2>
                      </div>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        The practitioner must resolve the suspended protocol through one of two
                        mutually exclusive determinations.
                      </span>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md pt-space-xs">
                      <div className="p-space-lg bg-surface-container-low rounded-lg flex flex-col gap-space-xs border-t-2 border-primary">
                        <span className="font-label-md text-label-md uppercase font-semibold text-primary">
                          Option A: Clinical Stabilization
                        </span>
                        <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                          Patient remained at home, acute distress resolved, Red Crescent cleared
                          the patient for home monitoring.
                        </p>
                      </div>
                      <div className="p-space-lg bg-surface-container-low rounded-lg flex flex-col gap-space-xs border-t-2 border-status-now">
                        <span className="font-label-md text-label-md uppercase font-semibold text-tertiary-container">
                          Option B: Hospital Transfer
                        </span>
                        <p className="font-body-sm text-body-sm text-on-surface-variant leading-relaxed">
                          Requires structured reason per §5.10; triggers mandatory emergency
                          timeline close gate and EHR lock.
                        </p>
                      </div>
                    </div>
                    <div className="p-space-md bg-surface-container-low rounded-xl flex flex-col gap-space-sm border border-black/10">
                      <div className="flex items-center justify-between px-space-xs">
                        <span className="font-label-sm text-label-sm uppercase font-semibold tracking-wider text-on-surface-variant">
                          Exit Determination Trigger
                        </span>
                        <span className="font-label-sm text-label-sm uppercase text-on-surface-variant">
                          Binary Protocol Choice
                        </span>
                      </div>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                        <button
                          className="min-h-[48px] w-full px-space-md bg-surface-container-high text-on-surface hover:bg-surface-container-highest rounded-full font-label-md text-label-md uppercase font-semibold transition-colors flex items-center justify-center"
                          onClick={() => void resumeProtocol()}
                          type="button"
                        >
                          Resume Visit Protocol
                        </button>
                        <button
                          className="min-h-[48px] w-full px-space-md bg-tertiary-container text-on-tertiary hover:bg-tertiary-container/90 rounded-full font-label-md text-label-md uppercase font-semibold transition-colors flex items-center justify-center"
                          onClick={() => void openDrawer()}
                          type="button"
                        >
                          End Visit Early (Transferred)
                        </button>
                      </div>
                    </div>
                    {drawerOpen && (
                      <div className="flex flex-col gap-space-sm p-space-md bg-surface-container-high rounded-lg mt-space-xs">
                        <span className="font-label-sm text-label-sm uppercase font-semibold text-primary">
                          Section 5.10 Mandatory Close-Out Codification
                        </span>
                        {reasonsError !== null && (
                          <span className="font-body-sm text-body-sm text-on-surface-variant">
                            {reasonsError}
                          </span>
                        )}
                        {reasonRows === null && reasonsError === null && (
                          <span className="font-body-sm text-body-sm text-on-surface-variant">
                            Reading the reason list…
                          </span>
                        )}
                        {reasonRows !== null && (
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-space-xs">
                            {reasonRows.map((row) => (
                              <button
                                className={
                                  chosenRow === row.id
                                    ? "px-space-sm py-space-sm bg-primary text-on-primary rounded font-label-sm text-label-sm uppercase text-left font-medium transition-colors"
                                    : "px-space-sm py-space-sm bg-surface-container-lowest text-on-surface rounded font-label-sm text-label-sm uppercase text-left font-medium hover:bg-primary hover:text-on-primary transition-colors"
                                }
                                key={row.id}
                                onClick={() => setChosenRow(row.id)}
                                type="button"
                              >
                                {row.label}
                              </button>
                            ))}
                          </div>
                        )}
                        {chosenRow === "other" && (
                          <textarea
                            className="w-full p-space-md bg-surface-container-lowest rounded-lg font-body-md text-body-md text-on-surface focus:outline-none placeholder:text-on-surface-variant/60 resize-none"
                            dir="auto"
                            onChange={(e) => setOtherText(e.target.value)}
                            placeholder="Write what happened…"
                            rows={2}
                            value={otherText}
                          ></textarea>
                        )}
                        <button
                          className="min-h-[48px] w-full mt-space-xs bg-primary text-on-primary rounded-full font-label-md text-label-md uppercase font-semibold"
                          onClick={() => void finalizeTransfer()}
                          type="button"
                        >
                          Finalize Emergency Handover Closure
                        </button>
                      </div>
                    )}
                  </section>
                ) : (
                  <section className="bg-surface-container-lowest p-space-xl rounded-xl shadow-md flex flex-col gap-space-sm">
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Emergency Protocol closed
                    </h2>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      This record ended
                      {record.ended_at === null ? "" : ` at ${clockTime(record.ended_at)}`}
                      {documented ? " and is written down." : " but has no timeline entry yet."}
                      {!documented && " One entry is what lets this Visit close."} The
                      workspace holds the Visit Protocol.
                    </p>
                    <a
                      className="min-h-[48px] px-space-lg rounded-full font-label-md text-label-md uppercase tracking-wider bg-primary text-on-primary font-semibold flex items-center justify-center self-start"
                      href={`/visit/${visitId}?day=${day}`}
                    >
                      Back to Workspace
                    </a>
                  </section>
                )}
              </>
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
