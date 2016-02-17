RasterDisplayComposer
=============

Raster display composer is QGIS plugin to create a 3 bands colored image from 3 loaded raster.

# What works

- Create and load a on-the-fly VRT
- Manage no data
- Save the VRT into a specific file
- Set a specific name to the loaded band
- Update available bands in case of layer addition or deletion
- Set a "Refresh" button, just in case

# Limitations
- Works on loaded layers only
- Works with the first band of each selected layer
- May not work with layers with different bands, extent, and resolution
- Does not manage same layers name

# ToDo:
- Add tip with band layers order for l8, S2...
- Add Alpha management (GUI is ok but hidden)
- Choose layer from file
- Select a specific band
- Mix resolutions

Enjoy !
