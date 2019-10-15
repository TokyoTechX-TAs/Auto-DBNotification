#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/[WORKSPACE DIR]

cd /[WORKSPACE DIR]/ 
echo 'ready to update' >> /tmp/crontest.log 2>&1
python update_DB_crawler.py >> /tmp/crontest.log 2>&1 && 

echo "PASSWORD" | sudo -S /usr/sbin/rtcwake -m disk -l -t $(date +\%s -d 'next Monday 05:30')>> /tmp/crontest.log 2>&1








