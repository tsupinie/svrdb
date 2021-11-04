# svrdb
This package allows you to load and manipulate SPC severe reports, including searching and basic plotting. It does all the work of matching the tornado segments from the all_tors database so you don't have to. The 2019 tornado, wind, and hail databases from SPC are included. Some basic QC is done (limited to fixing some tornado segments that should be matched), but otherwise the data are provided as-is from SPC. See [below](#caveats) for known caveats.

## Dependencies
* pandas
* numpy (optional)
* matplotlib (optional)
* cartopy (optional)

## Installation

Run `python setup.py install` to install.

## Usage

### Searching
```python
from svrdb import TornadoList, WindList, HailList

tor_db = TornadoList.load_db()            # Load the tornado database
ok_tors = tor_db.search(state='OK')       # Search for all tornadoes in Oklahoma
ok_ef5 = ok_tors.search(magnitude=5)      # Search for all (E)F5 tornadoes in Oklahoma
ok_ef5 = tor_db.search(state='OK', mag=5) # Same as the above two lines, but in one step
                                          # (Also 'mag' is an alias for 'magnitude')
print(ok_ef5)                             # Print out results
num_ok_ef5 = len(ok_ef5)                  # Get the number of tornadoes

wind_db = WindList.load_db()              # Load the wind database
hail_db = HailList.load_db()              # Load the hail database
```
The above code should print out the following:
```
   ---Time-(UTC)---  --States-- -Mag-
1. 1955-05-26 03:26      OK, KS    F5
2. 1955-05-26 04:00      OK, KS    F5
3. 1960-05-05 23:00          OK    F5
4. 1976-03-26 21:28          OK    F5
5. 1982-04-02 21:50          OK    F5
6. 1999-05-03 23:26          OK    F5
7. 2011-05-24 20:50          OK   EF5
8. 2013-05-20 19:56          OK   EF5
```

The search function is fairly powerful. The basic structure is ```db.search(col=value, ...)```, with as many (col, value) pairs as you want. The search function will return events that match all (col, value) pairs. As in the example above, `db.search(state='OK', mag=5)` will return all events whose magnitude is 5 (EF5 tornadoes) and whose state is 'OK' (occurring in Oklahoma).

In this case, col is a column of the database. Columns common to all three databases are as follows:

|           Column           |                      Description                       |
| -------------------------- | ------------------------------------------------------ |
| state (alias: st)          | Postal abbreviation of the state the event occurred in |
| county                     | County name and state the event occurred in as a tuple (e.g. `county=('Tuscaloosa', 'AL')`) |
| datetime                   | Date and time of the event (start time for tornadoes)  |
| magnitude (alias: mag)     | Magnitude of the event. For tornadoes, this is the (E)F-scale category. For hail, it is the size in inches. For wind, it is the gust speed in kts. |
| fatalities (alias: fat)    | Number of fatalities the event caused                  |
| injuries (alias: inj)      | Number of injuries the event caused                    |
| loss*                      | Property damage the event caused                       |
| closs*                     | Crop damage the event caused                           |

