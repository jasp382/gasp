from setuptools import setup

setup(
    name='gasp',
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
        'gasp',
        # ******************************************************************** #
        'gasp.adv', 'gasp.adv.dsn', 'gasp.adv.dsn.fb',
        'gasp.adv.sat',
        # ******************************************************************** #
        'gasp.alg', 'gasp.alg.osm2lulc', 'gasp.alg.osm2lulc.utils',
        # ******************************************************************** #
        'gasp.cons',
        # ******************************************************************** #
        'gasp.df',
        # ******************************************************************** #
        'gasp.dt', 'gasp.dt.txtcls',
        # ******************************************************************** #
        'gasp.g', 'gasp.g.gop', 'gasp.g.prop',
        # ******************************************************************** #
        'gasp.gd.floc', 'gasp.gd.terrain',
        # ******************************************************************** #
        'gasp.gs',
        # ******************************************************************** #
        'gasp.gt',
        'gasp.gt.anls', 'gasp.gt.anls.exct', 'gasp.gt.anls.ovlay',
        'gasp.gt.anls.prox',
        'gasp.gt.fm',
        'gasp.gt.gop', 'gasp.gt.lyr',
        'gasp.gt.mng', 'gasp.gt.nc',
        'gasp.gt.nop', 'gasp.gt.nop.sat',
        'gasp.gt.prop', 'gasp.gt.prop.feat',
        'gasp.gt.to', 'gasp.gt.stats', 'gasp.gt.wenv',
        # ******************************************************************** #
        'gasp.pyt', 'gasp.pyt.xls',
        # ******************************************************************** #
        'gasp.sql',
        'gasp.sql.anls', 'gasp.sql.charts', 'gasp.sql.mng', 'gasp.sql.to',
        'gasp.sql.gop',
        # ******************************************************************** #
        'gasp.web',
        'gasp.web.djg', 'gasp.web.djg.ff', 'gasp.web.djg.mdl',
        'gasp.web.geosrv', 'gasp.web.geosrv.sld'
        # ******************************************************************** #
    ],
    install_requires=[
        'numpy==1.18.0',
        'psycopg2-binary==2.8.4',
        'sqlalchemy==1.3.12', 'geoalchemy2==0.6.3',
        'shapely==1.6.4', 'fiona==1.8.6',
        'pyproj==2.4.2',
        'pandas==0.25.3', 'geopandas==0.6.2',
        'netCDF4==1.5.3', 'xlrd==1.2.0', 'xlwt==1.3.0',
        'xlsxwriter==1.2.7',
        'dbf==0.98.3',
        'requests==2.22.0', 'requests-oauthlib==1.3.0',
        'requests-toolbelt==0.9.1', 'urllib3==1.25.3',
        'flickrapi==2.4.0', 'tweepy==3.8.0',
        'jupyter',
        'scipy==1.4.1', 'scikit-learn==0.22',
        'pyexcel-ods==0.5.6',
        'bs4==0.0.1',
        'seaborn==0.9.0',
        'sentinelsat==0.13',
        'django==2.2.4', 'django-widget-tweaks==1.4.5',
        'django-cors-headers==3.2.0', 'djangorestframework==3.11.0',
        'nltk==3.4.5',
        'simpledbf==0.2.6'
        #'mysqlclient==1.4.6'
    ],
    include_package_data=True
)