import operator
import pandas as pd
import fitbit
import sheets


# so now the idea is to just take whatever the simplest thing is and write up something for the modafinil data....
# which come to think of it i don't actually have
#
#but you are supposed to write out a basic structure..
# read modafinil binary data
# read sleep data 
# read log and find last "sleep" for each day
# read fitbit data and find first sleep minute
# new column, sleep onset? 


# my idea in this document is to sketch out how i might want to use
# the code that I'm trying to write, and play with a few different ways of
# arranging things to figure out which one makes more sense,
# and THEN figure out what my data structure looks like based on my actual
# use cases

# tangentially inspired by the idea of sketching out incorrect but interesting
# programs in APL before getting into the details of a specific one



# fitbit gives me sleep, fairly obviously
# sheets gives me my log of meds, energy levels, depression score,
# when i went to bed, and so on

# there's also a seperate sheets file that tracks pomodoro cycles,
# task durtion predictions, etc.


sleep = fitbit.get_data(...)
# get_data should also label unusual days and all of the analysis should ignore
# unusual days (too much or too little sleep or unusual times) by default
log = sheets.get_data(...)

other_log = pd.from_csv(log)
# randomized modafinil data, stored seperately
# probably YYYY-MM-DD, (True|False)
# will have to be edited by hand because it wasn't recorded perfectly

# i guess it's reasonable to keep a seperate copy
# but otherwise merge it with the rest of the meds log
# (and prune any redundency)


association(other_log["blinded modafinil"], sleep["sleep efficacy"])
# this gives me p-value, cohen's d, STDEV for total and subgroup
# distributions, and a histogram
association(other_log["blinded modafinil"], aggregate["sleep latency"])

# worth noting that sleep latency requires both log and sleep information
# (I note when I go to sleep in the log,
# then fitbit detects when I actually go to sleep)

# log is a timeseries
# there are sometimes multiple sleeps per day
# but what you probably want to do is assume that the per-time data is
#  relatively immutable (it may actually need to be cleaned though so you'll
#  need to regenerate things)

# so based on the various sources, generate aggregate per-day information
# and then just do your analyses on that

# and when you have to use per-time information you can choose whatever
# approach you want (max, average, min; present/not presentl; even just a
# bunch of fields
# or even revert to operating on per-time information
# (e.g. if you switched to wanting to model serum concernations of meds
# and study effect on diurinal mood, for example. that would be tricky)


# it would be useful to clean the entire log by defining
# valid patterns and editing everything else
# but you can also get away with simply parsing it some at a time)


aggregate.add_column("latest caffeine", "log", lambda day_entries:
    max(time for time, entry in day_entries if "caffeine" in entry))


aggregate.merge(
    {day: max(time for time, entry in day_entries if "caffeine" in "entry")
    for day, day_entries in log.groupby(date)},
    on="date"
)


### let's try a different approach
# some ways you might want to work with data?

# label, extract, view, aggregate, summary statistics,
# categorical and multivariate correlations, tests, etc

QS.log.label(pattern=".*(coffee|lattee?|chai|tea|mate).*", name="caffeine")
QS.log.extract(pattern="([0-9]+)mg caffeine", value=r"\0", type=int, "caffeine dose")
QS.view(filter=lambda item: item["label"] == "caffeine" and "caffeine dose" not in item)
# this is kind of ugly and verbose
# but you really do just want an SQL query for this sort of thing
# SELECT date, max(time) AS latest_caffeine FROM log WHERE label="caffeine" GROUP BY date
# SELECT entry FROM log WHERE label="caffeine" AND NOT caffeine_dose
# excluse my python-sql syntax mashup
# maybe panadas has a better  way of doing this kind of thing?

QS.log.extract(
    pattern="([0-9]|1[0-8])/18",
    value=r"\0", # should be the default
    type=int, # should be the default
    exclude="full beck",
    name="tonight depression"
)
QS.aggregate(
    "latest caffeine",
    select="time",
    filter={"label": "caffeine"}, # ugly but actually deals with the problem
    # unlike later approaches
    combine=max
)
QS.aggregate(name="total caffeine", select="caffeine dose", combine=sum)


QS.log.label(pattern="sleep", name="lights off")
QS.aggregate(name="lights off", select="time"
# so there's a difficulty here because select could refer to:
# - a composed aggregate
# - an extracted value (e.g. the dose)
# - a labeled log entry
# - time or the full entry that matches a certain pattern

# in particular we're often interested in selecting the time something happened
# or when the last of a label happened
# or sometimes instead the dose of the last thing that happened


# not sure what to do about this, will return later


### what about other kinds of analyses?


analyzer.correlate("total caffeine", "sleep effic")

QS.log.label(pattern="(-?[0-3],? ?){5}", name="5-scale energy")
# i log energy levels as
# mental freshness, physical freshness, starting this is easy, focus, clarity
# where each one is -3 to +3
# but currently i just average them because i'm not sure how to do a more
# useful analysis without discovering that green jelly beans cause acne

QS.log.aggregate(select="5-scale energy", process=lambda entry: sum(map(int, entry.split(",")))/5, combine=lambda energies:sum(energies)/len(energies))

QS.sleep.aggregate(select="sleep effic", date_offset=-1, "yesterday sleep effic")
QS.log.extract(pattern="([0-9]+)mg", name="modafinil dose")
QS.log.extract(pattern="(modafinil|adrafinil|moda)", select="time")

analyzer.correlation_matrix([
    "average energy",
    "tonight depression",
    "yesterday sleep effic",
    "sleep effic",
    "caffeine dose",
    "modafinil dose",
    "cycles"
)

# a different style

class QS: ...

class Log(QS): ..

class Sleep(QS): ...

...

class Caffeine

# this doesn't quite work either
# we're interested in labeling which entries refer to caffeine
# what are the doses of the ones that note dosage,
# and then seperate *aggregates* of the last caffeine and the total dose

class Caffeine(Log, Label):
    dose
    time
    pattern = ".*(coffee|lattee?|chai|tea|mate).*"

class Caffeine_Summary(Log, Aggregate):
    latest_caffeine
    total_caffeine

# also bad!

class Label: ...


Label(pattern=..., name="caffeine")
# this is the same pattern as above, essentially

class Caffeine
    general_pattern = ".*(coffee|lattee?|chai|tea|mate).*"
    dose_pattern = "([0-9]+)mg"

class LatestCaffeine(Caffeine, Aggregate):
    reduce = max of time

class TotalCaffeine(Caffeine, Aggregate):
    reduce = sum of dose



# will think about this later
