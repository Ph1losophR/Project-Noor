"use client";

// Write-Back Queue — initial throwaway (see initial/README.md). The Field
// Team's explicit-resend surface: closed Visits the EMR has not accepted, with
// their assembled items, owners, due times, refusals, and queued Addenda —
// all from GET /api/queue, with Transmit Now and Attempt Dispatch for All
// Queued posting the real dispatches. Demo where Phase 1 has no source:
// envelope IDs, payload sizes, SHA keys, FHIR transaction IDs, endpoint URLs,
// NFC/export, signature verification, storage-meter figures.
import { useCallback, useEffect, useState } from "react";
import { TAILWIND_CONFIG } from "../../../initial/tailwind-config";
import {
  CLUSTER,
  HEADER_DAY,
  HEADER_TEAM,
  NAV_COUNTS,
  QUEUE_DEMO,
  STATION,
} from "../../../initial/demo-text";

type QueueItem = { kind: string; payload: Record<string, unknown> };
type QueueVisit = {
  visit_id: string;
  patient_id: string;
  patient_name: string;
  state: string;
  scheduled_for: string;
  scheduled_reason: string;
  closed_at: string | null;
  closed_by: string | null;
  refused_at: string | null;
  refusal: string | null;
  items: QueueItem[];
};
type QueueAddendum = {
  addendum_id: string;
  visit_id: string;
  patient_id: string;
  patient_name: string;
  text: string;
  author: string;
  written_at: string;
  refused_at: string | null;
  refusal: string | null;
};
type VisitDetail = { kind: string | null };
type Owed = { subject: string; owner: string; due_at: string };

const KIND_WORD: Record<string, string> = {
  VISIT_OUTCOME: "Visit outcome",
  OBSERVATIONS: "Observations",
  SELF_CARE_FINDINGS: "Self-Care Findings",
  RECONCILIATION: "Medication Reconciliation",
  RECOMMENDATIONS: "Recommendations",
  BETWEEN_VISIT_PLAN: "Between-Visit Plan",
  PROPOSED_GOAL_OF_CARE: "Proposed Goal of Care",
};

const STATE_WORD: Record<string, string> = {
  completed: "Completed",
  ended_early: "Ended Early",
};

function nowIso(): string {
  return new Date().toISOString();
}

function owed(visit: QueueVisit): Owed[] {
  const found: Owed[] = [];
  for (const item of visit.items) {
    if (item.kind === "RECOMMENDATIONS") {
      const recs = (item.payload["recommendations"] ?? []) as Array<
        Record<string, unknown>
      >;
      for (const rec of recs) {
        const response = rec["response"] as {
          owner: string;
          due_at: string;
        } | null;
        if (response !== null)
          found.push({
            subject: String(rec["id"]),
            owner: response.owner,
            due_at: response.due_at,
          });
      }
    } else if (item.kind === "PROPOSED_GOAL_OF_CARE") {
      const response = item.payload["response"] as {
        owner: string;
        due_at: string;
      } | null;
      if (response !== null)
        found.push({
          subject: "proposed-goal-of-care",
          owner: response.owner,
          due_at: response.due_at,
        });
    }
  }
  return found;
}

function dueText(dueAt: string): string {
  const ms = new Date(dueAt).getTime() - Date.now();
  if (ms < 0) {
    const late = Math.floor(Math.abs(ms) / 3600000);
    return late < 1 ? "Overdue — answers late" : `Overdue by ${late} hour${late === 1 ? "" : "s"}`;
  }
  const absDays = Math.floor(ms / 86400000);
  const absHours = Math.floor(ms / 3600000);
  if (absDays >= 1) return `Due in ${absDays} day${absDays === 1 ? "" : "s"}`;
  if (absHours >= 1) return `Due in ${absHours} hour${absHours === 1 ? "" : "s"}`;
  return "Due within the hour";
}

function kindWord(detail: VisitDetail | undefined): string {
  if (detail?.kind === "baseline") return "Baseline";
  if (detail?.kind === "routine") return "Routine";
  return "Closed";
}

