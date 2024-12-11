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


# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')


def read_config(db_file='config.ini', tag_file=None):
    parser = configparser.ConfigParser(interpolation=None)

    # Read database configurations
    parser.read(db_file)
    db_configs = {section: dict(parser.items(section)) for section in parser.sections() if section.startswith('Source')}

    # Read stream configurations
    streams = {}
    for section in parser.sections():
        if section.startswith("stream"):
            streams[parser.get(section, "name")] = parser.get(section, "source")

    # Read tags configuration only if tag_file is provided
    tag_configs = {}
    if tag_file:
        try:
            parser.read(tag_file)
            tag_configs = {section: dict(parser.items(section)) for section in parser.sections() if section.startswith('Source')}
        except Exception as e:
            print(f"Error reading tags file: {e}")

    return db_configs, tag_configs, streams


def build_connection_string(db_config):
    return (
        f"Driver={db_config['driver']};"
        f"SERVER={db_config['server']};"
        f"DATABASE={db_config['database']};"
        f"UID={db_config['uid']};"
        f"PWD={db_config['pwd']};"
    )


def initialize_latest_values(tag_configs):
    valid_values = {source: {tag: "Fetching..." for tag, value in tags.items() if ";" in value} for source, tags in tag_configs.items()}
    return valid_values


def get_latest_values(conn, tags, source, latest_values):
    try:
        cursor = conn.cursor()
        for tag_name, tag_info in tags.items():
            tag_db_name = tag_info.split(';')[0]
            query = f"SELECT TOP (1) ValueString FROM [WWALMDB].[dbo].[Events] WHERE [TagName] LIKE '{tag_db_name}' ORDER BY EventID DESC"
            cursor.execute(query)
            row = cursor.fetchone()
            if row:
                latest_values[source][tag_name] = row[0]
            else:
                latest_values[source][tag_name] = "No data"
    except pyodbc.Error as e:
        logging.error(f"Database error for {source}: {e}")
        for tag_name in tags.keys():
            latest_values[source][tag_name] = "DB Error"


def query_database_periodically(source, db_config, tags, latest_values):
    try:
        connection_string = build_connection_string(db_config)
        conn = pyodbc.connect(connection_string)
        while True:
            get_latest_values(conn, tags, source, latest_values)
            time.sleep(1)
    except pyodbc.Error as e:
        logging.error(f"Error connecting to the database for source {source}: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in process for {source}: {e}")


def draw_visualizations(frame, latest_values, aesthetics, tag_configs):
    font = cv2.FONT_HERSHEY_DUPLEX
    y_position = aesthetics.get("start_y")
    padding = aesthetics.get("padding")
    text_scale = aesthetics.get("text_scale")
    text_color = aesthetics.get("text_color")
    rect_color = aesthetics.get("rect_color")
    rect_thickness = aesthetics.get("rect_thickness")
    line_spacing = aesthetics.get("line_spacing")

    for source, tags in latest_values.items():
        for tag_name, value in tags.items():
            if tag_name not in tag_configs[source]:
                continue

            tag_info = tag_configs[source][tag_name]
            if ";" not in tag_info:
                continue

            tag_parts = tag_info.split(';')
            comment = tag_parts[2] if len(tag_parts) > 2 else "No Comment"
            unit = tag_parts[1] if len(tag_parts) > 1 else ""
            display_text = f"{comment} [{unit}]" if unit else comment
            value_text = f"= {value}"

            # Calculate text sizes
            (display_width, text_height), _ = cv2.getTextSize(display_text, font, text_scale, 1)
            (value_width, _), _ = cv2.getTextSize(value_text, font, text_scale, 1)
            total_width = display_width + value_width + 3 * padding
            total_height = text_height + 2 * padding

            # Ensure rectangle and text fit
            top_left = (padding, y_position)
            bottom_right = (padding + total_width, y_position + total_height)

            # Draw rectangle frame (transparent background)
            frame = cv2.rectangle(frame, top_left, bottom_right, rect_color, rect_thickness)

            # Calculate text positions
            text_y_position = y_position + padding + text_height

            # Draw text inside the rectangle
            frame = cv2.putText(frame, display_text,
                                (padding + 5, text_y_position),
                                font,
                                text_scale,
                                text_color,
                                1,
                                cv2.LINE_AA)
            frame = cv2.putText(frame, value_text,
                                (padding + display_width + padding, text_y_position),
                                font,
                                text_scale,
                                text_color,
                                1,
                                cv2.LINE_AA)

            # Update y_position for next text box
            y_position += total_height + line_spacing

    return frame


