# MARCout
MARCout is a system for exporting bibliographic records in local form to the MARC specification.

This repo includes the following key items:

-**`marcout.py` module:** The working export engine.

-**`test-marcout`:** A commandline script that wraps `marcout.py` and exposes.

-**`marcout-webservice.py`:** A minimal Flask webservice that exposes the `marcout.py` export and serialization functionality. (NOT a production-quality server setup: among other things, the Flask server is unsecured. Suitable only as a localhost utility server, or a working example of an HTTP service wrapping the `marcout.py` module.)

This repo also includes:

-**`unified-json.json`:** An example of the JSON input required for export and serialization:
  - the MARCout export definition
  - collection-specific information
  - requested export serialization
  - records (in local JSON format) to be exported.

-**`setup.txt`:** Instructions for setting up a Python 3 virtual environment with `pip3` in the repo, and installing the Flask webserver. Covers Debian/Ubuntu and Max OSX.

-**`marcout-service`:** A command line script that activates the virtual environment and starts the `marcout-webservice.py` webservice.

