"""
Sanitize data for Text Classification
"""

def get_stop_words(conPSQL, inTbl, fidCol, txtCol, outFile,
                   lang='portuguese', inSheet=None):
    """
    Pick a text column and save it in a new column only with the stop words.
    
    Uses PostgreSQL dictionaries to get stop words
    """
    
    from gasp3.pyt.oss    import get_filename
    from gasp3.sql.i      import cols_name
    from gasp3.sql.mng.db import create_db
    from gasp3.to         import tbl_to_db, db_to_tbl
    
    
    FILENAME = get_filename(inTbl)
    
    # Create Temp database
    db = conPSQL["DATABASE"] if "DATABASE" in conPSQL else "db_" + FILENAME
    conPSQL["DATABASE"] = create_db(conPSQL, db)
    
    # Send table to PostgreSQL
    tbl = tbl_to_db(inTbl, conPSQL, FILENAME, sheet=inSheet, api_db='psql')
    
    cols = cols_name(conPSQL, tbl, sanitizeSpecialWords=None, api='psql')
    
    # Sanitize data  and create a new column only with stop words
    Q1 = (
        "(SELECT *, to_tsvector('{_lang}', regexp_replace("
            "regexp_replace(lower(unaccent({txt_c})), 'http://[^:\s]+(\S+)', "
            "' ', 'g'), '[^\w]+', ' ', 'g')) "
        "AS txt_data FROM {t}) AS stop_table"
    ).format(_lang=lang, txt_c=txtCol, t=tbl)
    
    Q2 = (
        "SELECT {selCols}, ARRAY_TO_STRING(array_agg("
            "word ORDER BY word_index), ' ', '*') AS {outCol}, "
        "REPLACE(CAST(STRIP("
            "stop_table.txt_data) AS text), '''', '') AS no_duplicated "
        "FROM ("
            "SELECT fid, word, CAST(UNNEST(word_index) AS integer) "
            "AS word_index FROM ("
                "SELECT fid, SPLIT_PART(tst, ';', 1) AS word, "
                "STRING_TO_ARRAY(SPLIT_PART(tst, ';', 2), ',') AS word_index FROM ("
                    "SELECT {fid} AS fid, REPLACE(REPLACE(REPLACE(REPLACE(REPLACE("
                        "CAST(UNNEST(txt_data) AS text), "
                            "',{{', ',\"{{'), ',\"{{', ';'), '}}\"', ''), "
                            "'(', ''), '}}', '') AS tst "
                    "FROM {tbl}"
                ") AS foo"
            ") AS foo2"
        ") AS foo3 INNER JOIN {tbl} ON foo3.fid = stop_table.{fid} "
        "GROUP BY {selCols}, stop_table.txt_data"
    ).format(
        outCol="clean_" + txtCol, tbl=Q1, fid=fidCol,
        selCols=", ".join(["stop_table.{}".format(i) for i in cols])
    )
    
    # Export new table
    return db_to_tbl(conPSQL, Q2, outFile, sheetsNames=inSheet)

