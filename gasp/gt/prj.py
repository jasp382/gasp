# -*- coding: utf-8 -*-

"""
Data Management Tools > Manage Spatial Reference Systems
"""

from osgeo import osr

def get_trans_param(in_epsg, out_epsg, export_all=None):
    """
    Return transformation parameters for two Spatial Reference Systems
    """
    
    i = osr.SpatialReference()
    i.ImportFromEPSG(in_epsg)
    o = osr.SpatialReference()
    o.ImportFromEPSG(out_epsg)
    t = osr.CoordinateTransformation(i, o)
    if not export_all:
        return t
    else:
        return {'input': i, 'output': o, 'transform': t}


def ogr_def_proj(shp, epsg=None, template=None):
    """
    Create/Replace the prj file of a ESRI Shapefile
    """
    
    import os
    
    prj_file = '{}.prj'.format(
        os.path.join(
            os.path.dirname(shp),
            os.path.splitext(os.path.basename(shp))[0]
        )
    )
    if epsg and not template:
        s = osr.SpatialReference()
        s.ImportFromEPSG(int(epsg))
        s.MorphToESRI()
        prj = open(prj_file, 'w')
        prj.write(s.ExportToWkt())
        prj.close()
        return prj_file
    
    elif not epsg and template:
        prj_template = '{}.prj'.format(
            os.path.splitext(os.path.basename(template))[0]
        )
        
        if not os.path.exists(prj_template):
            return 0
        
        try:
            os.remove(prj_file)
            shutil.copyfile(prj_template, prj_file)
        except:
            shutil.copyfile(prj_template, prj_file)
        
        return prj_file


