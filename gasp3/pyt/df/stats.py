"""
Statistic in Dataframes
"""

def df_to_freqdf(df, col):
    """
    Dataframe To frequencies DataFrame
    """
    
    import pandas
    
    freq = df[col].value_counts()
    
    freq = pandas.DataFrame(freq)
    freq.reset_index(inplace=True)
    freq.rename(columns={col : 'count', 'index' : col}, inplace=True)
    
    Total = freq['count'].sum()
    freq['percentage'] = freq['count'] / Total * 100 
    
    return freq

