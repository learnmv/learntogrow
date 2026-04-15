"""
Prompt templates for question generation.
Database is the source of truth; this module falls back to text files in prompts/ if DB entry missing.
"""

from enum import Enum
from functools import lru_cache
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from app.models import GeoGebra, QuestionPrompt

PROMPTS_DIR = Path(__file__).parent / "prompts"


class AppletType(str, Enum):
    """GeoGebra applet types."""
    GRAPHING = "graphing"
    GEOMETRY = "geometry"
    THREE_D = "3d"
    CLASSIC = "classic"
    CAS = "cas"
    SCIENTIFIC = "scientific"


# Default applet type
DEFAULT_APPLET_TYPE = AppletType.GRAPHING


def load_prompt_template(db: Session, question_type: str) -> str:
    """Load prompt template from database, fallback to file.

    Args:
        db: Database session
        question_type: The type of question (multiple_choice, open_ended, geogebra_diagram, etc.)

    Returns:
        The prompt template string
    """
    # Try database first
    prompt = db.query(QuestionPrompt).filter(QuestionPrompt.name == question_type).first()
    if prompt:
        return prompt.content

    # Fallback to file
    template_file = PROMPTS_DIR / f"{question_type}.txt"
    if not template_file.exists():
        template_file = PROMPTS_DIR / "open_ended.txt"
    return template_file.read_text()


# Keep cached version for backward compatibility with non-db contexts
@lru_cache(maxsize=10)
def load_prompt_template_cached(question_type: str) -> str:
    """Load prompt template from text file (cached, no database).

    Used as fallback when database is not available.

    Args:
        question_type: The type of question (multiple_choice, open_ended, geogebra_diagram, etc.)

    Returns:
        The prompt template string from the text file
    """
    template_file = PROMPTS_DIR / f"{question_type}.txt"
    if not template_file.exists():
        template_file = PROMPTS_DIR / "open_ended.txt"
    return template_file.read_text()


# Applet-specific command references for LLM context
APPLET_COMMANDS = {
    "graphing": """
- Points: A = (1, 2), Point(circle), Midpoint(A, B)
- Lines: Line(A, B), Segment(A, B), Ray(A, B)
- Functions: f(x) = x^2, g: y = 2x + 1
- Circles: Circle(A, 3), Circle(A, B)
- Polygons: Polygon(A, B, C), Triangle(A, B, C)
- Measurements: Distance(A, B), Area(polygon), Slope(line)
- Styling: SetColor(A, 255, 0, 0), SetPointSize(A, 5), SetLineThickness(f, 3), SetFixed(A, true, false)
- View: SetCoordSystem(-10, 10, -5, 5), SetAxesVisible(true, true), SetGridVisible(true)""",

    "geometry": """
- Points: A = (1, 2), Point(circle), Midpoint(A, B), Center(circle)
- Lines: Line(A, B), Segment(A, B), Ray(A, B), Vector(A, B)
- Special Lines: PerpendicularLine(A, line), ParallelLine(A, line), PerpendicularBisector(A, B)
- Circles: Circle(A, 3), Circle(A, B), Circumcircle(A, B, C), Incircle(A, B, C)
- Polygons: Polygon(A, B, C, D), Triangle(A, B, C), Quadrilateral(A, B, C, D), RegularPolygon(A, B, 5)
- Angles: Angle(A, B, C), PerpendicularBisector(A, B)
- Transformations: Reflect(A, line), Rotate(A, angle, center), Translate(A, vector), Dilate(A, factor, center)
- Styling: SetColor(A, 255, 0, 0), SetPointSize(A, 5), SetFixed(A, true, false), SetVisible(A, false)""",

    "3d": """
- Points: A = (1, 2, 3), Point(plane), Midpoint(A, B), Center(sphere)
- Lines: Line(A, B), Segment(A, B)
- Planes: Plane(A, B, C), Plane(A, line), PerpendicularPlane(A, line)
- Solids: Sphere(A, 3), Cube(A, B), Cone(A, B, 2), Cylinder(A, B, 2), Prism(polygon, height), Pyramid(polygon, height)
- Polyhedra: Tetrahedron(A, B), Octahedron(A, B), Dodecahedron(A, B), Icosahedron(A, B)
- Circles: Circle(A, 3), Circle(A, B, C) (in 3D)
- Curves: Curve(u, u^2, sin(u), u, 0, 10)
- Surfaces: Surface(u*cos(v), u*sin(v), v, u, 0, 5, v, 0, 2*pi)
- Measurements: Volume(solid), Area(surface), Distance(A, B)
- Styling: SetColor(A, 255, 0, 0), SetFixed(A, true, false), SetVisible(A, false)
- View: SetCoordSystem(-5, 5, -5, 5, -5, 5, true)""",

    "classic": """
- All commands from graphing, geometry, and 3d applets are available
- CAS: Solve[equation], Derivative[function], Integral[function]
- Advanced: Tangent(function, point), Root(function), Extremum(function)""",

    "cas": """
- Primarily symbolic mathematics, limited geometry commands
- Functions: f(x) = x^2, g(x) = sin(x)
- CAS: Solve[equation], NSolve[equation], Derivative[function], Integral[function]
- Analysis: Tangent(function, point), Root(function), Extremum(function), InflectionPoint(function)""",

    "scientific": """
- Basic calculator functions only
- Limited geometry support
- Functions: f(x) = x^2, g(x) = sin(x)
- Basic: Point(A, B), Line(A, B), Circle(A, r)"""
}


