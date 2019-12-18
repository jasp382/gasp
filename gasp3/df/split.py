"""
Split Pandas DataFrame
"""


def split_df(df, N):
    """
    Split Dataframe making each sub dataframe
    having only N rows
    """
    
    __len = int(df.shape[0])
    
    if __len < N:
        L = [df]
    
    else:
        L= []
        for i in range(0, __len, N):
            if i + N < __len:
                L.append(df.iloc[i:i+N])
            else:
                L.append(df.iloc[i:__len])
    
    return L


def split_df_inN(df, N_new_Df):
    """
    Split df in several dataframe in number equal to N_new_Df
    """
    
    __len = float(df.shape[0])
    
    N = int(round(__len / N_new_Df, 0))
    
    return split_df(df, N)

