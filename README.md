# google_drive_cli

python based cli for google drive. 
Tested in debian linux and mac os


#disclaimer

This is currently a very early no-support-whatsoever project. 
If you want to contribute let me know. Im tailoring it to suit my specific needs which are:

1. we have several hundered GB on our server including very large video files
2. we have hunderesds of direcotires, and duplicate files that make it difficult to navigate
3. we have about a dozen user all with auto-syncing accounts. 


#setup.

1. follow this tutorial: https://developers.google.com/drive/v3/web/quickstart/python
2. fill out the start of the file for your local directory the same as you did in the tutorial
3. install requirements:

   pip install --upgrade google-api-python-client

4. python backup.py

# current features. 

1. browse around google drive with 
2. basic cli commands cd, ls and exit
3. tells you i a file does not exist locally (flagged with an N) (not if its newer/older/different)
4. caches file informtion for faster navigation
5. checks for new files and folders from a top-down tree perspective 
    (ie: does not decend all the way down the first directory, then check from the bottom up)
6. used threads to pre-load folder and file information in the background while browsing, so you can quickly navigate. 

#coming soon. 

1. pull / direcotries files to local in background
2. add pull requests to start or end of the queue
