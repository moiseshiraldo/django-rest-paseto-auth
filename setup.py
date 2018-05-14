from io import open

from setuptools import find_packages, setup


setup(
  name='django-rest-paseto-auth',
  version='0.1.1',
  description='Paseto authentication for Django Rest Framework',
  long_description=open('README.md').read(),
  long_description_content_type='text/markdown',
  url='https://github.com/moiseshiraldo/django-rest-paseto-auth',
  author='Moises Hiraldo',
  author_email='moiseshiraldo@gmail.com',
  license='MIT',
  packages=find_packages(exclude=['tests*']),
  include_package_data=True,
  python_requires=">=3.6",
  install_requires=[
        'Django>=2',
        'djangorestframework>=3.8',
        'paseto>=0.0.5',
    ],
  classifiers=[
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Environment :: Web Environment',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 3.6',
    'Framework :: Django :: 2.0',
    'License :: OSI Approved :: MIT License',
    'Topic :: Internet :: WWW/HTTP',
  ],
)
