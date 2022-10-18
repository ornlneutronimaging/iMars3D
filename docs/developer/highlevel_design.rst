.. _highlevel_design:

#####################################################
iMars3D High-Level Design: Interactive Reconstruction
#####################################################

Overview
########

iMars3D is a collection of python applications and library that can be used in the reconstruction of neutron imaging data.
Based on the requirements there are three capabilities iMars3D provides:

* Provide a library of filters and functions for performing neutron image reconstruction
* UI Application that allows a user to:

  * Interactively define required configuration data
  * Interactively define a reconstruction workflow
  * Interactively run a reconstruction
  * Launch a reconstruction and monitor the processing

* Run an auto reconstruction

When running the reconstruction application the process is partitioned into stages as follows:

* Configuration (downloading) - user specifies all configuration data that is required for perform a reconstruction.
* Region of Interest - user interactively selects a region of interest from the raw ct_scan that is to be reconstructed
* Preprocessing - prepare the data for reconstruction which involves running filters against it
* Reconstruction - Perform the actual reconstruction
* Visualization - visualize and explore the result of the reconstruction

iMars3D Logical Partitions
##########################

Logically the software is loosely partitioned into a Front End partition and a Backend partition.
The Front End partition is primarily responsible for presenting and collecting data and information from the user and controlling their interactions for preparing and running reconstructions.
The Backend is responsible for managing and performing the actual reconstruction.

Backend Logical Partition
=========================

The Backend partition holds the codes that perform a reconstruction process.

Logically the software in the Backend partition is broken up as follows:

* The library of filters and functions
* Reconstruction Workflow (engine(s) or drivers)
* I/O

Library of Filters & Functions
------------------------------

The logical library of filters and functions contains the core computational aspects that can be used to perform a reconstruction process.

.. note:: The terms reconstruction process refer to the entire workflow for performing a reconstruction.  This includes the applying and any and all filters and any other process of the data so it can be reconstructed.

The filters and functions are partitioned into categories that represent their role in a reconstruction process.
The library contains the following filter and functions for use in a reconstruction process:

* Morph

    * Crop

* Preparation

    * Normalization

* Correction

    * Denoise
    * Gamma Filtering
    * Intensity Fluctuation Correction
    * Ring Removal

* Diagnostic

    * Rotation
    * Tilt

.. note:: Currently the implementation is python so the user of the library has access to any and all codes in the library.  However, the filters and functions listed are the interfaces to those reconstruction processing logically exposed for use.

Reconstruction Workflow
-----------------------

Workflow is the logical partition that contains the reconstruction engine capability.
There are currently two logical workflow (or reconstruction) engines

* One for interactive reconstruction and
* One for non-interactive reconstruction

I/O
---

*  Reading (loading) from files that hold raw image data and other data that is used in the reconstruction process, e.g. Open Beam, Direct Current, etc.
*  Extracting metadata that is embedded in the data files

.. note:: Currently metadata extraction only works for TIFF files as we don't know how the metadata is embedded in other image file formats


Front End Logical Partition
===========================

The Front End partition contains the codes for the interface users interact with to perform, manage, and monitory a reconstruction process.

The front end is partitioned into:

* Stages
* Widgets

iMars3D Logical Packages
##########################

iMars3D codes are packaged in a number of ways:

* iMars3D UI Application for interactive reconstruction
* iMars3D non-interactive application for autoreduction and/or command line execution
* iMars3D Filter/Function Library

iMars3D UI Application
======================

The UI application is a relatively simple python application that is intended to run in a Jupyter notebook.
The application is composed of both front end parts (UI) and backend parts.
The UI (part of the front end) operates in a separate thread and is event driven based on user interaction.
As is typical with this type of UI technology, callback functions are registered to handle the user generated events and are implemented to be asynchronous.

The UI itself is implemented using Panel widgets which is build on top of Bokeh.
These aspects of the UI application are not specific to jupyter and can be refactored into a web application with nominal impact to the behavior of the UI or the application.

As indicated the UI is implemented using a set of widgets.
There is a widget for each filter/function to handle any user interaction required to collect filter/function specific data and invoke the filter/function when at the request of the user.
This paring of filter/function widgets and the execution of the filter/function from the library is a logical pairing.
The application contains an engine that actually executes the the filter/function upon request from the UI.
In this way it is the engine that maintains state for the reconstruction process.

