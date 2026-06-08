-- Add California/Common Core State Standards for Grade 8 Mathematics.
-- Source: Common Core State Standards Initiative, Grade 8 K-8 Mathematics.
-- This migration follows the text-only curriculum schema.

DO $$
DECLARE
    math_subject_id INTEGER;
    grade8_id INTEGER;
    ns_domain_id INTEGER;
    ee_domain_id INTEGER;
    f_domain_id INTEGER;
    g_domain_id INTEGER;
    sp_domain_id INTEGER;
    ns_a_cluster_id INTEGER;
    ee_a_cluster_id INTEGER;
    ee_b_cluster_id INTEGER;
    ee_c_cluster_id INTEGER;
    f_a_cluster_id INTEGER;
    f_b_cluster_id INTEGER;
    g_a_cluster_id INTEGER;
    g_b_cluster_id INTEGER;
    g_c_cluster_id INTEGER;
    sp_a_cluster_id INTEGER;
BEGIN
    INSERT INTO subjects (code, name, description)
    VALUES ('MATH', 'Mathematics', 'California Common Core Mathematics Standards')
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description
    RETURNING id INTO math_subject_id;

    INSERT INTO grades (level, subject_id, display_name)
    VALUES (8, math_subject_id, 'Grade 8')
    ON CONFLICT (level, subject_id) DO UPDATE
    SET display_name = EXCLUDED.display_name
    RETURNING id INTO grade8_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('8.NS', 'The Number System', math_subject_id, 1)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO ns_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('8.EE', 'Expressions and Equations', math_subject_id, 2)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO ee_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('8.F', 'Functions', math_subject_id, 3)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO f_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('8.G', 'Geometry', math_subject_id, 4)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO g_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('8.SP', 'Statistics and Probability', math_subject_id, 5)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO sp_domain_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.NS.A', 'Know that there are numbers that are not rational, and approximate them by rational numbers', ns_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ns_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.EE.A', 'Work with radicals and integer exponents', ee_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ee_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.EE.B', 'Understand the connections between proportional relationships, lines, and linear equations', ee_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ee_b_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.EE.C', 'Analyze and solve linear equations and pairs of simultaneous linear equations', ee_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ee_c_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.F.A', 'Define, evaluate, and compare functions', f_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO f_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.F.B', 'Use functions to model relationships between quantities', f_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO f_b_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.G.A', 'Understand congruence and similarity using physical models, transparencies, or geometry software', g_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO g_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.G.B', 'Understand and apply the Pythagorean Theorem', g_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO g_b_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.G.C', 'Solve real-world and mathematical problems involving volume of cylinders, cones, and spheres', g_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO g_c_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('8.SP.A', 'Investigate patterns of association in bivariate data', sp_domain_id, grade8_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO sp_a_cluster_id;

    INSERT INTO standards (
        code,
        description,
        cluster_id,
        grade_id,
        domain_id,
        keywords,
        difficulty_base,
        conceptual_category
    )
    VALUES
        ('8.NS.1', 'Know that numbers that are not rational are called irrational. Understand informally that every number has a decimal expansion; for rational numbers, show that the decimal expansion repeats eventually and convert a repeating decimal expansion into a rational number.', ns_a_cluster_id, grade8_id, ns_domain_id, ARRAY['irrational numbers', 'rational numbers', 'decimal expansion', 'repeating decimals', 'real numbers'], 0.55, 'Supporting'),
        ('8.NS.2', 'Use rational approximations of irrational numbers to compare their size, locate them approximately on a number line diagram, and estimate the value of expressions.', ns_a_cluster_id, grade8_id, ns_domain_id, ARRAY['irrational numbers', 'rational approximations', 'number line', 'estimate', 'square roots'], 0.60, 'Supporting'),

        ('8.EE.1', 'Know and apply the properties of integer exponents to generate equivalent numerical expressions.', ee_a_cluster_id, grade8_id, ee_domain_id, ARRAY['integer exponents', 'exponent properties', 'equivalent expressions', 'powers'], 0.45, 'Major Work'),
        ('8.EE.2', 'Use square root and cube root symbols to represent solutions to equations of the form x squared equals p and x cubed equals p, evaluate roots of small perfect squares and cubes, and know that the square root of 2 is irrational.', ee_a_cluster_id, grade8_id, ee_domain_id, ARRAY['square roots', 'cube roots', 'perfect squares', 'perfect cubes', 'irrational numbers'], 0.55, 'Major Work'),
        ('8.EE.3', 'Use numbers expressed as a single digit times an integer power of 10 to estimate very large or very small quantities and express how many times as much one quantity is than another.', ee_a_cluster_id, grade8_id, ee_domain_id, ARRAY['scientific notation', 'powers of ten', 'estimate', 'very large numbers', 'very small numbers'], 0.50, 'Major Work'),
        ('8.EE.4', 'Perform operations with numbers expressed in scientific notation, including problems with decimal and scientific notation, choose appropriate units for very large or very small quantities, and interpret scientific notation generated by technology.', ee_a_cluster_id, grade8_id, ee_domain_id, ARRAY['scientific notation', 'operations', 'decimal notation', 'units', 'technology notation'], 0.60, 'Major Work'),
        ('8.EE.5', 'Graph proportional relationships, interpret the unit rate as the slope of the graph, and compare proportional relationships represented in different ways.', ee_b_cluster_id, grade8_id, ee_domain_id, ARRAY['proportional relationships', 'graphing', 'unit rate', 'slope', 'compare relationships'], 0.55, 'Major Work'),
        ('8.EE.6', 'Use similar triangles to explain why slope is the same between any two distinct points on a non-vertical line in the coordinate plane, and derive equations for lines through the origin and lines with vertical intercepts.', ee_b_cluster_id, grade8_id, ee_domain_id, ARRAY['slope', 'similar triangles', 'linear equations', 'coordinate plane', 'y-intercept'], 0.65, 'Major Work'),
        ('8.EE.7', 'Solve linear equations in one variable, including equations with one solution, infinitely many solutions, or no solutions, and equations with rational number coefficients requiring expansion and collecting like terms.', ee_c_cluster_id, grade8_id, ee_domain_id, ARRAY['linear equations', 'one variable', 'rational coefficients', 'distributive property', 'like terms'], 0.65, 'Major Work'),
        ('8.EE.8', 'Analyze and solve pairs of simultaneous linear equations, including understanding intersections of graphs as solutions, solving systems algebraically or by graphing, and solving real-world problems that lead to two linear equations in two variables.', ee_c_cluster_id, grade8_id, ee_domain_id, ARRAY['systems of equations', 'simultaneous equations', 'graphing', 'intersection', 'two variables'], 0.75, 'Major Work'),

        ('8.F.1', 'Understand that a function is a rule that assigns to each input exactly one output, and that the graph of a function is the set of ordered pairs consisting of an input and its corresponding output.', f_a_cluster_id, grade8_id, f_domain_id, ARRAY['functions', 'input', 'output', 'ordered pairs', 'function graph'], 0.45, 'Major Work'),
        ('8.F.2', 'Compare properties of two functions represented in different ways, including algebraically, graphically, numerically in tables, or by verbal descriptions.', f_a_cluster_id, grade8_id, f_domain_id, ARRAY['compare functions', 'tables', 'graphs', 'algebraic representations', 'rate of change'], 0.55, 'Major Work'),
        ('8.F.3', 'Interpret the equation y = mx + b as defining a linear function whose graph is a straight line, and give examples of functions that are not linear.', f_a_cluster_id, grade8_id, f_domain_id, ARRAY['linear functions', 'nonlinear functions', 'slope-intercept form', 'graphs', 'equations'], 0.55, 'Major Work'),
        ('8.F.4', 'Construct a function to model a linear relationship between two quantities, determine the rate of change and initial value from descriptions, tables, graphs, or two points, and interpret them in context.', f_b_cluster_id, grade8_id, f_domain_id, ARRAY['linear relationship', 'rate of change', 'initial value', 'modeling', 'tables', 'graphs'], 0.65, 'Major Work'),
        ('8.F.5', 'Describe qualitatively the functional relationship between two quantities by analyzing a graph, including where the function is increasing or decreasing and whether it is linear or nonlinear, and sketch a graph from a verbal description.', f_b_cluster_id, grade8_id, f_domain_id, ARRAY['qualitative graph analysis', 'increasing', 'decreasing', 'linear', 'nonlinear', 'sketch graphs'], 0.60, 'Major Work'),

        ('8.G.1', 'Verify experimentally the properties of rotations, reflections, and translations, including that lines and line segments map to lines and line segments of the same length, angles map to angles of the same measure, and parallel lines map to parallel lines.', g_a_cluster_id, grade8_id, g_domain_id, ARRAY['rotations', 'reflections', 'translations', 'transformations', 'congruence'], 0.55, 'Supporting'),
        ('8.G.2', 'Understand that a two-dimensional figure is congruent to another if the second can be obtained by a sequence of rotations, reflections, and translations, and describe a sequence that exhibits congruence between two figures.', g_a_cluster_id, grade8_id, g_domain_id, ARRAY['congruence', 'rotations', 'reflections', 'translations', 'transformations'], 0.60, 'Supporting'),
        ('8.G.3', 'Describe the effect of dilations, translations, rotations, and reflections on two-dimensional figures using coordinates.', g_a_cluster_id, grade8_id, g_domain_id, ARRAY['dilations', 'translations', 'rotations', 'reflections', 'coordinates'], 0.60, 'Supporting'),
        ('8.G.4', 'Understand that a two-dimensional figure is similar to another if the second can be obtained by a sequence of rotations, reflections, translations, and dilations, and describe a sequence that exhibits similarity between two figures.', g_a_cluster_id, grade8_id, g_domain_id, ARRAY['similarity', 'dilations', 'transformations', 'two-dimensional figures', 'scale factor'], 0.65, 'Supporting'),
        ('8.G.5', 'Use informal arguments to establish facts about triangle angle sums and exterior angles, angles created when parallel lines are cut by a transversal, and the angle-angle criterion for triangle similarity.', g_a_cluster_id, grade8_id, g_domain_id, ARRAY['angle relationships', 'triangle angle sum', 'exterior angles', 'parallel lines', 'transversals', 'triangle similarity'], 0.70, 'Supporting'),
        ('8.G.6', 'Explain a proof of the Pythagorean Theorem and its converse.', g_b_cluster_id, grade8_id, g_domain_id, ARRAY['Pythagorean Theorem', 'proof', 'converse', 'right triangles'], 0.65, 'Supporting'),
        ('8.G.7', 'Apply the Pythagorean Theorem to determine unknown side lengths in right triangles in real-world and mathematical problems in two and three dimensions.', g_b_cluster_id, grade8_id, g_domain_id, ARRAY['Pythagorean Theorem', 'right triangles', 'unknown side lengths', 'two dimensions', 'three dimensions'], 0.70, 'Supporting'),
        ('8.G.8', 'Apply the Pythagorean Theorem to find the distance between two points in a coordinate system.', g_b_cluster_id, grade8_id, g_domain_id, ARRAY['Pythagorean Theorem', 'distance formula', 'coordinate plane', 'points'], 0.65, 'Supporting'),
        ('8.G.9', 'Know the formulas for the volumes of cones, cylinders, and spheres and use them to solve real-world and mathematical problems.', g_c_cluster_id, grade8_id, g_domain_id, ARRAY['volume', 'cones', 'cylinders', 'spheres', 'formulas'], 0.65, 'Supporting'),

        ('8.SP.1', 'Construct and interpret scatter plots for bivariate measurement data to investigate patterns of association between two quantities, including clustering, outliers, positive or negative association, linear association, and nonlinear association.', sp_a_cluster_id, grade8_id, sp_domain_id, ARRAY['scatter plots', 'bivariate data', 'association', 'outliers', 'clustering'], 0.55, 'Additional'),
        ('8.SP.2', 'Know that straight lines are widely used to model relationships between two quantitative variables; for scatter plots suggesting a linear association, informally fit a straight line and assess model fit by judging closeness of data points to the line.', sp_a_cluster_id, grade8_id, sp_domain_id, ARRAY['linear models', 'scatter plots', 'line of fit', 'quantitative variables', 'model fit'], 0.60, 'Additional'),
        ('8.SP.3', 'Use the equation of a linear model to solve problems in the context of bivariate measurement data, interpreting the slope and intercept.', sp_a_cluster_id, grade8_id, sp_domain_id, ARRAY['linear model', 'slope', 'intercept', 'bivariate data', 'interpretation'], 0.65, 'Additional'),
        ('8.SP.4', 'Understand that patterns of association can also be seen in bivariate categorical data by displaying frequencies and relative frequencies in a two-way table, and use relative frequencies to describe possible association between variables.', sp_a_cluster_id, grade8_id, sp_domain_id, ARRAY['two-way tables', 'categorical data', 'relative frequency', 'association', 'bivariate data'], 0.60, 'Additional')
    ON CONFLICT (code) DO UPDATE
    SET description = EXCLUDED.description,
        cluster_id = EXCLUDED.cluster_id,
        grade_id = EXCLUDED.grade_id,
        domain_id = EXCLUDED.domain_id,
        keywords = EXCLUDED.keywords,
        difficulty_base = EXCLUDED.difficulty_base,
        conceptual_category = EXCLUDED.conceptual_category;
END $$;
