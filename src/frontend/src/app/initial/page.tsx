"use client";

// Roster — initial throwaway (see initial/README.md). The layout is the pasted
// design verbatim; the card fields the backend owns (name, reason, state word,
// Baseline/Routine indicator, readiness) come from GET /api/roster. Everything
// else on screen is demo text from initial/demo-text.ts and has no source.
import { useEffect, useRef, useState } from "react";
import {
  CARD_EXTRAS,
  CLUSTER,
  FALLBACK_EXTRA,
  HEADER_DAY,
  HEADER_TEAM,
  NAV_COUNTS,
  STATION,
} from "../../../initial/demo-text";
import { TAILWIND_CONFIG } from "../../../initial/tailwind-config";

type Readiness = { prepared_at: string | null; unreadable: string[] };
type RosterVisit = {
  visit_id: string;
  patient_id: string;
  patient_name: string;
  reason: string;
  state: string;
  planning: string;
  readiness: Readiness;
};

const STATE_WORD: Record<string, string> = {
  scheduled: "Scheduled",
  in_progress: "In Progress",
  emergency: "Emergency",
  completed: "Completed",
  cancelled: "Cancelled",
  ended_early: "Ended Early",
};

const DEMO_DAY = "2026-08-28";

function shiftDate(day: string, delta: number): string {
  const [y, m, d] = day.split("-").map(Number);
  const next = new Date(y, m - 1, d + delta);
  const mm = String(next.getMonth() + 1).padStart(2, "0");
  const dd = String(next.getDate()).padStart(2, "0");
  return `${next.getFullYear()}-${mm}-${dd}`;
}

function readinessLine(r: Readiness): string {
  const at = r.prepared_at === null ? "no office read yet" : `read ${r.prepared_at}`;
  const unread =
    r.unreadable.length === 0 ? "all reads ready" : `unreadable: ${r.unreadable.join(", ")}`;
  return `${at} · ${unread}`;
}

