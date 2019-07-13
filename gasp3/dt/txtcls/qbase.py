"""
Query based methods
"""

def get_rows_related_with_event(conObj, tblSchema, words, resultTbl,
                                startTime=None, endTime=None):
    """
    Take a table of a database and see if the text in one column
    is related with some event. The relation between rows and event will
    be true when a set of words given as input exists in a row.
    
    tblSchema = {
        "TNAME"   : "facedata",
        "TEXTCOL" : "message",
        "TIMECOL" : "datahora",
        "SELCOL"  : [post_id, type],
        "TEXTCASE" : (
            "CASE WHEN type = 'link' THEN lower(unaccent(description)) "
            "ELSE lower(unaccent(message)) END"
        )
    }
    
    NOTE: only works for PostgreSQL
    """
    
    from gasp3    import goToList
    from gasp3.to import db_to_tbl
    
    if "TNAME" not in tblSchema or "TEXTCOL" not in tblSchema:
        raise ValueError((
            "tblSchema input should be a dict with at least TNAME and TEXTCOL "
            "keys. The value of the first should be a table name; "
            "the value of the second shoulbe the name of a column with text "
            "to classify!"
        ))
    
    # Words to list
    words = goToList(words)
    
    cols = None if "SELCOL" not in tblSchema else goToList(tblSchema["SELCOL"])
    
    like_words = " OR ".join(["{} LIKE '%%{}%%'".format(
        tblSchema["TEXTCOL"], word) for word in words])
    
    time_where = "" if "TIMECOL" not in tblSchema or not startTime \
        or not endTime else (
            " {w} TO_TIMESTAMP({c}, 'YYYY-MM-DD HH24:MI:SS') > "
            "TO_TIMESTAMP('{l}', 'YYYY-MM-DD HH24:MI:SS') AND "
            "TO_TIMESTAMP({c}, 'YYYY-MM-DD HH24:MI:SS') < "
            "TO_TIMESTAMP('{h}', 'YYYY-MM-DD HH24:MI:SS')"
        ).format(
            w="WHERE" if "TEXTCASE" in tblSchema else "AND",
            c=tblSchema["TIMECOL"], l=startTime, h=endTime
        )
    
    Q = (
        "SELECT * FROM ("
            "SELECT {selCols} FROM {tbl}{timeWhr}"
        ") AS foo WHERE {wordsWhr}"
        ).format(
            tbl=tblSchema["TNAME"], wordsWhr=like_words,
            selCols="{} AS {}".format(
                tblSchema["TEXTCASE"], tblSchema["TEXTCOL"]
            ) if not cols else "{}, {} AS {}".format(
                ", ".join(cols), tblSchema["TEXTCASE"], tblSchema["TEXTCOL"]
            ),
            timeWhr=time_where
        ) if "TEXTCASE" in tblSchema else (
            "SELECT {selCols} FROM {tbl} WHERE ({wordsWhr}){timeWhr}"
        ).format(
            selCols=", ".join(cols + [tblSchema["TEXTCOL"]]),
            tbl=tblSchema["TNAME"], wordsWhr=like_words,
            timeWhr=time_where
            
        )
    
    return db_to_tbl(conObj, Q, resultTbl)