#!/bin/sh

################################################################################################
#
# Purpose: Runs stl analysis and produces final plots for website for Baring Head, Arrival Heights CH4 and 13CH4 data,
#          and Lauder CH4.
#          Also creates comparison plots of monthly means for all 3 sites (Step 3).
#          Also creates "quick plots" for QA in Step 5.
#          Also compares NOAA ICP CH4 same flask measurements (Step 6)   
#
#          Takes the "site"_ch4_stripped.dat, "site"_13ch4_stripped.dat, and "site"_14ch4_stripped.dat files
#          See notes below at start of each Step, for useful info.
#
#          To create the stripped data files run create_stripped_files.sh in top level directory
#          
#          To run me on thotter do:
#          chmod 0774 do_stl_and_create_webplots_ch4.sh
#          source do_stl_and_create_webplots_ch4.sh
#
# Script written by Sylvia Nichol, started May 2013.
# Uses R and matlab programs written by Sara Mikaloff-Fletcher
#
#  NB from June 2014 uses Lauder Ooofti CH4
#
####################################################################################################   


#Step 1: Create input files for stl analysis. 

#        Run take_monthly_means_BHD'gas'.m files, which have been modified for new input file format
#
#        Input is bhd_"gas"_stripped.dat
#
#        Output is :bhd_"gas"_mm.dat and bhd_"gas"_mm_nohead.dat  which are the monthly means used for stl analysis
#                   bhd_"gas"_mm.pdf is a graph of the monthly means
#                   bhd_"gas"_data.pdf is a graph of the baseline data 
#                   bhd_"gas"_growthrt.pdf is a graph of the growth rate

         echo " running take_monthly_means_BHDch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_BHDch4;exit;"
	         echo " running take_monthly_means_BHDch4_MFE.m"   #baseline only
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_BHDch4_MFE;exit;"

         echo " running take_monthly_means_BHD13ch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_BHD13ch4;exit;"
         echo " running take_monthly_means_BHD14ch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_BHD14ch4;exit;"

         echo " running take_monthly_means_ARHch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_ARHch4;exit;"
         echo " running take_monthly_means_ARH13ch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_ARH13ch4;exit;"
         echo " running take_monthly_means_ARH14ch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_ARH14ch4;exit;"

         echo " running take_monthly_means_LAUch4.m"
    matlab -nodesktop -nosplash -nojvm -r "take_monthly_means_LAUch4;exit;"



#*****************************************************************************************************
#Step 2: Run stl analysis 
#          2 lots of stl analysis are run:
#          (1) With swin=5 and twin=25; this is for our QA.  This one is 
#              plotted out in plotfile.
#          (2) With swin=10 and twin=50; this is for producing the web plot. Here
#              we only produce 'bhd_'gas'_stl_swin10_twin50_nohead.dat' which is used 
#              as input to 'web_plots_'gas'.m'  
#
#          Input is  bhd_"gas"_mm_nohead.dat
#   
#          Output is bhd_"gas"_stl_swin5_twin25.pdf  which are stl plots
#                    bhd_"gas"_stl_swin5_twin25.dat, bhd_"gas"_stl_swin5_twin25_nohead.dat, bhd_"gas"_stl_swin10_twin50_nohead.dat

          echo " running stl_analysis_ch4BHD.R"
   R CMD BATCH stl_analysis_ch4BHD.R
             echo " running stl_analysis_ch4BHD_baseline.R"
   R CMD BATCH stl_analysis_ch4BHD_MFE.R
          echo " running stl_analysis_13ch4BHD.R"
   R CMD BATCH stl_analysis_13ch4BHD.R
          echo " running stl_analysis_ch4ARH.R"
   R CMD BATCH stl_analysis_ch4ARH.R
          echo " running stl_analysis_13ch4ARH.R"
   R CMD BATCH stl_analysis_13ch4ARH.R
          echo " running stl_analysis_ch4LAU.R"
   R CMD BATCH stl_analysis_ch4LAU.R

