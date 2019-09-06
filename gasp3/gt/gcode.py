"""
Google Data To ESRI Shapefile
"""

def shp_from_address(inTbl, idAddr, addrCol, outShp,
                     epsg_out=4326, sheet_name=None,
                     doorNumber=None, zip4=None, zip3=None,
                     city=None, language=None, useComponents=None,
                     country=None):
    """
    Receive a table with a list of addresses and use the Google Maps API
    to get their position
    
    Preferred Address Structure:
    Rua+dos+Combatentes+da+Grande+Guerra,+14,+3030-185,+Coimbra
    
    Table Structure:
    idAddr | addrCol | doorNumber | zip4 | zip3 | city
    idAddr field and address field are demandatory
    
    For now, The input table must be a excel file or a dbf table
    
    # TODO: Some of the rows could not have Geometry
    """
    
    from gasp3.dt.glg.geocod import get_position
    from gasp3.dt.fm         import tbl_to_obj
    from gasp3.dt.to.geom    import pnt_dfwxy_to_geodf
    from gasp3.pyt.oss       import get_fileformat
    from gasp3.pyt.df.fld    import fld_types
    from gasp3.dt.to.obj     import df_to_dict, dict_to_df
    from gasp3.dt.to.shp     import df_to_shp
    
    # Get Addresses
    tblFormat = get_fileformat(inTbl)
    
    tblAdr = tbl_to_obj(inTbl, sheet=sheet_name)
    
    # Check if given columns are in table
    fields = [idAddr, addrCol, doorNumber, zip4, zip3, city]
    for f in fields:
        if f:
            if f not in tblAdr.columns.values:
                raise ValueError("{} column not in {}".format(f, inTbl))
    
    # Convert numeric fields to unicode
    colTypes = fld_types(tblAdr)
    for col in colTypes:
        if colTypes[col] != 'object':
            if colTypes[col] == 'float32' or colTypes[col] == 'float64':
                tblAdr[col] = tblAdr[col].astype(int)
            
        tblAdr[col] = tblAdr[col].astype(unicode, 'utf-8')
    
    # Create search field
    if not useComponents:
        if doorNumber and zip4 and zip3 and city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[doorNumber].astype(unicode, "utf-8") + unicode(",", "utf-8") + \
                tblAdr[zip4] + unicode("-", "utf-8") + \
                tblAdr[zip3] + unicode(",", "utf-8") + tblAdr[city]
    
        elif not doorNumber and zip4 and zip3 and city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[zip4] + unicode("-", "utf-8") + \
                tblAdr[zip3] + unicode(",", "utf-8") + tblAdr[city]
    
        elif doorNumber and not zip4 and not zip3 and not city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[doorNumber]
    
        elif not doorNumber and not zip4 and not zip3 and not city:
            tblAdr["search"] = tblAdr[addrCol]
    
        elif doorNumber and zip4 and not zip3 and city:
            tblAdr = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[doorNumber] + unicode(",", "utf-8") + \
                tblAdr[zip4] + unicode(",", "utf-8") + tblAdr[city]
    
        elif doorNumber and not zip4 and not zip3 and city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[doorNumber] + unicode(",", "utf-8") + tblAdr[city]
    
        elif not doorNumber and zip4 and not zip3 and city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[city]
    
        elif not doorNumber and zip4 and zip3 and not city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[zip4] + unicode("-", "utf-8") + tblAdr[zip3]
    
        elif doorNumber and zip4 and not zip3 and not city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[doorNumber] + unicode(",", "utf-8") + tblAdr[zip4]
    
        elif doorNumber and zip4 and zip3 and not city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[doorNumber] + unicode(",", "utf-8") + tblAdr[zip4] + \
                unicode("-", "utf-8") + tblAdr[zip3]
    
        elif not doorNumber and zip4 and not zip3 and not city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[zip4]
    
        elif not doorNumber and not zip4 and not zip3 and city:
            tblAdr["search"] = tblAdr[addrCol] + unicode(",", "utf-8") + \
                tblAdr[city]
    
        else:
            raise ValueError('Parameters are not valid')
    
        # Sanitize search string
        tblAdr["search"] = tblAdr.search.str.replace(' ', '+')
    tblAdr = df_to_dict(tblAdr)
    
    # Geocode Addresses
    for idx in tblAdr:
        if not useComponents:
            glg_response = get_position(
                tblAdr[idx]["search"], country=None,
                language=None, locality=None, postal_code=None
            )
        else:
            if zip4 and zip3:
                _postal = u'{}-{}'.format(tblAdr[idx][zip4], tblAdr[idx][zip3])
            
            elif zip4 and not zip3:
                _postal = u'{}'.format(tblAdr[idx][zip4])
            
            else:
                _postal = None
            
            glg_response = get_position(
                u"{}{}".format(
                    tblAdr[idx][addrCol], u",{}".format(
                        tblAdr[idx][doorNumber]
                    ) if doorNumber else u""
                ),
                country=country, language=language,
                locality=tblAdr[idx][city].replace(" ", "+") if city else None,
                postal_code=_postal.replace(" ", "+")
            )
        
        if not glg_response: continue
        
        tblAdr[idx]["x"] = glg_response[0]['geometry']['location']['lng']
        tblAdr[idx]["y"] = glg_response[0]['geometry']['location']['lat']
        
        tblAdr[idx]["G_ADRS"] = glg_response[0]["formatted_address"]
        
        for i in glg_response[0]["address_components"]:
            if   i["types"][0] == 'street_number' : F = "G_PORT"
            elif i["types"][0] == 'route'         : F = "G_STREET"
            elif i["types"][0] == 'postal_code'   : F = "G_ZIPCODE"
            else: continue
            
            tblAdr[idx][F] = i["long_name"]
    
    # Convert Dataframe to GeoDataframe
    geoAdr = pnt_dfwxy_to_geodf(dict_to_df(tblAdr), "x", "y", 4326)
    
    # Reproject if user wants it
    if epsg_out != 4326:
        from gasp.mng.prj import project
        geoAdr = project(geoAdr, None, epsg_out, gisApi='pandas')
    
    # To Shapefile
    df_to_shp(geoAdr, outShp)
    
    return geoAdr