def get_applet_commands(db: Session, applet_type: AppletType) -> str:
    """Get available commands for a specific applet type from database.

    Args:
        db: Database session
        applet_type: The GeoGebra applet type

    Returns:
        String listing available commands for that applet
    """
    geogebra = db.query(GeoGebra).filter(GeoGebra.applet_type == applet_type.value).first()
    if geogebra and geogebra.valid_command_template:
        # Convert array to formatted string with dashes
        return "\n".join(f"- {cmd}" for cmd in geogebra.valid_command_template)
    # Fallback to empty string if not found
    return ""


# Deprecated: Kept for backward compatibility until all code is migrated
# Use get_applet_commands(db, applet_type) instead
@lru_cache(maxsize=16)
def _get_applet_commands_cached(applet_type: AppletType) -> str:
    """Cached version for non-DB contexts (deprecated)."""
    return APPLET_COMMANDS.get(applet_type.value, APPLET_COMMANDS[DEFAULT_APPLET_TYPE.value])


def _get_answer_field(question_type: str) -> str:
    """Get the answer field JSON snippet based on question type."""
    if question_type == "multiple_choice":
        return '"options": ["option A", "option B", "option C", "option D"],\n    "answer": "the correct option text",'
    return '"answer": "the correct answer",'


def _get_question_requirements(question_type: str) -> str:
    """Get question-specific requirements text."""
    if question_type == "multiple_choice":
        return "- Provide exactly 4 multiple choice options (A, B, C, D)\n- Only one option should be correct\n- Distractors should be plausible but clearly wrong"
    return ""


def format_prompt(
    db: Session,
    question_type: str,
    grade_level: str,
    standard_code: str,
    standard_description: str,
    difficulty: float,
    keywords: str,
    requires_diagram: bool = False,
    applet_type: Optional[AppletType] = None,
) -> str:
    """Format a prompt template with the given parameters.

    Args:
        db: Database session
        question_type: Type of question (multiple_choice, open_ended, geogebra_diagram)
        grade_level: The grade level (e.g., "6", "7", "8")
        standard_code: Standard code (e.g., "6.EE.A.1")
        standard_description: Description of the standard
        difficulty: Difficulty level 0.0-1.0
        keywords: Comma-separated keywords
        requires_diagram: Whether this question needs a GeoGebra diagram
        applet_type: GeoGebra applet type if requires_diagram is True

    Returns:
        Formatted prompt string ready for LLM
    """
    # Pre-compute formatted question type (used in both branches)
    formatted_question_type = question_type.replace("_", " ")

    # If requires_diagram, use the geogebra_diagram template
    if requires_diagram and question_type in ["multiple_choice", "open_ended"]:
        template = load_prompt_template(db, "geogebra_diagram")
        applet = applet_type or DEFAULT_APPLET_TYPE
        applet_commands = get_applet_commands(db, applet)

        return template.format(
            question_type=formatted_question_type,
            grade_level=grade_level,
            standard_code=standard_code,
            standard_description=standard_description,
            difficulty=difficulty,
            keywords=keywords,
            applet_type=applet.value,
            applet_commands=applet_commands,
            question_specific_requirements=_get_question_requirements(question_type),
            answer_field=_get_answer_field(question_type),
        )

    # Standard template for non-diagram questions
    template = load_prompt_template(db, question_type)
    return template.format(
        question_type=formatted_question_type,
        grade_level=grade_level,
        standard_code=standard_code,
        standard_description=standard_description,
        difficulty=difficulty,
        keywords=keywords,
    )


__all__ = [
    'AppletType',
    'DEFAULT_APPLET_TYPE',
    'load_prompt_template',
    'load_prompt_template_cached',
    'get_applet_commands',
    '_get_applet_commands_cached',  # Deprecated
    'format_prompt',
    'APPLET_COMMANDS',  # Deprecated
]
