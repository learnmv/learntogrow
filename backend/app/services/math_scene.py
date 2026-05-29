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


def _point_name(prefix: str, index: int) -> str:
    return f"{prefix}{index + 1}"


class GeoGebraSceneCompiler:
    """Compiles structured diagram specs into conservative GeoGebra commands."""

    SAFE_COMMAND_PREFIXES = (
        "Point",
        "Segment",
        "Line",
        "Ray",
        "Vector",
        "Text",
        "SetColor",
        "SetPointSize",
        "SetLineThickness",
        "SetCaption",
        "ShowLabel",
        "ZoomIn",
        "xAxis",
        "yAxis",
        "f",
        "A",
        "B",
        "C",
        "D",
        "P",
        "Q",
        "R",
        "Axis",
        "Move",
        "Start",
        "End",
        "Target",
        "Origin",
    )

    def compile(self, scene: dict[str, Any]) -> list[str]:
        diagram_spec = scene.get("diagram_spec") or {}
        scene_type = diagram_spec.get("type")
        if scene_type == "number_line":
            return self._number_line(diagram_spec)
        if scene_type == "coordinate_graph":
            return self._coordinate_graph(diagram_spec)
        if scene_type == "angle_relationship":
            return self._angle_relationship(diagram_spec)
        return []

    def validate_commands(self, commands: Any) -> list[str]:
        if not isinstance(commands, list) or not commands:
            return ["GeoGebra commands must be a non-empty list"]
        errors = []
        for index, command in enumerate(commands):
            if not isinstance(command, str) or not command.strip():
                errors.append(f"GeoGebra command {index + 1} is empty")
                continue
            stripped = command.strip()
            if any(token in stripped.lower() for token in ["javascript", "<script", "eval("]):
                errors.append(f"GeoGebra command {index + 1} contains unsafe text")
            if not stripped.startswith(self.SAFE_COMMAND_PREFIXES) and "=" not in stripped:
                errors.append(f"GeoGebra command {index + 1} uses unsupported syntax")
        return errors

    def _number_line(self, spec: dict[str, Any]) -> list[str]:
        min_value = _fmt_number(float(spec.get("min", -10)))
        max_value = _fmt_number(float(spec.get("max", 10)))
        commands = [
            f"Axis = Segment(({min_value}, 0), ({max_value}, 0))",
            "SetColor(Axis, 80, 80, 80)",
            "SetLineThickness(Axis, 4)",
        ]
        ticks = int(spec.get("ticks") or 1)
        lower = int(float(min_value))
        upper = int(float(max_value))
        tick_values = range(lower, upper + 1, max(1, ticks))
        for index, value in enumerate(tick_values):
            name = _point_name("T", index)
            commands.extend([
                f"{name} = ({value}, 0)",
                f"Tick{index + 1} = Segment(({value}, -0.08), ({value}, 0.08))",
                f'Text("{value}", ({value - 0.12}, -0.35))',
            ])
        for point in spec.get("points") or []:
            point_id = str(point.get("id") or "P").title().replace("_", "")
            value = _fmt_number(float(point.get("value", 0)))
            label = str(point.get("label") or point_id)
            commands.extend([
                f"{point_id} = ({value}, 0)",
                f"SetPointSize({point_id}, 7)",
                f'SetCaption({point_id}, "{label}")',
                f"ShowLabel({point_id}, true)",
            ])
        for index, arrow in enumerate(spec.get("arrows") or []):
            start = _fmt_number(float(arrow.get("from", 0)))
            end = _fmt_number(float(arrow.get("to", 0)))
            label = str(arrow.get("label") or "")
            lift = 0.45 + (index * 0.15)
            commands.extend([
                f"Move{index + 1} = Vector(({start}, {lift}), ({end}, {lift}))",
                f"SetLineThickness(Move{index + 1}, 5)",
            ])
            if label:
                midpoint = (float(start) + float(end)) / 2
                commands.append(f'Text("{label}", ({_fmt_number(midpoint)}, {_fmt_number(lift + 0.25)}))')
        return commands

    def _coordinate_graph(self, spec: dict[str, Any]) -> list[str]:
        line = spec.get("line") or {}
        slope = _fmt_number(float(line.get("slope", 1)))
        intercept = _fmt_number(float(line.get("intercept", 0)))
        x_max = _fmt_number(float(spec.get("x_max", 10)) + 1)
        y_max = _fmt_number(float(spec.get("y_max", 10)) + 1)
        commands = [
            f"f(x) = {slope} * x + {intercept}",
            f"ZoomIn(-1, -1, {x_max}, {y_max})",
        ]
        for index, point in enumerate(spec.get("points") or []):
            name = _point_name("P", index)
            x_value = _fmt_number(float(point.get("x", 0)))
            y_value = _fmt_number(float(point.get("y", 0)))
            label = str(point.get("label") or f"({x_value}, {y_value})")
            commands.extend([
                f"{name} = ({x_value}, {y_value})",
                f"SetPointSize({name}, 6)",
                f'SetCaption({name}, "{label}")',
                f"ShowLabel({name}, true)",
            ])
        highlight = spec.get("highlight")
        if isinstance(highlight, dict):
            x_value = _fmt_number(float(highlight.get("x", 0)))
            y_value = _fmt_number(float(highlight.get("y", 0)))
            commands.extend([
                f"Target = ({x_value}, {y_value})",
                "SetPointSize(Target, 8)",
                "SetColor(Target, 46, 125, 50)",
                'SetCaption(Target, "Target")',
                "ShowLabel(Target, true)",
            ])
        return commands

    def _angle_relationship(self, spec: dict[str, Any]) -> list[str]:
        commands = [
            "Line1 = Line((-4, 0), (4, 0))",
            "Line2 = Line((0, -3), (0, 3))",
            "A = (0, 0)",
            "SetPointSize(A, 4)",
        ]
        relationship = spec.get("relationship")
        if relationship == "vertical_angles":
            commands = [
                "Line1 = Line((-4, -2), (4, 2))",
                "Line2 = Line((-4, 2), (4, -2))",
                "A = (0, 0)",
                "SetPointSize(A, 4)",
            ]
        elif relationship in {"supplementary_angles", "complementary_angles"}:
            commands.extend([
                "B = (3, 0)",
                "C = (0, 2.5)",
                "Segment(A, B)",
                "Segment(A, C)",
            ])
        expr_a = str(spec.get("expression_a") or "")
        expr_b = str(spec.get("expression_b") or "")
        if expr_a:
            commands.append(f'Text("{expr_a}", (0.7, 1.0))')
        if expr_b:
            commands.append(f'Text("{expr_b}", (-1.8, 1.0))')
        return commands


