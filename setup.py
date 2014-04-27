from distutils.core import setup

with open("README.rst", "r") as f:
    readme = f.read()

setup(name='astcheck',
      version='0.2.1',
      description='Check Python ASTs against templates',
      long_description = readme,
      author='Thomas Kluyver',
      author_email='thomas@kluyver.me.uk',
      url='https://github.com/takluyver/astcheck',
      py_modules=['astcheck'],
      classifiers=[
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2',
          'Programming Language :: Python :: 3',
          'Topic :: Software Development :: Code Generators',
          'Topic :: Software Development :: Testing',
      ]
)