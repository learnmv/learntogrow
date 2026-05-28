-- Add structured stimulus support for tables and future rich question context.

ALTER TABLE questions
ADD COLUMN IF NOT EXISTS stimulus JSONB;

UPDATE question_prompts
SET content = content || E'

STRUCTURED STIMULUS SUPPORT:
- If the problem needs a table, chart-like values, or organized data, do NOT put markdown table syntax in the question text.
- Keep "question" as the readable prompt only.
- Put table data in this optional JSON field:
  "stimulus": {{
    "type": "table",
    "columns": ["column 1", "column 2"],
    "rows": [["row 1 col 1", "row 1 col 2"], ["row 2 col 1", "row 2 col 2"]]
  }}
- Use 2 to 5 columns and 1 to 8 rows. Every row must have exactly the same number of cells as columns.
- If no table or stimulus is needed, omit "stimulus" or set it to null.
- Never include markdown separators such as "---|---" in "question".
'
WHERE name IN ('multiple_choice', 'open_ended', 'geogebra_diagram')
  AND content NOT LIKE '%STRUCTURED STIMULUS SUPPORT:%';

UPDATE question_prompts
SET content = content || E'

Stimulus review rule:
- If a question includes table data, the table must be represented as stimulus.type = "table"; reject raw markdown tables inside question text.
- If stimulus.type is "table", verify that the columns and rows support the math and are clear for a student.
'
WHERE name = 'question_reviewer'
  AND content NOT LIKE '%Stimulus review rule:%';

UPDATE question_prompts
SET content = content || E'

Stimulus repair rule:
- If the original question has a markdown table in question text, move it into a stimulus table object and leave only the prompt sentence in "question".
- Keep table columns and row cell counts consistent.
'
WHERE name = 'question_repair'
  AND content NOT LIKE '%Stimulus repair rule:%';