class MathSceneEngine:
    """Builds verifiable math worlds and GeoGebra-backed diagram scenes."""

    SUPPORTED_CODES = {"7.NS.1", "7.RP.2", "7.G.5"}

    def __init__(self) -> None:
        self.compiler = GeoGebraSceneCompiler()

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
            "geogebra_commands": scene["geogebra_commands"],
            "applet_type": scene["applet_type"],
            "correct_answer": scene["answer"],
            "options": scene["options"],
            "explanation": scene["explanation"],
            "question_goal": scene["question_goal"],
        }
        return f"""{base_prompt}

MATH SCENE CONTRACT
This contract is mandatory. Build the question around this exact math world.
Do not change numbers, labels, the answer, or the answer options.
Return math_world, diagram_spec, geogebra_commands, and applet_type exactly as provided here.

{json.dumps(contract, indent=2, default=str)}

SCENE RULES:
- The question text should sound natural for a student.
- Do not mention "math_world", "diagram_spec", "GeoGebra", or implementation details.
- The correct answer field must exactly equal correct_answer.
- The options field must exactly equal the provided options.
- The explanation must use the same math as the provided explanation.
- The geogebra_commands field must exactly equal the provided geogebra_commands.
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
        result["geogebra_commands"] = list(scene.get("geogebra_commands") or self.compiler.compile(scene))
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
        commands = question_data.get("geogebra_commands") or []
        errors.extend(self.compiler.validate_commands(commands))
        return errors

    def scene_to_text(self, value: Any) -> str:
        if not isinstance(value, dict):
            return ""
        return json.dumps(value, sort_keys=True, default=str)

    def _number_line_scene(self, standard: Any, difficulty: float, attempt_index: int, rng: random.Random) -> dict[str, Any]:
        variant = rng.choice(["final_value", "missing_change", "distance"])
        denominators = [2, 4] if difficulty < 0.75 else [4, 5, 8]
        denominator = rng.choice(denominators)
        start = Fraction(rng.randint(-24, 12), denominator)
        change = Fraction(rng.choice([-1, 1]) * rng.randint(5, 18), denominator)
        end = start + change
        operation = "addition" if change >= 0 else "subtraction"
        answer_value = end
        question_goal = (
            f"Ask the student to use the number line to find the final value after starting at "
            f"{_fmt_number(start)} and changing by {_fmt_number(change)}."
        )
        explanation = (
            f"Start at {_fmt_number(start)}. A change of {_fmt_number(change)} moves to {_fmt_number(end)}, "
            f"so the final value is {_fmt_number(end)}."
        )
        arrows = [{"from": _fmt_number(start), "to": _fmt_number(end), "label": _fmt_number(change)}]
        if variant == "missing_change":
            answer_value = change
            question_goal = (
                f"Ask the student to use the number line to find the signed change from "
                f"{_fmt_number(start)} to {_fmt_number(end)}."
            )
            explanation = (
                f"The movement from {_fmt_number(start)} to {_fmt_number(end)} is "
                f"{_fmt_number(end)} - {_fmt_number(start)} = {_fmt_number(change)}."
            )
        elif variant == "distance":
            answer_value = abs(end - start)
            question_goal = (
                f"Ask the student to use the number line to find the distance between "
                f"{_fmt_number(start)} and {_fmt_number(end)}."
            )
            explanation = (
                f"Distance is the absolute difference: |{_fmt_number(end)} - {_fmt_number(start)}| = "
                f"{_fmt_number(answer_value)}."
            )
            arrows = [{"from": _fmt_number(start), "to": _fmt_number(end), "label": "distance"}]

        answer = _fmt_number(answer_value)
        wrong_sign = _fmt_number(start - change)
        wrong_start = _fmt_number(change)
        wrong_abs = _fmt_number(abs(end))
        options = _finalize_options(rng, [wrong_sign, wrong_start, wrong_abs], answer)
        min_value = min(float(start), float(end), 0) - 1
        max_value = max(float(start), float(end), 0) + 1
        start_text = _fmt_number(start)
        change_text = _fmt_number(change)
        end_text = _fmt_number(end)
        scene = {
            "question_goal": question_goal,
            "answer": answer,
            "options": options,
            "explanation": explanation,
            "applet_type": "graphing",
            "math_world": {
                "type": "number_line_operation",
                "standard_code": standard.code,
                "variant": variant,
                "operation": operation,
                "start": start_text,
                "change": change_text,
                "end": answer,
                "actual_end": end_text,
                "answer": answer,
            },
            "diagram_spec": {
                "type": "number_line",
                "min": _fmt_number(min_value),
                "max": _fmt_number(max_value),
                "ticks": 1,
                "points": [
                    {"id": "start", "value": _fmt_number(start), "label": "Start"},
                    {"id": "end", "value": end_text, "label": "End"},
                ],
                "arrows": arrows,
            },
        }
        scene["geogebra_commands"] = self.compiler.compile(scene)
        return scene

    def _proportional_graph_scene(self, standard: Any, difficulty: float, attempt_index: int, rng: random.Random) -> dict[str, Any]:
        variant = rng.choice(["find_y", "find_x", "constant", "equation"])
        rate = rng.choice([2, 3, 4, 5, 6, 8])
        target_x = rng.choice([3, 4, 5, 6, 7])
        target_y = rate * target_x
        points = [[1, rate], [2, 2 * rate], [target_x, target_y]]
        answer = f"{target_y}"
        options = [str(target_y + rate), str(target_y - rate), str(target_x + rate)]
        question_goal = (
            f"Ask the student to use the proportional graph with constant of proportionality "
            f"{rate} to find y when x = {target_x}."
        )
        explanation = (
            f"The graph represents y = {rate}x. When x = {target_x}, "
            f"y = {rate} x {target_x} = {target_y}."
        )
        if variant == "find_x":
            answer = str(target_x)
            options = [str(target_x + 1), str(max(1, target_x - 1)), str(target_y)]
            question_goal = (
                f"Ask the student to use the proportional graph y = {rate}x to find x "
                f"when y = {target_y}."
            )
            explanation = f"Since y = {rate}x, solve {target_y} = {rate}x. The value of x is {target_x}."
        elif variant == "constant":
            answer = str(rate)
            options = [str(rate + 1), str(target_y), str(target_x)]
            question_goal = "Ask the student to identify the constant of proportionality from the graph."
            explanation = f"For each point, y divided by x equals {rate}, so the constant of proportionality is {rate}."
        elif variant == "equation":
            answer = f"$y = {rate}x$"
            options = [f"$y = {rate + 1}x$", f"$y = x + {rate}$", f"$y = {target_x}x$"]
            question_goal = "Ask the student to choose the equation represented by the proportional graph."
            explanation = f"The graph passes through the origin and has constant of proportionality {rate}, so y = {rate}x."

        scene = {
            "question_goal": question_goal,
            "answer": answer,
            "options": _finalize_options(rng, options, answer),
            "explanation": explanation,
            "applet_type": "graphing",
            "math_world": {
                "type": "proportional_relationship",
                "standard_code": standard.code,
                "variant": variant,
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
        scene["geogebra_commands"] = self.compiler.compile(scene)
        return scene

    def _angle_relationship_scene(self, standard: Any, difficulty: float, attempt_index: int, rng: random.Random) -> dict[str, Any]:
        variant = rng.choice(["vertical_angles", "supplementary_angles", "complementary_angles"])
        if variant == "supplementary_angles":
            known = rng.choice([45, 58, 63, 72, 105, 118])
            answer_angle = 180 - known
            answer = f"{answer_angle} degrees"
            scene = {
                "question_goal": (
                    f"Ask the student to find the angle supplementary to {known} degrees "
                    "in a straight-line angle pair."
                ),
                "answer": answer,
                "options": _finalize_options(
                    rng,
                    [f"{known} degrees", f"{90 - (known % 90)} degrees", f"{answer_angle + 10} degrees"],
                    answer,
                ),
                "explanation": (
                    f"Supplementary angles add to 180 degrees, so the missing angle is "
                    f"180 - {known} = {answer_angle} degrees."
                ),
                "applet_type": "geometry",
                "math_world": {
                    "type": "angle_relationship",
                    "standard_code": standard.code,
                    "variant": variant,
                    "relationship": variant,
                    "known_angle": known,
                    "angle": answer_angle,
                    "answer": answer,
                },
                "diagram_spec": {
                    "type": "angle_relationship",
                    "relationship": variant,
                    "expression_a": f"{known} degrees",
                    "expression_b": "?",
                    "angle": answer_angle,
                },
            }
            scene["geogebra_commands"] = self.compiler.compile(scene)
            return scene
        if variant == "complementary_angles":
            known = rng.choice([22, 35, 41, 53, 64])
            answer_angle = 90 - known
            answer = f"{answer_angle} degrees"
            scene = {
                "question_goal": (
                    f"Ask the student to find the angle complementary to {known} degrees "
                    "in a right-angle pair."
                ),
                "answer": answer,
                "options": _finalize_options(
                    rng,
                    [f"{known} degrees", f"{180 - known} degrees", f"{answer_angle + 10} degrees"],
                    answer,
                ),
                "explanation": (
                    f"Complementary angles add to 90 degrees, so the missing angle is "
                    f"90 - {known} = {answer_angle} degrees."
                ),
                "applet_type": "geometry",
                "math_world": {
                    "type": "angle_relationship",
                    "standard_code": standard.code,
                    "variant": variant,
                    "relationship": variant,
                    "known_angle": known,
                    "angle": answer_angle,
                    "answer": answer,
                },
                "diagram_spec": {
                    "type": "angle_relationship",
                    "relationship": variant,
                    "expression_a": f"{known} degrees",
                    "expression_b": "?",
                    "angle": answer_angle,
                },
            }
            scene["geogebra_commands"] = self.compiler.compile(scene)
            return scene

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
        scene = {
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
            "math_world": {
                "type": "angle_relationship",
                "standard_code": standard.code,
                "variant": variant,
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
        scene["geogebra_commands"] = self.compiler.compile(scene)
        return scene

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
        if math_world.get("relationship") not in {"vertical_angles", "supplementary_angles", "complementary_angles"}:
            errors.append("unsupported angle relationship")
        for key in ["relationship", "angle", "answer"]:
            if key not in math_world:
                errors.append(f"angle relationship math_world missing {key}")
        if math_world.get("relationship") == "vertical_angles":
            for key in ["expression_a", "expression_b", "x"]:
                if key not in math_world:
                    errors.append(f"angle relationship math_world missing {key}")
        if diagram_spec.get("type") != "angle_relationship":
            errors.append("angle relationship scene has wrong diagram type")
        return errors
