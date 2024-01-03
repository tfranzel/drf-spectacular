Contributing to drf-spectacular
===============================

As an open source project, drf-spectacular welcomes any form of contribution. The
project was initially forked off DRF's schema generator and has since then been
continually receiving improvements from the community. Your contribution matters
even if it is only a small one.

Contributions come in different shapes and sizes.

* Documentation improvements, clarifications & fixing typos
* Creating issues for feature requests & bug reports
* Creating pull requests for features and bug fixes
* Questions that highlight inconsistencies or workflow issues
* Adding `blueprints`_ for not officially supported 3rd party tools.

Issues
------

Generating schemas is a complicated business and the devil often lies in the details.
A concise description with examples goes a long way towards getting a good understanding
of the issue at hand. If possible/applicable please include

* A concise description
* Example code that produces the issue
* Generated (partial) schema with the issue
* Stacktraces if an error occurred
* drf-spectacular/Django/DRF versions

Pull requests
-------------

drf-spectacular prides itself on having very high `code coverage`_ and an extensive `test suite`_.
It is really well tested, which enables us to maintain quality, reliability, and consistency.

* The git history is important to the project. Please make minimally invasive changes where possible.
  On receiving feedback, we prefer having a small set of amended commits.
  Consider using ``git commit --amend`` and ``git push --force`` for updating your PR.
* If you have a non-trivial PR please consider getting `early feedback`_. We don't want to waste anyone's time.
* We have great tooling around tests. Have a look into `test_regressions.py`_ for inspiration.
  The tests are mainly structured in feature units but in doubt small things go into the regressions.
* We use tox to make sure drf-spectacular works for a range of Django/DRF versions.
  Your PR must pass the whole test suite to get merged. Local testing with ``./runtests.py`` usually suffices.
  You don't need to install a bunch of python versions. The github actions for PRs will take care of the rest.

A quick cheat sheet to get you rolling

.. code:: console

  $ # fork the repo on github
  $ git clone https://github.com/YOURGITHUBNAME/drf-spectacular
  $ cd drf-spectacular
  $ python -m venv venv
  $ source venv/bin/activate
  (venv) $ pip install -r requirements.txt
  (venv) $ ./runtests.py  # runs tests (pytest) & linting (isort, flake8, mypy)


With that out of the way, we hope to hear from you soon.

.. _code coverage: https://app.codecov.io/gh/tfranzel/drf-spectacular
.. _test suite: https://github.com/tfranzel/drf-spectacular/tree/master/tests
.. _blueprints: https://drf-spectacular.readthedocs.io/en/latest/blueprints.html
.. _early feedback: https://github.com/tfranzel/drf-spectacular/issues
.. _test_regressions.py: https://github.com/tfranzel/drf-spectacular/blob/master/tests/test_regressions.py
