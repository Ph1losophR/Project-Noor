"use client";

// Clinical Addendum — initial throwaway (see initial/README.md). The only way
// a closed Visit changes (§5.9): an additive, timestamped, attributed entry
// with its own Write-Back, optionally flagged to the Supervisor as a manual
// flag on Tier 1's window. Wired where the backend owns it (visit detail,
// commit + list addenda endpoints, commit refusals, confirmation state);
// demo where Phase 1 has no source — the MRN/age line, author role line, NTP
// timestamp line, supervisor name/licence (no sign-in, the inbox's fiction),
// hash copy, and envelope labels.
import { Suspense, useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";
import { TAILWIND_CONFIG } from "../../../../../initial/tailwind-config";
import {
  ADDENDUM_DEMO,
  CLUSTER,
  HEADER_DAY,
  HEADER_TEAM,
  INBOX_SUPERVISOR,
  NAV_COUNTS,
  STATION,
} from "../../../../../initial/demo-text";

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
};

type PriorAddendum = {
  addendum_id: string;
  text: string;
  author: string;
  written_at: string;
  flagged: boolean;
};

const STATE_WORD: Record<string, string> = {
  scheduled: "Scheduled",
  in_progress: "In Progress",
  emergency: "Emergency",
  completed: "Completed",
  cancelled: "Cancelled",
  ended_early: "Ended Early",
};

const TERMINAL = ["completed", "cancelled", "ended_early"];

function nowIso(): string {
  return new Date().toISOString();
}

function closedLine(detail: VisitDetail): string {
  const word = STATE_WORD[detail.state] ?? detail.state;
  const when =
    detail.closed_at === null
      ? ""
      : ` ${detail.closed_at.slice(0, 10)} at ${detail.closed_at.slice(11, 16)} AST`;
  const by = detail.closed_by === null ? "" : ` · Closed by ${detail.closed_by}`;
  return `Target Encounter: Visit ${word.toLowerCase()}${when}${by}`;
}

export default function AddendumView() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <AddendumBody />
    </Suspense>
  );
}

