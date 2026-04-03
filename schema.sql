-- PostgreSQL Schema for LearnToGrow Question Generation System
-- Compatible with California Common Core Standards (extensible)

-- Create UUID extension if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- Layer 1: Curriculum Definition (Static Data)
-- ============================================

CREATE TABLE subjects (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE grades (
    id SERIAL PRIMARY KEY,
    level INTEGER NOT NULL CHECK (level BETWEEN -1 AND 12),
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    display_name VARCHAR(50),
    UNIQUE(level, subject_id)
);

CREATE TABLE domains (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    subject_id INTEGER REFERENCES subjects(id) ON DELETE CASCADE,
    display_order INTEGER DEFAULT 0
);

CREATE TABLE clusters (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) NOT NULL,
    name TEXT NOT NULL,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    grade_id INTEGER REFERENCES grades(id) ON DELETE CASCADE,
    UNIQUE(code, domain_id)
);

CREATE TABLE standards (
    id SERIAL PRIMARY KEY,
    code VARCHAR(20) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    cluster_id INTEGER REFERENCES clusters(id) ON DELETE CASCADE,
    grade_id INTEGER REFERENCES grades(id) ON DELETE CASCADE,
    domain_id INTEGER REFERENCES domains(id) ON DELETE CASCADE,
    keywords TEXT[],
    difficulty_base DECIMAL(3,2) CHECK (difficulty_base BETWEEN 0.00 AND 1.00),
    prerequisites INTEGER[],
    conceptual_category VARCHAR(50),
    requires_diagram BOOLEAN DEFAULT FALSE,
    applet_type VARCHAR(20),
    created_at TIMESTAMP DEFAULT NOW()
);

-- ============================================

-- ============================================
-- ============================================


-- ============================================
-- Layer 4: Users
-- ============================================


-- ============================================
-- ============================================



-- ============================================
-- Layer 6: Sessions & Activity Logs
-- ============================================



-- ============================================
-- Indexes for Performance
-- ============================================

-- Standards and curriculum
CREATE INDEX idx_standards_grade ON standards(grade_id);
CREATE INDEX idx_standards_domain ON standards(domain_id);
CREATE INDEX idx_standards_cluster ON standards(cluster_id);
CREATE INDEX idx_standards_code ON standards(code);
CREATE INDEX idx_clusters_domain ON clusters(domain_id);
CREATE INDEX idx_clusters_grade ON clusters(grade_id);
CREATE INDEX idx_domains_subject ON domains(subject_id);
CREATE INDEX idx_grades_subject ON grades(subject_id);

-- Question management

-- User activity

-- Full-text search on questions

-- ============================================
-- Seed Data: 6th Grade Math (California Common Core)
-- ============================================

-- Insert Math subject
INSERT INTO subjects (code, name, description) VALUES
('MATH', 'Mathematics', 'California Common Core State Standards for Mathematics');

-- Insert 6th grade
INSERT INTO grades (level, subject_id, display_name) VALUES
(6, 1, 'Grade 6');

-- Insert Domains for 6th Grade Math
INSERT INTO domains (code, name, subject_id, display_order) VALUES
('RP', 'Ratios and Proportional Relationships', 1, 1),
('NS', 'The Number System', 1, 2),
('EE', 'Expressions and Equations', 1, 3),
('G', 'Geometry', 1, 4),
('SP', 'Statistics and Probability', 1, 5);

-- Insert Clusters for each Domain
INSERT INTO clusters (code, name, domain_id, grade_id) VALUES
-- Ratios & Proportional Relationships (Domain 1)
('6.RP.A', 'Understand ratio concepts and use ratio reasoning to solve problems', 1, 1),
-- The Number System (Domain 2)
('6.NS.A', 'Apply and extend previous understandings of multiplication and division to divide fractions by fractions', 2, 1),
('6.NS.B', 'Compute fluently with multi-digit numbers and find common factors and multiples', 2, 1),
('6.NS.C', 'Apply and extend previous understandings of numbers to the system of rational numbers', 2, 1),
-- Expressions & Equations (Domain 3)
('6.EE.A', 'Apply and extend previous understandings of arithmetic to algebraic expressions', 3, 1),
('6.EE.B', 'Reason about and solve one-variable equations and inequalities', 3, 1),
('6.EE.C', 'Represent and analyze quantitative relationships between dependent and independent variables', 3, 1),
-- Geometry (Domain 4)
('6.G.A', 'Solve real-world and mathematical problems involving area, surface area, and volume', 4, 1),
-- Statistics & Probability (Domain 5)
('6.SP.A', 'Develop understanding of statistical variability', 5, 1),
('6.SP.B', 'Summarize and describe distributions', 5, 1);