The UI guides the user through a set of stages to prepare for and execute a reconstruction.  The stages are as follows:

* **Loading** - which guides the user to provide all the basic configuration data the reconstruction process requires.  The configuration (metadata) is put into a dictionary.  It is then persisted in a json file to be use for any reconstruction process.
* **Select Region of Interest (ROI)** - This stage allows the user to interactively select a region of interest from the raw ct_scans to be used for reconstruction rather than the entire raw data set.
* **Preprocess** - this stage allows the user to specify the filter/functions to be applied to the data and the order in which to apply them prior to the actual reconstruction
* **Reconstruction** - This stage performs the actual reconstruction based on the intermediate results established during the preprocessing stage.
* **Visualization** - This stage allows the user to interactively view and explore the result of the reconstruction.

The loading stage is always presented to the user to either fill out the required data or ensure the existing data is correct.
However, when the user chooses to run a non-interactive reconstruction the software performs the reconstruction process based on the configuration data and a predefined workflow that has been specified in the json configuration file.



Capabilities
------------

The iMars3D UI Application provides the user the following capabilities:

* Interactively specify the configuration information required for performing a reconstruction (configuration data)
* Interactively perform a reconstruction
* Interactively specify the workflow to execute to perform a reconstruction
* Launch a non-interactive reconstruction process and monitor its progress

Structure
---------

The iMars3D UI application is comprised of:

* The Front End (UI)

    * Stages - Stages group and control the user interaction
    * Widgets - There is a widget for each filter/function to handle the user interaction with the specific filter/function.

* The Backend

    * iMars3D Filter/Function Library
    * iMars3D Interactive Workflow Engine


iMars3D Auto Reconstruction Application
=======================================

iMars3D auto reconstruction application and the application to be used when performing auto reconstruction.

.. note:: Auto reconstruction is equivalent to auto reduction. It is invoked in the same way automatically after data acquisition.

Auto reconstruction takes an already specified configuration json file which contains all the information required to run a reconstruction process.

Structure
---------

The iMars3D auto reconstruction application is comprised of:

* The Backend

    * iMars3D Filter/Function Library
    * IMars3D non-interactive Workflow Engine

The auto reduction application could also be run from the command line.

For auto reconstruction a wrapper script is required.
The system that invokes the auto reconstruction assumes an interface that takes the location of the raw ct_scans.

iMars3D Library
===============

The iMars3D (filter/function) library is simply the set of filters and functions involved in performing a reconstruction process.
The library is expected to be used within a python application.
It is the python application, which uses the iMars3D library, that needs to keep track of the state of the reconstruction and maintain the intermediate results as required to transition from one filter/function to the next.

iMars3D Key Design Decisions
############################

This section contains key design decision (DD)

DD: There is a UI widget for each filter/function.
The widget handles the interaction with the user to collect the data (parameters) required to execute the filter/function, if any.

DD: During Interactive reconstruction the UI software will wait for the user to execute the filter before saving the associated configuration (parameter) data.

DD:The option to save to disk the result of running a filter/function (intermediate data) will be a checkbox.
The intermediate data will be saved when the user selects to save the configuration data.
If the box is checked prior to running the filter it is ignored.

DD:The widget associated with the filter/function calls a single function (interface) on the interactive reconstruction engine method.  The filter/function widget serializes itself to a dictionary entry that is passed to this single interface on the engine.  There is one interface function all filter/functions user on the engine instead of the engine having an interface for each filter/function.

DD:There will be two buffers to hold results.
The current buffer holds the accepted result from the previous filter/function.
A temporary buffer holds the result of the current filter/function execution.
This is to allow the user the ability to reject the intermediate result if desired.
If/when the intermediate result from executing the current filter/function is satisfactory it will be copied to the current buffer and the temporary buffer will be used for the next filter/function to execute.

DD: There is a single widget used for displaying the filter/function intermediate result. The viewer widget does not copy the data to be visualized but rather uses the content of temporary buffer directly.

DD: Currently the UI Application only performs one reconstruction.  It must then be closed and restarted.

DD: [Future] Reset and clear all fields and release any numpy arrays retained by the kernel.  This would allow a user to execute another reconstruction without having to stop and restart the app.  This will be necessary prior to implementing this app as a web app.