def video_stream_process(selected_stream, tag_file_name, db_configs):
    db_configs, tag_configs, _ = read_config(tag_file=tag_file_name)
    latest_values = initialize_latest_values(tag_configs)

    # Start threads for database querying
    threads = []
    for source, db_config in db_configs.items():
        if source in tag_configs:
            tags = tag_configs[source]
            thread = threading.Thread(target=query_database_periodically, args=(source, db_config, tags, latest_values))
            thread.daemon = True
            thread.start()
            threads.append(thread)

    cap = cv2.VideoCapture(selected_stream)

    if not cap.isOpened():
        logging.error("Unable to open video stream.")
        return

    aesthetics = {
        "start_y": 20,
        "padding": 10,
        "text_scale": 1,
        "text_color": (255, 255, 255),
        "rect_color": (128, 128, 128),
        "rect_thickness": 2,
        "line_spacing": 5
    }

    while True:
        ret, frame = cap.read()
        if not ret:
            logging.error("Failed to grab frame")
            break

        frame = draw_visualizations(frame, latest_values, aesthetics, tag_configs)
        cv2.imshow(f'Video Stream - {selected_stream}', frame)

        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    # Wait for threads to complete (optional cleanup)
    for thread in threads:
        thread.join()


def create_gui(streams, db_configs):
    def select_file():
        file_path = filedialog.askopenfilename(
            title="Select Tags File",
            filetypes=(("INI files", "*.ini"), ("All files", "*.*"))
        )
        tags_file_label.delete(1.0, tk.END)
        tags_file_label.insert(tk.END, file_path)
        
        try:
            with open(file_path, 'r') as file:
                file_content = file.read()
                file_content_text.delete(1.0, tk.END)
                file_content_text.insert(tk.END, file_content)
        except Exception as e:
            messagebox.showerror("Error", f"Unable to read file: {e}")

    def on_start():
        selected_camera = streams_listbox.get(tk.ACTIVE)
        if not selected_camera:
            messagebox.showwarning("Warning", "Please select a camera stream!")
            return
        tag_file_name = tags_file_label.get(1.0, tk.END).strip()
        if not tag_file_name:
            messagebox.showwarning("Warning", "Please select a tags file!")
            return
        stream_url = streams[selected_camera]
        proc = multiprocessing.Process(target=video_stream_process, args=(stream_url, tag_file_name, db_configs))
        proc.start()

    root = tk.Tk()
    root.title("AR Video Stream Selector")
    root.geometry("800x600")
    root.resizable(True, True)

    streams_frame = ttk.Frame(root)
    streams_frame.pack(fill=tk.BOTH, padx=10, pady=10)

    tk.Label(streams_frame, text="Select Camera Stream", font=("Arial", 12)).pack(anchor="w", pady=5)

    listbox_frame = ttk.Frame(streams_frame)
    listbox_frame.pack(fill=tk.BOTH)

    streams_listbox = tk.Listbox(listbox_frame, height=5)
    streams_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
    for stream in streams.keys():
        streams_listbox.insert(tk.END, stream)

    scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=streams_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    streams_listbox.config(yscrollcommand=scrollbar.set)

    tags_frame = ttk.Frame(root)
    tags_frame.pack(fill=tk.BOTH, padx=10, pady=10)

    tk.Label(tags_frame, text="Select Tags File", font=("Arial", 12)).pack(anchor="w", pady=5)

    tags_file_label = tk.Text(tags_frame, height=1, wrap=tk.NONE, bg="#f0f0f0", state=tk.NORMAL)
    tags_file_label.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    browse_button = ttk.Button(tags_frame, text="Browse", command=select_file)
    browse_button.pack(pady=5, anchor="e")

    content_frame = ttk.Frame(root)
    content_frame.pack(fill=tk.BOTH, padx=10, pady=10, expand=True)

    tk.Label(content_frame, text="File Content", font=("Arial", 12)).pack(anchor="w", pady=5)

    file_content_text = tk.Text(content_frame, height=10, wrap=tk.WORD, bg="#f9f9f9", state=tk.NORMAL)
    file_content_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

    start_button = ttk.Button(root, text="Start Stream", command=on_start)
    start_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    multiprocessing.set_start_method('spawn')
    db_configs, _, streams = read_config()
    create_gui(streams, db_configs)
