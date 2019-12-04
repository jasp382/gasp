"""
Undersee Database to SRM Files and NetCDF Files
"""

# Python Packages
import os
import argparse

"""
Script Arguments
"""
def args_parse():
    p = argparse.ArgumentParser(
        description="Undersee database content to files"
    )
    
    p.add_argument(
        '-nc', '--netcdf', action='store_true',
        help="Use this flag to produce a netCDF4 file"
    )
    
    p.add_argument(
        '-ng', '--netgeo', action='store_true',
        help="Use this flag to produce a netCDF4 file"
    )
    
    return p.parse_args()


###############################################################################
###############################################################################
"""
Conversion Methods
"""
def db_to_srm(conDB, TABLE, TIME, DAY, COLS_ORDER, COL_MAP, OUT_SRM):
    """
    Database to SRM
    
    TODO: depth is not in the database, how to solve the issue
    """
    
    import codecs
    from gasp3.sql.fm     import Q_to_df
    from gasp3.gt.to.shp  import df_to_shp
    
    # Get Data from the Database
    df = Q_to_df(conDB, (
        "SELECT {cols}, {tmCol} AS daytime{dep} "
        "FROM {t} WHERE {tmCol} >= TIMESTAMP('{d} 00:00:00') "
        "AND {tmCol} <= TIMESTAMP('{d} 23:59:59') "
        "ORDER BY {tmCol}"
    ).format(
        t=TABLE, d=DAY, tmCol=TIME, cols=", ".join(COLS_ORDER),
        dep="" if 'depth' not in COL_MAP else ", 1 AS depth"
    ), db_api='mysql')
    
    if 'depth' in COL_MAP:
        COLS_ORDER.insert(2, 'depth')
    
    """
    Calculate time differences between the time of each row
    and the time of the first row
    """
    df['idx'] = df.index + 1
    
    lagDf = df.copy()
    lagDf['lag_idx'] = df.idx + 1
    lagDf.drop(['idx'] + list(COL_MAP.keys()), axis=1, inplace=True)
    lagDf.rename(columns={'daytime' : 'lagtime'}, inplace=True)
    
    df = df.merge(lagDf, how='left', left_on="idx", right_on='lag_idx')
    df['seconds'] = df.daytime - df.lagtime
    df['seconds'] = df.seconds.dt.total_seconds()
    df['seconds'] = df.seconds.fillna(0)
    df['cumseconds'] = df.seconds.cumsum()
    df.seconds = df.seconds.astype(int)
    df.cumseconds = df.cumseconds.astype(int)
    
    """
    Write Output File
    """
    initialTime = df.loc[0, 'daytime']
    with codecs.open(OUT_SRM, 'w', encoding='utf-8') as txt:
        txt.write("Time Serie Results File\n")
        txt.write((
            " SERIE_INITIAL_DATA      : {}.  {}. {}.  {}.  {}.  {}.\n"
        ).format(
            str(initialTime.year), str(initialTime.month),
            str(initialTime.day), str(initialTime.hour),
            str(initialTime.minute), str(initialTime.second)
        ))
        
        txt.write("TIME_UNITS              : SECONDS\n")
        
        txt.write("Seconds       {}\n".format(
            "   ".join([COL_MAP[c] for c in COLS_ORDER])
        ))
        
        txt.write("<BeginTimeSerie>\n")
        
        # Write Rows
        df['txt'] = df.cumseconds.astype(str)
        for c in COLS_ORDER:
            df['txt'] = df.txt + "   " + df[c].astype(str)
        
        txt.write(df.txt.str.cat(sep="\n"))
            
        txt.write("<EndTimeSerie>")
    
    return OUT_SRM


