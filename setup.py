from setuptools import setup, find_packages


requires = [
    'pyramid',
    'pyramid_debugtoolbar',
    'pyramid_tm',
    'transaction',
    'sqlalchemy',
    'pyramid_jinja2',
    'waitress'
    ]

tests_require = [
    'WebTest >= 1.3.1',  # py3 compat
    'pytest',  # includes virtualenv
    'pytest-cov',
    ]

setup(name='blog',
      version='0.1',
      description='blog',
      long_description='Very cool blog by Alexander Ivanov',
      classifiers=[
          "Programming Language :: Python",
          "Framework :: Pyramid",
          "Topic :: Internet :: WWW/HTTP",
          "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
      ],
      author='Alexander Ivanov',
      author_email='oz.sasha.ivanov@gmail.com',
      url='/',
      keywords='web pyramid blog',
      packages=find_packages(),
      include_package_data=True,
      zip_safe=False,
      extras_require={
          'testing': tests_require,
      },
      install_requires=requires,
      entry_points="""\
      [paste.app_factory]
      main = blog:main
      """,
      )
