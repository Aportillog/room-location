from setuptools import setup, find_packages
import pathlib

here = pathlib.Path(__file__).parent.resolve()

# Get the long description from the README file
long_description = (here / 'README.md').read_text(encoding='utf-8')


setup(
    name='localizationpy',
    version='1.0.0',
    description='Application for localization NewFasant simulations analysis',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Aitor Portillo Gonzalez',
    author_email='aitor.pg@tutanota.com',
    license='MIT',
    packages=find_packages(),
    py_modules=["localizationpy"],
    python_requires='>=3.8, <4',
    install_requires=[
        "PySimpleGUI",
        "matplotlib",
        "numpy",
    ],
    entry_points={
            'console_scripts': [
                'locpy=localizationpy:run',
            ],
        },
)