-- Insert Standards for 6th Grade Math
INSERT INTO standards (code, description, cluster_id, grade_id, domain_id, keywords, difficulty_base, conceptual_category, requires_diagram, applet_type) VALUES
-- Ratios & Proportional Relationships
('6.RP.1', 'Understand the concept of a ratio and use ratio language to describe a ratio relationship between two quantities.', 1, 1, 1, ARRAY['ratio', 'relationship', 'quantities', 'language'], 0.30, 'Major Work', FALSE, NULL),
('6.RP.2', 'Understand the concept of a unit rate a/b associated with a ratio a:b with b != 0, and use rate language in the context of a ratio relationship.', 1, 1, 1, ARRAY['unit rate', 'ratio', 'rate language'], 0.40, 'Major Work', FALSE, NULL),
('6.RP.3', 'Use ratio and rate reasoning to solve real-world and mathematical problems.', 1, 1, 1, ARRAY['ratio', 'rate', 'reasoning', 'real-world', 'tables', 'percent', 'measurement'], 0.60, 'Major Work', FALSE, NULL),

-- The Number System
('6.NS.1', 'Interpret and compute quotients of fractions, and solve word problems involving division of fractions by fractions.', 2, 1, 2, ARRAY['fractions', 'division', 'quotients', 'word problems'], 0.65, 'Major Work', FALSE, NULL),
('6.NS.2', 'Fluently divide multi-digit numbers using the standard algorithm.', 3, 1, 2, ARRAY['division', 'multi-digit', 'algorithm'], 0.35, 'Major Work', FALSE, NULL),
('6.NS.3', 'Fluently add, subtract, multiply, and divide multi-digit decimals using the standard algorithm for each operation.', 3, 1, 2, ARRAY['decimals', 'addition', 'subtraction', 'multiplication', 'division', 'algorithm'], 0.40, 'Major Work', FALSE, NULL),
('6.NS.4', 'Find the greatest common factor of two whole numbers and the least common multiple of two whole numbers. Use the distributive property to express a sum of two whole numbers with a common factor as a multiple of a sum of two whole numbers with no common factor.', 3, 1, 2, ARRAY['GCF', 'LCM', 'greatest common factor', 'least common multiple', 'distributive property'], 0.50, 'Major Work', FALSE, NULL),
('6.NS.5', 'Understand that positive and negative numbers are used together to describe quantities having opposite directions or values. Understand a rational number as a point on the number line.', 4, 1, 2, ARRAY['positive', 'negative', 'rational numbers', 'number line', 'opposite'], 0.35, 'Major Work', TRUE, 'graphing'),
('6.NS.6', 'Understand a rational number as a point on the number line. Extend number line diagrams and coordinate axes familiar from previous grades to represent points on the line and in the plane with negative number coordinates.', 4, 1, 2, ARRAY['number line', 'coordinate plane', 'negative numbers', 'rational numbers'], 0.50, 'Major Work', TRUE, 'graphing'),
('6.NS.7', 'Understand ordering and absolute value of rational numbers.', 4, 1, 2, ARRAY['ordering', 'absolute value', 'rational numbers', 'inequality'], 0.45, 'Major Work', TRUE, 'graphing'),
('6.NS.8', 'Solve real-world and mathematical problems by graphing points in all four quadrants of the coordinate plane. Include use of coordinates and absolute value to find distances between points.', 4, 1, 2, ARRAY['coordinate plane', 'graphing', 'distance', 'quadrants', 'absolute value'], 0.60, 'Major Work', TRUE, 'graphing'),

