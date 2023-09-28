import os
import sys

from setuptools import find_packages, setup
from setuptools.command.test import test as TestCommand


def read_readme():
    if not os.path.exists("./README.md"):
        return ""
    with open("./README.md") as f:
        return f.read()


class PyTest(TestCommand):
    def finalize_options(self):
        TestCommand.finalize_options(self)
        self.test_args = []
        self.test_suite = True

    def run_tests(self):
        import pytest

        errcode = pytest.main(self.test_args)
        sys.exit(errcode)


with open(os.path.join("./haupt/pkg.py"), encoding="utf8") as f:
    pkg = {}
    exec(f.read(), pkg)


with open("requirements/requirements.txt") as requirements_file:
    requirements = requirements_file.read().splitlines()

with open("requirements/platform.txt") as requirements_file:
    platform_requirements = requirements_file.read().splitlines()

with open("requirements/sandbox.txt") as requirements_file:
    sandbox_requirements = requirements_file.read().splitlines()

with open("requirements/dev.txt") as requirements_file:
    dev_requirements = requirements_file.read().splitlines()

with open("requirements/fs.txt") as requirements_file:
    fs_requirements = requirements_file.read().splitlines()

with open("requirements/streams.txt") as requirements_file:
    stream_requirements = requirements_file.read().splitlines()

if os.environ.get("USE_PROD_PACKAGES"):
    with open("requirements/prod.txt") as requirements_file:
        requirements += requirements_file.read().splitlines()

extra = {
    "platform": platform_requirements,
    "sandbox": sandbox_requirements + stream_requirements,
    "fs": fs_requirements,
    "streams": stream_requirements,
    "dev": dev_requirements,
}

setup(
    name=pkg["NAME"],
    version=pkg["VERSION"],
    description=pkg["DESC"],
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    maintainer=pkg["AUTHOR"],
    maintainer_email=pkg["EMAIL"],
    author=pkg["AUTHOR"],
    author_email=pkg["EMAIL"],
    url=pkg["URL"],
    license=pkg["LICENSE"],
    platforms="any",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    keywords=[
        "polyaxon",
        "aws",
        "s3",
        "microsoft",
        "azure",
        "google cloud storage",
        "gcs",
        "deep-learning",
        "machine-learning",
        "data-science",
        "neural-networks",
        "artificial-intelligence",
        "ai",
        "reinforcement-learning",
        "kubernetes",
        "aws",
        "microsoft",
        "azure",
        "google cloud",
        "tensorFlow",
        "pytorch",
        "paddlepaddle",
        "matplotlib",
        "plotly",
        "visualization",
        "analytics",
        "hyperopt",
        "scikit-learn",
        "optimization",
        "bayesian-optimization",
    ],
    install_requires=[requirements],
    extras_require=extra,
    entry_points={"console_scripts": ["haupt = haupt.main:cli"]},
    python_requires=">=3.8",
    classifiers=[
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Application Frameworks",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Software Development :: Libraries",
        "Topic :: Software Development",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Typing :: Typed",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    tests_require=["pytest"],
    cmdclass={"test": PyTest},
)
