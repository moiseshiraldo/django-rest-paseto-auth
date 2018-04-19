from io import open

from setuptools import setup


def read(*paths):
    """
    Build a file path from paths and return the contents.
    """
    with open(os.path.join(*paths), 'r') as f:
        return f.read()


setup(
  name='django-rest-paseto-auth',
  version='0.1.0',
  description='Paseto authentication for Django Rest Framework',
  long_description=open('README.md').read(),
  url='https://github.com/moiseshiraldo/django-rest-paseto-auth',
  author='Moises Hiraldo',
  author_email='moiseshiraldo@gmail.com',
  license='MIT',
  packages=['paseto_auth'],
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
    'Programming Language :: Python :: 3.5',
    'Programming Language :: Python :: 3.6',
    'Framework :: Django :: 2.0',
    'License :: OSI Approved :: MIT License',
    'Topic :: Internet :: WWW/HTTP',
    
  ],
)
