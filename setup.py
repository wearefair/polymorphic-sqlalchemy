from setuptools import setup

try:
    with open('README.md') as file:
        long_description = file.read()
except:
    long_description = "Polymorphic relations for SQLAlchemy"

setup(name='polymorphic_sqlalchemy',
      version='0.2.7',
      description='Polymorphic relations for SQLAlchemy',
      url='https://github.com/wearefair/polymorphic-sqlalchemy',
      author='Seperman',
      author_email='sepd@fair.com',
      packages=['polymorphic_sqlalchemy'],
      zip_safe=False,
      test_suite="tests",
      tests_require=['Flask==1.0',
                     'Flask-SQLAlchemy==2.4.0',
                     'pytest==4.5.0', ],
      long_description=long_description,
      long_description_content_type='text/markdown',
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
