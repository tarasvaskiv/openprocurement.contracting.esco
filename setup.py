from setuptools import setup, find_packages

version = '2.3'

requires = [
    'setuptools',
    'openprocurement.contracting.api',  # TODO set version
]
test_requires = requires + [
    'webtest',
    'python-coveralls',
]
docs_requires = requires + [
    'sphinxcontrib-httpdomain',
]

entry_points = {
}

setup(name='openprocurement.contract.esco',
      version=version,
      description="",
      long_description=open("README.txt").read(),
      # Get more strings from
      # http://pypi.python.org/pypi?:action=list_classifiers
      classifiers=[
          "License :: OSI Approved :: Apache Software License",
          "Programming Language :: Python",
      ],
      keywords='',
      author='Quintagroup, Ltd.',
      author_email='info@quintagroup.com',
      url='https://github.com/openprocurement/openprocurement.contract.esco',
      license='Apache License 2.0',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['openprocurement', 'openprocurement.contract'],
      include_package_data=True,
      zip_safe=False,
      install_requires=requires,
      tests_require=test_requires,
      extras_require={'test': test_requires, 'docs': docs_requires},
      test_suite="openprocurement.contract.esco.tests.main.suite",
      entry_points=entry_points
      )
