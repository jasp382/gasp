from setuptools import setup

setup(
    name='gasp3',
    version='0.0.1',
    description=(
        'gasp is a python package with methods to assist '
        'programmers on tasks related with spatial analysis '
        'and production of geographic information.'
    ),
    url='https://github.com/jasp382/gasp3',
    author='jasp382',
    author_email='jpatriarca@mat.uc.pt',
    license='GPL',
    packages=[
        # Main module
        'gasp3',
        # ******************************************************************** #
        'gasp3.alg',
        # ******************************************************************** #
        'gasp3.cons',
        # ******************************************************************** #
        'gasp3.dt',
        'gasp3.dt.txtcls',
        # ******************************************************************** #
        'gasp3.fm',
        # ******************************************************************** #
        'gasp3.gt',
        'gasp3.gt.mng', 'gasp3.gt.mng.fld',
        # ******************************************************************** #
        'gasp3.pyt',
        # ******************************************************************** #
        'gasp3.sql',
        'gasp3.sql.mng',
        # ******************************************************************** #
        'gasp3.to',
        # ******************************************************************** #
        'gasp3.web'
    ],
    install_requires=[
        'numpy==1.16.4',
        'psycopg2-binary==2.8.3',
        'sqlalchemy==1.3.5', 'geoalchemy2==0.6.3',
        'shapely==1.6.4', 'fiona==1.8.6',
        'pyproj==2.2.1',
        'pandas==0.24.2', 'geopandas==0.5.0',
        'google-api-python-client==1.7.9',
        'netCDF4==1.5.1', 'xlrd==1.2.0', 'xlwt==1.3.0',
        'xlsxwriter==1.1.8',
        'dbf==0.98.0',
        'requests==2.22.0', 'requests-oauthlib==1.2.0',
        'requests-toolbelt==0.9.1', 'urllib3==1.25.3',
        'flickrapi==2.4.0',
        'tweepy==3.7.0',
        'jupyter',
        'scipy==1.3.0', 'sklearn==0.0', 'scikit-learn==0.21.2',
        'pyexcel-ods==0.5.6',
        'bs4==0.0.1',
        'seaborn==0.9.0',
        'sentinelsat==0.13'
    ],
    include_package_data=True
)