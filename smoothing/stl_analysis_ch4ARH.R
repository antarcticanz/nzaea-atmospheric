##################################################################
#
# Purpose: This routine reads output file from "take_monthly_means_ARHch4_B.m"  
#          does seasonal decomposition by Loess (STL), and makes plots.
#
#          2 lots of stl analysis are run:
#          (1) With swin=5 and twin=25; this is for our QA.  This one is 
#              plotted out in plotfile.
#          (2) With swin=10 and twin=50; this is for producing the web plot. Here
#              we only produce 'arh_ch4_stl_swin10_twin50_nohead.dat' which is used 
#              as input to 'web_plots_ch4.m'  
#
#           
#
# Author: Sara M-F
#
# Date: Started coding June 2011
#
# Modified Feb2013 by Sylvia Nichol to produce pdf plot with Title, and to produce 2nd
# stl using swin=10 and twin=50.
#
##################################################################


# Go get 'em, Tiger! 

infile<-'arh_ch4_mm_all_nohead.dat'
plotfile<-'arh_ch4_stl_swin5_twin25.pdf'
outfile <-'arh_ch4_stl_swin5_twin25.dat'
outfile2 <-'arh_ch4_stl_swin5_twin25_nohead.dat'
outfile3 <-'arh_ch4_stl_swin10_twin50_nohead.dat'

data=read.table(infile,header=F,col.names=c('year','month','mix','flag','stdev','growthrt','growthrt_smoo'))
data.ts<-ts(data$mix,c(data$year[1],data$month[1]+1),frequency=12)

# Set up windows for the stl plot
# Antony was using a 25 month window in Splus
# R allows adjustment for the seasonal window and the trend window separately
# Britt uses 5 for swin and 25 or 120 for the twin  
swin<-5
twin<-25

data.stl=stl(data.ts,s.window=swin,t.window=twin)

swin2<-10
twin2<-50

data2.stl=stl(data.ts,s.window=swin2,t.window=twin2)

# Make a plot to look at for now and write out a plot for later 
pdf(plotfile)
plot(data.stl)
title('Arrival Heights CH4 (swin=5, twin=25)')
dev.off()

# also write out the results
write('Year; Month; CH4(ppb); Flag (=0 for true data; =1 for filled; Growth Rate (ppb/yr); Smoothed Growth Rate (ppb/yr); Seasonal cycle (ppb); trend (ppb); residual',file=outfile)
write(rbind(data$year,data$month,data$mix,data$flag,data$growthrt,data$growthrt_smoo,data.stl$time.series[,'seasonal'],data.stl$time.series[,'trend'],data.stl$time.series[,'remainder']),file=outfile,append=T,ncol=9)
write(rbind(data$year,data$month,data$mix,data$flag,data$growthrt,data$growthrt_smoo,data.stl$time.series[,'seasonal'],data.stl$time.series[,'trend'],data.stl$time.series[,'remainder']),file=outfile2,ncol=9)
write(rbind(data$year,data$month,data$mix,data$flag,data$growthrt,data$growthrt_smoo,data2.stl$time.series[,'seasonal'],data2.stl$time.series[,'trend'],data2.stl$time.series[,'remainder']),file=outfile3,ncol=9)

