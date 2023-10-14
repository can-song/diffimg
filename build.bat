% where pyside6-designer %
:: where pyside6-designer
del /F /S /Q build
del /F /S /Q dist
pyinstaller ^
    --windowed ^
    --onefile ^
    --icon=res\diffimg.ico ^
    --add-data=ui\viewer.ui;ui ^
    --add-data=load\raster\*;load\raster ^
    --add-data=load\vector\*;load\vector ^
    --hidden-import PySide6.QtXml ^
    --hidden-import=skimage.filters.edges ^
    --copy-metadata rasterio ^
    --hidden-import=rasterio.sample ^
    --hidden-import=rasterio.vrt ^
    --hidden-import=rasterio._features ^
    --hidden-import=geopandas ^
    --copy-metadata pyproj ^
    --hidden-import=importlib.metadata ^
    --copy-metadata=importlib_metadata ^
    --key=asfjkl#932,ML.ksdf ^
    --add-binary %CONDA_PREFIX%\Lib\site-packages\pyproj.libs\*;pyproj.libs\ ^
    --add-binary %CONDA_PREFIX%\Lib\site-packages\rasterio.libs\*;rasterio.libs\ ^
    -p src\context.py ^
    -p src\file_dialog.py ^
    -p src\main_window.py ^
    -p src\scene.py ^
    -p src\view.py ^
    -p .qt_for_python\uic\*.py ^
    -p .qt_for_python\rcc\diffimg.py ^
    diffimg.py


    @REM --collect-all rasterio.libs ^