def proj(inShp, outShp, outEPSG, inEPSG=None,
        gisApi='ogr', sql=None, con_psql=None):
    """
    Project Geodata using GIS
    
    API's Available:
    * ogr;
    * ogr2ogr;
    * pandas;
    * OGRGeom;
    * ogr2ogr_SQLITE;
    * psql;
    """
    import os
    
    if gisApi == 'ogr':
        """
        Using ogr Python API
        """
        
        if not inEPSG:
            raise ValueError(
                'To use ogr API, you should specify the EPSG Code of the'
                ' input data using inEPSG parameter'
            )
        
        from osgeo             import ogr
        from gasp.gt.lyr.fld   import copy_flds
        from gasp.gt.prop.feat import get_gtype
        from gasp.gt.prop.ff   import drv_name
        from gasp.gt.prop.prj  import get_sref_from_epsg
        from gasp.pyt.oss      import get_filename
        
        def copyShp(out, outDefn, lyr_in, trans):
            for f in lyr_in:
                g = f.GetGeometryRef()
                g.Transform(trans)
                new = ogr.Feature(outDefn)
                new.SetGeometry(g)
                for i in range(0, outDefn.GetFieldCount()):
                    new.SetField(outDefn.GetFieldDefn(i).GetNameRef(), f.GetField(i))
                out.CreateFeature(new)
                new.Destroy()
                f.Destroy()
        
        # ####### #
        # Project #
        # ####### #
        transP = get_trans_param(inEPSG, outEPSG)
        
        inData = ogr.GetDriverByName(
            drv_name(inShp)).Open(inShp, 0)
        
        inLyr = inData.GetLayer()
        out = ogr.GetDriverByName(
            drv_name(outShp)).CreateDataSource(outShp)
        
        outlyr = out.CreateLayer(
            get_filename(outShp), get_sref_from_epsg(outEPSG),
            geom_type=get_gtype(
                inShp, name=None, py_cls=True, gisApi='ogr'
            )
        )
        
        # Copy fields to the output
        copy_flds(inLyr, outlyr)
        # Copy/transform features from the input to the output
        outlyrDefn = outlyr.GetLayerDefn()
        copyShp(outlyr, outlyrDefn, inLyr, transP)
        
        inData.Destroy()
        out.Destroy()
    
    elif gisApi == 'ogr2ogr':
        """
        Transform SRS of any OGR Compilant Data. Save the transformed data
        in a new file
        """

        if not inEPSG:
            from gasp.gt.prop.prj import get_epsg_shp
            inEPSG = get_epsg_shp(inShp)
        
        if not inEPSG:
            raise ValueError('To use ogr2ogr, you must specify inEPSG')
        
        from gasp            import exec_cmd
        from gasp.gt.prop.ff import drv_name
        
        cmd = (
            'ogr2ogr -f "{}" {} {}{} -s_srs EPSG:{} -t_srs EPSG:{}'
        ).format(
            drv_name(outShp), outShp, inShp,
            '' if not sql else ' -dialect sqlite -sql "{}"'.format(sql),
            str(inEPSG), str(outEPSG)
        )
        
        outcmd = exec_cmd(cmd)
    
    elif gisApi == 'ogr2ogr_SQLITE':
        """
        Transform SRS of a SQLITE DB table. Save the transformed data in a
        new table
        """
        
        from gasp import exec_cmd
        
        if not inEPSG:
            raise ValueError((
                'With ogr2ogr_SQLITE, the definition of inEPSG is '
                'demandatory.'
            ))
        
        # TODO: Verify if database is sqlite
        
        db, tbl = inShp['DB'], inShp['TABLE']
        sql = 'SELECT * FROM {}'.format(tbl) if not sql else sql
        
        outcmd = exec_cmd((
            'ogr2ogr -update -append -f "SQLite" {db} -nln "{nt}" '
            '-dialect sqlite -sql "{_sql}" -s_srs EPSG:{inepsg} '
            '-t_srs EPSG:{outepsg} {db}'
        ).format(
            db=db, nt=outShp, _sql=sql, inepsg=str(inEPSG),
            outepsg=str(outEPSG)
        ))
    
    elif gisApi == 'pandas':
        # Test if input Shp is GeoDataframe
        from geopandas import GeoDataFrame as gdf
        
        if type(inShp) == gdf:
            # Is DataFrame
            df = inShp
        
        else:
            # Assuming is file
            if os.path.exists(inShp):
                # Is File 
                from gasp.fm import tbl_to_obj
                
                df = tbl_to_obj(inShp)
            else:
                raise ValueError((
                    "For pandas API, inShp must be file or GeoDataFrame"
                ))
        
        # Project df
        newDf = df.to_crs({'init' : 'epsg:{}'.format(str(outEPSG))})
        
        if outShp:
            # Try to save as file
            from gasp.gt.to.shp import df_to_shp
            
            return df_to_shp(df, outShp)
        
        else:
            return newDf
    
    elif gisApi == 'OGRGeom':
        if not inEPSG:
            raise ValueError((
                'With OGRGeom, the definition of inEPSG is '
                'demandatory.'
            ))
        
        from osgeo import ogr
        
        g = ogr.CreateGeometryFromWkt(inShp.ExportToWkt())
        
        g.Transform(get_trans_param(inEPSG, outEPSG))
        
        return g
    
    elif gisApi == 'psql':
        from gasp.sql.db    import create_db
        from gasp.pyt.oss   import get_filename
        from gasp.sql.to    import shp_to_psql
        from gasp.gt.to.shp import dbtbl_to_shp
        from gasp.gql.prj   import sql_proj

        con_db = {
            "HOST" : 'localhost', 'PORT' : '5432', 'USER' : 'postgres',
            'PASSWORD' : 'admin', 'TEMPLATE' : 'postgis_template'
        } if not con_psql else con_psql

        # Create Database
        if "DATABASE" not in con_db:
            con_db["DATABASE"] = create_db(
                con_db, get_filename(outShp, forceLower=True),
                api='psql'
            )
        
        else:
            from gasp.sql.i import db_exists

            isDb = db_exists(con_db, con_db["DATABASE"])

            if not isDb:
                con_db["DB"] = con_db["DATABASE"]
                del con_db["DATABASE"]

                con_db["DATABASE"] = create_db(con_db, con_db["DB"], api='psql')

        # Import Data
        inTbl = shp_to_psql(con_db, inShp, api='shp2pgsql', encoding="LATIN1")

        # Transform
        oTbl = sql_proj(
            con_db, inTbl, get_filename(outShp, forceLower=True),
            outEPSG, geomCol='geom', newGeom='geom'
        )

        # Export
        outShp = dbtbl_to_shp(
            con_db, oTbl, 'geom',outShp, api='psql', epsg=outEPSG
        )
    
    else:
        raise ValueError('Sorry, API {} is not available'.format(gisApi))
    
    return outShp


"""
Manage spatial reference systems of any raster dataset
"""

def set_proj(rst, epsg):
    """
    Define Raster projection
    """
    
    from osgeo import osr
    from osgeo import gdal
    
    img = gdal.Open(rst, 1)
    
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(epsg)
    
    img.SetProjection(srs.ExportToWkt())
    
    img.FlushCache()


def reprj_rst(inRst, outRst, inEPSG, outEPSG):
    """
    Reproject Raster dataset using gdalwarp
    """
    
    import sys
    from gasp import exec_cmd
    
    cmd = (
        'gdalwarp -overwrite {inrst} {outrst} -s_srs EPSG:{inepsg} '
        '-t_srs EPSG:{outepsg}'
    ).format(
        inrst=inRst, inepsg=inEPSG,
        outrst=outRst, outepsg=outEPSG
    )
    
    codecmd = exec_cmd(cmd)
    
    return outRst

