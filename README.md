Python v.3.12

using:
import numpy as np
import cv2
import pyodbc
import threading
import multiprocessing
import time
import configparser
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import logging

STEP 2 (Ready for testing - all from STEP1 already available)
Start: generate-tag-list to get GUI
- select one of camera feeds (currently linked to public cameras for testing only).
- select tags file (TagList.ini) -> previously generated with generate-tag-list.py from exported HMI db (DB.CSV).
- hit  the button -> stream loop will contain tag comments loaded from teh TagList.ini, with missing data stream (no connection to SQL db).

STEP1 (generate necessary files from prevousy exported HMI db - DB.csv)
To generate necessary files (pre-configured files already exists for testing):
- start generate-tag-list.py to get GUI
- select input file (DB.CSV)
- define output file (overwrite existing output1.csv, or new file name)
- select SCADA type (corresponding to DB.CSV file structure).
- hit process input file to generate available tag list from DB.CSV
  
- select created output file
- hit Load output file to grid
- select tags from the grid (to generate the tag list to be loaded on the video feed).
- insert tag list file name
- hit Append to final tag list (to create final list to be loaded with generate-tag-list.py GUI).
