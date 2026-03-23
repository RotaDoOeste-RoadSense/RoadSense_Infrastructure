from setuptools import setup, Extension
from Cython.Build import cythonize

extensions = [
    Extension("inference_detection", ["inference_detection.py"])
]

setup(
    name="inference_detection",
    ext_modules=cythonize(
        extensions,
        language_level="3",
        compiler_directives={"boundscheck": False, "wraparound": False},
    ),
)