#*****************************************************************************************************
#Step 3: Takes Monthly mean ch4 and 13ch4 data from BHD, ARH and  
#          LAU (only actual data are used) and plots on same graph.
#          Output graph is BHD_ARH_LAU_ch4_graphs_monthlymeans.pdf, BHD_ARH_13ch4_graphs_monthlymeans.pdf 

          echo " running compare_ch4_BHD_ARH_LAU_monthly_means.R"
   R CMD BATCH compare_ch4_BHD_ARH_LAU_monthly_means.R

          echo " running compare_13ch4_BHD_ARH_monthly_means.R"
   R CMD BATCH compare_13ch4_BHD_ARH_monthly_means.R


#*****************************************************************************************************
#Step 4: Create webplots for ch4 and 13ch4 
# 
#        Input is bhd_"gas"_stl_swin10_twin50_nohead.dat and 
#                 bhd_"gas"_stripped.dat
#
#        Output is "gas"_at_Baring_Head_new.png  is graph of mixing ratio
#                  "gas"_gwthrt_Baring_Head_new.png  is graph of growth rate
   
         echo " running web_plots_ch4_NEW.m"
    matlab -nodesktop -nosplash -nojvm -r "web_plots_ch4_NEW;exit;"
#	        echo " running web_plots_ch4_NEW_no_titles.m"
#    matlab -nodesktop -nosplash -nojvm -r "web_plots_ch4_NEW_no_titles;exit;"

         echo " running web_plots_13ch4_NEW.m"
    matlab -nodesktop -nosplash -nojvm -r "web_plots_13ch4_NEW;exit;"

#*****************************************************************************************************
#Step 5: Create "quickplots" for ch4, 13ch4 and 14ch4
#
#       Input is bhd_flask.csv, arh_flask.csv, lau_flask.csv, bhd_isotopes.csv, arh_isotopes.csv
#
#       Output is bhd_ch4_graphs_all.pdf, bhd_ch4_graphs_last8yrs.pdf,
#                 arh_ch4_graphs_all.pdf, arh_ch4_graphs_last8yrs.pdf,
#                 lau_ch4_graphs_last8yrs.pdf,
#                 bhd_13ch4_graphs_all.pdf, bhd_13ch4_graphs_last8yrs.pdf,
#                 arh_13ch4_graphs_all.pdf, arh_13ch4_graphs_last8yrs.pdf,
#                 bhd_14ch4_graphs_all.pdf, bhd_14ch4_graphs_last8yrs.pdf,
#                 arh_14ch4_graphs_all.pdf

          echo " running quickplot_ch4_png.r"
   R CMD BATCH quickplot_ch4_png.r

         echo " running quickplot_ch4_with_picarro.R"
   R CMD BATCH quickplot_ch4_with_picarro.R
          echo " running quickplot_13ch4.R"
   R CMD BATCH quickplot_13ch4.R
          echo " running quickplot_14ch4.R"
   R CMD BATCH quickplot_14ch4.R

#*****************************************************************************************************
#Step 6: Compares NOAA ICP CH4 same flask measurements on BHD icp samples
#
#       Input file is P05_p2d1_bhd_ch4_niwa_flask_bhd_ch4_noaa_flask_same-air_matchdata.txt from NOAA ICP website (need to download and put in original_data subdirectory)
#       Output is bhd_icp_ch4_graphs.pdf graph, and also bhd_NOAAicp_ch4.dat data file.
 
          echo " running compare_ch4_icp_NEW3.r"
   R CMD BATCH compare_ch4_icp_NEW3.r
          echo " running compare_13ch4_icp_NEW3.r"
   R CMD BATCH compare_13ch4_icp_NEW3.r

#****************************  Tidy up
        echo " deleting the .Rout files"
 #   rm *.Rout

        echo "moving output files to directories" 
        mv CH4_* for_web
        mv 13CH4_* for_web
        mv *jpg  internal_use
        mv *jpeg  internal_use
        mv *pdf  internal_use
		cp *png  ../netdir/ch4
		mv *png  internal_use
        mv *dat processed_data

 
echo "all done"
