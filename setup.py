from setuptools import setup
from pathlib import Path


setup(name='ascii_designer',
      version='0.3.3',
      description='Builds dialogs from ASCII art definition.',
      long_description=Path('README.rst').read_text(),
      long_description_content_type='text/x-rst',
      url='http://github.com/loehnertj/ascii_designer',
      author='Johannes Loehnert',
      author_email='loehnert.kde@gmx.de',
      license='MIT',
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Topic :: Software Development :: User Interfaces',
      ],
      packages=['ascii_designer'],
      python_requires='>3.0',
      zip_safe=True
    )
