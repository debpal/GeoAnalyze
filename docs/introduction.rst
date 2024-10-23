==============
Introduction
==============    
    
GeoAnalyze is a Python package designed to streamline geoprocessing by handling internal complexities and intermediate steps. Conceptualized and launched on October 10, 2024, this package is tailored for users with limited geospatial processing experience, allowing them to focus on desired outputs. The package is still in the planning stage, but active development is ongoing, with exciting new features planned for future releases.

Leveraging open-source geospatial Python modules, GeoAnalyze aims to empower users by providing high-level geoprocessing tools with fewer lines of code.


File Operations (Irrespective of Extensions)
----------------------------------------------

When managing GIS files, each main file is often associated with several auxiliary files. For example, a `.shp` file (shapefile) is commonly accompanied by `.cpg`, `.dbf`, `.prj`, and `.shx` files, which are necessary for the shapefile to function correctly. In geospatial processing, these associated files must be handled together to prevent errors or data loss. GeoAnalyze simplifies this process by ensuring that any operation performed on a main file automatically includes its associated auxiliary files, making file management seamless and error-free. The package offers the following file operation features:

* Deleting files in a folder.
* Transferring files from the source folder to the destination folder.
* Renaming files in a folder.
* Copying files from the source folder and renames them in the destination folder.
* Extracting files with the same extension from a folder.