function AddendumBody() {
  const params = useParams<{ visitId: string }>();
  const search = useSearchParams();
  const visitId = params.visitId;
  const day = search.get("day") ?? "2026-08-28";

  const [detail, setDetail] = useState<VisitDetail | null>(null);
  const [prior, setPrior] = useState<PriorAddendum[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [draft, setDraft] = useState("");
  const [author, setAuthor] = useState("");
  const [authorTouched, setAuthorTouched] = useState(false);
  const [flagged, setFlagged] = useState(false);
  const [posting, setPosting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [staged, setStaged] = useState<{ id: string; flagged: boolean; at: string } | null>(null);

  const refresh = useCallback(async () => {
    const d = await fetch(`/api/visits/${visitId}`);
    if (!d.ok) throw new Error(`visit HTTP ${d.status}`);
    const body = (await d.json()) as VisitDetail;
    setDetail(body);
    if (!authorTouched && body.junior_physician !== null) setAuthor(body.junior_physician);
    const a = await fetch(`/api/visits/${visitId}/addenda`);
    if (!a.ok) throw new Error(`addenda HTTP ${a.status}`);
    const listed = (await a.json()) as { addenda: PriorAddendum[] };
    setPrior(listed.addenda);
  }, [visitId, authorTouched]);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    refresh().catch(() => {
      if (live) {
        setDetail(null);
        setPrior(null);
        setLoadError("The Visit could not be read.");
      }
    });
    return () => {
      live = false;
    };
  }, [refresh]);

  async function commit() {
    if (posting || draft.trim() === "") return;
    setPosting(true);
    setActionError(null);
    const at = nowIso();
    const r = await fetch(`/api/visits/${visitId}/addenda`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: draft, author, at, flagged }),
    });
    setPosting(false);
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The addendum was refused.");
      return;
    }
    const body = (await r.json()) as { addendum_id: string; flagged: boolean };
    setStaged({ id: body.addendum_id, flagged: body.flagged, at });
    setDraft("");
    setFlagged(false);
    try {
      await refresh();
    } catch {
      setLoadError("Committed, but the prior addenda could not be re-read.");
    }
  }

  const terminal = detail !== null && TERMINAL.includes(detail.state);
  const stateWord = detail === null ? "…" : (STATE_WORD[detail.state] ?? detail.state);

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
            <section className="mb-space-lg">
              <div className="bg-surface-container-high rounded-lg p-space-lg shadow-sm">
                <div className="flex flex-col gap-space-xs">
                  <div className="flex items-center justify-between">
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                      Governance Protocol §5.9
                    </span>
                    <span className="font-label-sm text-label-sm text-on-surface-variant font-mono">
                      SEALED · NON-MUTABLE
                    </span>
                  </div>
                  <p className="font-body-md text-body-md text-on-surface leading-relaxed">
                    <strong className="font-semibold text-primary">
                      Immutability Notice (§5.9):
                    </strong>{" "}
                    The visit record is sealed and dispatched. Addenda are strictly
                    additive, permanently timestamped, and clinically attributed. The
                    original encounter ledger remains unaltered in local cache and
                    central EHR.
                  </p>
                </div>
              </div>
            </section>
            <section className="mb-space-xl flex flex-col gap-space-xs">
              <div className="flex items-baseline justify-between">
                <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant">
                  Post-Closure Clinical Entry
                </span>
                <span className="font-label-sm text-label-sm text-on-surface-variant font-mono">
                  ENVELOPE TYPE N6
                </span>
              </div>
              <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight">
                Clinical Addendum to Closed Visit
              </h1>
              <div className="mt-space-sm bg-surface-container-low rounded-lg p-space-md flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                <div>
                  <div className="flex items-baseline gap-space-sm">
                    <span className="font-headline-sm text-headline-sm text-primary" dir="auto">
                      {detail?.patient_name ?? "…"}
                      {ADDENDUM_DEMO.suffix}
                    </span>
                    <span className="font-label-sm text-label-sm text-outline font-mono">
                      {ADDENDUM_DEMO.mrnLine}
                    </span>
                  </div>
                  <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                    {detail === null ? "…" : closedLine(detail)}
                  </p>
                </div>
                <div className="flex items-center sm:self-center">
                  <span className="inline-flex items-center px-space-md py-1 rounded-full bg-surface-container-highest text-primary font-label-sm text-label-sm uppercase tracking-wider">
                    {terminal ? "Encounter Closed" : stateWord}
                  </span>
                </div>
              </div>
            </section>
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
            {detail !== null && !terminal && (
              <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-lg">
                <div className="flex flex-col gap-space-xs">
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                    Refused — the Visit is still open (§5.9)
                  </span>
                  <h2 className="font-headline-sm text-headline-sm text-primary">
                    This Visit takes no Addendum yet
                  </h2>
                  <p className="font-body-md text-body-md text-on-surface-variant">
                    An Addendum is the only way a closed Visit changes. This Visit is{" "}
                    {stateWord}, so it is edited in its workspace — return there to keep
                    working, and come back here once it has closed.
                  </p>
                </div>
                <div>
                  <a
                    className="min-h-[48px] px-space-xl inline-flex items-center justify-center rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase tracking-wider hover:bg-surface-tint transition-colors"
                    href={`/visit/${visitId}?day=${day}`}
                  >
                    Back to Visit Workspace
                  </a>
                </div>
              </div>
            )}
            {terminal && (
              <div className="flex flex-col gap-space-xl">
                <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-lg">
                  <div className="flex flex-col gap-space-xs">
                    <div className="flex items-center justify-between">
                      <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                        Section §7.4 Ingestion Buffer
                      </span>
                      <span className="font-label-sm text-label-sm text-outline font-mono">
                        PAYLOAD RECOVERED
                      </span>
                    </div>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Late Verification Entry
                    </h2>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Clinician input captured post-closure. Verified against central
                      reconciliation queue prior to local ledger staging.
                    </p>
                  </div>
                  <div className="flex flex-col gap-space-xs">
                    <label
                      className="font-label-md text-label-md text-on-surface font-semibold uppercase tracking-wider"
                      htmlFor="addendum-text"
                    >
                      Addendum Statement (Additive Record)
                    </label>
                    <div className="bg-surface-container-low rounded-lg p-space-sm focus-within:bg-surface-container-lowest focus-within:shadow-sm transition-all">
                      <textarea
                        className="w-full bg-transparent border-0 resize-y p-space-sm font-body-md text-body-md text-on-surface focus:outline-none placeholder:text-outline leading-relaxed"
                        dir="auto"
                        id="addendum-text"
                        onChange={(e) => setDraft(e.target.value)}
                        placeholder="Document rationale, clinical justification, late diagnostic data, or medication amendments..."
                        rows={6}
                        value={draft}
                      ></textarea>
                    </div>
                    <div className="flex items-center justify-between px-space-xs pt-1">
                      <span className="font-label-sm text-label-sm text-on-surface-variant">
                        {ADDENDUM_DEMO.hashLine}
                      </span>
                      <span className="font-label-sm text-label-sm text-outline font-mono">
                        {draft.length} characters
                      </span>
                    </div>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md pt-space-xs">
                    <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col justify-between gap-space-xs">
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant">
                        Author Attribution (§5.13)
                      </span>
                      <input
                        aria-label="Addendum author"
                        className="w-full bg-transparent border-0 border-b border-outline-variant/40 focus:border-primary rounded-none font-label-lg text-label-lg text-primary font-semibold focus:outline-none"
                        dir="auto"
                        onChange={(e) => {
                          setAuthor(e.target.value);
                          setAuthorTouched(true);
                        }}
                        type="text"
                        value={author}
                      />
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        {ADDENDUM_DEMO.authorRole}
                      </span>
                    </div>
                    <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col justify-between">
                      <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant">
                        Local Device Timestamp
                      </span>
                      <div className="mt-space-xs">
                        <div className="font-data-metric text-data-metric text-primary font-semibold">
                          {ADDENDUM_DEMO.timestampLine}
                        </div>
                        <div className="font-body-sm text-body-sm text-on-surface-variant">
                          {ADDENDUM_DEMO.ntpLine}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-lg">
                  <div className="flex flex-col gap-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                      Clinical Oversight Route (§5.11)
                    </span>
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      Supervisor Review Routing
                    </h2>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Addenda with potential pharmacologic or dose impact should be
                      routed. A flagged addendum takes Tier 1&apos;s 72-hour window.
                    </p>
                  </div>
                  <label className="group flex items-start gap-space-md cursor-pointer min-h-[48px] p-space-md rounded-lg bg-surface-container-low hover:bg-surface-container transition-colors select-none">
                    <input
                      checked={flagged}
                      className="mt-1 w-5 h-5 accent-primary"
                      id="supervisor-toggle"
                      onChange={(e) => setFlagged(e.target.checked)}
                      type="checkbox"
                    />
                    <div className="flex flex-col">
                      <span className="font-label-lg text-label-lg text-on-surface font-semibold group-hover:text-primary transition-colors">
                        Flag to Supervisor Queue for Review
                      </span>
                      <span className="font-body-sm text-body-sm text-on-surface-variant">
                        Enforces a Tier 1 mandatory 72-hour clinical sign-off window per
                        governance SOP §5.11.
                      </span>
                    </div>
                  </label>
                  <div
                    className="flex flex-col gap-space-xs transition-opacity duration-200"
                    style={{ opacity: flagged ? 1 : 0.35 }}
                  >
                    <span className="font-label-md text-label-md text-on-surface font-semibold uppercase tracking-wider">
                      Designated Consultant Reviewer
                    </span>
                    <div className="bg-surface-container-low rounded-lg px-space-md py-space-sm">
                      <div className="flex flex-col">
                        <span className="font-label-lg text-label-lg text-primary font-semibold">
                          {INBOX_SUPERVISOR}
                        </span>
                        <span className="font-body-sm text-body-sm text-on-surface-variant">
                          {ADDENDUM_DEMO.supervisorRole}
                        </span>
                      </div>
                    </div>
                    <span className="font-label-sm text-label-sm text-on-surface-variant px-space-xs">
                      {ADDENDUM_DEMO.supervisorNote}
                    </span>
                  </div>
                </div>
                <div className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-md">
                  <div className="flex items-center justify-between">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                      Prior Addenda on this Visit
                    </span>
                    <span className="font-label-sm text-label-sm text-on-surface-variant">
                      {(prior ?? []).length} recorded
                    </span>
                  </div>
                  {prior !== null && prior.length === 0 && (
                    <p className="font-body-md text-body-md text-on-surface">
                      No addenda recorded on this Visit.
                    </p>
                  )}
                  {(prior ?? []).map((item) => (
                    <div
                      className="p-space-md bg-surface-container-low rounded-lg flex flex-col gap-space-xs"
                      key={item.addendum_id}
                    >
                      <div className="flex items-center justify-between gap-space-sm">
                        <span className="font-label-md text-label-md text-primary font-semibold" dir="auto">
                          {item.author}
                        </span>
                        <span className="inline-flex items-center px-space-sm py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider bg-surface-container-high text-on-surface-variant">
                          {item.flagged ? "Flagged to Supervisor" : "Standard audit"}
                        </span>
                      </div>
                      <p className="font-body-md text-body-md text-on-surface" dir="auto">
                        {item.text}
                      </p>
                      <span className="font-label-sm text-label-sm text-on-surface-variant font-mono">
                        {item.written_at.slice(0, 10)} · {item.written_at.slice(11, 16)}
                      </span>
                    </div>
                  ))}
                </div>
                <div className="bg-surface-container-high rounded-xl p-space-lg flex flex-col sm:flex-row sm:items-center justify-between gap-space-md">
                  <div className="flex flex-col gap-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-secondary font-semibold">
                      Dispatch Architecture §4.9
                    </span>
                    <div className="font-label-lg text-label-lg text-primary font-semibold">
                      {ADDENDUM_DEMO.envelopeLine}
                    </div>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      {ADDENDUM_DEMO.envelopeSub}
                    </p>
                  </div>
                  <div className="flex items-center gap-space-sm shrink-0">
                    <div className="h-3 w-3 rounded-full bg-secondary"></div>
                    <span className="font-label-sm text-label-sm uppercase font-mono tracking-widest text-on-surface">
                      Queue Ready
                    </span>
                  </div>
                </div>
                <div className="sticky bottom-4 z-20 bg-surface-container-lowest rounded-xl p-space-md shadow-[0_4px_24px_rgba(40,35,28,0.12)] flex flex-col sm:flex-row items-center justify-between gap-space-md">
                  <a
                    className="w-full sm:w-auto min-h-[48px] px-space-xl inline-flex items-center justify-center rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface hover:bg-surface-container-high transition-colors"
                    href={`/visit/${visitId}?day=${day}`}
                  >
                    Discard Addendum &amp; Return
                  </a>
                  <button
                    className="w-full sm:w-auto min-h-[48px] px-space-xl flex items-center justify-center rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase tracking-wider hover:bg-surface-tint transition-colors shadow-sm disabled:opacity-40"
                    disabled={posting || draft.trim() === "" || author.trim() === ""}
                    onClick={() => void commit()}
                    type="button"
                  >
                    {posting ? "Committing…" : "Commit Addendum & Dispatch Write-Back"}
                  </button>
                </div>
              </div>
            )}
            {staged !== null && (
              <div className="fixed inset-0 z-50 flex items-center justify-center p-space-lg bg-inverse-surface/40">
                <div className="bg-surface rounded-xl max-w-[480px] w-full p-space-xl shadow-xl flex flex-col gap-space-lg">
                  <div className="flex flex-col gap-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-secondary font-semibold">
                      Write-Back Dispatch Staged
                    </span>
                    <h3 className="font-headline-sm text-headline-sm text-primary">
                      Envelope N6 Prepared
                    </h3>
                    <p className="font-body-md text-body-md text-on-surface-variant leading-relaxed">
                      {ADDENDUM_DEMO.stagedLine}
                    </p>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-space-md flex flex-col gap-space-xs font-mono text-body-sm">
                    <div className="flex justify-between text-on-surface-variant">
                      <span className="">TARGET_ENCOUNTER:</span>
                      <span className="text-primary font-semibold">{visitId}</span>
                    </div>
                    <div className="flex justify-between text-on-surface-variant">
                      <span className="">SUPERVISOR_ROUTING:</span>
                      <span className="text-primary font-semibold">
                        {staged.flagged ? "TIER-1 ACTIVE" : "NONE (STANDARD AUDIT)"}
                      </span>
                    </div>
                    <div className="flex justify-between text-on-surface-variant">
                      <span className="">TIMESTAMP:</span>
                      <span className="text-primary font-semibold">{staged.at}</span>
                    </div>
                  </div>
                  <div className="flex justify-end gap-space-sm pt-space-xs">
                    <a
                      className="min-h-[48px] px-space-xl inline-flex items-center rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase tracking-wider hover:bg-surface-tint transition-colors"
                      href={`/visit/${visitId}?day=${day}`}
                    >
                      Return to Closed Visit
                    </a>
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
