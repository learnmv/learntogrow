# GeoGebra JavaScript API Reference

> Complete reference for programmatically controlling GeoGebra applets via JavaScript.

## Table of Contents
- [Overview](#overview)
- [Embedding GeoGebra](#embedding-geogebra)
- [Core API Methods](#core-api-methods)
- [Object Properties](#object-properties)
- [Event Listeners](#event-listeners)
- [Export & Serialization](#export--serialization)
- [Parameters Reference](#parameters-reference)
- [Examples](#examples)
- [Sources](#sources)

---

## Overview

GeoGebra's JavaScript API enables programmatic control over embedded applets. Access the API through:
- The `api` parameter in `appletOnLoad` callback
- The global `ggbApplet` variable (default, customizable via `id` parameter)

### API Categories
- **Commands & Evaluation** - Execute GeoGebra commands
- **Object Manipulation** - Get/set values, coordinates, visibility
- **Construction Control** - Reset, clear, change modes
- **Event Handling** - Listen to user interactions
- **Export/Import** - Save/load constructions

---

## Embedding GeoGebra

### Basic Setup

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>GeoGebra Integration</title>
</head>
<body>
    <div id="ggb-element"></div>

    <script src="https://www.geogebra.org/apps/deployggb.js"></script>
    <script>
        var params = {
            "appName": "graphing",
            "width": 800,
            "height": 600,
            "showToolBar": true,
            "showAlgebraInput": true,
            "showMenuBar": true
        };

        var applet = new GGBApplet(params, true);

        window.addEventListener("load", function() {
            applet.inject('ggb-element');
        });
    </script>
</body>
</html>
```

### App Types

| App Name | Description |
|----------|-------------|
| `"graphing"` | Graphing Calculator (default) |
| `"geometry"` | Geometry |
| `"3d"` | 3D Graphing |
| `"classic"` | Classic GeoGebra |
| `"cas"` | CAS Calculator |
| `"scientific"` | Scientific Calculator |

### Loading Existing Content

```javascript
// Load from GeoGebra Materials (use material ID)
var params = {
    "material_id": "RHYH3UQ8",
    "width": 800,
    "height": 600
};

// Load from local .ggb file
var params = {
    "filename": "myFile.ggb",
    "width": 800,
    "height": 600
};
```

### Advanced Initialization

```javascript
var params = {
    // Identity
    "id": "myApplet",           // Custom ID (default: ggbApplet)
    "material_id": "fwz3d6c3",  // Load from GeoGebra tube
    "filename": "file.ggb",     // Load local file

    // Dimensions
    "width": 800,
    "height": 600,

    // UI Controls
    "showToolBar": false,
    "showAlgebraInput": false,
    "showMenuBar": false,
    "showResetIcon": false,
    "enableLabelDrags": false,
    "enableShiftDragZoom": true,
    "enableRightClick": false,
    "enableCAS": false,

    // Behavior
    "allowStyleBar": false,
    "useBrowserForJS": false,
    "language": "en",
    "country": "US",
    "ggbBase64": "...",         // Inline base64 content
    "appletOnLoad": function(api) {
        // API is ready
        console.log("GeoGebra loaded");
    }
};
```

---

## Core API Methods

### Commands & Evaluation

#### `evalCommand(String cmdString)`
Executes GeoGebra commands as if entered in the Input Bar.

```javascript
// Create objects
api.evalCommand("A = (1, 2)");
api.evalCommand("B = (3, 4)");
api.evalCommand("C = Midpoint(A, B)");

// Create functions
api.evalCommand("f(x) = x^2");
api.evalCommand("g: y = 2x + 1");

// Create shapes
api.evalCommand("poly = Polygon(A, B, 5)");
api.evalCommand("c = Circle(A, 3)");

// Delete objects
api.evalCommand("Delete(A)");
```

#### `evalCommandGetLabels(String cmdString)`
Returns comma-separated labels of created objects.

```javascript
var labels = api.evalCommandGetLabels("A = (1,2); B = (3,4)");
// Returns: "A,B"
```

#### `evalCommandCAS(String expression)`
Evaluates expressions in the CAS (Computer Algebra System).

```javascript
api.evalCommandCAS("Solve[x^2 - 4 = 0]");
api.evalCommandCAS("Derivative[x^3 + 2x]");
```

### Setting Object Properties

#### `setValue(String objName, double value)`
Set numeric or boolean values.

```javascript
api.setValue("a", 5);           // Set slider value
api.setValue("showGrid", true); // Boolean
api.setValue("step", 0.1);
```

#### `setCoords(String objName, double x, double y)`
Set 2D coordinates.

```javascript
api.setCoords("A", 5, 3);
```

#### `setCoords(String objName, double x, double y, double z)`
Set 3D coordinates.

```javascript
api.setCoords("A", 1, 2, 3);
```

#### `setColor(String objName, int red, int green, int blue)`
Set object color (0-255 RGB).

```javascript
api.setColor("A", 255, 0, 0);    // Red
api.setColor("poly", 0, 128, 255); // Blue
```

#### `setLineThickness(String objName, int thickness)`
Set line thickness (1-13).

```javascript
api.setLineThickness("f", 3);
```

#### `setLineStyle(String objName, int style)`
Set line style (0=solid, 1=dash, 2=dot, 3=dash-dot).

```javascript
api.setLineStyle("g", 1); // Dashed
```

#### `setPointSize(String objName, int size)`
Set point size (1-9).

```javascript
api.setPointSize("A", 5);
```

#### `setPointStyle(String objName, int style)`
Set point style (0=circle, 1=cross, 2=diamond, etc.).

```javascript
api.setPointStyle("A", 2); // Diamond
```

#### `setFixed(String objName, boolean fixed, boolean selectionAllowed)`
Lock objects from being moved.

```javascript
api.setFixed("A", true, false);   // Fixed, not selectable
api.setFixed("center", true, true); // Fixed but selectable
```

#### `setVisible(String objName, boolean visible)`
Show or hide objects.

```javascript
api.setVisible("A", false);
api.setVisible("grid", true);
```

#### `setLabelVisible(String objName, boolean visible)`
Show or hide labels.

```javascript
api.setLabelVisible("A", true);
```

#### `setLayer(String objName, int layer)`
Set drawing layer (0=back, higher numbers=front).

```javascript
api.setLayer("background", 0);
api.setLayer("foreground", 10);
```

### Getting Object Properties

#### `getValue(String objName)`
Returns numeric value (length, area, slider value, etc.).

```javascript
var area = api.getValue("poly");
var xCoord = api.getValue("A");
```

#### `getXcoord(String objName)`, `getYcoord(String objName)`, `getZcoord(String objName)`
Get coordinates of points.

```javascript
var x = api.getXcoord("A");
var y = api.getYcoord("A");
var z = api.getZcoord("A"); // 3D only
```

#### `getColor(String objName)`
Returns hex color string.

```javascript
var color = api.getColor("A");
// Returns: "#FF0000"
```

#### `getObjectType(String objName)`
Returns object type.

```javascript
var type = api.getObjectType("A");
// Returns: "point", "line", "circle", "polygon", etc.
```

#### `getAllObjectNames()`
Returns array of all object names.

```javascript
var objects = api.getAllObjectNames();
// Returns: ["A", "B", "f", "poly", ...]
```

#### `getObjectNumber()`
Returns count of objects.

```javascript
var count = api.getObjectNumber();
```

#### `exists(String objName)`
Check if object exists.

```javascript
if (api.exists("A")) {
    // Object exists
}
```

### View & Coordinate System

#### `setCoordSystem(double xmin, double xmax, double ymin, double ymax)`
Set coordinate system bounds.

```javascript
api.setCoordSystem(-10, 10, -5, 5);
```

#### `setAxesVisible(boolean xAxis, boolean yAxis)`
Show/hide axes.

```javascript
api.setAxesVisible(true, true);   // Both axes
api.setAxesVisible(true, false);  // X-axis only
```

#### `setGridVisible(boolean flag)`
Show/hide grid.

```javascript
api.setGridVisible(true);
```

#### `setAxisLabels(int axis, String label)`
Set axis labels (1=x, 2=y).

```javascript
api.setAxisLabels(1, "Time (s)");
api.setAxisLabels(2, "Distance (m)");
```

#### `setAxisUnits(int axis, String unit)`
Set axis units.

```javascript
api.setAxisUnits(1, "sec");
api.setAxisUnits(2, "m");
```

#### `getViewProperties()`
Get current view settings.

```javascript
var props = api.getViewProperties();
```

### Construction Control

#### `setMode(int mode)`
Set mouse/tool mode.

```javascript
api.setMode(0);   // Move mode
api.setMode(1);   // Point mode
api.setMode(2);   // Line mode
api.setMode(3);   // Parallel line mode
// ... see Mode Constants below
```

#### `reset()`
Reload initial construction.

```javascript
api.reset();
```

#### `newConstruction()`
Clear all objects.

```javascript
api.newConstruction();
```

#### `refreshViews()`
Refresh the display.

```javascript
api.refreshViews();
```

#### `repaint()`
Force redraw.

```javascript
api.repaint();
```

### Mode Constants

| Mode | Constant | Description |
|------|----------|-------------|
| 0 | `MODE_MOVE` | Move tool |
| 1 | `MODE_POINT` | New point |
| 2 | `MODE_LINE` | Line through two points |
| 3 | `MODE_PARALLEL` | Parallel line |
| 4 | `MODE_PERPENDICULAR` | Perpendicular line |
| 5 | `MODE_INTERSECT` | Intersection point |
| 6 | `MODE_DELETE` | Delete object |
| 7 | `MODE_VECTOR` | Vector |
| 8 | `MODE_LINE_BISECTOR` | Perpendicular bisector |
| 9 | `MODE_ANGULAR_BISECTOR` | Angle bisector |
| 10 | `MODE_CIRCLE_TWO_POINTS` | Circle with center through point |
| 11 | `MODE_CIRCLE_THREE_POINTS` | Circle through three points |
| 12 | `MODE_CONIC_FIVE_POINTS` | Conic through five points |
| 13 | `MODE_TANGENTS` | Tangents |
| 14 | `MODE_POLYGON` | Polygon |
| 15 | `MODE_RELATION` | Relation between two objects |
| 16 | `MODE_SEGMENT` | Segment between two points |
| 17 | `MODE_RAY` | Ray through two points |
| 18 | `MODE_VECTOR_FROM_POINT` | Vector from point |
| 19 | `MODE_CIRCLE_ARC_THREE_POINTS` | Circular arc |
| 20 | `MODE_CIRCLE_SECTOR_THREE_POINTS` | Circular sector |
| 21 | `MODE_CIRCUMCIRCLE_ARC_THREE_POINTS` | Circumcircular arc |
| 22 | `MODE_CIRCUMCIRCLE_SECTOR_THREE_POINTS` | Circumcircular sector |
| 23 | `MODE_SEMICIRCLE` | Semicircle |
| 24 | `MODE_SLIDER` | Slider |
| 25 | `MODE_MIRROR_AT_POINT` | Reflect about point |
| 26 | `MODE_MIRROR_AT_LINE` | Reflect about line |
| 27 | `MODE_MIRROR_AT_CIRCLE` | Reflect about circle |
| 28 | `MODE_ROTATE_BY_ANGLE` | Rotate around point |
| 29 | `MODE_TRANSLATE_BY_VECTOR` | Translate by vector |
| 30 | `MODE_DILATE_FROM_POINT` | Dilate from point |
| 31 | `MODE_SHOW_HIDE_OBJECT` | Show/hide object |
| 32 | `MODE_SHOW_HIDE_LABEL` | Show/hide label |
| 33 | `MODE_COPY_VISUAL_STYLE` | Copy visual style |
| 34 | `MODE_ANGLE` | Angle |
| 35 | `MODE_ANGLE_FIXED` | Angle with given size |
| 36 | `MODE_VECTOR_POLYGON` | Vector polygon |
| 37 | `MODE_DISTANCE` | Distance or length |
| 38 | `MODE_MOVE_ROTATE` | Move around point |
| 39 | `MODE_ZOOM_IN` | Zoom in |
| 40 | `MODE_ZOOM_OUT` | Zoom out |
| 41 | `MODE_SHOW_HIDE_axes` | Show/hide axes |
| 42 | `MODE_SHOW_HIDE_GRID` | Show/hide grid |
| 43 | `MODE_UNDO` | Undo |
| 44 | `MODE_REDO` | Redo |
| 45 | `MODE_PEN` | Pen tool |
| 46 | `MODE_FREEHAND` | Freehand shape |
| 47 | `MODE_MIRROR_AT_PLANE` | Reflect about plane (3D) |
| 48 | `MODE_ROTATE_AROUND_LINE` | Rotate around line (3D) |
| 49 | `MODE_CIRCLE_POINT_RADIUS` | Circle with center and radius |
| 50 | `MODE_CIRCLE_POINT_RADIUS_DIRECTION` | Circle with center, radius, direction (3D) |
| 51 | `MODE_ELLIPSE_THREE_POINTS` | Ellipse |
| 52 | `MODE_HYPERBOLA_THREE_POINTS` | Hyperbola |
| 53 | `MODE_PARABOLA_FOCUS_DIRECTRIX` | Parabola |
| 54 | `MODE_FIT_LINE` | Best fit line |
| 55 | `MODE_RECORD_TO_SPREADSHEET` | Record to spreadsheet |
| 60 | `MODE_SLIDER` | Slider (alternative) |
| 61 | `MODE_TEXT` | Insert text |
| 62 | `MODE_IMAGE` | Insert image |
| 64 | `MODE_BUTTON_ACTION` | Insert button |
| 65 | `MODE_INPUT_BOX` | Input box |
| 66 | `MODE_ZOOM_IN` | Zoom in (alternative) |
| 67 | `MODE_ZOOM_OUT` | Zoom out (alternative) |
| 68 | `MODE_SELECTION_LISTENER` | Select object |
| 70 | `MODE_RULER` | Ruler |
| 71 | `MODE_PROTRACTOR` | Protractor |
| 72 | `MODE_PENCIL` | Pencil |
| 73 | `MODE_COMPASSES` | Compass |
| 74 | `MODE_MIRROR_AT_LINE_SEGMENT` | Reflect about segment |
| 75 | `MODE_MIDPOINT` | Midpoint or center |
| 76 | `MODE_CIRCLE_THREE_POINTS` | Circle through three points |
| 77 | `MODE_SEMICIRCLE` | Semicircle |
| 78 | `MODE_CIRCLE_ARC_CENTER_TWO_POINTS` | Circular arc with center |
| 79 | `MODE_CIRCLE_SECTOR_CENTER_TWO_POINTS` | Circular sector with center |

---

## Event Listeners

### Registering Listeners

#### `registerAddListener(String JSFunctionName)`
Called when objects are created.

```javascript
api.registerAddListener("onObjectAdded");

function onObjectAdded(objName) {
    console.log("Created: " + objName);
    console.log("Type: " + api.getObjectType(objName));
}
```

#### `registerRemoveListener(String JSFunctionName)`
Called when objects are deleted.

```javascript
api.registerRemoveListener("onObjectRemoved");

function onObjectRemoved(objName) {
    console.log("Deleted: " + objName);
}
```

#### `registerUpdateListener(String JSFunctionName)`
Called when objects are updated (moved, values changed).

```javascript
api.registerUpdateListener("onObjectUpdated");

function onObjectUpdated(objName) {
    var x = api.getXcoord(objName);
    var y = api.getYcoord(objName);
    console.log(objName + " moved to (" + x + ", " + y + ")");
}
```

#### `registerUpdateListenerForObject(String objName, String JSFunctionName)`
Listen to updates for specific object only.

```javascript
api.registerUpdateListenerForObject("A", "onAUpdated");

function onAUpdated() {
    var x = api.getXcoord("A");
    var y = api.getYcoord("A");
    document.getElementById("coords").innerHTML = "A: (" + x + ", " + y + ")";
}
```

#### `registerClickListener(String JSFunctionName)`
Called when objects are clicked.

```javascript
api.registerClickListener("onObjectClicked");

function onObjectClicked(objName) {
    console.log("Clicked: " + objName);
    api.setColor(objName, 255, 0, 0); // Highlight in red
}
```

#### `registerClientListener(String JSFunctionName)`
Generic listener for various events.

```javascript
api.registerClientListener("onClientEvent");

function onClientEvent(event) {
    // event.type can be:
    // "update", "add", "remove", "rename", "clear", "setMode", "select", "deselect"
    console.log("Event: " + event.type);
    if (event.target) {
        console.log("Target: " + event.target);
    }
}
```

### Unregistering Listeners

```javascript
api.unregisterAddListener("onObjectAdded");
api.unregisterRemoveListener("onObjectRemoved");
api.unregisterUpdateListener("onObjectUpdated");
api.unregisterUpdateListenerForObject("A", "onAUpdated");
api.unregisterClickListener("onObjectClicked");
api.unregisterClientListener("onClientEvent");
```

---

## Export & Serialization

### XML Export/Import

#### `getXML()`
Export entire construction as XML.

```javascript
var xml = api.getXML();
// Save to server or localStorage
localStorage.setItem("ggbConstruction", xml);
```

#### `getXML(String objName)`
Export specific object.

```javascript
var pointXML = api.getXML("A");
```

#### `setXML(String xmlString)`
Load construction from XML.

```javascript
var xml = localStorage.getItem("ggbConstruction");
api.setXML(xml);
```

### Base64 Export/Import

#### `getBase64()`
Export as base64-encoded .ggb file content.

```javascript
var base64 = api.getBase64();
// Save to server
fetch('/save', {
    method: 'POST',
    body: JSON.stringify({content: base64})
});
```

#### `setBase64(String base64String)`
Load from base64.

```javascript
fetch('/load')
    .then(r => r.text())
    .then(base64 => api.setBase64(base64));
```

### Image Export

#### `getPNGBase64(double exportScale, boolean transparent, boolean dpi144)`
Export graphics view as PNG (base64 encoded).

```javascript
// Get PNG at 1x scale, transparent background
var pngBase64 = api.getPNGBase64(1, true, false);

// Use in image element
document.getElementById("screenshot").src = "data:image/png;base64," + pngBase64;
```

#### `getSVG()`
Export as SVG.

```javascript
var svg = api.getSVG();
```

### PDF Export

```javascript
api.exportPDF();
```

---

## Parameters Reference

### Initialization Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `id` | String | `"ggbApplet"` | Applet identifier |
| `appName` | String | `"classic"` | App type (graphing, geometry, 3d, etc.) |
| `width` | Integer | `800` | Applet width |
| `height` | Integer | `600` | Applet height |
| `material_id` | String | - | GeoGebra Material ID |
| `filename` | String | - | Local .ggb file path |
| `ggbBase64` | String | - | Inline base64 content |
| `enableRightClick` | Boolean | `true` | Allow right-click context menu |
| `enableLabelDrags` | Boolean | `true` | Allow dragging labels |
| `enableShiftDragZoom` | Boolean | `true` | Allow zoom with shift+drag |
| `enableCAS` | Boolean | `false` | Enable CAS view |
| `showToolBar` | Boolean | `true` | Show toolbar |
| `showMenuBar` | Boolean | `true` | Show menu bar |
| `showAlgebraInput` | Boolean | `true` | Show input bar |
| `showResetIcon` | Boolean | `false` | Show reset icon |
| `allowStyleBar` | Boolean | `true` | Allow style bar |
| `useBrowserForJS` | Boolean | `true` | Use browser for scripting |
| `language` | String | browser | UI language code |
| `country` | String | browser | Country code |
| `appletOnLoad` | Function | - | Callback when loaded |

### 3D-Specific Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `enable3D` | Boolean | Enable 3D mode |
| `showPlane` | Boolean | Show xy-plane |
| `showAxisX`, `showAxisY`, `showAxisZ` | Boolean | Show individual axes |

---

## Examples

### Example 1: Basic Construction

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>GeoGebra Demo</title>
</head>
<body>
    <div id="ggb-container"></div>
    <button onclick="createTriangle()">Create Triangle</button>
    <button onclick="measureArea()">Measure Area</button>

    <script src="https://www.geogebra.org/apps/deployggb.js"></script>
    <script>
        var ggbAPI;

        var applet = new GGBApplet({
            "appName": "geometry",
            "width": 600,
            "height": 400,
            "showToolBar": false,
            "showMenuBar": false,
            "showAlgebraInput": false,
            "appletOnLoad": function(api) {
                ggbAPI = api;
                api.setGridVisible(true);
            }
        }, true);

        window.addEventListener("load", function() {
            applet.inject('ggb-container');
        });

        function createTriangle() {
            if (!ggbAPI) return;

            ggbAPI.evalCommand("A = (0, 0)");
            ggbAPI.evalCommand("B = (5, 0)");
            ggbAPI.evalCommand("C = (2, 4)");
            ggbAPI.evalCommand("triangle = Polygon(A, B, C)");
            ggbAPI.setColor("triangle", 100, 200, 255);
        }

        function measureArea() {
            if (!ggbAPI) return;

            var area = ggbAPI.getValue("triangle");
            alert("Area: " + area.toFixed(2) + " square units");
        }
    </script>
</body>
</html>
```

### Example 2: Interactive Graph

```javascript
// Create an interactive function plotter
var applet = new GGBApplet({
    "appName": "graphing",
    "width": 800,
    "height": 600,
    "appletOnLoad": function(api) {
        // Set up coordinate system
        api.setCoordSystem(-10, 10, -10, 10);
        api.setAxesVisible(true, true);
        api.setGridVisible(true);

        // Create a slider for 'a'
        api.evalCommand("a = 1");
        api.setFixed("a", false, true);

        // Create function with slider
        api.evalCommand("f(x) = a*x^2");

        // Listen to slider updates
        api.registerUpdateListenerForObject("a", "updateFunction");
    }
}, true);

function updateFunction() {
    var a = ggbApplet.getValue("a");
    document.getElementById("value-display").innerHTML =
        "f(x) = " + a.toFixed(2) + "x²";
}
```

### Example 3: Student Answer Verification

```javascript
// Check if student created correct geometric construction
function verifyConstruction() {
    // Check if point exists at correct location
    if (!ggbApplet.exists("A")) {
        return {correct: false, message: "Point A not found"};
    }

    var x = ggbApplet.getXcoord("A");
    var y = ggbApplet.getYcoord("A");

    // Check if point is at (3, 4) within tolerance
    if (Math.abs(x - 3) < 0.1 && Math.abs(y - 4) < 0.1) {
        return {correct: true, message: "Correct!"};
    } else {
        return {correct: false, message: "Point should be at (3, 4)"};
    }
}
```

### Example 4: Recording Student Work

```javascript
// Save student construction
function saveWork() {
    var state = {
        xml: ggbApplet.getXML(),
        timestamp: new Date().toISOString(),
        studentId: "student123"
    };

    fetch('/api/save-work', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify(state)
    });
}

// Restore student work
function loadWork(workId) {
    fetch('/api/load-work/' + workId)
        .then(r => r.json())
        .then(data => {
            ggbApplet.setXML(data.xml);
        });
}
```

### Example 5: Custom Question with GeoGebra

```javascript
// Create a question about finding the midpoint
function createMidpointQuestion() {
    var api = ggbApplet;

    // Clear previous
    api.newConstruction();
    api.setCoordSystem(-10, 10, -10, 10);

    // Create two random points
    var x1 = Math.floor(Math.random() * 10) - 5;
    var y1 = Math.floor(Math.random() * 10) - 5;
    var x2 = Math.floor(Math.random() * 10) - 5;
    var y2 = Math.floor(Math.random() * 10) - 5;

    // Ensure points are different
    while (x1 === x2 && y1 === y2) {
        x2 = Math.floor(Math.random() * 10) - 5;
        y2 = Math.floor(Math.random() * 10) - 5;
    }

    // Create points
    api.evalCommand(`A = (${x1}, ${y1})`);
    api.evalCommand(`B = (${x2}, ${y2})`);
    api.evalCommand("segment = Segment(A, B)");

    // Hide the actual midpoint
    // Student must construct it

    // Store expected answer
    window.expectedMidpoint = {
        x: (x1 + x2) / 2,
        y: (y1 + y2) / 2
    };

    document.getElementById("question").innerHTML =
        `Find the midpoint of the segment from A(${x1}, ${y1}) to B(${x2}, ${y2}). ` +
        `Use the tools to construct the midpoint, then create a point at that location.`;
}

// Check student's answer
function checkMidpoint() {
    var api = ggbApplet;
    var expected = window.expectedMidpoint;

    // Find student's point
    var objects = api.getAllObjectNames();
    for (var i = 0; i < objects.length; i++) {
        if (api.getObjectType(objects[i]) === "point" &&
            objects[i] !== "A" && objects[i] !== "B") {

            var x = api.getXcoord(objects[i]);
            var y = api.getYcoord(objects[i]);

            if (Math.abs(x - expected.x) < 0.1 &&
                Math.abs(y - expected.y) < 0.1) {
                return {correct: true, message: "Correct!"};
            }
        }
    }
    return {correct: false, message: "Not quite. Try using the Midpoint tool."};
}
```

---

## Sources

- [GeoGebra JavaScript Reference - Official Wiki](https://wiki.geogebra.org/en/Reference:JavaScript)
- [GeoGebra Apps Embedding Guide](https://geogebra.github.io/docs/reference/en/GeoGebra_Apps_Embedding/)
- [Scripting Documentation](https://geogebra.github.io/docs/manual/en/Scripting/)
- [API Examples](https://geogebra.github.io/integration/example-api.html)
- [GeoGebra JavaScript Methods Reference](https://online.math.uh.edu/HoustonACT/GeoGebraWorkshop/WebPages/GeoGebra_JavaScript_Methods.html)

---

*Last Updated: 2024*
