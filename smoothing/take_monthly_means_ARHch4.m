!##########################################################
!
!  This script reads in methane and methane isotope data, 
!  takes monthly means and writes the output to a file for 
!  analysis. 
!
!  Author: Sara M-F
!  
!##########################################################

! Show me the data!!

source_dir='/data/san-02/tropac/timeseries_analysis/original_data' 
file='arh_ch4_stripped.dat'
outfile='arh_ch4_mm_all.dat'
outfile2='arh_ch4_mm_all_nohead.dat'
jpgmmfile='arh_ch4_mm.jpg'
pdfmmfile='arh_ch4_mm.pdf'
jpgallfile='arh_ch4_all.jpg'
pdfallfile='arh_ch4_all.pdf'
jpggrfile='arh_ch4_growthrt.jpg'
pdfgrfile='arh_ch4_growthrt.pdf'

cd(source_dir) 
data=load(file);
cd ../ch4
year=data(:,1);
month=data(:,2);
day=data(:,3);
mix=data(:,4);

decdate_all=zeros(length(year),1);
for i=1:(length(year));
if (month(i)==1);
  decdate_all(i)=year(i)+day(i)./(365+eomday(year(i),2)-28);
end
if (month(i)==2);
  decdate_all(i)=year(i)+(eomday(year(i),1)++day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==3);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==4);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==5);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==6);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==7);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+eomday(year(i),6)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==8);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+eomday(year(i),6)+eomday(year(i),7)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==9);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+eomday(year(i),6)+eomday(year(i),7)+eomday(year(i),8)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==10);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+eomday(year(i),6)+eomday(year(i),7)+eomday(year(i),8)+eomday(year(i),9)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==11);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+eomday(year(i),6)+eomday(year(i),7)+eomday(year(i),8)+eomday(year(i),9)+eomday(year(i),10)+day(i))./(365+eomday(year(i),2)-28);
end 
if (month(i)==12);
  decdate_all(i)=year(i)+(eomday(year(i),1)+eomday(year(i),2)+eomday(year(i),3)+eomday(year(i),4)+eomday(year(i),5)+eomday(year(i),6)+eomday(year(i),7)+eomday(year(i),8)+eomday(year(i),9)+eomday(year(i),10)+eomday(year(i),11)+day(i))./(365+eomday(year(i),2)-28);
end 
end 



! Determine the number of monthly datapoints we are going to have 

!number of months in first and last years in the timeseries 
ninst=length(year);
nfirst=12-month(1)+1;
nlast=month(ninst);

! number of months in complete years
nmonths=((year(ninst))-(year(1)+1))*12.;

nmonths=nmonths+nfirst+nlast; 

! Set up an empty matrix of missing values 
monthly_mean=ones(nmonths,5)*(-999.99);
 
! take monthly means 

mo=month(1);
yr=year(1);
for i=1:nmonths; 
  ii=find(month == mo & year==yr)
  monthly_mean(i,1)=yr;
  monthly_mean(i,2)=mo;
  if (length(ii) > 0) 
    monthly_mean(i,5)=std(mix(ii));
    kk=find(abs(mix(ii)-mean(mix(ii)))<=2*std(mix(ii)))
    monthly_mean(i,3)=mean(mix(ii(kk)));
    monthly_mean(i,5)=std(mix(ii));
  end
  if (mo == 12) 
   yr=yr+1 
   mo=1
  else 
   mo=mo+1 
 end  
end 


% Use Spline fitting to fill in any gaps

decdate=monthly_mean(:,1)+((monthly_mean(:,2)-0.5)/12); 
igood=find(monthly_mean(:,3)>-999.99);
ibad=find(monthly_mean(:,3)==-999.99);
monthly_mean(ibad,3)=pchip(decdate(igood),monthly_mean(igood,3),decdate(ibad));
% Make a flag for fill values; =0 for real data, =1 for fill
monthly_mean(igood,4)=0;
monthly_mean(ibad,4)=1;

scrsz=get(0,'ScreenSize');
figure(1)
%figure('Position',[1 scrsz(4)*0.7 scrsz(3)*0.6 scrsz(4)*1]) 
subplot(2,1,1)
plot(decdate_all,mix,'o')
xlim([min(decdate_all),max(decdate_all)])
hold on
ylabel('CH4 (ppb)')
title('Arrival Heights All Data')	
hold off


figure(2)
%figure('Position',[1 scrsz(4)*0.7 scrsz(3)*0.6 scrsz(4)*1]) 
subplot(2,1,1)
plot(decdate,monthly_mean(:,3))
hold on
ii= find(monthly_mean(:,5)>-99)
test=2*mean(monthly_mean(ii,5))
jj=find(monthly_mean(:,5)>test)
plot(decdate(igood),monthly_mean(igood,3),'go')
plot(decdate(ibad),monthly_mean(ibad,3),'c*')
h=errorbar(decdate(jj),monthly_mean(jj,3),monthly_mean(jj,5),'.c')
errorbar_tick(h,0)
ylabel('CH4 (ppb)')
title('Arrival Heights CH4 Monthly Means')	
xlim([min(decdate_all),max(decdate_all)])
legend('Spline Fit','Monthly Means','Filled Values')
legend('Location','Southeast')
legend('Boxoff')
hold off

subplot(2,1,2)
plot(decdate(igood),monthly_mean(igood,5),'go')
xlim([min(decdate_all),max(decdate_all)])
hold on
ylabel('CH4 (ppb)')
title('Standard Deviation of Monthly Means')	
hold off

%saveas(2,jpgmmfile)
saveas(2,pdfmmfile)

% Take the growth rate
grwthrt=ones(length(decdate),1)*-99.99;
for i=13:length(decdate)-12;
  grwthrt(i)=mean(monthly_mean(i+1:i+12,3))-mean(monthly_mean(i-12:i-1,3))
end 

%Calculate the smoothed growth rate 
grwthrt_filt=filtfilt(ones(1,12)/12,1,grwthrt);
% over write areas contaminated by edge effects with missing values 
grwthrt_filt(1:24)=-99.99
grwthrt_filt(length(decdate)-24:length(decdate))=-99.99

monthly_mean=[monthly_mean, grwthrt,grwthrt_filt]


figure(3)
plot(decdate(13:length(decdate)-12),monthly_mean(13:length(decdate)-12,6),'--k','linewidth',2)
hold on 
plot(decdate(25:length(decdate)-25),grwthrt_filt(25:length(decdate)-25),'g','linewidth',4)
xlim([decdate(13),decdate(length(decdate)-12)])
ylabel('Growth Rate (CH4 ppb/yr)')
title('Arrival Heights Atmospheric Growth Rate')
hold off

%saveas(3,jpggrfile)
saveas(3,pdfgrfile)

dlmwrite(outfile,'Monthly mean CH4 at Arrival Heights','delimiter','')
dlmwrite(outfile,'Year; Month; CH4 (ppb); Flag (1=filled; 0=true data); standard deviation around monthly means (ppb); growth rate (ppb/yr); smoothed growth rate (ppb/yr)','delimiter','','-append')
dlmwrite(outfile,monthly_mean,'delimiter','\t','precision',10,'-append')
dlmwrite(outfile2,monthly_mean,'delimiter','\t','precision',10)






