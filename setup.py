from setuptools import setup, find_packages

import jsonview


setup(
    name='django-jsonview',
    version=jsonview.__version__,
    description='Always return JSON from your Django view.',
    long_description=open('README.rst').read(),
    author='James Socol',
    author_email='me@jamessocol.com',
    url='https://github.com/jsocol/django-jsonview',
    license='Apache v2.0',
    packages=find_packages(exclude=['test_settings.py']),
    include_package_data=True,
    package_data={'': ['README.rst']},
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
