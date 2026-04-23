
% This routine makes final web plots for CH4 at all stations  

% set up file names and text; most things we will want to adjust from 
% release to release will be located here 

% We don't plot the last 6 months of data BHD growth rate data (in line 106, 114).

% Updated 15May2014, removed bold from titles and set to font 14
%Turned graph string labels off for MFE report (line 78-80) 8/12/2014

% Updated 2/2/2015 to add Lauder Oofti data plot  (changed line 29 to be ooofti data; SEN 13/2/2019)

% Modified 25 June 2018 - for BHD webplot just use data <2018; commented out 29March2019 

% Modified 28 June 2021 - adding horizontal line at 0 for rate of change graph 

% Modified 31 March 2026 to give growth rate plot for ARH

% hard wired start of Figure 1 BHD plot to have xmin of 1989.6 (to match a 13CH4 version)
% label text 
str1(1)={'Earth Sciences NZ'} 
%str2(1)={'\rm\itTaihoro Nukurangi\rm'} 
str3a(1)={['Created ' datestr(now, 'mmmm yyyy')]}

source_dir='/data/san-02/tropac/timeseries_analysis/original_data'        
datamm_BHD=load('bhd_ch4_stl_swin10_twin50_nohead.dat');
datamm_ARH=load('arh_ch4_stl_swin10_twin50_nohead.dat');
datamm_LAU=load('lau_ch4_stl_swin10_twin50_nohead.dat');
cd(source_dir)
dataall_BHD=load('bhd_ch4_stripped.dat');
%dataall_BHD = dataall_BHD(dataall_BHD(:,1)<2018, :); 
dataall_ARH=load('arh_ch4_stripped.dat');
dataall_LAU=load('lau_ooofti_ch4_stripped.dat');
cd ../ch4

decdate_mm_BHD=datamm_BHD(:,1)+((datamm_BHD(:,2)-0.5)/12);
trend_BHD=datamm_BHD(:,8);
seas_BHD=datamm_BHD(:,7);
smoo_BHD=trend_BHD+seas_BHD
growthrt_BHD=datamm_BHD(:,5);
growthrt_smoo_BHD=datamm_BHD(:,6);
decdate_mm_ARH=datamm_ARH(:,1)+((datamm_ARH(:,2)-0.5)/12);
trend_ARH=datamm_ARH(:,8);
seas_ARH=datamm_ARH(:,7);
smoo_ARH=trend_ARH+seas_ARH

growthrt_ARH=datamm_ARH(:,5);    %new
growthrt_smoo_ARH=datamm_ARH(:,6);    %new

decdate_mm_LAU=datamm_LAU(:,1)+((datamm_LAU(:,2)-0.5)/12);
trend_LAU=datamm_LAU(:,8);
seas_LAU=datamm_LAU(:,7);
smoo_LAU=trend_LAU+seas_LAU

year_BHD=dataall_BHD(:,1);
month_BHD=dataall_BHD(:,2);
day_BHD=dataall_BHD(:,3);
mix_BHD=dataall_BHD(:,4);
year_ARH=dataall_ARH(:,1);
month_ARH=dataall_ARH(:,2);
day_ARH=dataall_ARH(:,3);
mix_ARH=dataall_ARH(:,4);
year_LAU=dataall_LAU(:,1);
month_LAU=dataall_LAU(:,2);
day_LAU=dataall_LAU(:,3);
mix_LAU=dataall_LAU(:,4);

[decdate_all_BHD]=calc_decdate(year_BHD,month_BHD,day_BHD)
[decdate_all_ARH]=calc_decdate(year_ARH,month_ARH,day_ARH)
[decdate_all_LAU]=calc_decdate(year_LAU,month_LAU,day_LAU)

% Find the best axes 
xmin=min([decdate_all_BHD; decdate_all_ARH])
xmax=max([decdate_all_BHD; decdate_all_ARH]) %-0.5    %don't want to plot last 6 months of data

% This tidy little piece of code rounds the minimum and maximum 
% values to the nearest 5 and then bumps them up by 5 to make a nice 
% plot range 

ymin=round_special(min([mix_BHD; mix_ARH; mix_LAU]),5)-5
ymax=round_special(max([mix_BHD; mix_ARH; mix_LAU]),5)+5
ymin2=round_special(min(growthrt_BHD(13:length(decdate_mm_BHD)-12)),5)-5
ymax2=round_special(max(growthrt_BHD(13:length(decdate_mm_BHD)-12)),5)+5


set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])

