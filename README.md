# Geometry Shapes
This QGis plugin draws basic geometry shapes with user defined measurements and also allows free drawing. 

Features/usage:
* Integrates in the digitizing toolbar. 
* Options are rectangles, squares, ovals, and circles. 
* Use shift to fix the aspect ratio and create perfect squares and circles ...
* or otherwise freely draw and later enter exact dimensions.

_Currently the dimensions are dictated by the default map units of the project CRS which can be degrees. This will 
change to QGIS measurement units in a forthcoming release._   

## Changelog
* 0.7 Handle layer CRS that is different from the project CRS. Also don't prompt for non existing attributes.
* 0.6 Add Undo and make behave like the default polygon tool (fix issue 1 and a minor bug)
* 0.5 Make QGis3 compatible
* 0.4 Added ovals
    Use Shift-key to switch between squares/rectangles and circles/ovals
    Tips and feedback through gui
    Lots of minor improvements
* 0.3 Add basic support for circles
* 0.2 Allow for geometries with fields