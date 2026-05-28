-- Escape literal JSON braces added by migration 019 so Python str.format
-- does not treat the stimulus example as template placeholders.

UPDATE question_prompts
SET content = replace(
    replace(
        replace(
            content,
            E'  "stimulus": {\r\n    "type": "table",',
            E'  "stimulus": {{\r\n    "type": "table",'
        ),
        E'  "stimulus": {\n    "type": "table",',
        E'  "stimulus": {{\n    "type": "table",'
    ),
    E'\r\n  }\r\n- Use 2 to 5 columns and 1 to 8 rows.',
    E'\r\n  }}\r\n- Use 2 to 5 columns and 1 to 8 rows.'
)
WHERE name IN ('multiple_choice', 'open_ended', 'geogebra_diagram')
  AND content LIKE '%STRUCTURED STIMULUS SUPPORT:%';

UPDATE question_prompts
SET content = replace(
    content,
    E'\n  }\n- Use 2 to 5 columns and 1 to 8 rows.',
    E'\n  }}\n- Use 2 to 5 columns and 1 to 8 rows.'
)
WHERE name IN ('multiple_choice', 'open_ended', 'geogebra_diagram')
  AND content LIKE '%STRUCTURED STIMULUS SUPPORT:%';
