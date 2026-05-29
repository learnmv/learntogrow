-- Store machine-verifiable visual math worlds and native diagram scenes.

ALTER TABLE questions
ADD COLUMN IF NOT EXISTS math_world JSONB,
ADD COLUMN IF NOT EXISTS diagram_spec JSONB;

UPDATE question_prompts
SET content = content || E'

MATH SCENE ENGINE SUPPORT:
- If a MATH SCENE CONTRACT is provided, it is mandatory. Do not change its numbers, labels, answer, options, math_world, or diagram_spec.
- Treat math_world as the hidden source of truth and diagram_spec as the visual scene to render.
- The question text should ask naturally about that exact scene without mentioning implementation details.
- Return math_world and diagram_spec exactly as provided in the contract when present.
'
WHERE name IN ('multiple_choice', 'open_ended', 'geogebra_diagram')
  AND content NOT LIKE '%MATH SCENE ENGINE SUPPORT:%';
