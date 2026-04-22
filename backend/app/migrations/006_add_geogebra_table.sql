-- Migration: Add geogebra table for GeoGebra applet command templates
-- This table stores per-applet-type command reference data used when
-- generating diagram-based questions for standards with requires_diagram=true.

CREATE TABLE IF NOT EXISTS geogebra (
    id SERIAL PRIMARY KEY,
    applet_type VARCHAR(20) UNIQUE NOT NULL,
    valid_command_template TEXT[] NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add auto-update trigger if the helper function exists
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'update_updated_at_column') THEN
        CREATE TRIGGER update_geogebra_updated_at
            BEFORE UPDATE ON geogebra
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$;

-- Seed applet command templates matching dev environment
INSERT INTO geogebra (applet_type, valid_command_template, description) VALUES
('graphing',
 ARRAY[
     'A = (1, 2)', 'y = x', 'x = 2', 'f(x) = x^2', 'g(x) = sin(x)',
     'h(x) = cos(x)', 'i(x) = tan(x)', 'j(x) = log(x)', 'k(x) = ln(x)',
     'l(x) = sqrt(x)', 'm(x) = abs(x)', 'n(x) = x^3', 'o(x) = exp(x)'
 ],
 'Graphing Calculator: 13 valid commands (1 Point + 2 Lines + 10 Functions). Templates: Point="A = (x,y)", Lines="y=expr" or "x=num", Functions="f(x)=expr"'),

('3d',
 ARRAY[
     'A = (1, 2, 3)', 'B = (0, 0, 0)', 'C = (5, -2, 1.5)',
     'Sphere[(0, 0, 0), 3]', 'Sphere[B, 2]', 'Cube[(0, 0, 0), (1, 1, 1)]',
     'Cube[B, C]', 'Cone[(0, 0, 5), (0, 0, 0), 2]', 'Cylinder[(0, 0, 0), (0, 0, 5), 2]',
     'Plane[(0, 0, 0), (1, 0, 0), (0, 1, 0)]', 'z = 0', 'x = 0', 'y = 0',
     'Line[(0, 0, 0), (1, 1, 1)]', 'z = x^2 + y^2', 'Distance[A, B]',
     'Segment[(0, 0, 0), (1, 1, 1)]', 'Vector[(0, 0, 0), (1, 2, 3)]',
     'Ray[(0, 0, 0), (1, 1, 1)]', 'Polygon[(0, 0, 0), (2, 0, 0), (2, 2, 0), (0, 2, 0)]',
     'Midpoint[(0, 0, 0), (2, 2, 2)]', 'Circle[(0, 0, 0), 3, z=0]',
     'PerpendicularPlane[(1, 2, 3), Line[(0, 0, 0), (0, 0, 1)]]',
     'PlaneBisector[(0, 0, 0), (4, 0, 0)]',
     'Prism[(0,0,0), (2,0,0), (1,1,0), (0,1,0), (0,0,3)]',
     'Pyramid[(0,0,0), (2,0,0), (1,1,0), (0,1,0), (1, 0.5, 3)]'
 ],
 'GeoGebra 3D Calculator valid commands for 3D geometry questions. Tested on 2026-04-10.'),

('geometry',
 ARRAY[
     'A = (0, 0)', '(1, 2)', 'Circle((3, 0), 2)', 'Semicircle((0,0), (4,0))',
     'Incircle((0,0), (3,0), (1.5,2))', 'Center(Circle((0,0), 2))',
     'Segment((0,0), (4,0))', 'Line((0,0), (2,2))', 'Ray((0,0), (1,1))',
     'PerpendicularLine((2,2), Line((0,0),(3,3)))', 'PerpendicularBisector((0,0), (4,0))',
     'Midpoint((0,0), (4,0))', 'Polygon((0,0), (3,0), (2,2))',
     'Reflect((2,2), Line((0,0),(3,3)))', 'Rotate((2,0), 45°, (0,0))',
     'Translate((2,2), Vector((1,0)))', 'Dilate((2,2), 2, (0,0))'
 ],
 'Geometry commands - 17 valid commands tested'),

('classic',
 ARRAY[
     'A = (1, 2)', 'B = (3, 4)', 'C = (0, 0)', 'f(x) = x^2', 'g(x) = sin(x)',
     'h(x) = 2*x + 3', 'c = Circle((0,0), 3)', 'c2 = Circle(A, B)',
     't = Polygon((0,0), (3,0), (2,2))', 'q = Polygon((0,0), (2,0), (2,2), (0,2))',
     'Solve[x^2 = 4]', 'Factor[x^2 - 4]', 'Expand[(x+2)(x-3)]', 'Derivative[x^2]',
     'Integral[x]', 'Root[f]', 'Extremum[f]', 'M = {{1, 2}, {3, 4}}',
     'N = {{2, 0}, {0, 2}}', 'Mean[{1, 2, 3, 4, 5}]', 'D = Midpoint[A, B]',
     'l = Line[A, B]', 'm = PerpendicularLine[A, l]', 'n = Tangent[A, c]',
     'Segment(A, B)', 'Ray(C, A)', 'Angle(A, C, B)', 'Distance(A, B)',
     'Area(t)', 'Radius(c)', 'Circumference(c)', 'Semicircle(A, B)',
     'AngleBisector(A, C, B)', 'Solutions[x^2 = 4]', 'NSolve[x^2 = 4]',
     'Simplify[x + x]', 'GCD[12, 18]', 'LCM[12, 18]', 'Mod[17, 5]',
     'IsPrime[13]', 'Degree[x^3 + 2*x]', 'Coefficients[x^2 + 3*x + 2]',
     'Derivative[x^3 + 2*x, x]', 'Derivative[x^3, x, 2]', 'Integral[x^2, x]',
     'Integral[x, 0, 1]', 'Limit[sin(x)/x, 0]', 'TurningPoint[f]',
     'InflectionPoint[f]', 'TaylorPolynomial[sin(x), 0, 5]', 'Determinant[M]',
     'Invert[M]', 'Transpose[M]', 'Identity[3]', 'SD[{1, 2, 3, 4, 5}]',
     'Variance[{1, 2, 3, 4, 5}]', 'Median[{1, 2, 3, 4, 5}]',
     'Ellipse((0,0), (3,0), (1,2))', 'Hyperbola((0,0), (3,0), (1,2))',
     'u = Vector((1, 2))', 'Dot[u, (2, 3)]', 'PerpendicularVector(u)',
     'UnitVector(u)', 'Sequence[n^2, n, 1, 10]', 'Sum[n^2, n, 1, 10]',
     'ToComplex[(1, 2)]', 'ToPoint[1 + 2*i]', 'Solve[x^2 = -1]'
 ],
 'GeoGebra Classic commands - tested 2026-04-10'),

('cas',
 ARRAY[
     'Solve[x^2 = 4]', 'NSolve[x^2=4]', 'Expand[(x+1)^2]', 'Factor[x^2-1]',
     'Simplify[2x+3x]', 'Derivative[x^2]', 'Integral[x]'
 ],
 'CAS (Computer Algebra System): 7 valid commands for symbolic math including Solve, Derivative, Integral, Expand, Factor, Simplify'),

('scientific',
 ARRAY['2+3', 'sin(30)', 'cos(60)'],
 'Scientific Calculator: Basic arithmetic and functions (sin, cos, log, sqrt). Very limited - just a calculator.');

-- Handle conflict if running again
ON CONFLICT (applet_type) DO NOTHING;
