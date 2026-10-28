-- DEMO FIXTURE for the grill skill evals
CREATE TABLE scores (
  id INTEGER PRIMARY KEY,
  player TEXT NOT NULL,
  points INTEGER NOT NULL,
  played_on DATE NOT NULL,
  legacy_rank INTEGER,
  old_team_code TEXT
);