-- Expressions & Equations
('6.EE.1', 'Write and evaluate numerical expressions involving whole-number exponents.', 5, 1, 3, ARRAY['exponents', 'numerical expressions', 'evaluate'], 0.35, 'Major Work', FALSE, NULL),
('6.EE.2', 'Write, read, and evaluate expressions in which letters stand for numbers.', 5, 1, 3, ARRAY['expressions', 'variables', 'evaluate', 'terms', 'coefficients'], 0.45, 'Major Work', FALSE, NULL),
('6.EE.3', 'Apply the properties of operations to generate equivalent expressions.', 5, 1, 3, ARRAY['equivalent expressions', 'properties', 'distributive', 'associative', 'commutative'], 0.50, 'Major Work', FALSE, NULL),
('6.EE.4', 'Identify when two expressions are equivalent.', 5, 1, 3, ARRAY['equivalent', 'expressions', 'identify'], 0.55, 'Major Work', FALSE, NULL),
('6.EE.5', 'Understand solving an equation or inequality as a process of answering a question: which values from a specified set make the equation or inequality true?', 6, 1, 3, ARRAY['equations', 'inequalities', 'solving', 'solutions'], 0.50, 'Major Work', FALSE, NULL),
('6.EE.6', 'Use variables to represent numbers and write expressions when solving a real-world or mathematical problem.', 6, 1, 3, ARRAY['variables', 'expressions', 'real-world', 'represent'], 0.55, 'Major Work', FALSE, NULL),
('6.EE.7', 'Solve real-world and mathematical problems by writing and solving equations of the form x + p = q and px = q for cases in which p, q and x are all nonnegative rational numbers.', 6, 1, 3, ARRAY['equations', 'solve', 'real-world', 'one-step', 'addition', 'multiplication'], 0.60, 'Major Work', FALSE, NULL),
('6.EE.8', 'Write an inequality of the form x > c or x < c to represent a constraint or condition in a real-world or mathematical problem.', 6, 1, 3, ARRAY['inequalities', 'constraint', 'real-world', 'conditions'], 0.50, 'Major Work', FALSE, NULL),
('6.EE.9', 'Use variables to represent two quantities in a real-world problem that change in relationship to one another.', 7, 1, 3, ARRAY['variables', 'dependent', 'independent', 'relationship', 'graph', 'table', 'equation'], 0.65, 'Major Work', FALSE, NULL),

-- Geometry
('6.G.1', 'Find the area of right triangles, other triangles, special quadrilaterals, and polygons by composing into rectangles or decomposing into triangles and other shapes.', 8, 1, 4, ARRAY['area', 'triangles', 'quadrilaterals', 'polygons', 'compose', 'decompose'], 0.60, 'Supporting', TRUE, 'geometry'),
('6.G.2', 'Find the volume of a right rectangular prism with fractional edge lengths by packing it with unit cubes of the appropriate unit fraction edge lengths.', 8, 1, 4, ARRAY['volume', 'rectangular prism', 'fractional', 'unit cubes'], 0.70, 'Supporting', TRUE, '3d'),
('6.G.3', 'Draw polygons in the coordinate plane given coordinates for the vertices; use coordinates to find the length of a side joining points with the same first coordinate or the same second coordinate.', 8, 1, 4, ARRAY['coordinate plane', 'polygons', 'vertices', 'distance'], 0.65, 'Supporting', TRUE, 'geometry'),
('6.G.4', 'Represent three-dimensional figures using nets made up of rectangles and triangles, and use the nets to find the surface area of these figures.', 8, 1, 4, ARRAY['3D figures', 'nets', 'surface area', 'rectangles', 'triangles'], 0.65, 'Supporting', TRUE, '3d'),

-- Statistics & Probability
('6.SP.1', 'Recognize a statistical question as one that anticipates variability in the data related to the question and accounts for it in the answers.', 9, 1, 5, ARRAY['statistical question', 'variability', 'data'], 0.35, 'Additional', FALSE, NULL),
('6.SP.2', 'Understand that a set of data collected to answer a statistical question has a distribution which can be described by its center, spread, and overall shape.', 9, 1, 5, ARRAY['data distribution', 'center', 'spread', 'shape'], 0.50, 'Additional', FALSE, NULL),
('6.SP.3', 'Recognize that a measure of center for a numerical data set summarizes all of its values with a single number, while a measure of variation describes how its values vary with a single number.', 9, 1, 5, ARRAY['measure of center', 'measure of variation', 'mean', 'median', 'range', 'MAD'], 0.55, 'Additional', FALSE, NULL),
('6.SP.4', 'Display numerical data in plots on a number line, including dot plots, histograms, and box plots.', 10, 1, 5, ARRAY['dot plot', 'histogram', 'box plot', 'number line', 'display'], 0.60, 'Additional', TRUE, 'graphing'),
('6.SP.5', 'Summarize numerical data sets in relation to their context.', 10, 1, 5, ARRAY['summarize', 'data', 'context', 'observations', 'attributes', 'measures'], 0.60, 'Additional', FALSE, NULL);
    RETURN NEW;
END;
$$ language 'plpgsql';

COMMENT ON TABLE subjects IS 'Top-level subject areas (MATH, ELA, etc.)';
COMMENT ON TABLE grades IS 'Grade levels within subjects';
COMMENT ON TABLE domains IS 'Major conceptual domains within subjects';
COMMENT ON TABLE clusters IS 'Clusters of related standards';
COMMENT ON TABLE standards IS 'Individual learning standards with metadata';
