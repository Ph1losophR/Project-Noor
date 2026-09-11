"use client";

// Supervisor Inbox — initial throwaway (see initial/README.md). The remote
// review surface: rows derived on read (tiers, ratification, flags, the
// Silence Audit), each answered per item by a Review Verdict — agreeing with a
// target ratifies it instead. Wired where the backend owns it (inbox, verdict,
// goal, ratify, visit detail endpoints); demo where Phase 1 has no source —
// the Supervisor's name (no sign-in), the bedside-context card, search chrome.
import { Suspense, useCallback, useEffect, useMemo, useState } from "react";
import { useSearchParams } from "next/navigation";
import { TAILWIND_CONFIG } from "../../../initial/tailwind-config";
import {
  CLUSTER,
  HEADER_DAY,
  HEADER_TEAM,
  INBOX_DEMO,
  INBOX_SUPERVISOR,
  NAV_COUNTS,
  STATION,
} from "../../../initial/demo-text";

type InboxRow = {
  route: string;
  visit_id: string;
  patient_id: string;
  subject: string;
  due_at: string | null;
  patient_name: string;
  visit_date: string;
};
type InboxPatient = { patient_id: string; patient_name: string; rows: InboxRow[] };
type Rec = {
  id: string;
  text: string;
  tier: string;
  executor: string;
  provenance: string;
  strength: string;
};
type Disposition = {
  recommendation_id: string;
  outcome: string;
  by: string;
  at: string;
  level: string | null;
  reason: { row_id: string; free_text: string | null } | null;
};
type FlagItem = { subject: string; by: string; at: string; note: string };
type VisitDetail = {
  visit_id: string;
  patient_name: string;
  scheduled_reason: string;
  state: string;
  kind: string | null;
  junior_physician: string | null;
  nurse: string | null;
  shown: Rec[];
  dispositions: Disposition[];
  flags: FlagItem[];
};
type Band = { axis: string; floor: number; ceiling: number; rationale: string };
type Goal = {
  patient_id: string;
  bands: Band[];
  lineage: string;
  office_anchor: string;
  proposed_by: string;
  proposed_at: string;
  ratified_by: string | null;
  ratified_at: string | null;
};

const ROUTE_BADGE: Record<string, string> = {
  tier: "Route 1 · Tier Item",
  ratification: "Route 2 · Goal of Care",
  manual_flag: "Route 3 · Manual Flag",
  silence_audit: "Route 4 · Silence Audit",
};

function nowIso(): string {
  return new Date().toISOString();
}

function rowKey(row: InboxRow): string {
  return `${row.visit_id}|${row.route}|${row.subject}`;
}

function tierWord(tier: string): string {
  return `Tier ${tier.replace("tier_", "")}`;
}

function dueText(dueAt: string | null, route: string): string {
  if (dueAt === null)
    return route === "silence_audit" ? "Sampling rate — no deadline" : "Due now";
  const ms = new Date(dueAt).getTime() - Date.now();
  if (Math.abs(ms) < 3600000) return ms < 0 ? "Overdue — answers late" : "Due within the hour";
  const absDays = Math.floor(Math.abs(ms) / 86400000);
  const absHours = Math.floor(Math.abs(ms) / 3600000);
  const span = absDays >= 1 ? `${absDays} day${absDays === 1 ? "" : "s"}` : `${absHours} hour${absHours === 1 ? "" : "s"}`;
  return ms < 0 ? `Overdue by ${span}` : `Due in ${span}`;
}

function isOverdue(dueAt: string | null, route: string): boolean {
  if (dueAt === null) return route !== "silence_audit";
  return new Date(dueAt).getTime() < Date.now();
}

export default function InboxView() {
  return (
    <Suspense fallback={<div className="min-h-screen bg-surface" />}>
      <InboxBody />
    </Suspense>
  );
}

