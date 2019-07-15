"""
Datetime Objects Management
"""


def now_as_int():
    """
    Return Datetime.now as integer
    """
    
    import datetime
    
    _now = str(datetime.datetime.now())
    
    _now = _now.replace('-', '')
    _now = _now.replace(' ', '')
    _now = _now.replace(':', '')
    _now = _now.split('.')[0]
    
    return long(_now)


def day_to_intervals(interval_period):
    """
    Divide a day in intervals with a duration equal to interval_period
    
    return [
        ((lowerHour, lowerMinutes), (upperHour, upperMinutes)),
        ((lowerHour, lowerMinutes), (upperHour, upperMinutes)),
        ...
    ]
    """
    
    import datetime
    
    MINUTES_FOR_DAY = 24 * 60
    NUMBER_INTERVALS = MINUTES_FOR_DAY / interval_period
    
    hour = 0
    minutes = 0
    INTERVALS = []
    
    for i in range(NUMBER_INTERVALS):
        __minutes = minutes + interval_period
        __interval = (
            (hour, minutes),
            (hour + 1 if __minutes >= 60 else hour,
             0 if __minutes == 60 else __minutes - 60 if __minutes > 60 else __minutes)
        )
        
        INTERVALS.append(__interval)
        minutes += interval_period
        
        if minutes == 60:
            minutes = 0
            hour += 1
        
        elif minutes > 60:
            minutes = minutes - 60
            hour += 1
    
    return INTERVALS


def day_to_intervals2(intervaltime):
    """
    Divide a day in intervals with a duration equal to interval_period
    
    intervaltime = "01:00:00"
    
    return [
        ('00:00:00', '01:00:00'), ('01:00:00', '02:00:00'),
        ('02:00:00', '03:00:00'), ...,
        ('22:00:00', '23:00:00'), ('23:00:00', '23:59:00')
    ]
    """
    
    from datetime import datetime, timedelta
    
    TIME_OF_DAY = timedelta(hours=23, minutes=59, seconds=59)
    DURATION    = datetime.strptime(intervaltime, "%H:%M:%S")
    DURATION    = timedelta(
        hours=DURATION.hour, minutes=DURATION.minute,
        seconds=DURATION.second
    )
    
    PERIODS = []
    
    upperInt = timedelta(hours=0, minutes=0, seconds=0)
    
    while upperInt < TIME_OF_DAY:
        if not PERIODS:
            lowerInt = timedelta(hours=0, minutes=0, seconds=0)
        
        else:
            lowerInt = upperInt
        
        upperInt = lowerInt + DURATION
        
        PERIODS.append((
            "0" + str(lowerInt) if len(str(lowerInt)) == 7 else str(lowerInt),
            "0" + str(upperInt) if len(str(upperInt)) == 7 else str(upperInt)
        ))
    
    PERIODS[-1] = (PERIODS[-1][0], '23:59:59')
    
    return PERIODS
