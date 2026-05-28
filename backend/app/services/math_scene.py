import json
import random
from copy import deepcopy
from fractions import Fraction
from typing import Any, Optional


def _fmt_number(value: float | int | Fraction) -> str:
    if isinstance(value, Fraction):
        numeric = value.numerator / value.denominator
    else:
        numeric = float(value)
    if abs(numeric - round(numeric)) < 1e-9:
        return str(int(round(numeric)))
    text = f"{numeric:.2f}".rstrip("0").rstrip(".")
    return text


def _dedupe_options(options: list[str], answer: str) -> list[str]:
    result: list[str] = []
    for option in [answer, *options]:
        if option not in result:
            result.append(option)
    filler = 1
    while len(result) < 4:
        try:
            candidate = _fmt_number(float(answer.split()[0]) + filler)
            if "degrees" in answer:
                candidate = f"{candidate} degrees"
        except (ValueError, IndexError):
            candidate = f"Option {filler}"
        if candidate not in result:
            result.append(candidate)
        filler += 1
    return result[:4]


def _finalize_options(rng: random.Random, options: list[str], answer: str) -> list[str]:
    result = _dedupe_options(options, answer)
    rng.shuffle(result)
    return result


class MathSceneEngine:
    """Builds verifiable math worlds and native diagram scenes for visual questions."""

    SUPPORTED_CODES = {"7.NS.1", "7.RP.2", "7.G.5"}

    def supports(self, standard: Any) -> bool:
        return bool(getattr(standard, "requires_diagram", False)) and getattr(standard, "code", "") in self.SUPPORTED_CODES

    def build_scene(self, standard: Any, difficulty: float, attempt_index: int) -> Optional[dict[str, Any]]:
        code = getattr(standard, "code", "")
        seed = f"{getattr(standard, 'id', code)}:{difficulty:.2f}:{attempt_index}:{random.random()}"
        rng = random.Random(seed)
        if code == "7.NS.1":
            return self._number_line_scene(standard, difficulty, attempt_index, rng)
        if code == "7.RP.2":
            return self._proportional_graph_scene(standard, difficulty, attempt_index, rng)
        if code == "7.G.5":
            return self._angle_relationship_scene(standard, difficulty, attempt_index, rng)
        return None

    def compose_prompt(self, base_prompt: str, scene: Optional[dict[str, Any]]) -> str:
        if not scene:
            return base_prompt
        contract = {
            "math_world": scene["math_world"],
            "diagram_spec": scene["diagram_spec"],
            "correct_answer": scene["answer"],
            "options": scene["options"],
            "explanation": scene["explanation"],
            "question_goal": scene["question_goal"],
        }
        return f"""{base_prompt}

MATH SCENE CONTRACT
This contract is mandatory. Build the question around this exact math world.
Do not change numbers, labels, the answer, or the answer options.
Return math_world and diagram_spec exactly as provided here.

{json.dumps(contract, indent=2, default=str)}

SCENE RULES:
- The question text should sound natural for a student.
- Do not mention "math_world", "diagram_spec", "GeoGebra", or implementation details.
- The correct answer field must exactly equal correct_answer.
- The options field must exactly equal the provided options.
- The explanation must use the same math as the provided explanation.
""".strip()

    def apply_to_candidate(self, question_data: dict[str, Any], scene: Optional[dict[str, Any]]) -> dict[str, Any]:
        if not scene:
            return question_data
        result = dict(question_data)
        result["math_world"] = deepcopy(scene["math_world"])
        result["diagram_spec"] = deepcopy(scene["diagram_spec"])
        result["answer"] = scene["answer"]
        result["options"] = list(scene["options"])
        result["explanation"] = scene["explanation"]
        result["geogebra_commands"] = list(scene["geogebra_commands"])
        result["requires_diagram"] = True
        result["applet_type"] = scene["applet_type"]
        return result

    def validate_scene(self, question_data: dict[str, Any]) -> list[str]:
        diagram_spec = question_data.get("diagram_spec")
        math_world = question_data.get("math_world")
        if not diagram_spec and not math_world:
            return []
        if not isinstance(math_world, dict):
            return ["math_world must be an object when diagram_spec is present"]
        if not isinstance(diagram_spec, dict):
            return ["diagram_spec must be an object when math_world is present"]

        scene_type = diagram_spec.get("type")
        errors: list[str] = []
        if scene_type == "number_line":
            errors.extend(self._validate_number_line(math_world, diagram_spec))
        elif scene_type == "coordinate_graph":
            errors.extend(self._validate_coordinate_graph(math_world, diagram_spec))
        elif scene_type == "angle_relationship":
            errors.extend(self._validate_angle_relationship(math_world, diagram_spec))
        else:
            errors.append(f"Unsupported diagram_spec type: {scene_type!r}")

        expected_answer = math_world.get("answer")
        if expected_answer and question_data.get("answer") != expected_answer:
            errors.append("Question answer does not match math_world answer")
        return errors

    def scene_to_text(self, value: Any) -> str:
        if not isinstance(value, dict):
            return ""
        return json.dumps(value, sort_keys=True, default=str)

    def _number_line_scene(self, standard: Any, difficulty: float, attempt_index: int, rng: random.Random) -> dict[str, Any]:
        denominators = [2, 4] if difficulty < 0.75 else [4, 5, 8]
        denominator = rng.choice(denominators)
        start = Fraction(rng.randint(-24, 12), denominator)
        change = Fraction(rng.choice([-1, 1]) * rng.randint(5, 18), denominator)
        end = start + change
        operation = "addition" if change >= 0 else "subtraction"
        answer = _fmt_number(end)
        wrong_sign = _fmt_number(start - change)
        wrong_start = _fmt_number(change)
        wrong_abs = _fmt_number(abs(end))
        options = _finalize_options(rng, [wrong_sign, wrong_start, wrong_abs], answer)
        min_value = min(float(start), float(end), 0) - 1
        max_value = max(float(start), float(end), 0) + 1
        start_text = _fmt_number(start)
        change_text = _fmt_number(change)
        end_text = _fmt_number(end)
        return {
            "question_goal": (
                f"Ask the student to use the number line to find the final value after starting at "
                f"{start_text} and changing by {change_text}."
            ),
            "answer": answer,
            "options": options,
            "explanation": (
                f"Start at {start_text}. A change of {change_text} moves to {end_text}, "
                f"so the final value is {answer}."
            ),
            "applet_type": "graphing",
            "geogebra_commands": [
                f"A = ({_fmt_number(start)}, 0)",
                f"B = ({_fmt_number(end)}, 0)",
                f"Segment(({_fmt_number(min_value)}, 0), ({_fmt_number(max_value)}, 0))",
                "y = 0",
            ],
            "math_world": {
                "type": "number_line_operation",
                "standard_code": standard.code,
                "operation": operation,
                "start": _fmt_number(start),
                "change": _fmt_number(change),
                "end": answer,
                "answer": answer,
            },
            "diagram_spec": {
                "type": "number_line",
                "min": _fmt_number(min_value),
                "max": _fmt_number(max_value),
                "ticks": 1,
                "points": [
                    {"id": "start", "value": _fmt_number(start), "label": "Start"},
                    {"id": "end", "value": answer, "label": "End"},
                ],
                "arrows": [
                    {"from": _fmt_number(start), "to": answer, "label": change_text},
                ],
            },
        }

    def _proportional_graph_scene(self, standard: Any, difficulty: float, attempt_index: int, rng: random.Random) -> dict[str, Any]:
        rate = rng.choice([2, 3, 4, 5, 6, 8])
        target_x = rng.choice([3, 4, 5, 6, 7])
        target_y = rate * target_x
        points = [[1, rate], [2, 2 * rate], [target_x, target_y]]
        answer = f"{target_y}"
        options = _finalize_options(rng, [str(target_y + rate), str(target_y - rate), str(target_x + rate)], answer)
        return {
            "question_goal": (
                f"Ask the student to use the proportional graph with constant of proportionality "
                f"{rate} to find y when x = {target_x}."
            ),
            "answer": answer,
            "options": options,
            "explanation": (
                f"The graph represents y = {rate}x. When x = {target_x}, "
                f"y = {rate} x {target_x} = {target_y}."
            ),
            "applet_type": "graphing",
            "geogebra_commands": [
                f"f(x) = {rate} * x",
                *(f"P{index + 1} = ({x}, {y})" for index, (x, y) in enumerate(points)),
            ],
            "math_world": {
                "type": "proportional_relationship",
                "standard_code": standard.code,
                "equation": f"y = {rate}x",
                "constant_of_proportionality": rate,
                "target_x": target_x,
                "target_y": target_y,
                "answer": answer,
            },
            "diagram_spec": {
                "type": "coordinate_graph",
                "x_axis": "x",
                "y_axis": "y",
                "x_max": max(8, target_x + 1),
                "y_max": max(30, target_y + rate),
                "line": {"slope": rate, "intercept": 0, "label": f"y = {rate}x"},
                "points": [
                    {"x": x, "y": y, "label": f"({x}, {y})"} for x, y in points
                ],
                "highlight": {"x": target_x, "y": target_y, "label": "Target"},
            },
        }

    def _angle_relationship_scene(self, standard: Any, difficulty: float, attempt_index: int, rng: random.Random) -> dict[str, Any]:
        x_value = rng.choice([8, 10, 12, 14, 15, 18])
        angle = rng.choice([55, 62, 68, 73, 80])
        a = rng.choice([3, 4, 5])
        c = a + rng.choice([1, 2, 3])
        b = angle - a * x_value
        d = angle - c * x_value
        expr_a = f"{a}x {'+' if b >= 0 else '-'} {abs(b)}"
        expr_b = f"{c}x {'+' if d >= 0 else '-'} {abs(d)}"
        answer = f"{angle} degrees"
        options = _finalize_options(
            rng,
            [f"{angle + 10} degrees", f"{180 - angle} degrees", f"{x_value} degrees"],
            answer,
        )
        return {
            "question_goal": (
                f"Ask the student to solve vertical angles labeled {expr_a} and {expr_b}, "
                f"then find the angle measure."
            ),
            "answer": answer,
            "options": options,
            "explanation": (
                f"Vertical angles are equal, so {expr_a} = {expr_b}. Solving gives x = {x_value}. "
                f"Substituting gives an angle measure of {angle} degrees."
            ),
            "applet_type": "geometry",
            "geogebra_commands": [
                "Line((-3, -2), (3, 2))",
                "Line((-3, 2), (3, -2))",
                "A = (0, 0)",
            ],
            "math_world": {
                "type": "angle_relationship",
                "standard_code": standard.code,
                "relationship": "vertical_angles",
                "expression_a": expr_a,
                "expression_b": expr_b,
                "x": x_value,
                "angle": angle,
                "answer": answer,
            },
            "diagram_spec": {
                "type": "angle_relationship",
                "relationship": "vertical_angles",
                "expression_a": expr_a,
                "expression_b": expr_b,
                "angle": angle,
                "lines": [
                    {"from": [-3, -2], "to": [3, 2]},
                    {"from": [-3, 2], "to": [3, -2]},
                ],
            },
        }

    def _validate_number_line(self, math_world: dict[str, Any], diagram_spec: dict[str, Any]) -> list[str]:
        errors = []
        for key in ["start", "change", "end", "answer"]:
            if key not in math_world:
                errors.append(f"number line math_world missing {key}")
        if diagram_spec.get("type") != "number_line":
            errors.append("number line scene has wrong diagram type")
        if not isinstance(diagram_spec.get("points"), list) or len(diagram_spec["points"]) < 2:
            errors.append("number line diagram needs start and end points")
        if not isinstance(diagram_spec.get("arrows"), list) or not diagram_spec["arrows"]:
            errors.append("number line diagram needs an arrow")
        return errors

    def _validate_coordinate_graph(self, math_world: dict[str, Any], diagram_spec: dict[str, Any]) -> list[str]:
        errors = []
        if math_world.get("type") != "proportional_relationship":
            errors.append("coordinate graph math_world must be proportional_relationship")
        if "constant_of_proportionality" not in math_world:
            errors.append("coordinate graph missing constant_of_proportionality")
        if not isinstance(diagram_spec.get("points"), list) or len(diagram_spec["points"]) < 2:
            errors.append("coordinate graph needs at least two points")
        if not isinstance(diagram_spec.get("line"), dict):
            errors.append("coordinate graph needs a line object")
        return errors

    def _validate_angle_relationship(self, math_world: dict[str, Any], diagram_spec: dict[str, Any]) -> list[str]:
        errors = []
        if math_world.get("relationship") != "vertical_angles":
            errors.append("only vertical angle scenes are currently supported")
        for key in ["expression_a", "expression_b", "x", "angle", "answer"]:
            if key not in math_world:
                errors.append(f"angle relationship math_world missing {key}")
        if diagram_spec.get("type") != "angle_relationship":
            errors.append("angle relationship scene has wrong diagram type")
        return errors
