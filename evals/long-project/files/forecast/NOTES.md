# Forecast notes (demo material)

Things I've tried on the weekly sales forecast (forecast.py), scored on the last 8 weeks:

- moving average, 4 weeks: error 11.2%. baseline.
- moving average, 8 weeks: error 12.9%, worse. dropped it.
- add a holiday flag: error 9.8%. keeping it.
- weather (rain days): tried twice, no better than baseline both times, dead.
- exponential smoothing alpha 0.3: error 10.4%?? can't remember if that was with the holiday flag.
- day-of-week split: never finished, laptop died.

I keep re-trying the weather one. Also not sure which 8 weeks I scored on each time.
