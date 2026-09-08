-- Phase 1's tables. Later tasks append their own. There is no migration story:
-- one file, one process, and deleting the file is the migration (ADR 0006).

create table if not exists patients (
    id                text primary key,
    name              text not null,
    conditions        text not null,  -- json array: "diabetes", "hypertension"
    junior_physician  text not null,  -- §5.13: the Patient's standing Field Team, Noor's
    nurse             text not null   -- own fact, snapshotted onto the Visit at its Start
);

create table if not exists visits (
    id               text primary key,
    patient_id       text not null references patients(id),
    scheduled_for    text not null,  -- iso date; the roster is a query on this column
    reason           text not null,  -- §4.9: why this Visit was scheduled
    state            text not null,  -- lifted out of body, so no query parses json
    body             text not null,  -- serial.dump_visit
    written_back_at  text,           -- null until the EMR accepted it (§4.9)
    last_refused_at  text,           -- §5.1's third status: when the EMR last said no
    last_refusal     text            -- and what it said. Never cleared (§4.10)
);

-- §4.4: one target per Patient, persistent, and the thing every later reading is
-- compared against. Keyed on the Patient and not on the Visit that proposed it —
-- a Visit-keyed row would immediately raise "which one is in force", and the SSOT
-- does not ask that question.
create table if not exists goals (
    patient_id  text primary key references patients(id),
    ratified    integer not null,  -- 0/1, lifted out of body so the refusal is one query
    body        text not null      -- serial.dump_goal
);

-- §5.2: the reads that happen in the office, before the van leaves. Keyed on the
-- Patient for the same reason `goals` is — a prescribed list is a fact about a person,
-- not about the Visit that happened to read it. `subject` is 'prescribed', 'allergies',
-- or 'surveillance:<item id>'.
create table if not exists cached_reads (
    patient_id  text not null references patients(id),
    subject     text not null,
    read_at     text not null,  -- when Noor asked, not when the answer became true
    body        text not null,  -- serial.dump_datum: the three states survive the drive
    primary key (patient_id, subject)
);

-- §5.12, ADR 0009: the Supervisor's answer to one routed item, the only record that
-- removes it from the inbox. Keyed on the item's identity — the Visit, the route, and the
-- subject within it — so a re-answer replaces rather than duplicates.
create table if not exists verdicts (
    visit_id     text not null references visits(id),
    route        integer not null,  -- supervisor.Route's integer, one column, no json
    subject      text not null,     -- a Recommendation id, GOAL_OF_CARE, or SILENT_VISIT
    agreed       integer not null,  -- 0/1
    answered_by  text not null,     -- §5.13: a decision carries a name. `by` is a SQL keyword
    answered_at  text not null,
    note         text,              -- required on a disagreement, enforced by Verdict
    primary key (visit_id, route, subject)
);

-- §6.2, §5.9: the one write a closed Visit accepts. Its own Write-Back columns mirror
-- `visits` so `pending_addenda` derives the queue the same way `pending` does.
create table if not exists addenda (
    id               text primary key,
    visit_id         text not null references visits(id),
    text             text not null,
    author           text not null,  -- §5.13, asked for and not proved (§10)
    written_at       text not null,
    flagged          integer not null default 0,
    written_back_at  text,           -- null until the EMR accepted it
    last_refused_at  text,
    last_refusal     text
);