figure(1) 
plot(decdate_all_BHD,mix_BHD,'b.')
xlim([xmin,xmax])
ylim([ymin,ymax])
%yticks(25)
%set(gca,'yticklabel',{'1675','1725','1775'})
ylabel('Methane Mole Fraction (ppb)','fontsize',12)
%title('Atmospheric Methane at Baring Head','FontSize',12,'FontWeight','bold') 
title('Atmospheric Methane at Baring Head','FontSize',14) 
hold on 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
plot(decdate_mm_BHD,smoo_BHD,'linewidth',2)
plot(decdate_all_BHD,mix_BHD,'b.')
plot(decdate_mm_BHD,trend_BHD,'-.k','linewidth',2)
text(xmin+1,ymax-7,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax-17,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(xmin+1,ymax-17,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Observations','Deseasonalised Data')
% legend('Location','Southeast')
%legend('Boxoff')  
hold off 

figure(11)   %fixed x axis
plot(decdate_all_BHD,mix_BHD,'b.')
xlim([1989.6,2024.5])
ylim([ymin,ymax])
%yticks(25)
%set(gca,'yticklabel',{'1675','1725','1775'})
ylabel('Methane Mole Fraction (ppb)','fontsize',12)
%title('Atmospheric Methane at Baring Head','FontSize',12,'FontWeight','bold') 
title('Atmospheric Methane at Baring Head','FontSize',14) 
hold on 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
plot(decdate_mm_BHD,smoo_BHD,'linewidth',2)
plot(decdate_all_BHD,mix_BHD,'b.')
plot(decdate_mm_BHD,trend_BHD,'-.k','linewidth',2)
text(1990.6,ymax-7,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(1990.6,ymax-17,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(1990.6,ymax-17,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Observations','Deseasonalised Data')
% legend('Location','Southeast')
%legend('Boxoff')  
hold off 

figure(12)   %fixed x axis  for Sally Gray
plot(decdate_all_BHD,mix_BHD,'b.')
xlim([2018,2024])
ylim([1775,ymax])
%yticks(25)
%set(gca,'yticklabel',{'1675','1725','1775'})
ylabel('Methane Mole Fraction (ppb)','fontsize',12)
%title('Atmospheric Methane at Baring Head','FontSize',12,'FontWeight','bold') 
title('Atmospheric Methane at Baring Head - since 2018','FontSize',14) 
hold on 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
plot(decdate_mm_BHD,smoo_BHD,'linewidth',2)
plot(decdate_all_BHD,mix_BHD,'b.')
%plot(decdate_mm_BHD,trend_BHD,'-.k','linewidth',2)
text(2018.2,ymax-3,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(2018.2,ymax-10,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(2018.2,ymax-10,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Observations','Deseasonalised Data')
% legend('Location','Southeast')
%legend('Boxoff')  
hold off 


figure(10)   %for Sara M-F
plot(decdate_all_BHD,mix_BHD,'r.')
xlim([xmin,xmax])
ylim([ymin,1900])
%yticks(25)
%set(gca,'yticklabel',{'1675','1725','1775'})
ylabel('Methane Mole Fraction (ppb)','fontsize',12)
%title('Atmospheric Methane at Baring Head','FontSize',12,'FontWeight','bold') 
title('Atmospheric Methane at Baring Head','FontSize',14) 
hold on 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
%plot(decdate_mm_BHD,smoo_BHD,'linewidth',2)
plot(decdate_all_BHD,mix_BHD,'r.')
plot(decdate_mm_BHD,trend_BHD,'-.k','linewidth',2)
%text(xmin+1,ymax-7,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax-17,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax-27,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Observations','Deseasonalised Data')
% legend('Location','Southeast')
%legend('Boxoff')  
hold off 

figure(2) 
plot(decdate_all_ARH,mix_ARH,'g.')
xlim([xmin,xmax])
ylim([ymin,ymax])
%yticks(25)
%set(gca,'yticklabel',{'1675','1725','1775'})
ylabel('Methane Mole Fraction (ppb)','FontSize',12)
%title('Atmospheric Methane at Arrival Heights','FontSize',12,'FontWeight','bold') 
title('Atmospheric Methane at Arrival Heights','FontSize',14) 
hold on 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
plot(decdate_mm_ARH ,smoo_ARH,'linewidth',2)
plot(decdate_all_ARH,mix_ARH,'g.')
plot(decdate_mm_ARH,trend_ARH,'-.k','linewidth',2)
text(xmin+1,ymax-7,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax-17,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(xmin+1,ymax-27,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Observations','Deseasonalised Data')
% legend('Location','Southeast')
%legend('Boxoff')  
hold off 

figure(3) 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
%plot(decdate_mm_BHD(13:length(decdate_mm_BHD)-12),growthrt_BHD(13:length(decdate_mm_BHD)-12),'--','linewidth',2)
plot(decdate_mm_BHD(13:length(decdate_mm_BHD)-18),growthrt_BHD(13:length(decdate_mm_BHD)-18),'--','linewidth',2)  %don't plot last 6 months
xlim([xmin,xmax])
ylim([ymin2,ymax2])
line([xmin,xmax],[0,0])
ylabel('Rate of change of CH4 (ppb/yr)','FontSize',12)
%title('Growth Rate of Methane Measured at Baring Head','FontSize',12,'FontWeight','bold')
title('Rate of change of Methane Measured at Baring Head','FontSize',14)
hold on 
%plot(decdate_mm_BHD(25:length(decdate_mm_BHD)-25),growthrt_smoo_BHD(25:length(decdate_mm_BHD)-25),'b','linewidth',2)
plot(decdate_mm_BHD(25:length(decdate_mm_BHD)-31),growthrt_smoo_BHD(25:length(decdate_mm_BHD)-31),'b','linewidth',2)  %don't plot last 6 months
text(xmin+1,ymax2-1,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax2-3,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(xmin+1,ymax2-3,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Growth Rate','Smoothed Growth Rate')
%legend('Location','Southeast')
%legend('Boxoff')  
hold off

figure(4)
plot(decdate_all_LAU,mix_LAU,'Color',[1 0.4 0])
xlim([xmin,xmax])
ylim([ymin,ymax])
%yticks(25)
%set(gca,'yticklabel',{'1675','1725','1775'})
ylabel('Methane Mole Fraction (ppb)','FontSize',12)
%title('Atmospheric Methane at Arrival Heights','FontSize',12,'FontWeight','bold') 
title('Atmospheric Methane at Lauder','FontSize',14) 
hold on 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
plot(decdate_mm_LAU ,smoo_LAU,'linewidth',2)
plot(decdate_all_LAU,mix_LAU,'Color',[1 0.4 0])
plot(decdate_mm_LAU,trend_LAU,'-.k','linewidth',2)
text(xmin+1,ymax-7,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax-17,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(xmin+1,ymax-17,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Observations','Deseasonalised Data')
% legend('Location','Southeast')
%legend('Boxoff')  
hold off

figure(5) 
set(0,'DefaultAxesColorOrder',[0.4 0.4 0.4])
plot(decdate_mm_ARH(13:length(decdate_mm_ARH)-18),growthrt_ARH(13:length(decdate_mm_ARH)-18),'--','linewidth',2)  %don't plot last 6 months
xlim([xmin,xmax])
ylim([ymin2,ymax2])
line([xmin,xmax],[0,0])
ylabel('Rate of change of CH4 (ppb/yr)','FontSize',12)
title('Rate of change of Methane Measured at Arrival Heights','FontSize',14)
hold on 
plot(decdate_mm_ARH(25:length(decdate_mm_ARH)-31),growthrt_smoo_ARH(25:length(decdate_mm_ARH)-31),'g','linewidth',2)  %don't plot last 6 months
text(xmin+1,ymax2-1,str1,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
%text(xmin+1,ymax2-3,str2,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',12)
text(xmin+1,ymax2-3,str3a,'HorizontalAlignment','left','VerticalAlignment','top','FontSize',10)
%legend('Growth Rate','Smoothed Growth Rate')
%legend('Location','Southeast')
%legend('Boxoff')  
hold off


%figure(1)
%print -djpeg100 'CH4_at_Baring_Head.jpeg'
%figure(2)
%print -djpeg100 'CH4_at_Arrival_Heights.jpeg'
%figure(3)
%print -djpeg100 'CH4_gwthrt_Baring_Head.jpeg'


figure(1)
print -dpdf 'CH4_at_Baring_Head.pdf'
figure(10)
print -dpdf 'CH4_at_Baring_Head_for_Sara.pdf'

figure(11)
print -dpdf 'CH4_at_Baring_Head_fixed_xaxis.pdf'
figure(12)
print -dpdf 'CH4_at_Baring_Head_2018-2024.pdf'

figure(2)
print -dpdf 'CH4_at_Arrival_Heights.pdf'
figure(3)
print -dpdf 'CH4_gwthrt_Baring_Head.pdf'
figure(4)
print -dpdf 'CH4_at_Lauder.pdf'


figure(5)
print -dpdf 'CH4_gwthrt_Arrival_Heights.pdf'

%figure(1)
%print -depsc2 'CH4_at_Baring_Head.eps'
%figure(2)
%print -depsc2 'CH4_at_Arrival_Heights.eps'
%figure(3)
%print -depsc2 'CH4_gwthrt_Baring_Head.eps'
%figure(4)
%print -depsc2 'CH4_at_Lauder.eps'

