/**
 * GeoGebra Applet Commands Registry
 * Maps each applet type to its valid commands and API methods
 */

export type AppletType = 'graphing' | 'geometry' | '3d' | 'classic' | 'cas' | 'scientific';

export interface AppletCapabilities {
  evalCommands: string[];      // Commands for evalCommand()
  apiMethods: string[];        // JavaScript API methods
  requires3D: boolean;         // Supports 3D operations
  categories: {
    creation: string[];        // Object creation commands
    measurement: string[];     // Measurement commands
    transformation: string[];  // Transformations
    styling: string[];         // Visual styling
    view: string[];            // View control
  };
}

/**
 * Command registry for all GeoGebra applet types
 */
export const GEOGEBRA_COMMANDS: Record<AppletType, AppletCapabilities> = {
  // GRAPHING CALCULATOR - 2D functions and coordinate geometry
  graphing: {
    requires3D: false,
    evalCommands: [
      // Functions
      'f(x)', 'g(x)', 'h(x)',
      // 2D Points
      'Point', 'Midpoint', 'Center',
      // 2D Lines
      'Line', 'Segment', 'Ray', 'Vector',
      // Circles and Conics
      'Circle', 'Ellipse', 'Hyperbola', 'Parabola',
      // Polygons
      'Polygon', 'Triangle', 'Quadrilateral', 'Rectangle', 'Square', 'Rhombus',
      // Angles
      'Angle', 'PerpendicularBisector', 'AngularBisector',
      // Intersections
      'Intersect', 'Root', 'Extremum',
      // Transformations (2D)
      'Reflect', 'Rotate', 'Translate', 'Dilate',
      // Special
      'Tangent', 'Polar', 'Diameter',
      // Sliders and text
      'Slider', 'Text',
    ],
    apiMethods: [
      'evalCommand', 'evalCommandGetLabels',
      'setValue', 'getValue',
      'setCoords', 'getXcoord', 'getYcoord',
      'setColor', 'setLineThickness', 'setLineStyle',
      'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      'setLabelVisible', 'setLayer',
      'setCoordSystem', 'setAxesVisible', 'setGridVisible',
      'setAxisLabels', 'setAxisUnits',
      'setMode', 'reset', 'newConstruction', 'refreshViews',
      'getXML', 'setXML', 'getBase64', 'setBase64',
      'getPNGBase64', 'getSVG',
      'registerAddListener', 'registerRemoveListener',
      'registerUpdateListener', 'registerClickListener',
      'unregisterAddListener', 'unregisterRemoveListener',
      'unregisterUpdateListener', 'unregisterClickListener',
    ],
    categories: {
      creation: [
        'Point', 'Midpoint', 'Center',
        'Line', 'Segment', 'Ray', 'Vector',
        'Circle', 'Ellipse', 'Hyperbola', 'Parabola',
        'Polygon', 'Triangle', 'Quadrilateral', 'Rectangle', 'Square',
        'Slider', 'Text',
      ],
      measurement: [
        'Distance', 'Length', 'Radius', 'Area', 'Angle', 'Slope',
      ],
      transformation: [
        'Reflect', 'Rotate', 'Translate', 'Dilate',
      ],
      styling: [
        'setColor', 'setLineThickness', 'setLineStyle',
        'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      ],
      view: [
        'setCoordSystem', 'setAxesVisible', 'setGridVisible',
        'setAxisLabels', 'setAxisUnits',
      ],
    },
  },

  // GEOMETRY - Constructions and geometric proofs
  geometry: {
    requires3D: false,
    evalCommands: [
      // Points
      'Point', 'Midpoint', 'Center', 'Intersect',
      // Lines
      'Line', 'Segment', 'Ray', 'Vector', 'Polyline',
      // Special lines
      'PerpendicularLine', 'ParallelLine', 'PerpendicularBisector',
      'AngularBisector', 'TangentLine', 'Asymptote', 'Directrix',
      // Circles
      'Circle', 'Semicircle', 'Circumcircle', 'Incircle',
      'CircularArc', 'CircularSector', 'CircumcircularArc', 'CircumcircularSector',
      // Conics
      'Conic', 'Ellipse', 'Hyperbola', 'Parabola',
      // Polygons
      'Polygon', 'Triangle', 'Quadrilateral', 'Rectangle', 'Square',
      'RegularPolygon', 'RigidPolygon', 'VectorPolygon',
      // Angles
      'Angle', 'InteriorAngles',
      // Transformations
      'Mirror', 'Reflect', 'Rotate', 'Translate', 'Dilate', 'Stretch',
      // Constructions
      'Locus', 'Tangent', 'Polar', 'Diameter',
      // Advanced
      'ConicThroughFivePoints', 'EllipseThreePoints', 'HyperbolaThreePoints',
      'ParabolaFocusDirectrix', 'FitLine', 'FitLineX',
    ],
    apiMethods: [
      'evalCommand', 'evalCommandGetLabels',
      'setValue', 'getValue',
      'setCoords', 'getXcoord', 'getYcoord',
      'setColor', 'setLineThickness', 'setLineStyle',
      'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      'setLabelVisible', 'setLayer',
      'setCoordSystem', 'setAxesVisible', 'setGridVisible',
      'setMode', 'reset', 'newConstruction', 'refreshViews',
      'getXML', 'setXML', 'getBase64', 'setBase64',
      'registerAddListener', 'registerRemoveListener',
      'registerUpdateListener', 'registerClickListener',
      'registerClientListener',
    ],
    categories: {
      creation: [
        'Point', 'Midpoint', 'Center', 'Intersect',
        'Line', 'Segment', 'Ray', 'Vector',
        'PerpendicularLine', 'ParallelLine', 'PerpendicularBisector',
        'Circle', 'Semicircle', 'Circumcircle', 'Incircle',
        'Polygon', 'Triangle', 'Quadrilateral', 'Rectangle', 'Square', 'RegularPolygon',
      ],
      measurement: [
        'Distance', 'Length', 'Radius', 'Area', 'Angle', 'InteriorAngles',
        'Circumference', 'Perimeter',
      ],
      transformation: [
        'Mirror', 'Reflect', 'Rotate', 'Translate', 'Dilate', 'Stretch',
      ],
      styling: [
        'setColor', 'setLineThickness', 'setLineStyle',
        'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      ],
      view: [
        'setCoordSystem', 'setAxesVisible', 'setGridVisible',
      ],
    },
  },

  // 3D - 3D geometry and graphing
  '3d': {
    requires3D: true,
    evalCommands: [
      // 3D Points and vectors
      'Point', 'PointIn', 'Midpoint', 'Center',
      // 3D Lines
      'Line', 'Segment', 'Ray', 'Vector', 'Polyline',
      'PerpendicularLine', 'PerpendicularBisector',
      // 3D Planes
      'Plane', 'PerpendicularPlane', 'PlaneBisector',
      // 3D Solids
      'Cube', 'Sphere', 'Cone', 'Cylinder', 'Prism', 'Pyramid',
      // Polyhedra
      'Tetrahedron', 'Octahedron', 'Dodecahedron', 'Icosahedron',
      // Infinite surfaces
      'InfiniteCone', 'InfiniteCylinder',
      // Circles in 3D
      'Circle', 'CircularArc', 'CircularSector',
      'CircumcircularArc', 'CircumcircularSector',
      // Intersections
      'Intersect', 'IntersectConic', 'IntersectPath',
      // Curves and surfaces
      'Curve', 'Surface', 'Function',
      // 3D Transformations
      'Mirror', 'Reflect', 'Rotate', 'Translate', 'Dilate',
      // Measurements
      'Volume', 'Height', 'Radius', 'Distance',
      // Net for unfolding
      'Net',
      // 3D specific
      'Top', 'Bottom', 'Ends', 'Side',
      'Vertex', 'Vertices',
    ],
    apiMethods: [
      'evalCommand', 'evalCommandGetLabels',
      'setValue', 'getValue',
      'setCoords', 'getXcoord', 'getYcoord', 'getZcoord',
      'setColor', 'setLineThickness', 'setLineStyle',
      'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      'setLabelVisible', 'setLayer',
      // 3D-specific view methods
      'setCoordSystem', // 6 params for 3D: xmin,xmax,ymin,ymax,zmin,zmax,yVertical
      'setAxesVisible', // with 3D support
      'setAxisLabels', 'setAxisUnits', // with 3D support
      'enable3D',
      'setMode', 'reset', 'newConstruction', 'refreshViews',
      'getXML', 'setXML', 'getBase64', 'setBase64',
      'registerAddListener', 'registerRemoveListener',
      'registerUpdateListener', 'registerClickListener',
    ],
    categories: {
      creation: [
        'Point', 'Midpoint', 'Center',
        'Line', 'Segment', 'Ray',
        'Plane', 'PerpendicularPlane', 'PlaneBisector',
        'Cube', 'Sphere', 'Cone', 'Cylinder', 'Prism', 'Pyramid',
        'Tetrahedron', 'Octahedron', 'Dodecahedron', 'Icosahedron',
        'Curve', 'Surface',
      ],
      measurement: [
        'Volume', 'Height', 'Radius', 'Distance',
        'Angle', 'Area',
      ],
      transformation: [
        'Mirror', 'Reflect', 'Rotate', 'Translate', 'Dilate',
      ],
      styling: [
        'setColor', 'setLineThickness', 'setLineStyle',
        'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      ],
      view: [
        'setCoordSystem', // 6 params for 3D
        'setAxesVisible', // supports 3D axes
        'enable3D',
      ],
    },
  },

  // CLASSIC - Full GeoGebra with all features
  classic: {
    requires3D: true, // Classic includes 3D view
    evalCommands: [
      // All graphing commands
      'f(x)', 'g(x)', 'h(x)',
      'Point', 'Midpoint', 'Center',
      'Line', 'Segment', 'Ray', 'Vector',
      'Circle', 'Ellipse', 'Hyperbola', 'Parabola',
      'Polygon', 'Triangle', 'Quadrilateral', 'Rectangle', 'Square',
      'Angle', 'PerpendicularBisector', 'AngularBisector',
      'Intersect', 'Root', 'Extremum', 'Tangent',
      // All geometry commands
      'PerpendicularLine', 'ParallelLine', 'TangentLine',
      'Semicircle', 'Circumcircle', 'Incircle',
      'CircularArc', 'CircularSector',
      'RegularPolygon', 'RigidPolygon', 'VectorPolygon',
      'Locus', 'Polar', 'Diameter',
      // All 3D commands
      'Plane', 'PerpendicularPlane', 'PlaneBisector',
      'Cube', 'Sphere', 'Cone', 'Cylinder', 'Prism', 'Pyramid',
      'Tetrahedron', 'Octahedron', 'Dodecahedron', 'Icosahedron',
      'InfiniteCone', 'InfiniteCylinder',
      'Curve', 'Surface', 'Net',
      // CAS-specific
      'Solve', 'NSolve', 'Derivative', 'Integral', 'Limit',
      'Expand', 'Factor', 'Simplify', 'Coefficients',
    ],
    apiMethods: [
      'evalCommand', 'evalCommandGetLabels',
      'evalCommandCAS', // CAS evaluation
      'setValue', 'getValue',
      'setCoords', 'getXcoord', 'getYcoord', 'getZcoord',
      'setColor', 'setLineThickness', 'setLineStyle',
      'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      'setLabelVisible', 'setLayer',
      'setCoordSystem',
      'setAxesVisible', 'setGridVisible',
      'setAxisLabels', 'setAxisUnits',
      'setMode', 'reset', 'newConstruction', 'refreshViews',
      'getXML', 'setXML', 'getBase64', 'setBase64',
      'getPNGBase64', 'getSVG', 'exportPDF',
      'enable3D', 'showCAS', // CAS view
      'registerAddListener', 'registerRemoveListener',
      'registerUpdateListener', 'registerClickListener',
      'registerClientListener',
    ],
    categories: {
      creation: [
        'Point', 'Midpoint', 'Center',
        'Line', 'Segment', 'Ray', 'Vector',
        'Circle', 'Ellipse', 'Hyperbola', 'Parabola',
        'Polygon', 'Triangle', 'Quadrilateral', 'Rectangle', 'Square',
        'Plane', 'Cube', 'Sphere', 'Cone', 'Cylinder',
        'Tetrahedron', 'Octahedron', 'Dodecahedron', 'Icosahedron',
        'Curve', 'Surface',
      ],
      measurement: [
        'Distance', 'Length', 'Radius', 'Area', 'Angle',
        'Volume', 'Height', 'Circumference', 'Perimeter',
      ],
      transformation: [
        'Mirror', 'Reflect', 'Rotate', 'Translate', 'Dilate', 'Stretch',
      ],
      styling: [
        'setColor', 'setLineThickness', 'setLineStyle',
        'setPointSize', 'setPointStyle', 'setFixed', 'setVisible',
      ],
      view: [
        'setCoordSystem', 'setAxesVisible', 'setGridVisible',
        'setAxisLabels', 'setAxisUnits', 'enable3D', 'showCAS',
      ],
    },
  },

  // CAS - Computer Algebra System
  cas: {
    requires3D: false,
    evalCommands: [
      // CAS symbolic operations
      'Solve', 'NSolve', 'CSolve', 'NSolutions',
      'Derivative', 'Integral', 'Limit', 'Sum', 'Product',
      'Expand', 'Factor', 'Simplify', 'CompleteSquare',
      'Coefficients', 'Degree', 'Numerator', 'Denominator',
      'PartialFractions', 'PrimeFactors', 'Divisors', 'LCM', 'GCD',
      'TrigExpand', 'TrigSimplify', 'TrigCombine',
      'ComplexRoot', 'Root', 'TurningPoint', 'InflectionPoint',
      // Still supports basic functions
      'f(x)', 'g(x)', 'h(x)',
      'Point', 'Line', 'Circle',
      'Intersect', 'Root',
    ],
    apiMethods: [
      'evalCommand', 'evalCommandGetLabels',
      'evalCommandCAS', // Primary method for CAS
      'setValue', 'getValue',
      'setCoords', 'getXcoord', 'getYcoord',
      'setColor', 'setFixed', 'setVisible',
      'setCoordSystem', 'setAxesVisible', 'setGridVisible',
      'setMode', 'reset', 'newConstruction',
      'getXML', 'setXML', 'getBase64', 'setBase64',
    ],
    categories: {
      creation: [
        'f(x)', 'Point', 'Line', 'Circle',
      ],
      measurement: [
        'Solve', 'NSolve', 'Derivative', 'Integral', 'Limit',
        'Root', 'Intersect',
      ],
      transformation: [
        'Expand', 'Factor', 'Simplify', 'CompleteSquare',
        'TrigExpand', 'TrigSimplify', 'TrigCombine',
      ],
      styling: [
        'setColor', 'setFixed', 'setVisible',
      ],
      view: [
        'setCoordSystem', 'setAxesVisible', 'setGridVisible',
      ],
    },
  },

  // SCIENTIFIC - Basic calculator, minimal commands
  scientific: {
    requires3D: false,
    evalCommands: [
      // Basic functions only
      'f(x)', 'g(x)',
      'Point',
      'Line', 'Segment',
      'Circle',
      // Basic calculations
      'Solve', 'NSolve',
      'Derivative', 'Integral',
    ],
    apiMethods: [
      'evalCommand',
      'setValue', 'getValue',
      'setCoordSystem', 'setAxesVisible',
      'reset', 'newConstruction',
    ],
    categories: {
      creation: [
        'f(x)', 'Point', 'Line', 'Segment', 'Circle',
      ],
      measurement: [
        'Solve', 'NSolve', 'Derivative', 'Integral',
      ],
      transformation: [],
      styling: [],
      view: [
        'setCoordSystem', 'setAxesVisible',
      ],
    },
  },
};

/**
 * Get all commands available for a specific applet type
 */
export function getCommandsForApplet(appletType: AppletType): AppletCapabilities {
  return GEOGEBRA_COMMANDS[appletType];
}

/**
 * Check if a command is valid for a specific applet type
 */
export function isValidCommand(appletType: AppletType, command: string): boolean {
  const capabilities = GEOGEBRA_COMMANDS[appletType];
  if (!capabilities) return false;

  return capabilities.evalCommands.includes(command) ||
         capabilities.apiMethods.includes(command);
}

/**
 * Check if an API method is available for a specific applet type
 */
export function isValidApiMethod(appletType: AppletType, method: string): boolean {
  const capabilities = GEOGEBRA_COMMANDS[appletType];
  if (!capabilities) return false;

  return capabilities.apiMethods.includes(method);
}

/**
 * Get commands by category for an applet type
 */
export function getCommandsByCategory(
  appletType: AppletType,
  category: keyof AppletCapabilities['categories']
): string[] {
  return GEOGEBRA_COMMANDS[appletType]?.categories[category] ?? [];
}

/**
 * Check if applet supports 3D operations
 */
export function supports3D(appletType: AppletType): boolean {
  return GEOGEBRA_COMMANDS[appletType]?.requires3D ?? false;
}

/**
 * Get all available applet types
 */
export function getAppletTypes(): AppletType[] {
  return Object.keys(GEOGEBRA_COMMANDS) as AppletType[];
}

/**
 * Find which applet types support a specific command
 */
export function findAppletTypesForCommand(command: string): AppletType[] {
  return (Object.keys(GEOGEBRA_COMMANDS) as AppletType[]).filter(
    appletType => isValidCommand(appletType, command)
  );
}

/**
 * Get suggestions for similar commands (simple fuzzy match)
 */
export function suggestCommands(
  appletType: AppletType,
  partial: string,
  limit: number = 5
): string[] {
  const capabilities = GEOGEBRA_COMMANDS[appletType];
  if (!capabilities) return [];

  const allCommands = [...capabilities.evalCommands, ...capabilities.apiMethods];
  const lowerPartial = partial.toLowerCase();

  return allCommands
    .filter(cmd => cmd.toLowerCase().includes(lowerPartial))
    .slice(0, limit);
}

export default GEOGEBRA_COMMANDS;
