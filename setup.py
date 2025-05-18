"""
Setup script for gSort Professional.
"""

import os
from setuptools import setup, find_packages

# Get version from package
with open(os.path.join('gsort', '__init__.py'), 'r') as f:
    for line in f:
        if line.startswith('__version__'):
            version = line.strip().split('=')[1].strip(' \'"')
            break
    else:
        version = '0.0.1'

# Read README for long description
with open('README.md', 'r', encoding='utf-8') as f:
    long_description = f.read()

# Setup configuration
setup(
    name='gsort-professional',
    version=version,
    description='Professional high-performance tool for processing and analyzing email:password combinations',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='gSort Professional',
    author_email='info@gsort.pro',
    url='https://github.com/krackn88/gsort-professional',
    packages=find_packages(),
    include_package_data=True,
    entry_points={
        'console_scripts': [
            'gsort-professional=main:main',
        ],
    },
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Information Technology',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Security',
        'Topic :: Utilities',
        'Operating System :: OS Independent',
        'Environment :: X11 Applications :: Qt',
    ],
    python_requires='>=3.8',
    install_requires=[
        'PyQt6>=5.15.9',
        'PySide6>=6.5.0',
        'pandas>=2.0.0',
        'numpy>=1.24.0',
        'matplotlib>=3.7.1',
        'qt-material>=2.14',
        'pillow>=9.5.0',
        'pyarrow>=12.0.0',
        'joblib>=1.2.0',
        'seaborn>=0.12.2',
        'plotly>=5.14.1',
        'openpyxl>=3.1.2',
        'tabulate>=0.9.0',
        'pdfkit>=1.0.0',
        'weasyprint>=59.0',
        'tqdm>=4.65.0',
        'colorama>=0.4.6',
        'psutil>=5.9.5',
        'python-dateutil>=2.8.2',
    ],
    extras_require={
        'dev': [
            'pytest>=7.3.1',
            'black>=23.3.0',
            'pylint>=2.17.4',
            'pyinstaller>=5.10.1',
        ],
    },
)