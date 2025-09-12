from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("model", ["model.py"])
]

setup(
    name="model",
    ext_modules=cythonize(
        extensions,
        language_level="3",
        compiler_directives={"boundscheck": False, "wraparound": False},
    ),
)
