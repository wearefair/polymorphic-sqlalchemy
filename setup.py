from setuptools import setup

try:
    with open('README.md') as file:
        long_description = file.read()
except:
    long_description = "Polymorphic relations for SQLAlchemy"

setup(name='polymorphic_sqlalchemy',
      version='0.2.6',
      description='Polymorphic relations for SQLAlchemy',
      url='https://github.com/wearefair/polymorphic_sqlalchemy',
      download_url='https://github.com/wearefair/polymorphic_sqlalchemy/tarball/master',
      author='Seperman',
      author_email='sepd@fair.com',
      packages=['polymorphic_sqlalchemy'],
      zip_safe=False,
      test_suite="tests",
      tests_require=['Flask==0.12.2',
                     'Flask-SQLAlchemy==2.1',
                     'pytest==3.0.6', ],
      long_description=long_description,
      install_requires=[
          'SQLAlchemy',
          'inflection'
      ],
      classifiers=[
          "Intended Audience :: Developers",
          "Operating System :: OS Independent",
          "Topic :: Software Development",
          "Programming Language :: Python :: 3.5",
          "Programming Language :: Python :: 3.6",
          "Development Status :: 4 - Beta",
      ],
      )