function InboxBody() {
  const search = useSearchParams();
  const week = search.get("week") ?? undefined;

  const [patients, setPatients] = useState<InboxPatient[] | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [details, setDetails] = useState<Record<string, VisitDetail>>({});
  const [goals, setGoals] = useState<Record<string, Goal>>({});
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [routeFilter, setRouteFilter] = useState("all");
  const [choice, setChoice] = useState<"agree" | "disagree" | null>(null);
  const [note, setNote] = useState("");
  const [posting, setPosting] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [actionDone, setActionDone] = useState<string | null>(null);

  const refresh = useCallback(async () => {
    const url = week === undefined ? "/api/inbox" : `/api/inbox?week=${week}`;
    const r = await fetch(url);
    if (!r.ok) throw new Error(`inbox HTTP ${r.status}`);
    const body = (await r.json()) as { patients: InboxPatient[] };
    setPatients(body.patients);
    const rows = body.patients.flatMap((p) => p.rows);
    const missing = rows
      .map((row) => row.visit_id)
      .filter((id, i, all) => all.indexOf(id) === i);
    const fetched: Record<string, VisitDetail> = {};
    await Promise.all(
      missing.map(async (id) => {
        const d = await fetch(`/api/visits/${id}`);
        if (d.ok) fetched[id] = (await d.json()) as VisitDetail;
      }),
    );
    setDetails((prev) => ({ ...prev, ...fetched }));
    return rows;
  }, [week]);

  useEffect(() => {
    let live = true;
    setLoadError(null);
    refresh()
      .then((rows) => {
        if (live && selected === null && rows.length > 0) setSelected(rowKey(rows[0]));
      })
      .catch(() => {
        if (live) {
          setPatients(null);
          setLoadError("The inbox could not be read.");
        }
      });
    return () => {
      live = false;
    };
  }, [refresh]);

  const flat = useMemo(
    () => (patients ?? []).flatMap((p) => p.rows),
    [patients],
  );
  const visible = flat.filter(
    (row) =>
      (routeFilter === "all" || row.route === routeFilter) &&
      (query.trim() === "" ||
        `${row.patient_name} ${row.subject} ${row.visit_id}`
          .toLowerCase()
          .includes(query.trim().toLowerCase())),
  );
  const current =
    visible.find((row) => rowKey(row) === selected) ?? visible[0] ?? null;
  const detail = current === null ? undefined : details[current.visit_id];

  useEffect(() => {
    if (current?.route !== "ratification" || current === null) return;
    if (goals[current.patient_id] !== undefined) return;
    let live = true;
    fetch(`/api/patients/${current.patient_id}/goal`)
      .then((r) => (r.ok ? r.json() : null))
      .then((body) => {
        if (live && body !== null) {
          const goal = body as Goal;
          setGoals((prev) => ({ ...prev, [goal.patient_id]: goal }));
        }
      })
      .catch(() => undefined);
    return () => {
      live = false;
    };
  }, [current, goals]);

  const goal = current === null ? undefined : goals[current.patient_id];
  const rec =
    current?.route === "tier" || current?.route === "manual_flag"
      ? detail?.shown.find((s) => s.id === current.subject)
      : undefined;
  const disposition = rec
    ? detail?.dispositions.find((d) => d.recommendation_id === rec.id)
    : undefined;
  const flag =
    current?.route === "manual_flag"
      ? detail?.flags.find((f) => f.subject === current.subject)
      : undefined;

  function rowSubtitle(row: InboxRow): string {
    if (row.route === "ratification") return "Baseline Visit · Target Proposal";
    if (row.route === "silence_audit")
      return "Completed Visit with 0 recommendations";
    if (row.route === "manual_flag") {
      const f = details[row.visit_id]?.flags.find((x) => x.subject === row.subject);
      return f?.note ?? row.subject;
    }
    const s = details[row.visit_id]?.shown.find((x) => x.id === row.subject);
    return s?.text ?? row.subject;
  }

  async function answer(agreed: boolean) {
    if (current === null || posting) return;
    setPosting(true);
    setActionError(null);
    setActionDone(null);
    if (agreed && current.route === "ratification") {
      const r = await fetch(`/api/patients/${current.patient_id}/goal/ratify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ by: INBOX_SUPERVISOR, at: nowIso() }),
      });
      setPosting(false);
      if (!r.ok) {
        const body = (await r.json()) as { detail?: string };
        setActionError(body.detail ?? "The ratification was refused.");
        return;
      }
      setGoals((prev) => {
        const next = { ...prev };
        delete next[current.patient_id];
        return next;
      });
      setActionDone("Target ratified — the row leaves the inbox on this read.");
    } else {
      const r = await fetch("/api/inbox/verdict", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          visit_id: current.visit_id,
          route: current.route,
          subject: current.subject,
          agreed,
          by: INBOX_SUPERVISOR,
          at: nowIso(),
          note: note.trim() === "" ? null : note.trim(),
        }),
      });
      setPosting(false);
      if (!r.ok) {
        const body = (await r.json()) as { detail?: string };
        setActionError(body.detail ?? "The verdict was refused.");
        return;
      }
      const body = (await r.json()) as { closed?: boolean };
      setActionDone(
        body.closed === false
          ? "Disagreement recorded — the target question stays open, correctly."
          : "Verdict recorded — the row leaves the inbox on this read.",
      );
    }
    setChoice(null);
    setNote("");
    try {
      const rows = await refresh();
      setSelected((prev) =>
        rows.some((row) => rowKey(row) === prev)
          ? prev
          : rows.length > 0
            ? rowKey(rows[0])
            : null,
      );
    } catch {
      setLoadError("Answered, but the inbox could not be re-read.");
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
      <div className="w-full max-w-[1280px] min-h-screen flex flex-col bg-surface shadow-[0_4px_20px_rgba(40,35,28,0.04)]">
        <header className="fixed top-0 w-full max-w-[1280px] z-50 bg-surface/95 shadow-[0_1px_8px_rgba(0,0,0,0.04)]">
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
              aria-current="page"
              className="min-h-[48px] px-space-lg flex items-center justify-center gap-space-sm uppercase tracking-wider transition-colors whitespace-nowrap bg-primary text-on-primary font-semibold rounded-full font-label-md text-label-md"
              data-path="supervisor-inbox"
              href="#"
            >
              <span className="">SUPERVISOR INBOX</span>
              <span className="px-1.5 py-0.5 rounded-full text-label-sm bg-surface-container-highest text-on-surface font-semibold">
                {flat.length}
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
            <section className="mb-space-lg flex flex-col gap-space-xs">
              <div className="flex flex-col sm:flex-row sm:items-baseline sm:justify-between gap-space-xs">
                <div>
                  <h1 className="font-headline-lg text-headline-lg text-primary tracking-tight mt-space-xs">
                    Supervisor Inbox
                  </h1>
                </div>
                <div className="flex items-center gap-space-md">
                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant">
                    Active Governance Queue
                  </span>
                  <span className="inline-flex items-center px-space-md py-1 rounded-full bg-surface-container-high text-primary font-label-sm text-label-sm">
                    {flat.length} Pending Action{flat.length === 1 ? "" : "s"}
                  </span>
                </div>
              </div>
            </section>
            <section className="mb-space-xl p-space-md bg-surface-container-low rounded-xl border border-outline-variant/30 flex flex-col md:flex-row md:items-center justify-between gap-space-md">
              <div className="flex-1 flex flex-col sm:flex-row sm:items-center gap-space-sm">
                <div className="relative flex-1 max-w-md flex items-center bg-surface rounded-lg border border-outline-variant/40 px-space-md py-1.5 focus-within:border-primary transition-colors">
                  <span className="material-symbols-outlined text-on-surface-variant text-[18px] mr-space-xs">
                    search
                  </span>
                  <input
                    className="w-full bg-transparent border-0 font-body-sm text-body-sm text-on-surface placeholder:text-on-surface-variant focus:outline-none"
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Search patient by name or visit…"
                    type="text"
                    value={query}
                  />
                </div>
                <div className="flex items-center gap-space-xs bg-surface rounded-lg border border-outline-variant/40 px-space-md py-1.5 min-w-[200px]">
                  <span className="material-symbols-outlined text-on-surface-variant text-[18px]">
                    filter_list
                  </span>
                  <select
                    className="w-full bg-transparent border-0 font-body-sm text-body-sm text-on-surface focus:outline-none cursor-pointer pr-1"
                    onChange={(e) => setRouteFilter(e.target.value)}
                    value={routeFilter}
                  >
                    <option value="all">All Routes</option>
                    <option value="tier">Route 1: Tier 1 &amp; Above</option>
                    <option value="ratification">Route 2: Goal Ratification</option>
                    <option value="manual_flag">Route 3: Manual Flag</option>
                    <option value="silence_audit">Route 4: Silence Audit</option>
                  </select>
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
            {actionDone !== null && (
              <div className="w-full bg-surface-container-low p-space-md rounded-lg mb-space-lg">
                <span className="font-body-md text-body-md text-on-surface">{actionDone}</span>
              </div>
            )}
            {patients !== null && flat.length === 0 && (
              <div className="w-full bg-surface-container-lowest p-space-xl rounded-xl shadow-sm flex flex-col gap-space-sm">
                <h2 className="font-headline-sm text-headline-sm text-primary">
                  No items awaiting review
                </h2>
                <p className="font-body-md text-body-md text-on-surface-variant">
                  Every routed item carries a verdict. Nothing here clears by being read —
                  only an answer removes a row.
                </p>
              </div>
            )}
            {current !== null && (
              <div className="grid grid-cols-1 lg:grid-cols-12 gap-space-xl items-start">
                <div className="lg:col-span-4 flex flex-col gap-space-md">
                  <div className="flex items-center justify-between px-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                      Awaiting Verdict ({visible.length})
                    </span>
                    <span className="font-label-sm text-label-sm text-on-surface-variant">
                      Most pressing first
                    </span>
                  </div>
                  {visible.map((row) => {
                    const k = rowKey(row);
                    const isCurrent = current !== null && k === rowKey(current);
                    return (
                      <button
                        className={
                          isCurrent
                            ? "p-space-lg rounded-xl bg-surface-container-lowest shadow-sm flex flex-col gap-space-sm cursor-pointer transition-all border border-primary/10 text-left"
                            : "p-space-lg rounded-xl bg-surface-container-low hover:bg-surface-container transition-colors flex flex-col gap-space-sm cursor-pointer text-left"
                        }
                        key={k}
                        onClick={() => {
                          setSelected(k);
                          setChoice(null);
                          setNote("");
                          setActionError(null);
                          setActionDone(null);
                        }}
                        type="button"
                      >
                        <div className="flex items-center justify-between">
                          <span
                            className={
                              isCurrent
                                ? "inline-flex items-center px-space-sm py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider text-secondary bg-secondary-container/30"
                                : "inline-flex items-center px-space-sm py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant bg-surface-container-high"
                            }
                          >
                            {ROUTE_BADGE[row.route] ?? row.route}
                          </span>
                          <span
                            className={
                              isOverdue(row.due_at, row.route)
                                ? "font-label-sm text-label-sm text-status-now font-semibold"
                                : "font-label-sm text-label-sm text-on-surface-variant font-medium"
                            }
                          >
                            {dueText(row.due_at, row.route)}
                          </span>
                        </div>
                        <div>
                          <h2 className="font-headline-sm text-headline-sm text-primary">
                            {row.patient_name}
                          </h2>
                          <p
                            className="font-body-sm text-body-sm text-on-surface-variant mt-0.5"
                            dir="auto"
                          >
                            {rowSubtitle(row)}
                          </p>
                        </div>
                        <div className="mt-space-xs pt-space-xs flex items-center justify-between font-label-sm text-label-sm text-on-surface-variant">
                          <span className="">Visit {row.visit_date}</span>
                          <span
                            className={
                              isCurrent
                                ? "font-semibold text-primary"
                                : "font-label-sm text-label-sm uppercase text-secondary"
                            }
                          >
                            {isCurrent ? "Selected for Action" : "Awaiting Review"}
                          </span>
                        </div>
                      </button>
                    );
                  })}
                </div>
                <div className="lg:col-span-8 flex flex-col gap-space-lg">
                  <div className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm flex flex-col gap-space-md">
                    <div className="flex flex-wrap items-center justify-between gap-space-sm">
                      <div className="flex items-center gap-space-sm">
                        <span className="inline-flex items-center px-space-sm py-0.5 rounded-full font-label-sm text-label-sm uppercase tracking-wider text-secondary bg-secondary-container/40">
                          {ROUTE_BADGE[current.route] ?? current.route} Evaluation
                        </span>
                        <span className="font-label-sm text-label-sm text-on-surface-variant">
                          Visit date: {current.visit_date}
                        </span>
                      </div>
                      <span
                        className={
                          isOverdue(current.due_at, current.route)
                            ? "font-label-sm text-label-sm uppercase tracking-wider text-status-now font-semibold"
                            : "font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant"
                        }
                      >
                        {current.due_at === null
                          ? "Window: none — answer when read"
                          : `Window: ${dueText(current.due_at, current.route)}`}
                      </span>
                    </div>
                    <div>
                      <h2 className="font-headline-lg text-headline-lg text-primary tracking-tight">
                        {current.patient_name}
                      </h2>
                      <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                        {detail === undefined
                          ? "…"
                          : `${detail.kind === "baseline" ? "Baseline" : "Routine"} Visit · ${detail.state.replace("_", " ")} · ${detail.scheduled_reason}`}
                      </p>
                    </div>
                    <div className="p-space-md bg-surface-container-low rounded-lg flex flex-col sm:flex-row sm:items-center justify-between gap-space-sm text-on-surface">
                      <div>
                        <span className="block font-label-sm text-label-sm uppercase text-on-surface-variant font-semibold">
                          Originating Bedside Physician
                        </span>
                        <span className="font-body-md text-body-md text-primary font-medium">
                          {detail?.junior_physician ?? "…"}
                        </span>
                      </div>
                      <div className="sm:text-right">
                        <span className="block font-label-sm text-label-sm uppercase text-on-surface-variant font-semibold">
                          Assigned Oversight Consultant
                        </span>
                        <span className="font-body-md text-body-md text-primary font-medium">
                          {INBOX_SUPERVISOR}
                        </span>
                      </div>
                    </div>
                  </div>
                  {current.route === "ratification" && (
                    <div className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm flex flex-col gap-space-lg">
                      <div>
                        <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                          Proposed Clinical Targets
                        </span>
                        <h3 className="font-headline-sm text-headline-sm text-primary mt-space-xs">
                          Physiological Control Bands
                        </h3>
                      </div>
                      {goal === undefined && (
                        <p className="font-body-md text-body-md text-on-surface-variant">
                          Reading the proposed target…
                        </p>
                      )}
                      {goal !== undefined && (
                        <>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-space-md">
                            {goal.bands.map((band) => (
                              <div
                                className="p-space-lg rounded-xl bg-surface-container-low flex flex-col justify-between gap-space-md"
                                key={band.axis}
                              >
                                <div>
                                  <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                                    {band.axis}
                                  </span>
                                  <div className="font-data-display text-data-display text-primary mt-space-sm tabular-nums">
                                    {band.floor}–{band.ceiling}
                                  </div>
                                </div>
                                <div className="pt-space-sm flex flex-col gap-1">
                                  <span className="font-label-sm text-label-sm text-on-surface-variant uppercase tracking-wider">
                                    Why this band
                                  </span>
                                  <p
                                    className="font-body-sm text-body-sm text-on-surface"
                                    dir="auto"
                                  >
                                    {band.rationale}
                                  </p>
                                </div>
                              </div>
                            ))}
                          </div>
                          <div className="p-space-lg rounded-xl bg-surface-container-low flex flex-col gap-space-xs">
                            <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                              Lineage — what the number stands on (N5)
                            </span>
                            <p className="font-body-md text-body-md text-on-surface mt-1" dir="auto">
                              {goal.lineage}
                            </p>
                            <p className="font-body-sm text-body-sm text-on-surface-variant" dir="auto">
                              Office anchor: {goal.office_anchor} · Proposed by{" "}
                              {goal.proposed_by}
                            </p>
                          </div>
                        </>
                      )}
                    </div>
                  )}
                  {(current.route === "tier" || current.route === "manual_flag") && (
                    <div className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm flex flex-col gap-space-lg">
                      <div>
                        <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                          {current.route === "tier" ? "Routed Recommendation" : "Flagged Item"}
                        </span>
                        <h3 className="font-headline-sm text-headline-sm text-primary mt-space-xs" dir="auto">
                          {rec?.text ?? current.subject}
                        </h3>
                      </div>
                      {rec !== undefined && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-space-md">
                          <div className="p-space-md rounded-lg bg-surface-container-low flex flex-col gap-1">
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                              Tier
                            </span>
                            <span className="font-data-metric text-data-metric text-primary">
                              {tierWord(rec.tier)}
                            </span>
                          </div>
                          <div className="p-space-md rounded-lg bg-surface-container-low flex flex-col gap-1">
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                              Executor
                            </span>
                            <span className="font-body-md text-body-md text-on-surface" dir="auto">
                              {rec.executor}
                            </span>
                          </div>
                          <div className="p-space-md rounded-lg bg-surface-container-low flex flex-col gap-1">
                            <span className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold">
                              Strength
                            </span>
                            <span className="font-body-md text-body-md text-on-surface" dir="auto">
                              {rec.strength}
                            </span>
                          </div>
                        </div>
                      )}
                      {rec !== undefined && (
                        <p className="font-body-sm text-body-sm text-on-surface-variant" dir="auto">
                          Provenance: {rec.provenance}
                        </p>
                      )}
                      {flag !== undefined && (
                        <div className="p-space-lg rounded-xl bg-surface-container-low flex flex-col gap-space-xs">
                          <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                            Why it was sent (§5.11)
                          </span>
                          <p className="font-body-md text-body-md text-on-surface" dir="auto">
                            {flag.note}
                          </p>
                          <p className="font-body-sm text-body-sm text-on-surface-variant">
                            Sent by {flag.by}
                          </p>
                        </div>
                      )}
                      {disposition !== undefined && (
                        <div className="p-space-lg rounded-xl bg-surface-container-low flex flex-col gap-space-xs">
                          <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                            What the Field Team did (N4 — the act stands)
                          </span>
                          <p className="font-body-md text-body-md text-on-surface">
                            {disposition.outcome === "overridden" ? "Overridden" : "Accepted"}{" "}
                            by {disposition.by}
                            {disposition.level !== null &&
                              ` · ${disposition.level.replaceAll("_", " ")}`}
                            {disposition.reason !== null &&
                              ` · ${disposition.reason.row_id.replaceAll("_", " ")}${disposition.reason.free_text ? ` — ${disposition.reason.free_text}` : ""}`}
                          </p>
                        </div>
                      )}
                    </div>
                  )}
                  {current.route === "silence_audit" && (
                    <div className="p-space-xl rounded-xl bg-surface-container-lowest shadow-sm flex flex-col gap-space-md">
                      <div>
                        <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                          Sampled Silence
                        </span>
                        <h3 className="font-headline-sm text-headline-sm text-primary mt-space-xs">
                          Completed Visit with 0 recommendations
                        </h3>
                        <p className="font-body-md text-body-md text-on-surface-variant mt-1">
                          {INBOX_DEMO.auditNote}
                        </p>
                      </div>
                    </div>
                  )}
                  <div className="p-space-xl rounded-xl bg-surface-container-highest shadow-sm flex flex-col gap-space-lg">
                    <div>
                      <div className="flex items-center justify-between">
                        <span className="font-label-sm text-label-sm uppercase tracking-widest text-primary font-semibold">
                          Supervisor Verdict (§5.12 Execution)
                        </span>
                        <span className="font-label-sm text-label-sm text-on-surface-variant">
                          {current.route === "ratification"
                            ? "Agreeing ratifies — disagreeing keeps the question open"
                            : "Action Closes Queue Record"}
                        </span>
                      </div>
                      <h3 className="font-headline-sm text-headline-sm text-primary mt-space-xs">
                        {current.route === "ratification"
                          ? "Ratification Decision"
                          : "Review Decision"}
                      </h3>
                    </div>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-space-md">
                      <button
                        className={
                          choice === "agree"
                            ? "min-h-[48px] px-space-xl py-space-sm rounded-full bg-primary text-on-primary font-label-lg text-label-lg tracking-wide uppercase flex items-center justify-center ring-2 ring-primary ring-offset-2 ring-offset-surface-container-highest"
                            : "min-h-[48px] px-space-xl py-space-sm rounded-full bg-primary text-on-primary font-label-lg text-label-lg tracking-wide uppercase flex items-center justify-center transition-transform active:scale-[0.98]"
                        }
                        onClick={() => setChoice("agree")}
                        type="button"
                      >
                        {current.route === "ratification" ? "Agree & Ratify" : "Agree & Sign Off"}
                      </button>
                      <button
                        className={
                          choice === "disagree"
                            ? "min-h-[48px] px-space-xl py-space-sm rounded-full bg-surface-container text-on-surface font-label-lg text-label-lg tracking-wide uppercase flex items-center justify-center ring-2 ring-primary ring-offset-2 ring-offset-surface-container-highest"
                            : "min-h-[48px] px-space-xl py-space-sm rounded-full bg-surface-container text-on-surface font-label-lg text-label-lg tracking-wide uppercase flex items-center justify-center hover:bg-surface-container-high transition-colors"
                        }
                        onClick={() => setChoice("disagree")}
                        type="button"
                      >
                        Disagree / Return with Comment
                      </button>
                    </div>
                    <div className="flex flex-col gap-space-xs">
                      <div className="flex items-center justify-between">
                        <label
                          className="font-label-sm text-label-sm uppercase tracking-wider text-on-surface-variant font-semibold"
                          htmlFor="supervisor-notes"
                        >
                          Supervisory Rationale &amp; Clinical Note
                        </label>
                        <span className="font-label-sm text-label-sm text-on-surface-variant">
                          Mandatory on Disagreement
                        </span>
                      </div>
                      <div className="p-space-md bg-surface-container-lowest rounded-lg">
                        <textarea
                          className="w-full bg-transparent border-0 resize-none font-body-md text-body-md text-on-surface focus:outline-none placeholder:text-on-surface-variant/60"
                          dir="auto"
                          id="supervisor-notes"
                          onChange={(e) => setNote(e.target.value)}
                          placeholder="Enter clinical rationale…"
                          rows={3}
                          value={note}
                        ></textarea>
                      </div>
                    </div>
                    <button
                      className="min-h-[48px] px-space-xl rounded-full bg-primary text-on-primary font-label-md text-label-md uppercase font-semibold disabled:opacity-40"
                      disabled={
                        posting ||
                        choice === null ||
                        (choice === "disagree" && note.trim() === "")
                      }
                      onClick={() => void answer(choice === "agree")}
                      type="button"
                    >
                      {posting
                        ? "Recording…"
                        : choice === "disagree"
                          ? "Record Disagreement"
                          : current.route === "ratification"
                            ? "Record Ratification"
                            : "Record Agreement"}
                    </button>
                    <div className="pt-space-md flex flex-col sm:flex-row sm:items-center justify-between gap-space-md font-label-sm text-label-sm text-on-surface-variant">
                      <div>
                        <span className="block font-semibold text-primary">{INBOX_SUPERVISOR}</span>
                        <span className="block text-on-surface-variant">
                          {INBOX_DEMO.consultantRole}
                        </span>
                        <span className="block font-mono text-[11px] mt-0.5">
                          {INBOX_DEMO.consultantLicence}
                        </span>
                      </div>
                      <div className="sm:text-right">
                        <span className="block text-on-surface-variant">Digital Sign-off Timestamp</span>
                        <span className="block font-semibold text-primary">
                          Pending Supervisor Dispatch
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="p-space-lg rounded-xl bg-surface-container-low flex flex-col gap-space-xs">
                    <span className="font-label-sm text-label-sm uppercase tracking-widest text-on-surface-variant font-semibold">
                      Bedside Context &amp; Household Competence
                    </span>
                    <p className="font-body-md text-body-md text-on-surface mt-1">
                      {INBOX_DEMO.contextParagraph}
                    </p>
                    <div className="flex flex-wrap gap-space-md mt-space-sm pt-space-sm font-label-sm text-label-sm text-on-surface-variant">
                      {INBOX_DEMO.contextChips.map((chip, i) => (
                        <span key={chip}>
                          {chip}
                          {i < INBOX_DEMO.contextChips.length - 1 && <span className=""> · </span>}
                        </span>
                      ))}
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
