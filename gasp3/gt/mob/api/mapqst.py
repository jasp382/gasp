"""
Maquest Things
"""


def rev_geocode_df(df, epsg, key=None, isOpen=None):
    """
    Add Locations after Reverse Geocoding to Pandas Dataframe
    """
    
    from gasp3.adv.mob.mapqst import rev_geocode
    from gasp3.gt.prj         import proj
    
    __df = df.copy() if epsg == 4326 else proj(df, None, 4326, gisApi='pandas')
    
    __df["latitude"]  = __df.geometry.y.astype(float)
    __df["longitude"] = __df.geometry.x.astype(float) 
    
    def add_locations(row):
        data = rev_geocode(
            row.latitude, row.longitude, keyToUse=key, useOpen=isOpen
        )
        
        row["locations"] = data["results"][0]["locations"][0]
        
        return row
        
    __df = __df.apply(lambda x: add_locations(x), axis=1)
    
    return __df

