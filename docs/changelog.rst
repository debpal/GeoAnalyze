===============
Release Notes
===============


Version 1.2.1
---------------

* **Release date:** 21-May-2025.

* **Features:**

    * Added a new function to compute statistics by reference raster in the :class:`GeoAnalyze.Raster` class.
    * Introduced a function to extract a rectangular bounding box from input geometries in the :class:`GeoAnalyze.Shape` class.
    * Remove the :class:`GeoAnalyze.PackageData` class, as the required data can be accessed
      from the `tests` directory of the the `GeoAnalyze  <https://github.com/debpal/GeoAnalyze/tree/main/tests>`_ package.


Version 1.2.0
---------------

* **Release date:** 28-Apr-2025.

* **Features:**

    * Added new functions to the :class:`GeoAnalyze.Stream` and :class:`GeoAnalyze.Raster` classes.
    * Introduced the new :class:`GeoAnalyze.Visual` class for geospatial data visualization and plotting..

* **Documentation:** A tutorial has been added on how to use the newly introduced features.

* **Development status:** Upgraded from Beta to Stable.


Version 1.1.0
---------------

* **Release date:** 05-Apr-2025.

* **Features:** New functions introduced in the :class:`GeoAnalyze.Raster` class.

* **Documentation:** Added a tutorial on how to use the newly introduced features.

* **Development status:** Upgraded from Alpha to Beta.


Version 1.0.0
---------------

* **Release date:** 10-Feb-2025.

* **Features:**

    * Delineation functions implemented in the :class:`GeoAnalyze.Watershed` and :class:`GeoAnalyze.Stream` classes.
    * Geoprocessing capabilities introduced in the :class:`GeoAnalyze.Raster` and :class:`GeoAnalyze.Shape` classes.

* **Documentation:** Added a tutorial on how to use the newly introduced features.

* **Development status:** Upgraded from Planning to Alpha.


Version 0.0.3
---------------

* **Release date:** 23-Oct-2024.

* **Features:** Introduced enhanced functionality for GIS file operations. The :class:`GeoAnalyze.File` class has now reached a stable and mature stage.


Version 0.0.2
---------------

* **Release date:** 10-Oct-2024.

* **GitHub Actions Integration:**

    * Linting with `flake8` to enforce PEP8 code formatting.
    * Type checking with `mypy` to verify annotations throughout the codebase.
    * Code testing with `pytest` to ensure code reliability.
    * Test Coverage with **Codecov** to monitor and report test coverage.


Version 0.0.1
---------------

* **Release date:** 10-Oct-2024.

* **Features:** Functionality for file operations.

* **Documentation:** Added a tutorial on how to use the features.

* **Development status:** Planning.

* **Roadmap:** Ongoing addition of new features.