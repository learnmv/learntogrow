-- Add California Common Core State Standards for Grade 7 Mathematics.
-- Source: California Common Core State Standards: Mathematics, adopted August 2010
-- and modified January 2013, Grade 7 K-8 Standards.

DO $$
DECLARE
    math_subject_id INTEGER;
    grade7_id INTEGER;
    rp_domain_id INTEGER;
    ns_domain_id INTEGER;
    ee_domain_id INTEGER;
    g_domain_id INTEGER;
    sp_domain_id INTEGER;
    rp_a_cluster_id INTEGER;
    ns_a_cluster_id INTEGER;
    ee_a_cluster_id INTEGER;
    ee_b_cluster_id INTEGER;
    g_a_cluster_id INTEGER;
    g_b_cluster_id INTEGER;
    sp_a_cluster_id INTEGER;
    sp_b_cluster_id INTEGER;
    sp_c_cluster_id INTEGER;
BEGIN
    INSERT INTO subjects (code, name, description)
    VALUES ('MATH', 'Mathematics', 'California Common Core Mathematics Standards')
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        description = EXCLUDED.description
    RETURNING id INTO math_subject_id;

    INSERT INTO grades (level, subject_id, display_name)
    VALUES (7, math_subject_id, 'Grade 7')
    ON CONFLICT (level, subject_id) DO UPDATE
    SET display_name = EXCLUDED.display_name
    RETURNING id INTO grade7_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('7.RP', 'Ratios and Proportional Relationships', math_subject_id, 1)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO rp_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('7.NS', 'The Number System', math_subject_id, 2)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO ns_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('7.EE', 'Expressions and Equations', math_subject_id, 3)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO ee_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('7.G', 'Geometry', math_subject_id, 4)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO g_domain_id;

    INSERT INTO domains (code, name, subject_id, display_order)
    VALUES ('7.SP', 'Statistics and Probability', math_subject_id, 5)
    ON CONFLICT (code) DO UPDATE
    SET name = EXCLUDED.name,
        subject_id = EXCLUDED.subject_id,
        display_order = EXCLUDED.display_order
    RETURNING id INTO sp_domain_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.RP.A', 'Analyze proportional relationships and use them to solve real-world and mathematical problems', rp_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO rp_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.NS.A', 'Apply and extend previous understandings of operations with fractions to add, subtract, multiply, and divide rational numbers', ns_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ns_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.EE.A', 'Use properties of operations to generate equivalent expressions', ee_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ee_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.EE.B', 'Solve real-life and mathematical problems using numerical and algebraic expressions and equations', ee_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO ee_b_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.G.A', 'Draw, construct, and describe geometrical figures and describe the relationships between them', g_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO g_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.G.B', 'Solve real-life and mathematical problems involving angle measure, area, surface area, and volume', g_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO g_b_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.SP.A', 'Use random sampling to draw inferences about a population', sp_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO sp_a_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.SP.B', 'Draw informal comparative inferences about two populations', sp_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO sp_b_cluster_id;

    INSERT INTO clusters (code, name, domain_id, grade_id)
    VALUES ('7.SP.C', 'Investigate chance processes and develop, use, and evaluate probability models', sp_domain_id, grade7_id)
    ON CONFLICT (code, domain_id) DO UPDATE
    SET name = EXCLUDED.name,
        grade_id = EXCLUDED.grade_id
    RETURNING id INTO sp_c_cluster_id;

    INSERT INTO standards (
        code,
        description,
        cluster_id,
        grade_id,
        domain_id,
        keywords,
        difficulty_base,
        conceptual_category,
        requires_diagram,
        applet_type
    )
    VALUES
        ('7.RP.1', 'Compute unit rates associated with ratios of fractions, including ratios of lengths, areas, and other quantities measured in like or different units.', rp_a_cluster_id, grade7_id, rp_domain_id, ARRAY['unit rate', 'ratios of fractions', 'complex fractions', 'rates', 'measurement'], 0.45, 'Major Work', FALSE, NULL),
        ('7.RP.2', 'Recognize and represent proportional relationships between quantities, including deciding whether relationships are proportional, identifying constants of proportionality, representing relationships by equations, and explaining points on graphs in context.', rp_a_cluster_id, grade7_id, rp_domain_id, ARRAY['proportional relationships', 'constant of proportionality', 'unit rate', 'tables', 'graphs', 'equations'], 0.55, 'Major Work', TRUE, 'graphing'),
        ('7.RP.3', 'Use proportional relationships to solve multistep ratio and percent problems.', rp_a_cluster_id, grade7_id, rp_domain_id, ARRAY['proportions', 'ratio', 'percent', 'tax', 'discount', 'markup', 'percent increase', 'percent error'], 0.60, 'Major Work', FALSE, NULL),

        ('7.NS.1', 'Apply and extend previous understandings of addition and subtraction to add and subtract rational numbers; represent addition and subtraction on a horizontal or vertical number line diagram.', ns_a_cluster_id, grade7_id, ns_domain_id, ARRAY['rational numbers', 'addition', 'subtraction', 'number line', 'opposites', 'additive inverse'], 0.55, 'Major Work', TRUE, 'graphing'),
        ('7.NS.2', 'Apply and extend previous understandings of multiplication and division and of fractions to multiply and divide rational numbers.', ns_a_cluster_id, grade7_id, ns_domain_id, ARRAY['rational numbers', 'multiplication', 'division', 'integers', 'signed numbers', 'decimal expansion'], 0.60, 'Major Work', FALSE, NULL),
        ('7.NS.3', 'Solve real-world and mathematical problems involving the four operations with rational numbers.', ns_a_cluster_id, grade7_id, ns_domain_id, ARRAY['rational numbers', 'four operations', 'real-world problems', 'fractions', 'decimals', 'integers'], 0.65, 'Major Work', FALSE, NULL),

        ('7.EE.1', 'Apply properties of operations as strategies to add, subtract, factor, and expand linear expressions with rational coefficients.', ee_a_cluster_id, grade7_id, ee_domain_id, ARRAY['linear expressions', 'rational coefficients', 'properties of operations', 'factor', 'expand'], 0.55, 'Major Work', FALSE, NULL),
        ('7.EE.2', 'Understand that rewriting an expression in different forms in a problem context can shed light on the problem and how the quantities in it are related.', ee_a_cluster_id, grade7_id, ee_domain_id, ARRAY['equivalent expressions', 'rewriting expressions', 'problem context', 'relationships'], 0.50, 'Major Work', FALSE, NULL),
        ('7.EE.3', 'Solve multi-step real-life and mathematical problems posed with positive and negative rational numbers in any form, using tools strategically; apply properties of operations and assess the reasonableness of answers.', ee_b_cluster_id, grade7_id, ee_domain_id, ARRAY['multi-step problems', 'positive rational numbers', 'negative rational numbers', 'estimation', 'reasonableness'], 0.65, 'Major Work', FALSE, NULL),
        ('7.EE.4', 'Use variables to represent quantities in real-world or mathematical problems, and construct simple equations and inequalities to solve problems by reasoning about the quantities.', ee_b_cluster_id, grade7_id, ee_domain_id, ARRAY['variables', 'equations', 'inequalities', 'word problems', 'solution set'], 0.65, 'Major Work', FALSE, NULL),

        ('7.G.1', 'Solve problems involving scale drawings of geometric figures, including computing actual lengths and areas from a scale drawing and reproducing a scale drawing at a different scale.', g_a_cluster_id, grade7_id, g_domain_id, ARRAY['scale drawings', 'scale factor', 'actual length', 'area', 'geometric figures'], 0.55, 'Supporting', TRUE, 'geometry'),
        ('7.G.2', 'Draw geometric shapes with given conditions, focusing on constructing triangles from measures of angles or sides and noticing when conditions determine a unique triangle, more than one triangle, or no triangle.', g_a_cluster_id, grade7_id, g_domain_id, ARRAY['geometric construction', 'triangles', 'angles', 'side lengths', 'unique triangle'], 0.65, 'Supporting', TRUE, 'geometry'),
        ('7.G.3', 'Describe the two-dimensional figures that result from slicing three-dimensional figures, as in plane sections of right rectangular prisms and right rectangular pyramids.', g_a_cluster_id, grade7_id, g_domain_id, ARRAY['cross sections', 'three-dimensional figures', 'two-dimensional figures', 'rectangular prism', 'rectangular pyramid'], 0.70, 'Supporting', TRUE, '3d'),
        ('7.G.4', 'Know formulas for the area and circumference of a circle and use them to solve problems; give an informal derivation of the relationship between circumference and area.', g_b_cluster_id, grade7_id, g_domain_id, ARRAY['circle', 'area', 'circumference', 'radius', 'diameter', 'pi'], 0.55, 'Supporting', TRUE, 'geometry'),
        ('7.G.5', 'Use facts about supplementary, complementary, vertical, and adjacent angles in a multi-step problem to write and solve simple equations for an unknown angle in a figure.', g_b_cluster_id, grade7_id, g_domain_id, ARRAY['angles', 'supplementary', 'complementary', 'vertical angles', 'adjacent angles', 'equations'], 0.60, 'Supporting', TRUE, 'geometry'),
        ('7.G.6', 'Solve real-world and mathematical problems involving area, volume, and surface area of two- and three-dimensional objects composed of triangles, quadrilaterals, polygons, cubes, and right prisms.', g_b_cluster_id, grade7_id, g_domain_id, ARRAY['area', 'volume', 'surface area', 'triangles', 'quadrilaterals', 'polygons', 'cubes', 'right prisms'], 0.70, 'Supporting', TRUE, '3d'),

        ('7.SP.1', 'Understand that statistics can be used to gain information about a population by examining a sample, and that valid generalizations require representative samples.', sp_a_cluster_id, grade7_id, sp_domain_id, ARRAY['population', 'sample', 'representative sample', 'random sampling', 'inference'], 0.40, 'Additional', FALSE, NULL),
        ('7.SP.2', 'Use data from a random sample to draw inferences about a population with an unknown characteristic of interest; generate multiple samples to gauge variation in estimates or predictions.', sp_a_cluster_id, grade7_id, sp_domain_id, ARRAY['random sample', 'inference', 'population', 'variation', 'estimate', 'prediction'], 0.55, 'Additional', FALSE, NULL),
        ('7.SP.3', 'Informally assess the degree of visual overlap of two numerical data distributions with similar variabilities, measuring the difference between centers as a multiple of a measure of variability.', sp_b_cluster_id, grade7_id, sp_domain_id, ARRAY['data distributions', 'visual overlap', 'center', 'variability', 'mean absolute deviation'], 0.60, 'Additional', TRUE, 'graphing'),
        ('7.SP.4', 'Use measures of center and variability for numerical data from random samples to draw informal comparative inferences about two populations.', sp_b_cluster_id, grade7_id, sp_domain_id, ARRAY['measures of center', 'measures of variability', 'random samples', 'comparative inference', 'populations'], 0.60, 'Additional', TRUE, 'graphing'),
        ('7.SP.5', 'Understand that the probability of a chance event is a number between 0 and 1 that expresses the likelihood of the event occurring.', sp_c_cluster_id, grade7_id, sp_domain_id, ARRAY['probability', 'chance event', 'likelihood', '0 to 1'], 0.35, 'Additional', FALSE, NULL),
        ('7.SP.6', 'Approximate the probability of a chance event by collecting data on the chance process and observing its long-run relative frequency; predict approximate relative frequency given probability.', sp_c_cluster_id, grade7_id, sp_domain_id, ARRAY['probability', 'relative frequency', 'chance process', 'long-run frequency', 'prediction'], 0.50, 'Additional', FALSE, NULL),
        ('7.SP.7', 'Develop a probability model and use it to find probabilities of events; compare probabilities from a model to observed frequencies and explain possible discrepancies.', sp_c_cluster_id, grade7_id, sp_domain_id, ARRAY['probability model', 'uniform model', 'observed frequency', 'discrepancy'], 0.60, 'Additional', FALSE, NULL),
        ('7.SP.8', 'Find probabilities of compound events using organized lists, tables, tree diagrams, and simulation.', sp_c_cluster_id, grade7_id, sp_domain_id, ARRAY['compound events', 'sample space', 'organized lists', 'tables', 'tree diagrams', 'simulation'], 0.70, 'Additional', TRUE, 'graphing')
    ON CONFLICT (code) DO UPDATE
    SET description = EXCLUDED.description,
        cluster_id = EXCLUDED.cluster_id,
        grade_id = EXCLUDED.grade_id,
        domain_id = EXCLUDED.domain_id,
        keywords = EXCLUDED.keywords,
        difficulty_base = EXCLUDED.difficulty_base,
        conceptual_category = EXCLUDED.conceptual_category,
        requires_diagram = EXCLUDED.requires_diagram,
        applet_type = EXCLUDED.applet_type;
END $$;
