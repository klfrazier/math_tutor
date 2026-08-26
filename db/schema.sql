CREATE TABLE IF NOT EXISTS students (
    student_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL UNIQUE,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS sessions (
    session_id        TEXT    PRIMARY KEY,
    student_name      TEXT    NOT NULL,
    standard_code     TEXT    NOT NULL,
    standard_name     TEXT    NOT NULL,
    target_count      INTEGER NOT NULL,
    problems_attempted INTEGER NOT NULL DEFAULT 0,
    problems_correct  INTEGER NOT NULL DEFAULT 0,
    problems_skipped  INTEGER NOT NULL DEFAULT 0,
    accuracy_pct      REAL    NOT NULL DEFAULT 0.0,
    duration_seconds  INTEGER NOT NULL DEFAULT 0,
    started_at        TEXT    NOT NULL,
    completed_at      TEXT,
    prompt_version    TEXT,
    FOREIGN KEY (student_name) REFERENCES students(name)
);

CREATE TABLE IF NOT EXISTS problem_results (
    result_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id         TEXT    NOT NULL,
    standard_code      TEXT    NOT NULL,
    problem_text       TEXT    NOT NULL,
    expected_answer    TEXT    NOT NULL,
    student_answer     TEXT,
    is_correct         INTEGER NOT NULL DEFAULT 0,
    attempts           INTEGER NOT NULL DEFAULT 1,
    skipped            INTEGER NOT NULL DEFAULT 0,
    time_taken_seconds INTEGER,
    created_at         TEXT    NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (session_id) REFERENCES sessions(session_id)
);

CREATE INDEX IF NOT EXISTS idx_sessions_student ON sessions(student_name);
CREATE INDEX IF NOT EXISTS idx_results_session   ON problem_results(session_id);
CREATE INDEX IF NOT EXISTS idx_results_standard  ON problem_results(standard_code);
