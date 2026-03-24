from setuptools import setup
# set up using "pip install -e ."
setup(
    name='pymd',
    version='1.0',
    py_modules=['pymd'],
    entry_points={
        'console_scripts': [
        ],
    },
    install_requires=["pyscf", "rdkit", "spyrmsd", "matplotlib",
                      "plotly", "pyscf-dispersion", "h5py",
                      "pytest", "pytest-cov", "pytest-html",
                      "pytest-subprocess", "numpy"]
)
