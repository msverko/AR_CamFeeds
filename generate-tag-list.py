import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import csv
import os
import configparser


# Base Class for SCADA Processors
class ScadaProcessor:
    def process_db_file(self, input_file, output_file, input_separator, output_separator, selected_source):
        raise NotImplementedError("This method should be implemented by subclasses")


# Wonderware SCADA Processor
class WonderwareProcessor(ScadaProcessor):
    def process_db_file(self, input_file, output_file, input_separator, output_separator, selected_source):
        sections = [
            ':MemoryDisc', ':IODisc', ':MemoryInt', ':IOInt', ':MemoryReal', ':IOReal',
            ':MemoryMsg', ':IOMsg', ':GroupVar', ':HistoryTrend', ':TagID',
            ':IndirectDisc', ':IndirectAnalog', ':IndirectMsg'
        ]
        try:
            with open(input_file, mode='r') as infile:
                reader = csv.reader(infile, delimiter=input_separator)
                with open(output_file, mode='w', newline='') as outfile:
                    writer = csv.writer(outfile, delimiter=output_separator)
                    writer.writerow(['Source', 'TagName', 'EngUnits', 'Comment'])
                    current_section, header = None, None

                    for row in reader:
                        if not row:
                            continue

                        if row[0] in sections:
                            current_section, header = row[0], row
                            event_logged_index = header.index('EventLogged') if 'EventLogged' in header else None
                            eng_units_index = header.index('EngUnits') if 'EngUnits' in header else None
                            comment_index = header.index('Comment') if 'Comment' in header else None
                            continue

                        if current_section and row[0] != '':
                            if event_logged_index is not None and row[event_logged_index].strip().lower() == 'yes':
                                tag = row[0]
                                eng_units = row[eng_units_index] if eng_units_index and len(row) > eng_units_index else ''
                                comment = row[comment_index] if comment_index and len(row) > comment_index else ''
                                writer.writerow([selected_source, tag, eng_units, comment])

            messagebox.showinfo("Success", f"Tag list has been created: {output_file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))


# Get the appropriate SCADA Processor
def get_scada_processor(scada_type):
    processors = {
        "wonderware": WonderwareProcessor,
    }
    processor_class = processors.get(scada_type.lower())
    if not processor_class:
        raise ValueError(f"No processor found for SCADA type: {scada_type}")
    return processor_class()


# Append selected rows to INI file
def append_to_ini_file(selected_items, treeview, ini_file, output_separator=';'):
    try:
        if not ini_file.endswith(".ini"):
            ini_file += ".ini"

        config = configparser.ConfigParser(interpolation=None)
        config.optionxform = str
        if os.path.exists(ini_file):
            config.read(ini_file)

        for item in selected_items:
            values = treeview.item(item, "values")
            if not values:
                continue

            source = values[0]
            tag_name = values[1]
            eng_units = values[2] if len(values) > 2 else ''
            comment = values[3] if len(values) > 3 else ''
            if source not in config.sections():
                config.add_section(source)

            entry = f"{tag_name}{output_separator}{eng_units}{output_separator}{comment}"
            config.set(source, tag_name, entry)

        with open(ini_file, "w") as file:
            config.write(file)

        messagebox.showinfo("Success", f"Selected tags have been appended to {ini_file}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


# Load output file into Treeview
def load_output_file(output_file, treeview, output_separator=';'):
    try:
        with open(output_file, mode='r') as infile:
            reader = csv.DictReader(infile, delimiter=output_separator)
            treeview.delete(*treeview.get_children())
            for row in reader:
                treeview.insert("", "end", values=(row['Source'], row['TagName'], row['EngUnits'], row['Comment']))
        messagebox.showinfo("Success", f"Loaded tags from {output_file}")
    except KeyError as e:
        messagebox.showerror("Error", f"Missing column: {e}")
    except Exception as e:
        messagebox.showerror("Error", str(e))


# Populate SCADA Types
def populate_scada_types(config_file, scada_dropdown):
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        if "scada type" in config.sections():
            scada_types = [value.capitalize() for key, value in config.items("scada type")]
            scada_dropdown['values'] = scada_types
            if scada_types:
                scada_dropdown.set(scada_types[0])
            else:
                scada_dropdown.set("")
        else:
            messagebox.showerror("Error", "No SCADA types found in config file.")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load SCADA types: {e}")


# Populate data sources from config.ini
def populate_data_sources(config_file, dropdown_widget):
    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        sources = [section for section in config.sections() if section.startswith("Source")]
        dropdown_widget['values'] = sources
        if sources:
            dropdown_widget.set(sources[0])
        else:
            dropdown_widget.set("")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to load data sources: {e}")


# GUI Setup
def create_gui():
    def browse_input_file():
        filename = filedialog.askopenfilename(title="Select CSV file", filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")))
        input_file_var.set(filename)

    def browse_output_file():
        filename = filedialog.asksaveasfilename(defaultextension=".csv", title="Save CSV file as", filetypes=(("CSV Files", "*.csv"), ("All Files", "*.*")))
        output_file_var.set(filename)

    def execute_processing():
        input_file = input_file_var.get()
        output_file = output_file_var.get()
        input_separator = input_sep_var.get()
        output_separator = output_sep_var.get()
        selected_source = data_source_var.get()
        scada_type = scada_type_var.get()

        if not os.path.exists(input_file):
            messagebox.showerror("Error", "Input file does not exist.")
            return

        if not output_file:
            messagebox.showerror("Error", "Please select an output file.")
            return

        if not input_separator or not output_separator:
            messagebox.showerror("Error", "Please select valid separators.")
            return

        if not selected_source:
            messagebox.showerror("Error", "Please select a data source.")
            return

        try:
            processor = get_scada_processor(scada_type)
            processor.process_db_file(input_file, output_file, input_separator, output_separator, selected_source)
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def load_tags():
        output_file = output_file_var.get()
        output_separator = output_sep_var.get()
        load_output_file(output_file, treeview, output_separator)

    def generate_ini():
        selected_items = treeview.selection()
        ini_file = ini_file_var.get().strip()
        if not ini_file:
            messagebox.showerror("Error", "Please specify a tag list file Name.")
            return
        if not selected_items:
            messagebox.showerror("Error", "No tags selected.")
            return
        append_to_ini_file(selected_items, treeview, ini_file)

    root = tk.Tk()
    root.title("Tag processor")
    root.geometry("800x600")
    root.minsize(800, 600)

    style = ttk.Style()
    style.theme_use("clam")

    # Variables
    input_file_var, output_file_var = tk.StringVar(), tk.StringVar()
    ini_file_var = tk.StringVar(value="tags")  # Default INI file name without extension
    input_sep_var, output_sep_var = tk.StringVar(value=';'), tk.StringVar(value=';')
    data_source_var, scada_type_var = tk.StringVar(), tk.StringVar()

    # Main Frame
    main_frame = ttk.Frame(root, padding=10)
    main_frame.grid(row=0, column=0, sticky="nsew")

    # Configure resizing
    root.grid_rowconfigure(0, weight=1)
    root.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(2, weight=1)  # Make the Treeview expandable
    main_frame.grid_columnconfigure(1, weight=1)

    # File Selection
    file_frame = ttk.LabelFrame(main_frame, text="File Selection", padding=10)
    file_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=5)

    ttk.Label(file_frame, text="Input File:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(file_frame, textvariable=input_file_var, width=50).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(file_frame, text="Browse", command=browse_input_file).grid(row=0, column=2, padx=5, pady=5)

    ttk.Label(file_frame, text="Output File:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(file_frame, textvariable=output_file_var, width=50).grid(row=1, column=1, padx=5, pady=5)
    ttk.Button(file_frame, text="Browse", command=browse_output_file).grid(row=1, column=2, padx=5, pady=5)

    # Configuration
    config_frame = ttk.LabelFrame(main_frame, text="Configuration", padding=10)
    config_frame.grid(row=1, column=0, columnspan=2, sticky="ew", pady=5)

    ttk.Label(config_frame, text="SCADA Type:").grid(row=0, column=0, sticky="e", padx=5, pady=5)
    scada_dropdown = ttk.Combobox(config_frame, textvariable=scada_type_var, state="readonly", width=47)
    scada_dropdown.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(config_frame, text="Data Source:").grid(row=1, column=0, sticky="e", padx=5, pady=5)
    data_source_dropdown = ttk.Combobox(config_frame, textvariable=data_source_var, state="readonly", width=47)
    data_source_dropdown.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(config_frame, text="Input Separator:").grid(row=2, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(config_frame, textvariable=input_sep_var, width=5).grid(row=2, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(config_frame, text="Output Separator:").grid(row=3, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(config_frame, textvariable=output_sep_var, width=5).grid(row=3, column=1, sticky="w", padx=5, pady=5)

    ttk.Label(config_frame, text="Tag List File Name:").grid(row=4, column=0, sticky="e", padx=5, pady=5)
    ttk.Entry(config_frame, textvariable=ini_file_var, width=50).grid(row=4, column=1, padx=5, pady=5)

    # Treeview for Output
    output_frame = ttk.Frame(main_frame, padding=10)
    output_frame.grid(row=2, column=0, columnspan=2, sticky="nsew", pady=5)

    columns = ("Source", "TagName", "EngUnits", "Comment")
    treeview = ttk.Treeview(output_frame, columns=columns, show="headings", height=15)
    for col in columns:
        treeview.heading(col, text=col)
        treeview.column(col, width=150, anchor="center")

    treeview.grid(row=0, column=0, sticky="nsew")

    scrollbar = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=treeview.yview)
    treeview.configure(yscroll=scrollbar.set)
    scrollbar.grid(row=0, column=1, sticky="ns")

    output_frame.grid_rowconfigure(0, weight=1)
    output_frame.grid_columnconfigure(0, weight=1)

    # Buttons
    button_frame = ttk.Frame(main_frame, padding=10)
    button_frame.grid(row=3, column=0, columnspan=2, sticky="ew", pady=5)

    ttk.Button(button_frame, text="Process Input File", command=execute_processing).grid(row=0, column=0, padx=5, pady=5)
    ttk.Button(button_frame, text="Load Output File to grid", command=load_tags).grid(row=0, column=1, padx=5, pady=5)
    ttk.Button(button_frame, text="Appent to final tag list", command=generate_ini).grid(row=0, column=2, padx=5, pady=5)

    # Populate SCADA Types and Data Sources from Config File
    config_file = "config.ini"
    if os.path.exists(config_file):
        populate_scada_types(config_file, scada_dropdown)
        populate_data_sources(config_file, data_source_dropdown)
    else:
        messagebox.showerror("Error", f"Config file not found: {config_file}")

    root.mainloop()


create_gui()
