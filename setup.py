from setuptools import setup
#
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
        'gasp.cons',
        # ******************************************************************** #
        'gasp.g', 'gasp.g.gop', 'gasp.g.prop', 'gasp.g.nop',
        'gasp.g.lyr',
        # ******************************************************************** #
        'gasp.gql', 'gasp.gql.to',
        # ******************************************************************** #
        'gasp.gt',
        'gasp.gt.attr', 'gasp.gt.gop', 'gasp.gt.gop.osm',
        'gasp.gt.nop', 'gasp.gt.nop.sat',
        'gasp.gt.prop', 'gasp.gt.prop.feat', 'gasp.gt.prox',
        'gasp.gt.toshp', 'gasp.gt.stats', 'gasp.gt.wenv',
        # ******************************************************************** #
        'gasp.pyt', 'gasp.pyt.xls', 'gasp.pyt.df', 'gasp.pyt.txtcls',
        # ******************************************************************** #
        'gasp.sde', 'gasp.sde.dsn'
        # ******************************************************************** #
        'gasp.sds.floc', 'gasp.sds.osm2lulc', 'gasp.sds.osm2lulc.utils',
        'gasp.sds.terrain',
        # ******************************************************************** #
        'gasp.sql', 'gasp.sql.q', 'gasp.sql.charts',
        # ******************************************************************** #
        'gasp.to',
        # ******************************************************************** #
        'gasp.web',
        'gasp.web.djg', 'gasp.web.djg.ff', 'gasp.web.djg.mdl',
        'gasp.web.geosrv', 'gasp.web.geosrv.sld'
        # ******************************************************************** #
    ],
    include_package_data=True
)
