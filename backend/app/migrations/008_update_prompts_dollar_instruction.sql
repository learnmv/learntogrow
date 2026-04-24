-- Migration: Update prompt templates to avoid ambiguous $ usage in currency amounts
-- The frontend KaTeX renderer pairs $...$ as math delimiters, so using $45 for
-- "45 dollars" causes the renderer to treat everything between currency symbols
-- as a math expression. We instruct the LLM to write "dollars" for currency
-- and only use $...$ for actual math.

UPDATE question_prompts
SET content = $prompt$Generate a {question_type} math question for Grade {grade_level}.

Standard: {standard_code} - {standard_description}
Difficulty: {difficulty:.1f}/1.0 (0=easy, 1=hard)
Key Concepts: {keywords}

CRITICAL REQUIREMENTS:
1. The question MUST be complete with ALL numbers, variables, and values included
2. The question text MUST make sense on its own without any missing information
3. Provide exactly 4 multiple choice options with ACTUAL CONTENT (not just letters)
4. The "answer" field MUST match EXACTLY one of the option texts

EXAMPLES OF WRONG OUTPUTS (DO NOT DO THESE):
- "Evaluate the expression when and ." (missing values)
- ["A", "B", "C", "D"] (empty options)
- ["A) 5", "B) 10", "C) 15", "D) 20"] (duplicate labels in options)

CORRECT EXAMPLES:
- "What is 2 + 3?" (complete question)
- ["5", "10", "15", "20"] (just the values, no labels)
- "answer": "5" (matches one option exactly)

Requirements:
- Create a clear, well-formed question with complete information
- Test understanding of the standard's learning objectives
- Provide the correct answer that exactly matches one option
- Include a brief explanation suitable for a student
- Provide exactly 4 multiple choice options (A, B, C, D) with actual content
- Only one option should be correct
- Distractors should be plausible but clearly wrong
- DO NOT include "A)", "B)", etc. in the option text - just the values
- Use $...$ ONLY for math expressions (e.g. $x + 5 = 10$). Do NOT use $ for currency amounts — write "dollars" instead (e.g. "45 dollars" not "$45")

IMPORTANT: Respond with ONLY the raw JSON object. Do NOT wrap in markdown code blocks (no ```json). Do NOT add any text before or after the JSON.

{{
    "question": "the complete question text with all values included",
    "options": ["first option value", "second option value", "third option value", "fourth option value"],
    "answer": "the correct option value (must match one option exactly)",
    "explanation": "explanation of why this is correct"
}}
$prompt$,
    updated_at = NOW()
WHERE name = 'multiple_choice';

UPDATE question_prompts
SET content = $prompt$Generate a {question_type} math question for Grade {grade_level}.

Standard: {standard_code} - {standard_description}
Difficulty: {difficulty:.1f}/1.0 (0=easy, 1=hard)
Key Concepts: {keywords}

Requirements:
- Create a clear, well-formed question
- Test understanding of the standard's learning objectives
- Provide the correct answer
- Include a brief explanation suitable for a student
- Use $...$ ONLY for math expressions (e.g. $x + 5 = 10$). Do NOT use $ for currency amounts — write "dollars" instead (e.g. "45 dollars" not "$45")

IMPORTANT: Respond with ONLY the raw JSON object. Do NOT wrap in markdown code blocks (no ```json). Do NOT add any text before or after the JSON.

{{
    "question": "the question text",
    "answer": "the correct answer",
    "explanation": "explanation of why this is correct"
}}
$prompt$,
    updated_at = NOW()
WHERE name = 'open_ended';

UPDATE question_prompts
SET content = $prompt$Generate a {question_type} math question for Grade {grade_level} that INCLUDES an interactive GeoGebra diagram.

Standard: {standard_code} - {standard_description}
Difficulty: {difficulty:.1f}/1.0 (0=easy, 1=hard)
Key Concepts: {keywords}
Applet Type: {applet_type}

CRITICAL REQUIREMENTS:
1. The question MUST be complete with ALL values specified
2. You MUST provide GeoGebra commands to create the diagram - this is REQUIRED
3. The question should describe what the diagram shows and what the student should find
4. Answer options should NOT include "A)", "B)" labels - just the values

Requirements:
- Create a clear, well-formed question that requires visual understanding
- The question should reference the GeoGebra diagram
- Provide the correct answer that matches one option exactly
- Include a brief explanation suitable for a student
- Use $...$ ONLY for math expressions (e.g. $x + 5 = 10$). Do NOT use $ for currency amounts — write "dollars" instead (e.g. "45 dollars" not "$45")
{question_specific_requirements}

GEOGEBRA COMMANDS (REQUIRED):
Generate GeoGebra commands to create an appropriate diagram for this question.

Use only from Available commands for {applet_type} applet:
{applet_commands}

Command Guidelines:
- You MUST provide commands to create a visible diagram
- Create objects in logical order (points first, then shapes)

DO NOT leave geogebra_commands empty. The diagram is REQUIRED for this question.

IMPORTANT: Respond with ONLY the raw JSON object. Do NOT wrap in markdown code blocks (no ```json). Do NOT add any text before or after the JSON.

{{
    "question": "the complete question text referencing the diagram",
    {answer_field}
    "explanation": "explanation of why this is correct",
    "geogebra_commands": [
        "command1",
        "command2",
        "command3",
        "command4",
        "command5"
    ],
    "applet_config": {{
        "width": 1000,
        "height": 1000.
        "showToolBar": false,
        "showAlgebraInput": false,
        "showMenuBar": false,
        "showAlgebraView": false
    }}
}}
$prompt$,
    updated_at = NOW()
WHERE name = 'geogebra_diagram';
