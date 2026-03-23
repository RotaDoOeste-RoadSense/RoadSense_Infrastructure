from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("inference", ["inference.py"])
]

setup(
    name="inference",
    ext_modules=cythonize(
        extensions,
        language_level="3",
        compiler_directives={"boundscheck": False, "wraparound": False},
    ),
)
