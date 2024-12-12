Python v.3.12

using: numpy, cv2, pyodbc, threading, multiprocessing, time, configparser, tkinter (ttk, messagebox, filedialog), logging

Files:
config.ini
- SCADA type selection (currently, only AVEVA Wonderware).
- SQL database connection parameters.
- link to public cameras (for testing only).

DB.csv
- HMI database export (generated using Wonderware SCADA-native DB export tool, with ";" set as a list separator).
Output1.csv
- Tag list extracted from the DB.csv.
- This file contains all the tags available in SQL db (those with "Logged" set to "Yes" in DB.csv).
- Each tag extracted from the DB.csv is linked to it's source (SCADA type).

TagList.ini 
- Tags selected from the GUI sorted by source db (these tag values will be displayed on the camera feed as a data stream).

# To test video feed, start with the step2, as all the files are already prepared (step1).
STEP 2 (Ready for testing - all from STEP1 already available).
Start: get-data-to-camera.py --> GUI.
- select one of the camera feeds (currently linked to public cameras for testing only).
- select tags file (TagList.ini) -> previously generated with generate-tag-list.py from exported HMI database (DB.CSV).
- hit the button -> stream loop will contain tag comments loaded from the TagList.ini, with teh missing data stream (no connection to SQL db).

STEP1 (generate necessary files from previously exported HMI database - DB.csv).
To generate necessary files:
- start generate-tag-list.py --> GUI.
- select the input file (DB.CSV).
- define the output file (overwrite existing output1.csv, or new file name).
- select SCADA type (corresponding to DB.CSV file structure).
- hit process input file to generate available tag list from DB.CSV.
  
- select (created) output file.
- hit Load output file to grid.
- select tags from the grid (to generate, or append, the tag list to be loaded on the video feed).
- insert tag list file name.
- hit Append to final tag list (to create the final list to be loaded with generate-tag-list.py GUI).
