set key off

set terminal png
# set terminal pngcairo size 1200,500 enhanced font 'Helvetica,15'
set output 'time_log.png'

set datafile separator "\t"

set xtics out nomirror

set style fill solid

set xtics rotate by 90 offset -0.2,-8.0
set bmargin 10

## Evenly spaced bars.
# set boxwidth 0.2
# plot "time_log.dat" using ($0+0.25):1:xtic(2) with boxes notitle, \
#      '' using ($0+0.25):1:1 with labels offset 0.5,0.5 notitle

set boxwidth 0.5
plot "time_log.dat" using 1:1:xtic(2) with boxes notitle, \
     '' using 1:1:1 with labels offset 0.5,0.5 notitle
