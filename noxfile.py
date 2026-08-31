import nox


@nox.session
def tests(session):
    session.install(".", "pytest", "pytest-cov")
    session.run("pytest")
