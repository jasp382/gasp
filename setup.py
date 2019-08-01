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
        'gasp3.alg.hydro', 'gasp3.alg.lndsld', 'gasp3.alg.terrain',
        # ******************************************************************** #
        'gasp3.cons',
        # ******************************************************************** #
        'gasp3.dt',
        'gasp3.dt.dsn', 'gasp3.dt.dsn.fb',
        'gasp3.dt.fm', 'gasp3.dt.glg', 'gasp3.dt.meteo',
        'gasp3.dt.mob', 'gasp3.dt.sat', 'gasp3.dt.to', 'gasp3.dt.txtcls',
        # ******************************************************************** #
        'gasp3.gt',
        'gasp3.gt.anls',
        'gasp3.gt.mng', 'gasp3.gt.mng.fld', 'gasp3.gt.mng.rst',
        'gasp3.gt.prop', 'gasp3.ft.prop.feat',
        'gasp3.gt.spnlst', 'gasp3.gt.spnlst.sat',
        'gasp3.gt.stats', 'gasp3.gt.wenv',
        # ******************************************************************** #
        'gasp3.pyt', 'gasp3.pyt.df',
        # ******************************************************************** #
        'gasp3.sql',
        'gasp3.sql.mng',
        # ******************************************************************** #
        'gasp3.web',
        'gasp3.web.djg', 'gasp3.web.djg.ff', 'gasp3.web.djg.mdl',
        'gasp3.web.geosrv', 'gasp3.web.geosrv.styl', 'gasp3.web.geosrv.styl.sld'
        # ******************************************************************** #
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
        'sentinelsat==0.13',
        'django==2.2.4', 'django-widget-tweaks==1.4.5',
        'django-cors-headers==3.1.0', 'djangorestframework==3.10.2'
    ],
    include_package_data=True
)