export default function RosterPage() {
  const [day, setDay] = useState(DEMO_DAY);
  const [visits, setVisits] = useState<RosterVisit[]>([]);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [visitFilter, setVisitFilter] = useState("all");
  const [cancelName, setCancelName] = useState<string | null>(null);
  const [cancelReason, setCancelReason] = useState("requested");
  const [otherText, setOtherText] = useState("");
  const [toast, setToast] = useState(false);
  const toastTimer = useRef<number | null>(null);

  useEffect(() => {
    return () => {
      if (toastTimer.current !== null) window.clearTimeout(toastTimer.current);
    };
  }, []);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    fetch(`/api/roster?day=${day}`)
      .then((r) => {
        if (!r.ok) throw new Error(`HTTP ${r.status}`);
        return r.json();
      })
      .then((body) => {
        if (live) setVisits(body.visits as RosterVisit[]);
      })
      .catch(() => {
        if (live) {
          setVisits([]);
          setLoadError("The roster could not be read.");
        }
      });
    return () => {
      live = false;
    };
  }, [day]);

  const visible = visits.filter((v) => {
    const q = query.trim().toLowerCase();
    const matches =
      q === "" ||
      v.patient_name.toLowerCase().includes(q) ||
      v.reason.toLowerCase().includes(q);
    const kind = visitFilter === "routine" ? v.planning === "routine" : true;
    const base = visitFilter === "baseline" ? v.planning === "baseline" : true;
    const active =
      visitFilter === "active" ? v.state === "in_progress" || v.state === "emergency" : true;
    return matches && kind && base && active;
  });

  function confirmCancel() {
    // THROWAWAY: front-end only on purpose. The four reasons below are the
    // pasted demo list, not the seven real `cancelled` rows in
    // docs/clinical-content/reason-lists.md, which POST
    // /api/visits/{id}/cancel validates against. Wiring this popover to the
    // real list is the shippable rebuild's first job — nothing here writes.
    setCancelName(null);
    setToast(true);
    if (toastTimer.current !== null) window.clearTimeout(toastTimer.current);
    toastTimer.current = window.setTimeout(() => setToast(false), 3500);
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
              aria-current="page"
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm uppercase tracking-wider transition-colors whitespace-nowrap bg-primary text-on-primary font-semibold rounded-full font-label-md text-label-md"
              data-path="roster"
              href="#"
            >
              <span className="">ROSTER</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-highest text-on-surface font-semibold">
                {NAV_COUNTS.roster}
              </span>
            </a>
            <a
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm rounded-full font-label-md text-label-md uppercase tracking-wider text-on-surface-variant hover:bg-surface-container-high hover:text-on-surface transition-colors whitespace-nowrap"
              data-path="active-visit"
              href="#"
            >
              <span className="">ACTIVE VISIT</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-high text-on-surface-variant font-semibold">
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
            <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between pb-space-lg gap-space-sm">
              <div>
                <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight mt-space-xs">
                  Scheduled Visits
                </h1>
              </div>
            </div>
            {loadError !== null && (
              <div className="w-full bg-surface-container-low p-space-md rounded-lg mb-space-lg">
                <span className="font-body-md text-body-md text-on-surface">{loadError}</span>
              </div>
            )}
            <div className="w-full bg-surface-container-low p-space-md rounded-lg mb-space-xl flex flex-col sm:flex-row sm:items-center justify-between gap-space-md shadow-sm">
              <div className="flex flex-col sm:flex-row sm:items-center gap-space-md flex-1">
                <div className="relative flex-1 max-w-[320px]">
                  <label className="sr-only" htmlFor="patient-search-input">
                    Search patient
                  </label>
                  <input
                    id="patient-search-input"
                    type="text"
                    placeholder="Search Patient Name or MRN"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    className="w-full min-h-[44px] px-space-md py-1.5 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded-lg outline-none border border-outline-variant hover:bg-surface-container-high focus:bg-surface-container-lowest transition-colors"
                  />
                </div>
                <div className="flex items-center gap-space-sm">
                  <label
                    className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold select-none"
                    htmlFor="filter-visit-type"
                  >
                    Filter:
                  </label>
                  <div className="relative flex items-center">
                    <select
                      id="filter-visit-type"
                      value={visitFilter}
                      onChange={(e) => setVisitFilter(e.target.value)}
                      className="min-h-[44px] pl-space-md pr-space-xl py-1.5 bg-surface-container-lowest text-on-surface font-body-sm text-body-sm rounded-lg outline-none cursor-pointer border border-outline-variant hover:bg-surface-container-high transition-colors"
                    >
                      <option value="all">All Visit Types</option>
                      <option value="routine">Routine Visit</option>
                      <option value="baseline">Baseline Visit</option>
                      <option value="active">Active Visit</option>
                    </select>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-space-xs bg-surface-container-lowest p-1 rounded-lg border border-outline-variant">
                <button
                  type="button"
                  aria-label="Previous Day"
                  onClick={() => setDay(shiftDate(day, -1))}
                  className="w-8 h-8 flex items-center justify-center rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">chevron_left</span>
                </button>
                <div className="flex items-center gap-space-xs px-space-sm">
                  <span className="material-symbols-outlined text-[18px] text-on-surface-variant">
                    calendar_today
                  </span>
                  <span className="font-body-sm text-body-sm font-semibold text-on-surface whitespace-nowrap">
                    {day}
                  </span>
                </div>
                <button
                  type="button"
                  aria-label="Next Day"
                  onClick={() => setDay(shiftDate(day, 1))}
                  className="w-8 h-8 flex items-center justify-center rounded text-on-surface-variant hover:text-on-surface hover:bg-surface-container transition-colors cursor-pointer"
                >
                  <span className="material-symbols-outlined text-[18px]">chevron_right</span>
                </button>
              </div>
            </div>
            <div className="flex flex-col gap-space-lg">
              {visible.map((v, i) => {
                const extra = CARD_EXTRAS[i] ?? FALLBACK_EXTRA;
                const planningWord = v.planning === "baseline" ? "Baseline Visit" : "Routine Visit";
                const planningTone =
                  v.planning === "baseline"
                    ? "bg-secondary-container text-on-secondary-container"
                    : "bg-surface-container text-on-surface-variant";
                const stateWord = STATE_WORD[v.state] ?? v.state;
                const closed = v.state === "completed" || v.state === "cancelled" || v.state === "ended_early";
                const active = v.state === "in_progress" || v.state === "emergency";
                return (
                  <div
                    key={v.visit_id}
                    className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-lg transition-all"
                  >
                    <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-space-md">
                      <div className="flex flex-col gap-space-xs">
                        <div className="flex flex-wrap items-center gap-space-sm">
                          <span
                            className={`font-label-sm text-label-sm uppercase tracking-wider px-space-sm py-0.5 rounded font-semibold ${extra.timeTone}`}
                          >
                            {extra.timeChip}
                          </span>
                          <span
                            className={`font-label-sm text-label-sm uppercase tracking-wider px-space-sm py-0.5 rounded font-semibold ${planningTone}`}
                          >
                            {planningWord}
                          </span>
                          <span className="font-label-sm text-label-sm text-on-surface-variant font-semibold tracking-wider uppercase">
                            {stateWord}
                          </span>
                        </div>
                        <h2 className="font-headline-sm text-headline-sm text-primary tracking-tight mt-1">
                          {v.patient_name}
                          {extra.suffix}
                        </h2>
                        <span className="font-label-sm text-label-sm text-on-surface-variant font-medium tracking-wide">
                          {extra.sub}
                        </span>
                        <span className="font-label-sm text-label-sm text-on-surface-variant tracking-wide">
                          {readinessLine(v.readiness)}
                        </span>
                      </div>
                      <div className="flex flex-col sm:items-end"></div>
                    </div>
                    <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm">
                      <div>
                        <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider block">
                          Visit Reason
                        </span>
                        <span className="font-body-md text-body-md text-on-surface">{v.reason}</span>
                      </div>
                      <div className="sm:text-right">
                        <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider block">
                          {extra.windowLabel}
                        </span>
                        <span className={`font-data-metric text-data-metric font-semibold ${extra.windowTone}`}>
                          {extra.windowValue}
                        </span>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center justify-end gap-space-md pt-space-xs">
                      {!closed && !active && (
                        <button
                          className="min-h-[48px] px-space-xl rounded-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-label-md text-label-md uppercase tracking-wider transition-colors cursor-pointer"
                          onClick={() => {
                            setCancelName(v.patient_name);
                            setCancelReason("requested");
                            setOtherText("");
                          }}
                          type="button"
                        >
                          Cancel Visit
                        </button>
                      )}
                      {!closed && !active && (
                        <a
                          href={`/brief/${v.visit_id}?day=${day}`}
                          className="min-h-[48px] px-space-xl rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase tracking-wider shadow-sm hover:opacity-95 transition-opacity cursor-pointer inline-flex items-center"
                        >
                          Open Brief
                        </a>
                      )}
                      {active && (
                        <a
                          href={`/visit/${v.visit_id}?day=${day}`}
                          className="min-h-[48px] px-space-xl rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase tracking-wider shadow-sm hover:opacity-95 transition-opacity cursor-pointer inline-flex items-center"
                        >
                          Resume Visit
                        </a>
                      )}
                      {closed && (
                        <a
                          href={`/visit/${v.visit_id}?day=${day}`}
                          className="min-h-[48px] px-space-xl rounded-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-label-md text-label-md uppercase tracking-wider transition-colors cursor-pointer inline-flex items-center"
                        >
                          View Closed Visit / Addendum
                        </a>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
            {cancelName !== null && (
              <div className="fixed inset-0 z-50 bg-primary/40 flex items-center justify-center p-space-md">
                <div
                  aria-labelledby="cancel-popover-title"
                  aria-modal="true"
                  className="bg-surface-container-lowest rounded-xl max-w-[620px] w-full p-space-xl shadow-xl flex flex-col gap-space-lg"
                  id="cancellation-panel"
                  role="dialog"
                >
                  <div className="flex flex-col gap-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                      Administrative Cancellation
                    </span>
                    <h3
                      className="font-headline-md text-headline-md text-primary tracking-tight"
                      id="cancel-popover-title"
                    >
                      Cancel Scheduled Visit — {cancelName}
                    </h3>
                    <p className="font-body-sm text-body-sm text-on-surface-variant mt-1 leading-relaxed">
                      No clinical Write-Back is produced because no clinical content exists. Cancelling
                      records the operational reason in Noor.
                    </p>
                  </div>
                  <div className="bg-surface-container-low p-space-md rounded-lg flex flex-col gap-space-sm">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold">
                      Sourced By
                    </span>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-sm">
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-lowest flex items-center gap-space-md cursor-pointer select-none">
                        <input
                          defaultChecked
                          className="w-5 h-5 text-primary accent-primary"
                          name="cancel_source"
                          type="radio"
                          value="phone"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Patient / Family phone call
                        </span>
                      </label>
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-lowest flex items-center gap-space-md cursor-pointer select-none">
                        <input
                          className="w-5 h-5 text-primary accent-primary"
                          name="cancel_source"
                          type="radio"
                          value="team"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Field Team initiative
                        </span>
                      </label>
                    </div>
                  </div>
                  <div className="flex flex-col gap-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold">
                      Operational Cancellation Reason
                    </span>
                    <div className="flex flex-col gap-space-xs" id="reason-list">
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-low hover:bg-surface-container flex items-center gap-space-md cursor-pointer select-none transition-colors">
                        <input
                          checked={cancelReason === "requested"}
                          onChange={() => setCancelReason("requested")}
                          className="w-5 h-5 text-primary accent-primary"
                          name="cancel_reason"
                          type="radio"
                          value="requested"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Patient / family requested cancellation
                        </span>
                      </label>
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-low hover:bg-surface-container flex items-center gap-space-md cursor-pointer select-none transition-colors">
                        <input
                          checked={cancelReason === "admitted"}
                          onChange={() => setCancelReason("admitted")}
                          className="w-5 h-5 text-primary accent-primary"
                          name="cancel_reason"
                          type="radio"
                          value="admitted"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Patient admitted elsewhere
                        </span>
                      </label>
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-low hover:bg-surface-container flex items-center gap-space-md cursor-pointer select-none transition-colors">
                        <input
                          checked={cancelReason === "incorrect"}
                          onChange={() => setCancelReason("incorrect")}
                          className="w-5 h-5 text-primary accent-primary"
                          name="cancel_reason"
                          type="radio"
                          value="incorrect"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Incorrectly scheduled
                        </span>
                      </label>
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-low hover:bg-surface-container flex items-center gap-space-md cursor-pointer select-none transition-colors">
                        <input
                          checked={cancelReason === "access"}
                          onChange={() => setCancelReason("access")}
                          className="w-5 h-5 text-primary accent-primary"
                          name="cancel_reason"
                          type="radio"
                          value="access"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Team unable to access residence
                        </span>
                      </label>
                      <label className="min-h-[48px] px-space-md rounded-lg bg-surface-container-low hover:bg-surface-container flex items-center gap-space-md cursor-pointer select-none transition-colors">
                        <input
                          checked={cancelReason === "other"}
                          onChange={() => setCancelReason("other")}
                          className="w-5 h-5 text-primary accent-primary"
                          id="reason-other-radio"
                          name="cancel_reason"
                          type="radio"
                          value="other"
                        />
                        <span className="font-body-md text-body-md text-on-surface">
                          Other (specify below)
                        </span>
                      </label>
                    </div>
                  </div>
                  {cancelReason === "other" && (
                    <div className="flex flex-col gap-space-xs" id="other-reason-container">
                      <label
                        className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold"
                        htmlFor="other-notes"
                      >
                        Operational Specification
                      </label>
                      <textarea
                        className="w-full p-space-md bg-surface-container-low rounded-lg font-body-md text-body-md text-on-surface outline-none focus:bg-surface-container"
                        id="other-notes"
                        placeholder="State precise reason for audit record..."
                        rows={2}
                        value={otherText}
                        onChange={(e) => setOtherText(e.target.value)}
                      ></textarea>
                    </div>
                  )}
                  <div className="flex flex-col-reverse sm:flex-row items-center justify-end gap-space-md pt-space-sm">
                    <button
                      className="w-full sm:w-auto min-h-[48px] px-space-xl rounded-full bg-surface-container-high hover:bg-surface-container-highest text-on-surface font-label-md text-label-md uppercase tracking-wider transition-colors cursor-pointer"
                      onClick={() => setCancelName(null)}
                      type="button"
                    >
                      Dismiss
                    </button>
                    <button
                      className="w-full sm:w-auto min-h-[48px] px-space-xl rounded-lg bg-tertiary text-on-tertiary font-label-md text-label-md uppercase tracking-wider shadow-sm hover:opacity-95 transition-opacity cursor-pointer font-semibold"
                      onClick={confirmCancel}
                      type="button"
                    >
                      Confirm Cancellation
                    </button>
                  </div>
                </div>
              </div>
            )}
            {toast && (
              <div
                className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-primary text-on-primary px-space-xl py-space-md rounded-full shadow-xl font-label-md text-label-md uppercase tracking-wider z-50 transition-all"
                id="toast"
              >
                Encounter state recorded in Noor
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