export default function QueueView() {
  const [visits, setVisits] = useState<QueueVisit[] | null>(null);
  const [addenda, setAddenda] = useState<QueueAddendum[]>([]);
  const [details, setDetails] = useState<Record<string, VisitDetail>>({});
  const [loadError, setLoadError] = useState<string | null>(null);
  const [toast, setToast] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [postingId, setPostingId] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const r = await fetch("/api/queue");
    if (!r.ok) throw new Error(`queue HTTP ${r.status}`);
    const body = (await r.json()) as {
      visits: QueueVisit[];
      addenda: QueueAddendum[];
    };
    setVisits(body.visits);
    setAddenda(body.addenda);
    const fetched: Record<string, VisitDetail> = {};
    await Promise.all(
      body.visits.map(async (visit) => {
        const d = await fetch(`/api/visits/${visit.visit_id}`);
        if (d.ok) fetched[visit.visit_id] = (await d.json()) as VisitDetail;
      }),
    );
    setDetails((prev) => ({ ...prev, ...fetched }));
    return body;
  }, []);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    refresh().catch(() => {
      if (live) {
        setVisits(null);
        setLoadError("The queue could not be read.");
      }
    });
    return () => {
      live = false;
    };
  }, [refresh]);

  useEffect(() => {
    if (toast === null) return;
    const timer = setTimeout(() => setToast(null), 5000);
    return () => clearTimeout(timer);
  }, [toast]);

  const pending = (visits ?? []).length + addenda.length;

  async function transmit(visitId: string) {
    if (postingId !== null) return;
    setPostingId(visitId);
    setActionError(null);
    setToast(null);
    const r = await fetch(`/api/visits/${visitId}/dispatch`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ at: nowIso() }),
    });
    setPostingId(null);
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The transmit was refused.");
      return;
    }
    const body = (await r.json()) as {
      sent: boolean;
      refusal?: string;
    };
    if (body.sent) setToast("Sent — the envelope leaves the queue on this read.");
    else setActionError(body.refusal ?? "The EMR refused. The envelope stays queued.");
    try {
      await refresh();
    } catch {
      setLoadError("Sent, but the queue could not be re-read.");
    }
  }

  async function dispatchAll() {
    if (postingId !== null) return;
    setPostingId("all");
    setActionError(null);
    setToast(null);
    const r = await fetch("/api/queue/dispatch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ at: nowIso() }),
    });
    setPostingId(null);
    if (!r.ok) {
      const body = (await r.json()) as { detail?: string };
      setActionError(body.detail ?? "The dispatch was refused.");
      return;
    }
    const body = (await r.json()) as {
      sent: string[];
      failed: Array<{ id: string; refusal: string }>;
    };
    if (body.failed.length === 0)
      setToast(
        body.sent.length === 0
          ? "Nothing queued — every close has been accepted."
          : `Sent ${body.sent.length} — the queue is clear.`,
      );
    else
      setActionError(
        `Sent ${body.sent.length}, refused ${body.failed.length}: ${body.failed.map((f) => f.refusal).join(" · ")}`,
      );
    try {
      await refresh();
    } catch {
      setLoadError("Dispatched, but the queue could not be re-read.");
    }
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
              aria-current="page"
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm uppercase tracking-wider transition-colors whitespace-nowrap bg-primary text-on-primary font-semibold rounded-full font-label-md text-label-md"
              data-path="write-back-queue"
              href="#"
            >
              <span className="">WRITE-BACK QUEUE</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-highest text-on-surface font-semibold">
                {pending}
              </span>
            </a>
          </nav>
        </header>
        <main className="w-full pt-36 px-margin pb-space-xl flex-1 bg-surface">
          <div className="flex flex-col w-full">
            <div className="flex flex-col gap-space-lg pb-space-xl">
              <div className="bg-surface-container-high rounded-xl p-space-xl shadow-sm flex flex-col gap-space-md">
                <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-xs">
                  <div>
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold block">
                      Protocol §4.10 · Deterministic Local Persistence
                    </span>
                    <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight">
                      Local Write-Back Dispatch Queue
                    </h1>
                  </div>
                  <div className="bg-surface-container-lowest px-space-md py-space-xs rounded-full self-start sm:self-auto shadow-sm">
                    <span className="font-label-md text-label-md text-primary tracking-wider uppercase font-semibold">
                      {visits === null ? "…" : `${pending} Write-Back${pending === 1 ? "" : "s"} pending`}
                    </span>
                  </div>
                </div>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Persistent on-device encrypted store (SQLite / IndexedDB) · Riyadh North
                  Cluster Dispatch
                </p>
                <div className="flex flex-wrap items-center gap-x-space-lg gap-y-space-xs pt-space-xs text-on-surface-variant font-label-md text-label-md">
                  <div className="flex items-center gap-space-xs">
                    <span className="text-on-surface font-semibold">Status:</span>
                    <span className="">{QUEUE_DEMO.syncLine}</span>
                  </div>
                  <span className="text-outline-variant">/</span>
                  <div className="flex items-center gap-space-xs">
                    <span className="text-on-surface font-semibold">Engine:</span>
                    <span className="">Single-Attempt On Close (§4.9) · Background Polling Suspended</span>
                  </div>
                </div>
              </div>
              <div className="bg-surface-container-low rounded-xl p-space-lg flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-space-md shadow-sm">
                <div className="flex flex-col">
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold">
                    Manual Dispatch Control
                  </span>
                  <span className="font-body-sm text-body-sm text-on-surface-variant">
                    Strict non-automated transmission requires explicit practitioner authorization
                  </span>
                </div>
                <div className="flex flex-col sm:flex-row items-stretch gap-space-md">
                  <button
                    className="min-h-[48px] px-space-lg rounded-full bg-surface-container-highest text-on-surface font-label-lg text-label-lg uppercase tracking-wider hover:bg-surface-container transition-colors active:scale-[0.99] flex items-center justify-center text-center"
                    onClick={() => setToast(QUEUE_DEMO.exportToast)}
                    type="button"
                  >
                    Export Encrypted Bundle to NFC / External Token
                  </button>
                  <button
                    className="min-h-[48px] px-space-lg rounded-full bg-primary text-on-primary font-label-lg text-label-lg uppercase tracking-wider hover:bg-primary-container transition-colors active:scale-[0.99] flex items-center justify-center text-center disabled:opacity-40"
                    disabled={postingId !== null || pending === 0}
                    onClick={() => void dispatchAll()}
                    type="button"
                  >
                    {postingId === "all"
                      ? "Dispatching…"
                      : `Attempt Dispatch for All Queued (${pending})`}
                  </button>
                </div>
              </div>
              {toast !== null && (
                <div className="rounded-lg bg-primary text-on-primary px-space-lg py-space-md font-body-md text-body-md shadow-md">
                  <div className="flex items-center justify-between gap-space-md">
                    <span className="">{toast}</span>
                    <button
                      className="font-label-sm text-label-sm uppercase tracking-wider text-primary-fixed underline px-space-sm py-space-xs shrink-0"
                      onClick={() => setToast(null)}
                      type="button"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}
              {loadError !== null && (
                <div className="w-full bg-surface-container-low p-space-md rounded-lg">
                  <span className="font-body-md text-body-md text-on-surface">{loadError}</span>
                </div>
              )}
              {actionError !== null && (
                <div className="w-full bg-error-container p-space-md rounded-lg">
                  <span className="font-body-md text-body-md text-on-error-container" dir="auto">
                    {actionError}
                  </span>
                </div>
              )}
              <div className="flex flex-col gap-space-lg">
                {(visits ?? []).map((visit) => {
                  const refused = visit.refusal !== null;
                  const due = owed(visit);
                  return (
                    <article
                      className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-lg"
                      key={visit.visit_id}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-sm">
                        <div className="flex flex-col gap-space-xs">
                          <div className="flex items-center gap-space-sm flex-wrap">
                            <span className="font-data-metric text-data-metric font-semibold text-primary">
                              Envelope #{visit.visit_id}
                            </span>
                            <span className="px-space-sm py-0.5 rounded-full bg-surface-container-high text-on-surface font-label-sm text-label-sm uppercase tracking-wider">
                              {refused ? "Ingestion Fault" : "Local Sealed Payload"}
                            </span>
                          </div>
                          <h2 className="font-headline-sm text-headline-sm text-primary" dir="auto">
                            {visit.patient_name} ({kindWord(details[visit.visit_id])} Visit)
                          </h2>
                        </div>
                        <div className="self-start sm:self-auto">
                          <span
                            className={
                              refused
                                ? "inline-block px-space-md py-space-xs rounded-full bg-tertiary-container text-on-tertiary font-label-md text-label-md font-semibold uppercase tracking-wider"
                                : "inline-block px-space-md py-space-xs rounded-full bg-secondary-container text-on-secondary-container font-label-md text-label-md font-semibold uppercase tracking-wider"
                            }
                          >
                            {refused
                              ? "Rejected by EMR"
                              : "Queued (Pending explicit transmission)"}
                          </span>
                        </div>
                      </div>
                      <div className="bg-surface-container-low rounded-lg p-space-lg flex flex-col gap-space-md">
                        <div>
                          <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold block">
                            Payload Summary
                          </span>
                          <p className="font-body-md text-body-md text-on-surface mt-space-xs">
                            Visit outcome ({STATE_WORD[visit.state] ?? visit.state}),{" "}
                            {visit.items.length} structured{" "}
                            {visit.items.length === 1 ? "item" : "items"}:{" "}
                            {visit.items
                              .map((item) => KIND_WORD[item.kind] ?? item.kind)
                              .join(" · ")}
                            .
                          </p>
                        </div>
                        {due.length > 0 && (
                          <div className="flex flex-col gap-space-xs">
                            {due.map((answer) => (
                              <p
                                className="font-body-sm text-body-sm text-on-surface"
                                key={answer.subject}
                              >
                                <span className="font-semibold">Owner: {answer.owner}</span>
                                <span className="text-on-surface-variant">
                                  {" "}
                                  · {dueText(answer.due_at)}
                                </span>
                              </p>
                            ))}
                          </div>
                        )}
                        {refused ? (
                          <div className="bg-error-container rounded-lg p-space-lg flex flex-col gap-space-xs">
                            <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-error-container font-semibold">
                              Refusal Diagnostic Record
                            </span>
                            <p
                              className="font-body-md text-body-md text-on-error-container font-medium"
                              dir="auto"
                            >
                              {visit.refusal}
                            </p>
                            <span className="font-body-sm text-body-sm text-on-error-container mt-space-xs">
                              {QUEUE_DEMO.endpointLine}
                            </span>
                          </div>
                        ) : (
                          <div className="bg-surface-container-high p-space-md rounded">
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface font-semibold block">
                              Transport &amp; Environment Diagnostics
                            </span>
                            <p className="font-body-sm text-body-sm text-on-surface-variant mt-0.5">
                              Sealed locally. Nothing retries by itself — this envelope waits
                              for an explicit transmit (§4.10).
                            </p>
                          </div>
                        )}
                      </div>
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-md pt-space-xs">
                        <div className="text-on-surface-variant font-label-sm text-label-sm">
                          <span className="">
                            {refused
                              ? "Attempted — the EMR refused; still sealed locally"
                              : "Attempts Recorded: 0"}
                          </span>
                          <span className="mx-space-xs text-outline-variant">·</span>
                          <span className="">{QUEUE_DEMO.sizeLine}</span>
                        </div>
                        <button
                          className={
                            refused
                              ? "min-h-[48px] px-space-xl rounded-full bg-tertiary-container text-on-tertiary font-label-lg text-label-lg uppercase tracking-wider hover:bg-tertiary transition-colors active:scale-[0.99] flex items-center justify-center disabled:opacity-40"
                              : "min-h-[48px] px-space-xl rounded-full bg-primary text-on-primary font-label-lg text-label-lg uppercase tracking-wider hover:bg-primary-container transition-colors active:scale-[0.99] flex items-center justify-center disabled:opacity-40"
                          }
                          disabled={postingId !== null}
                          onClick={() => void transmit(visit.visit_id)}
                          type="button"
                        >
                          {postingId === visit.visit_id
                            ? "Transmitting…"
                            : refused
                              ? "Review Error & Resubmit"
                              : "Transmit Now"}
                        </button>
                      </div>
                    </article>
                  );
                })}
                {visits !== null && visits.length === 0 && addenda.length === 0 && (
                  <div className="w-full bg-surface-container-lowest p-space-xl rounded-xl shadow-sm flex flex-col gap-space-sm">
                    <h2 className="font-headline-sm text-headline-sm text-primary">
                      The queue is clear
                    </h2>
                    <p className="font-body-md text-body-md text-on-surface-variant">
                      Every close has been accepted. A sent envelope leaves this queue on
                      the next read — nothing here clears by being read.
                    </p>
                  </div>
                )}
                {/* Demo: the confirmed state has no Phase 1 source — receipts are
                    not listed by any endpoint — so the paste's dispatched card
                    holds the layout (see initial/README.md). */}
                <article className="bg-surface-container-lowest rounded-xl p-space-xl shadow-sm flex flex-col gap-space-lg opacity-95">
                  <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-sm">
                    <div className="flex flex-col gap-space-xs">
                      <div className="flex items-center gap-space-sm flex-wrap">
                        <span className="font-data-metric text-data-metric font-semibold text-primary">
                          Envelope #{QUEUE_DEMO.dispatchedCard.envelope}
                        </span>
                        <span className="px-space-sm py-0.5 rounded-full bg-surface-container-high text-on-surface font-label-sm text-label-sm uppercase tracking-wider">
                          FHIR R4 Bundle
                        </span>
                      </div>
                      <h2 className="font-headline-sm text-headline-sm text-primary">
                        {QUEUE_DEMO.dispatchedCard.patient}
                      </h2>
                    </div>
                    <div className="self-start sm:self-auto">
                      <span className="inline-block px-space-md py-space-xs rounded-full bg-surface-container text-on-surface font-label-md text-label-md font-semibold uppercase tracking-wider">
                        Examined / Dispatched
                      </span>
                    </div>
                  </div>
                  <div className="bg-surface-container-low rounded-lg p-space-lg flex flex-col gap-space-sm">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-space-xs text-on-surface font-body-md text-body-md">
                      <span className="">{QUEUE_DEMO.dispatchedCard.sentLine}</span>
                      <span className="font-mono text-label-sm text-on-surface-variant">
                        {QUEUE_DEMO.dispatchedCard.transaction}
                      </span>
                    </div>
                    <p className="font-body-sm text-body-sm text-on-surface-variant">
                      Full synchronization confirmed. Cryptographic acknowledgment stored in
                      persistent local audit ledger. No further practitioner intervention
                      required.
                    </p>
                  </div>
                  <div className="flex items-center justify-between text-on-surface-variant font-label-sm text-label-sm pt-space-xs">
                    <span className="">Final State: Remote Ingestion Verified</span>
                    <span className="">HTTP 200 OK · Payload Archived</span>
                  </div>
                </article>
              </div>
              {addenda.length > 0 && (
                <div className="flex flex-col gap-space-md">
                  <h2 className="font-headline-sm text-headline-sm text-primary">
                    Addenda Queued Behind the Visits ({addenda.length})
                  </h2>
                  {addenda.map((addendum) => (
                    <article
                      className="bg-surface-container-lowest rounded-xl p-space-lg shadow-sm flex flex-col gap-space-xs"
                      key={addendum.addendum_id}
                    >
                      <div className="flex flex-col sm:flex-row sm:items-baseline justify-between gap-space-xs">
                        <span className="font-data-metric text-data-metric font-semibold text-primary">
                          {addendum.addendum_id} · {addendum.patient_name}
                        </span>
                        <span className="font-label-sm text-label-sm text-on-surface-variant">
                          {addendum.written_at}
                        </span>
                      </div>
                      <p className="font-body-md text-body-md text-on-surface" dir="auto">
                        {addendum.text}
                      </p>
                      <p className="font-body-sm text-body-sm text-on-surface-variant">
                        Sent by {addendum.author} · goes with Attempt Dispatch for All
                        Queued — no per-item action.
                        {addendum.refusal !== null && ` · Refused: ${addendum.refusal}`}
                      </p>
                    </article>
                  ))}
                </div>
              )}
              <div className="mt-space-lg bg-surface-container-low rounded-xl p-space-xl flex flex-col gap-space-md">
                <div className="flex flex-col gap-space-xs">
                  <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                    System Safeguards · §5.1 Encrypted Storage Architecture
                  </span>
                  <h3 className="font-headline-sm text-headline-sm text-primary">
                    On-Device Cryptographic Integrity
                  </h3>
                </div>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  All patient encounters, observations, overrides, and interim
                  reconciliations are encrypted utilizing hardware-backed AES-GCM 256 keys
                  prior to write-commit. Data survives physical tablet power cycles, sudden
                  battery depletions, and complete network isolation. In accordance with KSA
                  MoH Clinical Governance, payloads are transmitted exactly once upon
                  clinician verification and are never deleted from local storage until
                  remote cluster confirmation is cryptographically acknowledged.
                </p>
                <div className="pt-space-sm flex flex-col sm:flex-row items-stretch sm:items-center justify-between gap-space-md">
                  <div className="font-label-sm text-label-sm text-on-surface-variant flex items-center gap-space-md">
                    <span className="">{QUEUE_DEMO.storageLine}</span>
                    <span className="text-outline-variant">/</span>
                    <span className="">Engine Status: Quiescent</span>
                  </div>
                  <button
                    className="min-h-[48px] px-space-lg rounded-full bg-surface-container-highest text-on-surface font-label-md text-label-md uppercase tracking-wider hover:bg-surface-container transition-colors active:scale-[0.99] flex items-center justify-center"
                    onClick={() => setToast(QUEUE_DEMO.verifyToast)}
                    type="button"
                  >
                    Verify Cryptographic Signatures
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
