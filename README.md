# Geometry Shapes

This QGis plugin draws basic geometry shapes with user defined measurements and also allows free drawing. 

**Features/usage:**
* Integrates in the digitizing toolbar. 
* Options are rectangles, squares, ovals, and circles. 
* Use shift to fix the aspect ratio and create perfect squares and circles ...
* or otherwise freely draw and later enter exact dimensions.

[QGis plugin page](https://plugins.qgis.org/plugins/GeometryShapes/)

## Changelog

* Version 1.1
    - Add internationalization
    - Show geometry size in project measurement units (m, ft, etc.)
    - Improve tooltips for smaller objects
    - Avoid intersecting geometries if 'Avoid Overlap' is enabled in topology editing
* Version 1.0 
    - Configurable # of segments for circles (pull request 6)
    - Drop suport for QGis 2
    - Bug fixes:
        - Hopefully fix locale setting error on fresh QGis install (fix bug #13)
        - Set default values for attributes (fix bug #10)
        - Check for vector layer type (fix bug #7) 
        - Allow for smaller geometries >0.00001 (fix bug #11)
* Version 0.7 
    - Handle layer CRS that is different from the project CRS. 
    - Also don't prompt for non existing attributes.
* Version 0.6 
    - Add Undo and make behave like the default polygon tool (fix issue 1 and a minor bug)
* Version 0.5 
    - Make QGis3 compatible
* Version 0.4 
    - Added ovals
    - Use Shift-key to switch between squares/rectangles and circles/ovals
    - Tips and feedback through gui
    - Lots of minor improvements
* Version 0.3 
    - Add basic support for circles
* Version 0.2 
    - Allow for geometries with fields