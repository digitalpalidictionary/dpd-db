set key off

set terminal png
# set terminal pngcairo size 1200,500 enhanced font 'Helvetica,15'
set output 'time_log.png'

set yrange [0:]
set xrange [0:]
set datafile separator "\t"

set xtics out nomirror

set style fill solid

set xtics rotate by 90 offset 0.0,-4.5
set bmargin 20
set xtics time format "%tM:%.3tS"

## Evenly spaced bars.
# set boxwidth 0.2
# plot "time_log.dat" using ($0+0.25):1:xtic(2) with boxes notitle, \
#      '' using ($0+0.25):1:1 with labels offset 0.5,0.5 notitle

set boxwidth 0.5
plot "time_log.dat" using 1:1 with boxes notitle, \
     '' using 1:1:1 with labels offset 0.5,0.5 notitle, \
     '' using ($1):($0+0.5):2 with labels right offset 0.0,-7.0 rotate by 90 font ',10' notitle \
