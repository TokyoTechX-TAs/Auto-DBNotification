# Auto-DBNotification
Program that crawls edX MOOC discussion boards and sends email messages periodically regarding new posts/comments to course staff/discussion board monitors. Here we use crontab and rtcwake functionality of Ubuntu to control the scheduling and the transit to sleep mode respectively.  


## Prerequisites
Python libraries and modules:
* [Python](https://www.python.org/downloads/) - version 3.5+
* [Selenium with Python](https://selenium-python.readthedocs.io/) - API to access webdriver
* [Chrome webdriver](http://chromedriver.chromium.org/downloads) - Chrome webdriver which requires the installation of official Chrome brower.  
* [crontab](https://help.ubuntu.com/community/CronHowto) a system daemon used to execute desired tasks (in the background) at designated times.
* [rtc-wake](http://manpages.ubuntu.com/manpages/cosmic/man8/rtcwake.8.html) a command in Linux allowing a system to enter sleep state until specified wakeup time

## How to run

 1. Enter edx account and host email information in **account_info.json**
 2. Enter a list of desired courses url in **course table.xlsx** (column 1-2) 
 3. Run a python script `edx_DBcrawler3.py` to initially scrape all discussion board textual data as well as mark all items as read

	`python edx-discussion.py` 

4. Specify the subdirectory name (under **HTMLs** foloder) of each desired courses in **course table.xlsx** (column 3) 
5. Add recipients email address information in **course table.xlsx** (column 4). 
	- The format is as follow. attribute is comma-separated while each recipient  is semicolon-separated 
  [RECEPIENT NAME1] , [RECEPIENT EMAIL1] , [RECEPIENT FLAG1];
  [RECEPIENT NAME2] , [RECEPIENT EMAIL2] , [RECEPIENT FLAG2];
  
	 - The FLAG is either 'yes' or 'no' indicating whether this specific recipient will receive the notification even there is no update of new activity in discussion at certain period or not
6. Modify the scheduling task in `execute.sh` file
	- Repalce [WORKSPACE DIR] which directory of your workspace. For example, my workspace is in **auto-db** folder then 
		- [WORKSPACE DIR] --> home/user1/auto-db/
   - If you do not intend to sleep the machine, please remove the last line and ignore below bullets.
   - Change "PASSWORD" with your user password if your account is not ROOT
   - Indicate the next wake up time by replacing [WAKEUP DATETIME] with the datetime format as explained in [here](http://manpages.ubuntu.com/manpages/xenial/man1/date.1.html) in case of UBUNTU user. 
   - For example, to wake up the machine every Monday 05:30 AM then 
	   - [WAKEUP DATETIME] --> 'next Monday 05:30'

7. Setup the scheduling detail in crontab by typing a command `crontab -e`
8. Modify the time scheduling to execute the `execute.sh` file using crontab command. 
	- For example,   to execute every Monday 06:00 AM then
       -  0 6 * * MON ./[WORKSPACE DIR]/execute.sh
	- Please refer to the link in prerequisites for more detail.

9. DONE!!, you may execute the last line of `execute.sh` in terminal to sleep the machine. If noting goes wrong, it will wake up and do the task in the next cycle.

To debug the program, you may see the log file located /tmp/crontest.log
The output of crawled textual DB data is is stored in "HTMLs\[COURSE_NAME]" folder .
Please find the graphic instuction in **overview_slide.pdf**

## Test environment
Python 3.5, Windows 10, UBUNTU 14.04
