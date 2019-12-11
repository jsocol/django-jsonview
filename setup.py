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
    install_requires=["django>=2.0.0"],
    tests_require=["coverage"],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ]
)
