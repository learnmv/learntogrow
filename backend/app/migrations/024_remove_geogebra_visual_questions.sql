-- Remove GeoGebra and visual-scene question support.
-- The app now generates and serves text-based questions only.

DELETE FROM question_prompts
WHERE name = 'geogebra_diagram';

UPDATE question_prompts
SET content = replace(content, E'\n\nMATH SCENE ENGINE SUPPORT:\n- If a MATH SCENE CONTRACT is provided, it is mandatory. Do not change its numbers, labels, answer, options, math_world, or diagram_spec.\n- Treat math_world as the hidden source of truth and diagram_spec as the visual scene to render.\n- The question text should ask naturally about that exact scene without mentioning implementation details.\n- Return math_world and diagram_spec exactly as provided in the contract when present.\n', '')
WHERE name IN ('multiple_choice', 'open_ended');

UPDATE question_prompts
SET
    content = $prompt$You are planning one curriculum-aligned assessment question.

Return only valid JSON with this shape:
{{
  "skill_focus": "the exact skill to test",
  "grade_language": "language level and vocabulary guidance",
  "misconceptions": ["common student mistake 1", "common student mistake 2", "common student mistake 3"],
  "difficulty_strategy": "how to make this question match the target difficulty"
}}

Context:
- Grade: {grade_level}
- Standard: {standard_code}
- Standard description: {standard_description}
- Target difficulty: {difficulty}
- Keywords: {keywords}
- Question type: {question_type}

Keep the plan specific enough that a generator can produce a complete text-based question without inventing unrelated skills.$prompt$,
    description = 'Plans the target skill, misconceptions, difficulty strategy, and grade language before generation.'
WHERE name = 'question_planner';

UPDATE question_prompts
SET
    content = $prompt$You are reviewing a generated assessment question for quality.

Return only valid JSON with this shape:
{{
  "approved": true,
  "score": 0.0,
  "alignment_score": 0.0,
  "clarity_score": 0.0,
  "answer_score": 0.0,
  "distractor_score": 0.0,
  "explanation_score": 0.0,
  "difficulty_score": 0.0,
  "difficulty_estimate": 0.0,
  "issues": [],
  "improvement_notes": "short notes for an editor"
}}

Review rules:
- The question must directly assess {standard_code}: {standard_description}
- The wording must fit grade {grade_level}.
- The question must be complete and understandable as text.
- For multiple choice, exactly one option must be correct and distractors should reflect plausible misconceptions.
- The explanation must be mathematically/academically correct.
- Target difficulty is {difficulty}; reject if it is far too easy or far too hard.
- If a question includes table data, the table must be represented as stimulus.type = "table"; reject raw markdown tables inside question text.
- If stimulus.type is "table", verify that the columns and rows support the math and are clear for a student.
- Approve only if score is at least {min_review_score} and there are no serious issues.

Question JSON to review:
{question_json}$prompt$,
    description = 'Reviews generated text questions for alignment, clarity, answer validity, distractor quality, explanation quality, and difficulty.'
WHERE name = 'question_reviewer';

UPDATE question_prompts
SET
    content = $prompt$You are repairing a generated assessment question that failed validation or review.

Return only the corrected question JSON. Keep the same JSON shape expected from generation.

Context:
- Grade: {grade_level}
- Standard: {standard_code}
- Standard description: {standard_description}
- Target difficulty: {difficulty}
- Keywords: {keywords}
- Question type: {question_type}

Original question JSON:
{question_json}

Problems to fix:
{issues}

Repair requirements:
- Stay aligned to the standard.
- Preserve grade-appropriate language.
- The question must be complete and understandable as text.
- For multiple choice, provide exactly 4 options and exactly one correct answer.
- Make distractors plausible and based on misconceptions.
- Provide a correct explanation.
- If the original question has a markdown table in question text, move it into a stimulus table object and leave only the prompt sentence in "question".
- Keep table columns and row cell counts consistent.$prompt$,
    description = 'Repairs generated text question JSON using validation/review issues.'
WHERE name = 'question_repair';

ALTER TABLE questions
    DROP COLUMN IF EXISTS math_world,
    DROP COLUMN IF EXISTS diagram_spec,
    DROP COLUMN IF EXISTS requires_diagram,
    DROP COLUMN IF EXISTS applet_type,
    DROP COLUMN IF EXISTS geogebra_commands,
    DROP COLUMN IF EXISTS applet_config;

ALTER TABLE standards
    DROP COLUMN IF EXISTS requires_diagram,
    DROP COLUMN IF EXISTS applet_type;

DROP TABLE IF EXISTS geogebra;