def db_to_nc(conDB, tbl, tm, daystr, varCols, latCol, lngCol, nc, cellsize=0.001):
    """
    Produce netCDF4 File
    """
    
    import numpy as np;
    import netCDF4
    import datetime as dt
    from osgeo            import gdal, osr, gdal_array
    from gasp3.pyt.oss    import create_folder
    from gasp3.sql.fm     import Q_to_df
    from gasp3.gt.prop.ff import drv_name
    
    EPSG = 4326
    
    # Get Data From database
    geoDf = Q_to_df(conDB, (
        "SELECT {var}, {lat} AS latitude, "
        "{lng} AS longitude, {tmCol} AS daytime "
        "FROM {t} WHERE {tmCol} >= TIMESTAMP('{d} 00:00:00') "
        "AND {tmCol} <= TIMESTAMP('{d} 23:59:59') "
        "ORDER BY {tmCol}"
    ).format(
        t=tbl, d=daystr, tmCol=tm, lat=latCol, lng=lngCol,
        var=", ".join(["{} AS {}".format(
            k, varCols[k]["STANDARD_NAME"]) for k in varCols])
    ), db_api='mysql')
    
    # Rename axis columns
    geoDf.rename(columns={'latitude' : 'y', 'longitude' : 'x'}, inplace=True)
    
    # Get Rasters Extent
    left = geoDf.x.min(); right = geoDf.x.max()
    bottom = geoDf.y.min(); top = geoDf.y.max()
    
    # Get row and col number
    rows = int(round((top - bottom) / cellsize, 0))
    cols = int(round((right - left) / cellsize, 0))
    
    # Get Geo Transform Object
    geo_transform = (left, cellsize, 0, top, 0, -cellsize)
    
    # Create rasters for each point in geoDf and each variable
    tmpFolder = create_folder(os.path.join(
        os.path.dirname(nc), os.path.splitext(os.path.basename(nc))[0]
    ))
    geoDf['fid'] = geoDf.index
    
    def create_rsts(row):
        timeval = row.daytime
        for var in varCols:
            # Create raster
            OUT_RST_I = os.path.join(tmpFolder, 'rst_{}_{}.tif'.format(
                str(int(row.fid)), varCols[var]["STANDARD_NAME"]))
            
            # Get var value in that time
            varValue = row[varCols[var]["STANDARD_NAME"]]
            
            # Create array
            dataArray = np.zeros((rows, cols))
            
            # Get index for that position
            px = int((row.x - geo_transform[0]) / geo_transform[1])
            py = int((row.y - geo_transform[3]) / geo_transform[5])
            
            # Add value to Array in the correct position
            dataArray[py][px] = varValue
            
            # Save Raster just in case
            driver = gdal.GetDriverByName(drv_name(OUT_RST_I))
            outData = driver.Create(
                OUT_RST_I, cols, rows, 1,
                gdal_array.NumericTypeCodeToGDALTypeCode(dataArray.dtype)
            )
            
            outData.SetGeoTransform(geo_transform)
            
            outBand = outData.GetRasterBand(1)
            outBand.SetNoDataValue(0)
            outBand.WriteArray(dataArray)
            
            proj = osr.SpatialReference()
            proj.ImportFromEPSG(EPSG)
            
            outData.SetProjection(proj.ExportToWkt())
            outBand.FlushCache()
            
            del outData
            
            row[varCols[var]["STANDARD_NAME"] + '_f'] = OUT_RST_I
        
        return row
    
    geoDf = geoDf.apply(lambda x: create_rsts(x), axis=1)
    
    # Get list with latitude and longitudes values for x and y variables
    x = np.arange(cols)*geo_transform[1]+geo_transform[0]
    y = np.arange(rows)*geo_transform[5]+geo_transform[3]
    
    # Get base time
    year, month, day = daystr.split('-')
    basedate = dt.datetime(int(year),int(month),int(day),0,0,0)
    
    # create NetCDF file
    nco = netCDF4.Dataset(nc,'w',clobber=True)
    
    # chunking is optional, but can improve access a lot: 
    # (see: http://www.unidata.ucar.edu/blogs/developer/entry/chunking_data_choosing_shapes)
    chunk_x=2#16
    chunk_y=2#16
    chunk_time=12
    
    # create dimensions, variables and attributes:
    nco.createDimension('lon', cols)
    nco.createDimension('lat', rows)
    nco.createDimension('time', None)
    
    # Time variable
    timeo = nco.createVariable('time','f4',('time'))
    timeo.units = 'days since {} 00:00:00'.format(daystr)
    timeo.long_name= "Time"
    timeo.standard_name = 'time'
    timeo.axis = "T"
    
    # Longitude variable
    xo = nco.createVariable('lon','f4',('lon'))
    xo.long_name = "Longitude"
    xo.units = 'degrees_east'
    xo.standard_name = 'longitude'
    xo.axis="X"
    
    # Latitude variable
    yo = nco.createVariable('lat','f4',('lat'))
    yo.long_name="Latitude"
    yo.units = 'degrees_north'
    yo.standard_name = 'latitude'
    yo.axis="Y"
    
    # create container variable for CRS: x/y WGS84 datum
    crso = nco.createVariable('crs','i4')
    crso.grid_mapping_name='polar_stereographic'
    crso.straight_vertical_longitude_from_pole = -45.
    crso.latitude_of_projection_origin = 70.
    crso.scale_factor_at_projection_origin = 1.0
    crso.false_easting = 0.0
    crso.false_northing = 0.0
    crso.semi_major_axis = 6378137.0
    crso.inverse_flattening = 298.257223563
    
    # create data variables
    netcdfvar = {}
    for var in varCols:
        tmno = nco.createVariable(
            varCols[var]["SLUG"], 'f4', ('time', 'lat', 'lon'), zlib=True,
            #chunksizes=[chunk_time,chunk_y,chunk_x],
            fill_value=-9999
        )
        tmno.units = varCols[var]["UNIT"]
        tmno.scale_factor = 1
        tmno.long_name = varCols[var]["LONG_NAME"]
        tmno.standard_name = varCols[var]["STANDARD_NAME"]
        tmno.grid_mapping = 'crs'
        tmno.set_auto_maskandscale(False)
        
        netcdfvar[varCols[var]["SLUG"]] = tmno
    
    nco.Conventions='CF-1.6'
    
    #write x,y
    xo[:]=x
    yo[:]=y
    
    itime=0
    # Write variables data
    for idx, row in geoDf.iterrows():
        tempo = row.daytime
        date = dt.datetime(
            int(tempo.year), int(tempo.month), int(tempo.day),
            int(tempo.hour), int(tempo.minute), int(tempo.second)
        )
        dtime=(date-basedate).total_seconds()/86400
        timeo[idx]=dtime
        for var in varCols:
            # Get var obj
            varObj = netcdfvar[varCols[var]["SLUG"]]
            # Open Raster
            tmn=gdal.Open(row[varCols[var]["STANDARD_NAME"] + '_f'])
            # Raster to Array
            a = tmn.ReadAsArray()
            # Write Array in netCDF4
            a = np.where(a == 0, np.NaN, a)
            a = a.astype(np.float32)
            varObj[idx, :, :]=a
    
    # Close file
    nco.close()
    
    return nc


