"""
Methods to extract data from youtube
"""


# ------------------------------ #
"""
Global Variables
"""
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
GOOGLE_API_KEY = "AIzaSyAmyPmqtxD20urqtpCpn4ER74a6J4N403k"
# ------------------------------ #

def search_by_keyword(search_term, maxResults=20,
                      resources_type='video,channel,playlist'):
    """
    Search on youtube based on a key word
    
    Retrive a dict with the following structure:
    d = {
        'videos'   : [list with videos name],
        'channels' : [list with channels name],
        'playlists': [list with playlists name]
    }
    """
    
    from apiclient.discovery import build
    
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=GOOGLE_API_KEY
    )
    
    # Call the search.list method to retrieve results matching the specified
    # query term
    search_response = youtube.search().list(
        q=search_term,
        part="id,snippet",
        maxResults=maxResults,
        type=resources_type
    ).execute()
    
    videos = []
    channels = []
    playlists = []
    
    # Add each result to the appropriate list, and then display the lists of
    # matching videos, channels, and playlists.
    for search_result in search_response.get("items", []):
        if search_result["id"]["kind"] == "youtube#video":
            videos.append(
                {
                    'id' : search_result["id"]["videoId"],
                    'title': search_result["snippet"]["title"],
                    'description': search_result["snippet"]["description"],
                    'url' : search_result["snippet"]["thumbnails"]["default"]["url"],
                }
            )
        
        elif search_result["id"]["kind"] == "youtube#channel":
            channels.append(
                {
                    'id' : search_result["id"]["channelId"],
                    'title': search_result["snippet"]["title"],
                    'description': search_result["snippet"]["description"],
                    'url' : search_result["snippet"]["thumbnails"]["default"]["url"],
                }
            )
        
        elif search_result["id"]["kind"] == "youtube#palylist":
            playlists.append(
                {
                    'id' : search_result["id"]["palylistId"],
                    'title': search_result["snippet"]["title"],
                    'description': search_result["snippet"]["description"],
                    'url' : search_result["snippet"]["thumbnails"]["default"]["url"],
                }
            )
    
    if 'video' in resources_type and 'channel' in resources_type and \
       'playlist' in resources_type:
        return {
            'videos'   : videos,
            'channels' : channels,
            'playlists': playlists
        }
    
    elif 'video' in resources_type and 'channel' in resources_type and \
        'playlist' not in resources_type:
        return {
            'videos'   : videos,
            'channels' : channels
        }
    
    elif 'video' in resources_type and 'channel' not in resources_type and \
        'playlist' in resources_type:
        return {
            'videos'   : videos,
            'playlists': playlists
        }
    
    elif 'video' not in resources_type and 'channel' in resources_type and \
        'playlist' in resources_type:
        return {
            'channels' : channels,
            'playlists': playlists
        }
    
    elif 'video' in resources_type and 'channel' not in resources_type and \
        'playlist' not in resources_type:
        return videos
    
    elif 'video' not in resources_type and 'channel' in resources_type and \
        'playlist' not in resources_type:
        return channels
    
    elif 'video' not in resources_type and 'channel' not in resources_type \
        and 'playlist' in resources_type:
        return playlists


def get_video_details_by_keyword(keyword):
    """
    Return array with all details of a video object
    """
    
    from apiclient.discovery import build
    
    
    videos = search_by_keyword(
        keyword, maxResults=50, resources_type='video'
    )
    
    youtube = build(
        YOUTUBE_API_SERVICE_NAME,
        YOUTUBE_API_VERSION,
        developerKey=GOOGLE_API_KEY        
    )
    
    search_response = youtube.videos().list(
        part='id,snippet,statistics,recordingDetails',
        id=','.join([video['id'] for video in videos])
    ).execute()
    
    data = []
    for instance in search_response.get("items", []):
        if "recordingDetails" in instance.keys():
            if "location" in instance["recordingDetails"].keys():
                if "latitude" in instance["recordingDetails"]["location"].keys() and "longitude" in instance["recordingDetails"]["location"].keys():
                    latitude = instance["recordingDetails"]["location"]["latitude"]
                    longitude = instance["recordingDetails"]["location"]["longitude"]
                else:
                    latitude = None
                    longitude = None
            else:
                latitude = None
                longitude = None
            
            if "locationDescription" in instance["recordingDetails"].keys():
                location = instance["recordingDetails"]["locationDescription"]
            
            else:
                location = ''
            
            if "recordingDate" in instance["recordingDetails"].keys():
                date = instance["recordingDetails"]["recordingDate"]
            
            else:
                date = ''
        
        else:
            latitude = None
            longitude = None
            location = ''
            date = ''
        
        if "likeCount" in instance["statistics"]:
            likes = instance["statistics"]["likeCount"]
        else:
            likes = ''
        
        data.append(
            {
                'fid'         : instance["id"],
                'title'       : instance["snippet"]["title"],
                'description' : instance["snippet"]["description"],
                'url'         : 'https://www.youtube.com/watch?v=' + str(instance["id"]),
                'views'       : instance["statistics"]["viewCount"],
                'likes'       : likes,
                'y'           : latitude,
                'x'           : longitude,
                'location'    : location,
                'date'        : date
            }
        )
    
    return data

def geovideos_to_array(search_words, epsg_out=4326,
                  spatial_filter=None, epsg_filter=4326):
    """
    Locate videos on youtube and save these locations to a vectorial file
    """
    
    import os
    
    from gasp.oss.ops        import del_files_by_name
    from gasp.to.geom        import create_point
    from gasp.mng.prj        import project_geom
    from gasp.anls.tplgy     import point_in_polygon
    from gasp.anls.prox.bf   import draw_buffer
    
    videos = get_video_details_by_keyword(search_words)
    
    videos_with_location = []
    
    for video in videos:
        if video['y'] and video['x']:
            videos_with_location.append(video)
    
    if not len(videos_with_location):
        # Return nodata
        return 0
    
    if spatial_filter:
        from gasp.anls.prox.bf import getBufferParam
        
        x_center, y_center, dist = getBufferParam(
            spatial_filter, epsg_filter)
        
        bufferCenter = project_geom(
            create_point(x_center, y_center, api='ogr'),
            4326, 3857, api='ogr'
        )
        
        bufferGeom = draw_buffer(bufferCenter, dist)
        filterData = []
    
    for instance in videos_with_location:
        # Create point
        WGS_POINT = create_point(
            float(instance['x']),
            float(instance['y']), api='ogr'
        )
        
        point = project_geom(WGS_POINT, 4326, 3857, api='ogr')
        
        isPointInPolygon = point_in_polygon(point, bufferGeom)
        
        if isPointInPolygon:
            if epsg_out != 4326:
                trans_point = project_geom(WGS_POINT, 4326, epsg_out, api='ogr')
                
                instance['x'] = trans_point.GetX()
                instance['y'] = trans_point.GetY()
            
            filterData.append(instance)
    
    return filterData


def geovideos_to_shp(buffer_shp, epsg_in, outshp, keyword, epsg_out=4326):
    """
    Search for data in Youtube and return a Shapefile with that data
    """
    
    from gasp.to.shp import df_to_shp
    
    videos = geovideos_to_array(
        keyword, epsg_out=epsg_out, 
        spatial_filter=buffer_shp, 
        epsg_filter=epsg_in
    )
    
    if not videos: return None
    
    array_to_shp(videos, outshp, epsg=epsg_out)

