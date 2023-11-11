set key off

set terminal png size 1500,600
# set terminal pngcairo size 1200,500 enhanced font 'Helvetica,15'
set output 'time_log.png'

# set xlabel "Time"
set ylabel "Δt since last point"

set yrange [0:]
set xrange [0:]
set datafile separator "\t"

set xtics out nomirror

set style fill solid

#set xtics time format "%tM:%.3tS"
#set xtics rotate by 90 offset 0.0,-4.5
#set bmargin 20

set xtics time format "%tM:%S"
set xtics rotate by 90 offset 0.0,-2.5
set bmargin 17

## Evenly spaced bars.
# set boxwidth 0.2
# plot "time_log.dat" using ($0+0.25):1:xtic(2) with boxes notitle, \
#      '' using ($0+0.25):1:1 with labels offset 0.5,0.5 notitle

set boxwidth 0.5
plot "time_log.dat" using 1:1 with boxes notitle, \
     '' using 1:($2 != 0 ? $1 : 1/0):2 with labels offset 0.5,1.0 font ',12' notitle, \
     '' using ($1):($0+0.5):3 with labels right offset 0.0,-5.0 rotate by 90 font ',10' notitle \
