========
Overview
========

.. contents::
    :local:


Developer Account
-----------------

All the development work is done via Github, and the developers working on iMars3D must have a valid Github account with 2-step authentication enabled.
For developers who are part of SCSE@ORNL, please contact a senior developer to add you to the project.


Branches
--------

The default branch for development is ``next``, where all feature branches should be based on and all pull requests should be merged into.
Both ``main`` and ``qa`` branches are protected, and regular developers should not touch these branches unless instructed by a senior developer.


Development Cycle
-----------------

For developers who are part of SCSE@ORNL, the development cycle is as follows:

* Checkout a new branch based from ``next`` with a new branch name that contains the internal issue reference number.
* Working on the issue and making changes to the code.
* Make sure all tests are passing locally and new tests should be added to the test suite when introducing new features.
* Make a pull request to the ``next`` branch:

  * The title of the pull request should contain both the reference issue number and a brief description of the issue.
  * A link to the internal issue/task/story page should be provided at the top of the description.
  * Select a reviewer for the pull request.
  * Once the pull request is approved and all threads are resolved, ping the senior developers to merge the pull request.


It is recommended to use ``git rebase`` to clean-up the commit history before making a pull request as it will help keep the git history easy to search.


For independent contributors, the recommended development cycle is as follows:

* Open an issue to describe the motivation for the feature/bug fix/etc.
* Fork the repository and implement the features and bug fixes.
* Make sure all tests are passing locally and new tests should be added to the test suite when introducing new features.
* Make a pull request to the ``next`` branch:

  * Reference the previously opened issue that motivates this PR at the top of the description.
  * The title of the pull request should be concise and meaningful.
  * Select a reviewer for the pull request.
  * Once the pull request is approved, ping a developer from the list for merging.