def db_to_nc_v2(conDB, tbl, daystr, dimCols, varCols, timeCol, outNc):
    """
    DB to NC according Copernicus specifications for data collected IN SITU
    """
    
    import netCDF4
    import datetime as dt
    import numpy as np
    from gasp3.sql.fm import Q_to_df
    
    ############################################################################
    ########################## Global Variables ################################
    QCF = "quality flag"
    CT2 = "OceanSITES reference table 2"
    QFlags = np.array([0,1,2,3,4,5,6,7,8,9]).astype('int8')
    QC_STR = (
        "no_qc_performed good_data probably_good_data "
        "bad_data_that_are_potentially_correctable bad_data "
        "value_changed not_used nominal_value "
        "interpolated_value missing_value"
    )
    
    DM = 'method of data processing'
    DMC = 'OceanSITES reference table 5'
    DMFlag = "R, P, D, M"
    DMMean = 'real-time provisional delayed-mode mixed'
    ############################################################################
    """
    Get Data From Database
    """
    geoDf = Q_to_df(conDB, (
        "SELECT {dim}, {var} FROM {t} "
        "WHERE {tmCol} >= TIMESTAMP('{d} 00:00:00') AND "
        "{tmCol} <= TIMESTAMP('{d} 23:59:59') "
        "ORDER BY {tmCol}"
    ).format(
        dim=", ".join(["{} AS {}".format(d["DB_COL"], d["SLUG"]) for d in dimCols]),
        var=", ".join(["{} AS {}".format(v["DB_COL"], v["SLUG"]) for v in varCols]),
        t=tbl, d=daystr, tmCol=timeCol
    ), db_api='mysql')
    
    """ Create NC File """
    ncObj = netCDF4.Dataset(outNc, 'w', clobber=True)
    
    """ Create Default Dimensions """
    ncObj.createDimension("POSITION", geoDf.shape[0])
    ncObj.createDimension("STRING32", 32)
    ncObj.createDimension("STRING256", 256)
    
    """ Create User Dimensions and Related Variables """
    for d in dimCols:
        if d["AXIS"] == 'X' or d["AXIS"] == 'Y':
            varValues = geoDf[d["SLUG"]]
        elif d["AXIS"] == 'T':
            timeDim = d["SLUG"]
        else:
            varValues = geoDf[d["SLUG"]].unique()
        
        # Create Dimension
        ncObj.createDimension(
            d["SLUG"], varValues.shape[0] if d["AXIS"] != 'T' else None)
        
        # Create Variable
        d["VAROBJ"] = ncObj.createVariable(
            d["SLUG"], d["TYPE"],
            (d["SLUG"]) if 'IS_CHILD' not in d else d["IS_CHILD"]
        )
        
        # Add Attributes to Variable
        d["VAROBJ"].units         = d["UNIT"]
        d["VAROBJ"].long_name     = d["LONG_NAME"]
        d["VAROBJ"].standard_name = d["STANDARD_NAME"]
        d["VAROBJ"].axis          = d["AXIS"]
        d["VAROBJ"].valid_min     = d["MIN"]
        d["VAROBJ"].valid_max     = d["MAX"]
        
        # Set Variable Values
        if d["AXIS"] != 'T' and d["AXIS"] != 'Z':
            d["VAROBJ"][:] = varValues.tolist()
        
        # Add variable for Quality Flag
        if d["AXIS"] == 'T' or d["AXIS"] == 'Z':
            d["QC"] = ncObj.createVariable(
                d["SLUG"] + "_QC", 'byte',
                (d["SLUG"]) if 'IS_CHILD' not in d else d["IS_CHILD"],
                fill_value=-128
            )
            
            d["QC"].long_name    = QCF
            d["QC"].conventions  = CT2
            d["QC"].valid_min    = 0
            d["QC"].valid_max    = 9
            d["QC"].flag_values  = QFlags
            d["QC"].flag_meanings = QC_STR
            
            d["QC"][:] = np.zeros(geoDf.shape[0]) if 'IS_CHILD' not in d else \
                np.zeros((geoDf.shape[0], 1))
        
        # Add variable for Data processing method
        if d["AXIS"] == 'Z':
            d["DM"] = ncObj.createVariable(
                d["SLUG"] + "_DM", "S1",
                (timeDim, d["SLUG"]), fill_value= " "
            )
            
            d["DM"].long_name     = DM
            d["DM"].conventions   = DMC
            d["DM"].flag_values   = DMFlag
            d["DM"].flag_meanings = DMMean
    
    """ Create Data Variables """
    for v in varCols:
        v["VAROBJ"] = ncObj.createVariable(
            v["SLUG"], v["TYPE"], v["DIM"], zlib=True, fill_value=-9999
        )
        
        v["VAROBJ"].units         = v["UNIT"]
        v["VAROBJ"].long_name     = v["LONG_NAME"]
        v["VAROBJ"].standard_name = v["STANDARD_NAME"]
        
        # Create DM Var
        v["DM"] = ncObj.createVariable(
            v["SLUG"] + "_DM", "S1", v["DIM"], fill_value=" "
        )
        
        v["DM"].long_name     = DM
        v["DM"].conventions   = DMC
        v["DM"].flag_values   = DMFlag
        v["DM"].flag_meanings = DMMean
        
        # Create QC car
        v["QC"] = ncObj.createVariable(
            v["SLUG"] + "_QC", "byte", v["DIM"], fill_value=-128)
        
        v["QC"].long_name = QCF
        v["QC"].conventions  = CT2
        v["QC"].valid_min    = 0
        v["QC"].valid_max    = 9
        v["QC"].flag_values  = QFlags
        v["QC"].flag_meanings = QC_STR
    
    """ Create other meta variables """
    # Position QC
    pqc = ncObj.createVariable('POSITION_QC', "byte", ("POSITION"))
    pqc.long_name = QCF
    pqc.conventions = CT2
    pqc.valid_min = 0
    pqc.valid_max = 9
    pqc.flag_values = QFlags
    pqc.flag_meanings = QC_STR
    pqc[:] = np.zeros(geoDf.shape[0])
    
    # Create DC Reference
    dcref = ncObj.createVariable('DC_REFERENCE', 'S1', (timeDim, "STRING32"))
    dcref.long_name = "Station/Location unique identifier in data centre"
    dcref.conventions = "Data centre convention"
    
    # Create POSITION SYSTEM
    pos_sys = ncObj.createVariable('POSITIONING_SYSTEM', 'S1', ("POSITION"))
    pos_sys.long_name = "Positioning system"
    pos_sys.flag_values = "A, G, L, N, U"
    pos_sys.flag_meanings = "Argos, GPS, Loran, Nominal, Unknown"
    pos_sys[:] = ['G' for i in range(geoDf.shape[0])]
    
    """ Add data to Variables """
    year, month, day = daystr.split('-')
    basedate = dt.datetime(int(year),int(month),int(day),0,0,0)
    
    for d in dimCols:
        if d["SLUG"] != timeDim:
            continue
        else:
            timeDimObj = d
            break
    
    for idx, row in geoDf.iterrows():
        tempo = row[timeDim]
        date = dt.datetime(
            int(tempo.year), int(tempo.month), int(tempo.day),
            int(tempo.hour), int(tempo.minute), int(tempo.second)
        )
        dtime = (date - basedate).total_seconds()/86400
        timeDimObj["VAROBJ"][idx] = dtime
        
        for d in dimCols:
            if d["AXIS"] == 'Z':
                d["VAROBJ"][idx, :] = [row[d["SLUG"]]]
                break
            else:
                continue
        
        for v in varCols:
            v["VAROBJ"][idx, :] = [row[v["SLUG"]]]
            v["QC"][idx, :] = 1
    
    """ Close File """
    ncObj.close()
    
    return outNc