def address_from_featcls(inShp, outShp, epsg_in):
    """
    Read a point geometry and return a table with the addresses
    """
    
    from gasp3.dt.glg.geocod import get_address
    from gasp3.dt.fm         import tbl_to_obj
    from gasp3.dt.to.geom    import df_to_geodf
    from gasp3.dt.to.shp     import df_to_shp
    from gasp3.dt.to.obj     import df_to_dict, dict_to_df
    from gasp3.pyt.df.fld    import pointxy_to_cols
    from gasp3.gt.prop.feat  import get_gtype
    
    # Convert ESRI Shapefile to GeoDataFrame
    geoDf = tbl_to_obj(inShp)
    
    # Get Geometry field name
    for col in geoDf.columns.values:
        if col == 'geom' or col ==  'geometry':
            F_GEOM = col
            break
        else:
            continue
    
    # Check if inShp has a Geom of Type Point
    inGeomType = get_gtype(geoDf, geomCol=F_GEOM, gisApi='pandas')
    
    if inGeomType != 'Point' and inGeomType != 'MultiPoint':
        raise ValueError('The input geometry must be of type point')
    
    # Reproject geodf if necessary
    if epsg_in != 4326:
        from gasp3.gt.mng.prj import project
        
        geoDf = project(geoDf, None, 4326, gisApi='pandas')
    
    # Get Coords of each point
    geoDf = pointxy_to_cols(geoDf, F_GEOM, colX="x", colY='y')
    
    # Search for addresses
    geoDict = df_to_dict(geoDf)
    for idx in geoDict:
        glg_response = get_address(geoDict[idx]["y"], geoDict[idx]["x"])
        
        geoDict[idx]["G_ADDRESS"] = glg_response[0]['formatted_address']
        
        for i in glg_response[0]["address_components"]:
            if   i["types"][0] == 'street_mumber' : F = "G_PORT"
            elif i["types"][0] == 'route'         : F = "G_STREET"
            elif i["types"][0] == 'postal_code'   : F = "G_ZIPCODE"
            else: continue
            
            geoDict[idx][F] = i["long_name"]
    
    # Save results in a new file
    geoDf = dict_to_df(geoDict)
    geoDf = df_to_geodf(geoDf, F_GEOM, 4326)
    
    geoDf.drop(["x", "y"], axis=1, inplace=True)
    
    if epsg_in != 4326:
        geoDf = project(geoDf, None, epsg_in, gisApi='pandas')
    
    df_to_shp(geoDf, outShp)
    
    return geoDf
