# GeoAnalyze

GeoAnalyze is a Python package designed to streamline geoprocessing by handling internal complexities and intermediate steps. Conceptualized and launched on October 10, 2024, this package is tailored for users with limited geospatial processing experience, allowing them to focus on desired outputs. The package is still in the planning stage, but active development is ongoing, with exciting new features planned for future releases.

Leveraging open-source geospatial Python modules, GeoAnalyze aims to empower users by providing high-level geoprocessing tools with fewer lines of code.


## File Operations (Irrespective of Extensions)

When managing GIS files, each main file is often associated with several auxiliary files. For example, a `.shp` file (shapefile) is commonly accompanied by `.cpg`, `.dbf`, `.prj`, and `.shx` files, which are necessary for the shapefile to function correctly. In geospatial processing, these associated files must be handled together to prevent errors or data loss. GeoAnalyze simplifies this process by ensuring that any operation performed on a main file automatically includes its associated auxiliary files, making file management seamless and error-free. The package offers the following file operation features:

* Deleting files in a folder.
* Transferring files from the source folder to the destination folder.
* Renaming files in a folder.
* Copying files from the source folder and renames them in the destination folder.
* Extracting files with the same extension from a folder.

 
## Roadmap

* Raster processing.
* Shapefile analysis.
* Watershed delineation.


## Easy Installation

To install, use pip:

```bash
pip install GeoAnalyze
```

## Quickstart
A brief example of how to start:

```python
>>> import GeoAnalyze
>>> file = GeoAnalyze.File()
```

## Documentation

For detailed information, see the [documentation](http://geoanalyze.readthedocs.io/).

## Support

If this project has been helpful and you'd like to contribute to its development, consider sponsoring with a coffee! Support will help maintain, improve, and expand this open-source project, ensuring continued valuable tools for the community.


[![Buy Me a Coffee](https://img.shields.io/badge/☕_Buy_me_a_coffee-FFDD00?style=for-the-badge)](https://www.buymeacoffee.com/debasish_pal)


## Toolkit

| <big>Status</big> | <big>Description</big> |
| --- | --- |
| **PyPI**| ![PyPI - Version](https://img.shields.io/pypi/v/GeoAnalyze) ![PyPI - Status](https://img.shields.io/pypi/status/GeoAnalyze) ![PyPI - Python Version](https://img.shields.io/pypi/pyversions/GeoAnalyze) ![PyPI - Wheel](https://img.shields.io/pypi/wheel/GeoAnalyze) |
| **GitHub** | ![GitHub last commit](https://img.shields.io/github/last-commit/debpal/GeoAnalyze) [![flake8](https://github.com/debpal/GeoAnalyze/actions/workflows/linting.yml/badge.svg)](https://github.com/debpal/GeoAnalyze/actions/workflows/linting.yml) [![mypy](https://github.com/debpal/GeoAnalyze/actions/workflows/typing.yml/badge.svg)](https://github.com/debpal/GeoAnalyze/actions/workflows/typing.yml) [![pytest](https://github.com/debpal/GeoAnalyze/actions/workflows/testing.yml/badge.svg)](https://github.com/debpal/GeoAnalyze/actions/workflows/testing.yml) |
| **Codecov** | [![codecov](https://codecov.io/gh/debpal/GeoAnalyze/graph/badge.svg?token=9OW3TRHI7C)](https://codecov.io/gh/debpal/GeoAnalyze)  |
| **Read** _the_ **Docs** | [![Documentation Status](https://readthedocs.org/projects/geoanalyze/badge/?version=latest)](https://geoanalyze.readthedocs.io/en/latest/?badge=latest) |
| **PePy** | ![Pepy Total Downloads](https://img.shields.io/pepy/dt/GeoAnalyze) |
| **License** | ![GitHub License](https://img.shields.io/github/license/debpal/GeoAnalyze) |