###############################################################################
###############################################################################
"""
Run Script
"""
if __name__ == '__main__':
    """
    Get user Arguments
    """
    
    ARGS = args_parse()
    
    """
    Parameters to connect to Database
    """
    
    con_db = {
        'HOST' : 'localhost', 'PORT' : '3306', 'USER' : 'jasp',
        'PASSWORD' : 'admin', 'DATABASE' : 'undersee'
    }
    
    # Database Meta
    data_table = "buoys"
    time_col   = 'created_at'
    day        = "2019-09-20"
    
    BASE_FOLDER = '/home/jasp/undersee'
    if ARGS.netcdf:
        out_file = os.path.join(
            BASE_FOLDER, 'nc', "GL_LATEST_TS_TS_FGG8669_{}.nc".format(
                day.replace('-', '')
            )
        )
    else:
        out_file = os.path.join(
            BASE_FOLDER, 'srm' if not ARGS.netgeo else 'nc',
            'timeseries_{}.{}'.format(
                day.replace('-', ''), 'srm' if not ARGS.netgeo else 'nc'
            )
        )
    
    if not ARGS.netcdf and not ARGS.netgeo:
        """
        Produce SRM File
        """
        cols_order = ['value19', 'value18', 'value1', 'value4']
        cols_map   = {
            'value1' : 'temperature(C)', 'value18' : 'latitude',
            'value19' : 'longitude',
            'value4' : 'practical_salinity(psu)', 'depth' : 'depth(m)'
        }
        
        # Produce file
        db_to_srm(con_db, data_table, time_col, day, cols_order, cols_map, out_file)
    
    elif not ARGS.netcdf and ARGS.netgeo:
        """
        Produce netCDF4 file with geo reference
        """
        
        variableCols = {
            'value1'  : {
                "STANDARD_NAME" : 'temperature', 
                "LONG_NAME" : 'Sea Surface Temperature', 
                "UNIT" : 'degC', 'SLUG': 'sst'},
            'value4'  : {
                "STANDARD_NAME" : 'practical_salinity', 
                "LONG_NAME" : 'Salinity', 
                "UNIT" : 'degC', 'SLUG' : 'sal'
            }
        }
        
        latitudeCol = 'value18'
        longitudeCol = 'value19'
        
        db_to_nc(con_db, data_table, time_col, day, variableCols,
                 latitudeCol, longitudeCol, out_file)
    
    else:
        """
        Produce netCDF4 file according Copernicus specification
        """
        
        dimensionCols = [
            {
                "DB_COL" : 'value18',
                "STANDARD_NAME" : 'latitude',
                "LONG_NAME" : 'Latitude of each location',
                "UNIT" : "degree_north",
                "AXIS" : "Y", "SLUG" : "LATITUDE",
                "MIN" : -90.0, "MAX" : 90.0,
                "TYPE" : 'f4'
            },{
                "DB_COL" : 'value19',
                "STANDARD_NAME" : 'longitude',
                "LONG_NAME" : 'Longitude of each location',
                "UNIT" : 'degree_east', "SLUG" : "LONGITUDE",
                "AXIS" : "X", "MIN" : -180.0, "MAX" : 180.0,
                "TYPE" : 'f4'
            }, {
                "DB_COL" : 'created_at',
                "STANDARD_NAME" : 'time',
                "LONG_NAME" : 'Time', "SLUG" : "TIME",
                "UNIT" : "days since {}T00:00:00Z".format(day),
                "MIN" : -90000.0, "MAX" : 90000.0,
                "AXIS" : 'T', "TYPE" : 'f4'
            }, {
                "DB_COL" : '1',
                "STANDARD_NAME" : 'depth',
                "LONG_NAME" : 'Depth', 'UNIT' : 'm',
                "SLUG" : 'DEPH', "AXIS" : "Z",
                "MIN" : -12000.0, "MAX" : 12000,
                "TYPE" : 'i4', "IS_CHILD" : ("TIME", "DEPH")
            }
        ]
        
        variableCols = [
            {
                "DB_COL" : 'value1',
                "STANDARD_NAME" : 'sea_water_temperature', 
                "LONG_NAME" : 'Sea temperature', 
                "UNIT" : 'degrees_C', 'SLUG': 'TEMP',
                "TYPE" : 'f4',
                "DIM" : ("TIME", "DEPH")
            }, {
                "DB_COL" : '(value2 / 10000.0)',
                "STANDARD_NAME" : 'sea_water_electrical_conductivity',
                "LONG_NAME" : 'Electrical conductivity',
                "UNIT" : 'S m-1', "SLUG" : "CNDC",
                "TYPE" : 'f4', "DIM" : ("TIME", "DEPH")
            }, {
                "DB_COL" : 'value4',
                "STANDARD_NAME" : 'sea_water_practical_salinity', 
                "LONG_NAME" : 'Practical salinity', 
                "UNIT" : '0.001', 'SLUG' : 'PSAL',
                "TYPE" : 'f4', "DIM" : ("TIME", "DEPH")
            }
        ]
        
        db_to_nc_v2(
            con_db, data_table, day, dimensionCols, variableCols, time_col, out_file)