*See [caveat 1](#caveats), below.

Columns only in the tornado database are as follows:

|          Column         |              Description           |
| ----------------------- | ---------------------------------- |
| length (alias: len)     | Path length in statute miles for the tornado        |
| width (alias: wid)      | Path width in yards for the tornado         |
| start_lat (alias: slat) | Starting latitude for the tornado  |
| start_lon (alias: slon) | Starting longitude for the tornado |
| end_lat (alias: elat)   | Ending latitude for the tornado    |
| end_lon (alias: elon)   | Ending longitude for the tornado   |

Columns only in the wind and hail databases are as follows:

|       Column      |       Description      |
| ----------------- | ---------------------- |
| lat (alias: slat) | Latitude of the event  |
| lon (alias: slon) | Longitude of the event |

The value can take on several forms. 
1. A string, integer or float. In this case the function searches for that value exactly. For example, `db.search(state='OK')` searches for events in Oklahoma, and `db.search(mag=1.75)` searches for events where the magnitude is exactly 1.75 (presumably this is a hail size in inches).
2. A list or tuple. In this case, the function searches for events that match any of the items in the list. For example, `db.search(state=['OK', 'KS'])` searches for events that happen in either Oklahoma or Kansas, and `db.search(mag=[4, 5])` would search for magnitudes of 4 or 5 (presumeably (E)F-scale categories)
3. A function. The function should take one argument that is a value and return a boolean. In this case, the search function searches for events that match criteria set by the passed function. For example, to search for all significant wind events, you could call `wind_db.search(mag=lambda s: s >= 65)`. 

Some helper functions are available for searching by dates and times.
```python
from svrdb import byyear, bymonth, bycday, byhour

db.search(datetime=byyear(2011))                  # Search for all events in 2011
db.search(datetime=bymonth('April', 5, 'Jun'))    # Search for all events in April, May, or June 
db.search(datetime=bycday(datetime(2013, 5, 20))) # Search for all events on May 20, 2013
db.search(datetime=byhour(19, 20, 21))            # Search for all events in the 19, 20, or 21 UTC hours
```
These helper functions can take any number of arguments and will search for an event matching any of the arguments. All dates and times are assumed to reference convective days. Thus, the May 20, 2013 example above will return any events between 12 UTC May 20 and 12 UTC May 21, 2013.

The search function returns another instance of a database object, so anything you can do with the full database you can do with a database returned by search. This allows you to chain searches so if, say you want to search for tornadoes in Kansas *and* Oklahoma, you can do it with `db.search(state='KS').search(state='OK')`. Additionally, you can grab data or plot from subsets of the database rather than the full database (see subsequent sections).

### Getting Data
Getting data from a database object is fairly straightforward.
```python
db['datetime'] # Get a list of the dates/times of all the events in the database object
db['mag']      # Get a list of all the magnitudes in the database
db['length']   # Get a list of all the tornado path lengths
```
You can grab any column listed above in the search keys.

If you do searches on the tornado database and then get the data out, the data are for each entire tornado, not just the segments in a state. For example `tor_db.search(state='OK')['length']` will get the lengths of all the paths of any tornado that touched Oklahoma, including parts in other states. This is something I want to fix in the future.

### Plotting
Plotting data is also fairly straightforward.
```python
tor_db.plot(filename='tornadoes.png')              # Plot tornadoes and save the image in 'tornadoes.png'
tor_db.plot(label='mag', filename='tornadoes.png') # As above, but also add the magnitude as a label on each path
```
You can use any of the columns listed above as a label, but the algorithm for placing the labels is not very sophisticated, so it might not look good.

### Other Analysis Functions
There are two other (related) functions that might be useful for analyses: `groupby()` and `days()`. `groupby()` is inspired by Pandas's groupby function and works much the same way.
```python
db.groupby('mag')           # Group by magnitude
db.groupby('datetime.year') # Group by year
```
`groupby()` returns a dictionary with each unique value from the column being the key and each event that matched as the value. For example,
```python
db_years = db.groupby('datetime.year')
for year, year_db in db_years.items():
    # `year` is each year
    # `year_db` contains all the events in that year in a database object
```

`days()` is the same idea, but for grouping by convective days. For example,
```python
tor_days = tor_db.days()
for day, day_db in tor_days.items():
    # `day` is a datetime object containing the convective day
    # `day_db` is a database object containing all events on that convective day
```

### Potential Future Features
* More spatial searching methods, such as searching within some distance of a point.
* A "to grid" feature that would bin events on a spatial grid.
* Better support for state-specific tallies.

## Caveats
There are several caveats for working with these data.

1. Property and crop damage are inconsistently stored, and I haven't made an attempt to fix the inconsistencies. Property damage is stored as a category 1-6 prior to 1996, and in millions of dollars after 1996. Crop damage is in millions of dollars for all times. 0 means "unknown", not $0 damage. In addition, property and crop damage figures are known to be inaccurate. Use property and crop damage figures with extreme caution.
2. Reporting and detection methods have gotten better since the 1950s, so there is a pronounced upward trend in numbers of reports in all three databases that has nothing to do with meteorology.
3. For tornadoes, the 'width' column refers to the mean path width early in the database and the maximum path width later in the database.
4. For tornadoes, the (E)F-scale rating methods are inconsistent and didn't settle on the current methods until about the mid-1980s.
5. Hail and especially wind events whose magnitudes are estimated can be wildly inaccurate.
