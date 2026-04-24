-- Drop the quiz_attempts table
-- No code ever creates QuizAttempt records; the table has been empty since creation.
-- Admin stats now use answered_questions for activity metrics.

DROP TABLE IF EXISTS quiz_attempts;
