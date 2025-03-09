# required packages besides python standard modules (https://docs.python.org/3/library/index.html)
# parenthesis gives the version that worked with python (3.9.5) and pyinstaller (6.10.0)
# numpy (1.26.4), matplotlib (3.9.2)
from operator import truediv

GUINAME = 'ChartStacker'
GUIVERSION = '2.4.3'
print("Starting " + GUINAME + " " + GUIVERSION + " ...")

import tkinter as tk
import tkinter.font
import matplotlib as mpl
import glob, os, sys, datetime as dt, locale, math, ctypes, pandas, numpy as np
from functools import partial
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.ticker as tck
import matplotlib.backends.backend_tkagg as tkagg
from configparser import ConfigParser

# TIMEDIFF GLOBALS (<0.001 is same day)
TIMEDIFF_REPEATING      = 0.00001
TIMEDIFF_INTERPOLATION  = 0.0001
TIMEDIFF_SAME_DAY_DISTR = 0.0002
TIMEDIFF_AFTER_LAST     = 0.0004
TIMEDIFF_XLIM_DISTANCE  = 0.005

LINECOLORS = np.array([[1,.1,0],[0,.6,.2],[0,.2,.8],[.9,.6,0],[0,.6,.8],[1,0,.4]])

COMMENTS_CUTOFF_1 = 10
COMMENTS_CUTOFF_2 = 5
COMMENTS_CUTOFF_3 = 2

REL_SHIFT = 0.15
REL_ZOOM = 0.35
REL_SHIFT_MIN = 0.03

DEFAULT_FILENAME = "Datei wählen ..."

# ===========================================================
#        STATIC FUNCTIONS
# ===========================================================

def load_files(path):
    print(path)
    timer = MyTimer()
    files_this = glob.glob(path + os.sep + "**" + os.sep + "*.csv", recursive=True)
    files_this.sort()
    files_all = [DEFAULT_FILENAME] + files_this
    files_all_cmt_removed = []
    for i in range(len(files_all)):
        if files_all[i].find("_Kommentare.") == -1:
            files_all_cmt_removed.append(files_all[i])
    timer.stop("Search files")
    return files_all_cmt_removed

def pts(*args):
    # accepts str, str+'p', int, float and returns sum as str+'p'
    # '-' get() the following argument negative
    # pts(0.5, '1.5', '-', '3p') = '-1p'
    number = 0
    factor = 1
    for i in range(len(args)):
        if args[i]=='-':
            factor = -1
        elif args[i] == '':
            factor = 1
            continue
        else:
            try:
                number = number + factor*float(args[i])
            except:
                if args[i][len(args[i])-1] == 'p':
                    try:
                        number = number + factor*float(args[i][0:len(args[i])-1])
                    except:
                        print("WARNING: Could not add value to points!")
                else:
                    print("WARNING: Could not add value to points!")
            factor = 1
    return str(number) + "p"

def dropdown_y(y1, ystep, nr):
    this_y = y1
    for n in range(nr):
        this_y = pts(this_y, ystep)
    return this_y

def rgb_to_hex(rgb):
    return "#{:02x}{:02x}{:02x}".format(int(rgb[0]*255),int(rgb[1]*255),int(rgb[2]*255))

def datetime_to_excel_date_number(dt):
    # 12.11.2022 --> 44877
    return dt.toordinal() - 693594

def excel_date_number_to_float_year(excel_nr):
    # 44877 --> 2022.86301
    # JAHR(A1)+TAGE(A1;DATUM(JAHR(A1);1;1))/(TAGE(DATUM(JAHR(A1);12;31);DATUM(JAHR(A1);1;1))+1)
    thisdate = dt.datetime.fromordinal(int(excel_nr) + 693594)
    dayfrac = excel_nr - int(excel_nr)
    thisyear = thisdate.year
    days_since_beginning = (thisdate - dt.datetime(thisdate.year, 1, 1)).days
    days_this_year = (dt.datetime(thisdate.year + 1, 1, 1) - dt.datetime(thisdate.year, 1, 1)).days
    float_year = thisyear + (days_since_beginning + dayfrac)/days_this_year
    return float_year

def date_string_to_float_year(string):
    try:
        dots = [i for i in range(len(string)) if string.startswith(".", i)]
        mins = [i for i in range(len(string)) if string.startswith("-", i)]
        if len(dots) == 0 and len(mins) == 0:
            return excel_date_number_to_float_year(float(string))
        elif len(dots) == 2: # 18.7.2022
            thisday   = int(string[:dots[0]])
            thismonth = int(string[dots[0]+1:dots[1]])
            thisyear  = int(string[dots[1]+1:])
        elif len(mins) == 2: # 2022-7-18
            thisyear  = int(string[:mins[0]])
            thismonth = int(string[mins[0]+1:mins[1]])
            thisday   = int(string[mins[1]+1:])
        return datetime_to_float_year(dt.datetime(thisyear, thismonth, thisday))
    except Exception as e:
        raise Exception('Date string ' + string + ' could not be interpreted')

def float_year_to_datetime(float_year):
    # 2022.86301 --> 12.11.2022
    days_this_year = (dt.date(int(float_year)+1, 1, 1) - dt.date(int(float_year), 1, 1)).days
    days_since_first = int(days_this_year * (float_year - int(float_year)))
    return dt.date(int(float_year), 1, 1) + dt.timedelta(days_since_first, 0)

def datetime_to_float_year(dt):
    # 12.11.2022 --> 2022.86301
    float_year = excel_date_number_to_float_year(datetime_to_excel_date_number(dt))
    return float_year

def float_year_to_excel_date_number(float_year):
    # 2022.86301 --> 44877
    # DATUM(ABRUNDEN(A3;0);1;1)+RUNDEN((A3-ABRUNDEN(A3;0))*TAGE(DATUM(ABRUNDEN(A3;0)+1;1;1);DATUM(ABRUNDEN(A3;0);1;1));0)
    return datetime_to_excel_date_number(float_year_to_datetime(float_year))

def format_coord(x,y):
    this_date = float_year_to_datetime(x)
    this_excel_nr = float_year_to_excel_date_number(x)
    this_year = this_date.year
    this_month = this_date.month
    this_day = this_date.day
    return "{:02d}/{:02d}/{:02d} | {:05d} | {:.5f} | {:.2f}".format(this_year, this_month, this_day, this_excel_nr, x, y)

def format_coord_x(x,y):
    this_date = float_year_to_datetime(x)
    this_excel_nr = float_year_to_excel_date_number(x)
    this_year = this_date.year
    this_month = this_date.month
    this_day = this_date.day
    return "{:02d}/{:02d}/{:02d} | {:05d} | {:.5f}".format(this_year, this_month, this_day, this_excel_nr, x)

def format_coord_y(x,y):
    return "{:.2f}".format(y)

def format_coord_empty(x,y):
    return ""

def sort_array(array_2d):
    x = array_2d[:, 0]
    y = array_2d[:, 1]
    sortindex = x.argsort(kind='mergesort')
    x = x[sortindex]
    y = y[sortindex]
    array_2d = np.stack((x, y), axis=1)
    return array_2d

def add_edge_zeros_for_fill(array_2d):
    x = array_2d[:, 0]
    y = array_2d[:, 1]
    arraylength = len(x)
    x = np.append(x, x[arraylength-1])
    y = np.append(y, 0)
    arraylength = len(x)
    x = np.insert(x, 0, x[0])
    y = np.insert(y, 0, 0)
    array_2d = np.stack((x, y), axis=1)
    return array_2d

def remove_all_where_y_zero(array_2d):
    x = array_2d[:, 0]
    y = array_2d[:, 1]
    arraylength = len(x)
    x_new = np.array([])
    y_new = np.array([])
    for i in range(arraylength):
        if not y[i]==0:
            x_new = np.append(x_new, x[i])
            y_new = np.append(y_new, y[i])
    array_2d = np.stack((x_new, y_new), axis=1)
    return array_2d

def repeat_y_in_between(array_2d):
    x = array_2d[:, 0]
    y = array_2d[:, 1]
    arraylength = len(x)
    x_new = np.array([])
    y_new = np.array([])
    for i in range(1,arraylength):
        x_new = np.append(x_new, x[i] - TIMEDIFF_REPEATING)
        x_new = np.append(x_new, x[i])
        y_new = np.append(y_new, y[i-1])
        y_new = np.append(y_new, y[i])
    # also repeat last one with some distance
    x_new = np.append(x_new, x[arraylength-1] + TIMEDIFF_AFTER_LAST)
    y_new = np.append(y_new, y[arraylength-1])
    array_2d = np.stack((x_new, y_new), axis=1)
    return array_2d

def distribute_x_at_same_day(x):
    # Problem: Werte am gleichen Tag (mit gleichem x) können nicht
    # interpoliert werden und werden nicht gezeichnet
    # Das Anzeigen von großen Sprüngen kann so von kleinen Buchungen
    # verhindert werden
    # Tag ist der gleiche wenn die dritte Nachkommastelle von
    # 2019.231 identisch ist
    # Prüfe auf gleiche Nachkommastellen und ändere dort die vierte und fünfte
    arraylength = len(x)
    new_date_flag = 0
    process_flag = 0
    for i in range(1,arraylength):

        # note new date and process if not single one
        if not round(x[i],3) == round(x[i-1],3):
            if not new_date_flag == i-1:
                process_flag = 1
            else:
                new_date_flag = i

        # process at new date or end of array (excluding current one: range(new_date_flag, i))
        if (process_flag == 1):
            for k in range(new_date_flag, i):
                x[k] = x[new_date_flag] + TIMEDIFF_SAME_DAY_DISTR * (k - new_date_flag)
            process_flag = 0
            new_date_flag = i

        # always process at end of array (including current one: range(new_date_flag, i+1))
        if (i == arraylength-1):
            for k in range(new_date_flag, i+1):
                x[k] = x[new_date_flag] + TIMEDIFF_SAME_DAY_DISTR * (k - new_date_flag)
            process_flag = 0
            new_date_flag = i

    return x

def load_csv_data(filename):
    if not os.path.exists(filename):
        tk.messagebox.showerror(message="File not found:\n" + filename)
        raise Exception("File not found:\n" + filename)
    try:
        df = pandas.read_csv(filename, header=None, skip_blank_lines=True, delimiter=';', decimal=',', encoding='utf-8-sig')
        if len(df.columns) > 2:
            df.iloc[:,2] = df.iloc[:,2].fillna("")
        df = df[~df.iloc[:,0].isna()]
        print(df)
        data = np.array(df)
        #data = np.genfromtxt(filename, delimiter=';', usecols=(0,1,2), skip_header=1, dtype=str)
        x = data[:,0]
        y = [float(y_) for y_ in data[:,1]]
        if len(data[0,:]) > 2:
            cmt = data[:,2]
        else:
            cmt = [""] * len(x)
        x_ = []
        for i in range(len(x)):
            new_x = date_string_to_float_year(x[i])
            x_.append(new_x)
        x = np.array(x_)
        print("\nProcessed data:")
        print(x[:6])
        print(y[:6])
        print(cmt[:6])
        return x, y, cmt
    except Exception as e:
        tk.messagebox.showerror(message="Could not load file:\n" + filename)
        raise e

def powerscale_between(x_in, y_1, y_2, power):
    if x_in > 1:
        f = y_2
    elif x_in < 0:
        f = y_1
    else:
        f = (y_2 - y_1) * x_in**power + y_1
    return f

def norm_factor(x, y, xlim):
    y_max_within_xlim = min(abs(y))
    for i in range(len(y)):
        if x[i] >= xlim[0] and x[i] <= xlim[1] and abs(y[i]) > y_max_within_xlim:
            y_max_within_xlim = y[i]
    if y_max_within_xlim > 0:
        return 1/y_max_within_xlim
    else:
        return 1

def min_within_x(x, y, xlim):
    y_min_within_xlim = max(y)
    for i in range(len(y)):
        if x[i] >= xlim[0] and x[i] <= xlim[1] and y[i] < y_min_within_xlim:
            y_min_within_xlim = y[i]
    return y_min_within_xlim

def calc_y_limits(xlim, x, y, dropdown):
    ylim = [None, None]
    y_min = math.inf
    y_max = -math.inf
    for i in range(len(x)):
        if x[i] > xlim[0] and x[i] < xlim[1]:
            if y[i] < y_min:
                y_min = y[i]
            if y[i] > y_max:
                y_max = y[i]
    if y_min == math.inf:
        y_min = 0
    if y_max == -math.inf:
        y_max = 1
    if dropdown == "Auto":
        if y_min > 0 and (y_max-y_min)/y_max > 0.8:
            ylim = [0, y_max*1.02]
        else:
            ylim = [y_min-0.02*(y_max-y_min), y_max+0.02*(y_max-y_min)]
    if dropdown == "Inklusive x-Achse":
        if y_min > 0:
            ylim = [0, y_max*1.02]
        elif y_max < 0:
            ylim = [y_min * 1.02, 0]
        else:
            ylim = [y_min-0.02*(y_max-y_min), y_max+0.02*(y_max-y_min)]
    elif dropdown == "Datenbereich":
        ylim = [y_min-0.02*(y_max-y_min), y_max+0.02*(y_max-y_min)]
    return ylim

def calc_x_limits(x, dropdown, today):
    xlim = [None, None]
    x.sort()
    if today:
        float_jahr = datetime_to_float_year(dt.datetime.now().date()+dt.timedelta(days=1))
    else:
        float_jahr = max(x)
    thisyear = int(float_jahr)

    # Automatische
    if dropdown == "Auto": # min-max der letzten 365 Datenpunkte
        xlim = [min(x[-365:]), float_jahr]
    elif dropdown == "Alle":
        xlim = [min(x), float_jahr]

    # Fixe
    elif dropdown == "1 Woche":
        xlim = [float_jahr - 1 / 48, float_jahr]
    elif dropdown == "2 Wochen":
        xlim = [float_jahr - 1 / 24, float_jahr]
    elif dropdown == "1 Monat":
        xlim = [float_jahr - 1 / 12, float_jahr]
    elif dropdown == "2 Monate":
        xlim = [float_jahr - 2 / 12, float_jahr]
    elif dropdown == "4 Monate":
        xlim = [float_jahr - 4 / 12, float_jahr]
    elif dropdown == "6 Monate":
        xlim = [float_jahr - 6 / 12, float_jahr]
    elif dropdown == "1 Jahr":
        xlim = [float_jahr - 1, float_jahr]
    elif dropdown == "2 Jahre":
        xlim = [float_jahr - 2, float_jahr]
    elif dropdown == "4 Jahre":
        xlim = [float_jahr - 4, float_jahr]
    elif dropdown == "10 Jahre":
        xlim = [float_jahr - 10, float_jahr]
    return xlim

def center_positions(array):
    centers = []
    for i in range(1,len(array)):
        centers.append((array[i]+array[i-1])/2)
    centers.append(0)
    return centers

def myformat(x, perc=False, precision=3, thousand_sep=True):
    if x is None:
        return ""
    if isinstance(x, (tuple, str)):
        str_out = str(x)
    elif isinstance(x, int) or abs(x) > 120:
        if not isinstance(x, int):
            x = int(x)
        if abs(x) > 99999:
            if thousand_sep:
                str_out = '{:,}'.format(x).replace(',', '.')
            else:
                str_out = '{:,}'.format(x).replace(',', '')
        else:
            str_out = str(x)
    else:
        format_string = "{:#." + str(precision) + "g}"
        str_out = format_string.format(x)
    if perc:
        str_out += "%"
    return str_out

def nvl(value, replacement):
    if value == 0:
        value = replacement
    return value

def float_year_axis_labels(ax, xlim, nbins=6, nbins_maxfac=2, grid_alpha=0.2, only_grid=False, fontsize=11):
    xbin = 365.0 * (xlim[1] - xlim[0]) / nbins
    xticks_pos = []
    xticks_labels = []

    print("axis label xbin:", xbin)

    if xbin > 120:
        xlabel = "Jahr"
        years_step = nvl(int((xlim[1] - xlim[0]) / nbins), 1)
        if years_step > 1:
            grid_loc = "major"
        else:
            grid_loc = "minor"
        xticks_pos = np.arange(int(xlim[0]) - 1, int(xlim[1]) + 2, years_step)
        xticks_labels = [str(int(x)) for x in xticks_pos]

    elif xbin > 20:
        xlabel = float_year_to_datetime((xlim[1] + xlim[0]) / 2).strftime("%Y")
        month_step = nvl(int(((xlim[1] - xlim[0]) * 12) / nbins), 1)
        if month_step > 1:
            grid_loc = "major"
        else:
            grid_loc = "minor"
        for y in range(int(xlim[0]) - 1, int(xlim[1]) + 1):
            for m in range(1, 13):
                if m % month_step == 0:
                    thisdate = dt.date(y, m, 1)
                    xticks_pos.append(datetime_to_float_year(thisdate))
                    xticks_labels.append(thisdate.strftime("%b"))

    elif xbin > 2:
        xlabel = float_year_to_datetime((xlim[1] + xlim[0]) / 2).strftime("%Y")
        day_step = nvl(round(((xlim[1] - xlim[0]) * 365) / nbins), 1)
        if day_step > 1:
            grid_loc = "major"
        else:
            grid_loc = "minor"
        for d in range(0, int((xlim[1] - xlim[0]) * 365) + 10, day_step):
            thisdate = float_year_to_datetime(xlim[0]) + dt.timedelta(days=d)
            xticks_pos.append(datetime_to_float_year(thisdate))
            xticks_labels.append(thisdate.strftime("%d.%m."))

    else:
        grid_loc = "minor"
        xlabel = float_year_to_datetime((xlim[1] + xlim[0]) / 2).strftime("%Y")
        for d in range(0, int((xlim[1] - xlim[0]) * 365) + 10):
            thisdate = float_year_to_datetime(xlim[0]) + dt.timedelta(days=d)
            xticks_pos.append(datetime_to_float_year(thisdate))
            xticks_labels.append(thisdate.strftime("%d.%m."))

    # grid independent
    ax.set_xlabel(xlabel)
    ax.tick_params(axis='x', which='minor', length=0, labelsize=fontsize)

    # major label, minor grid
    if grid_loc == "minor":
        ax.minorticks_on()
        ax.set_xticks(xticks_pos, minor=True)
        ax.set_xticks(center_positions(xticks_pos), minor=False)
        ax.set_xticklabels(xticks_labels)
        ax.xaxis.grid(True, which='minor', alpha=grid_alpha)
        ax.xaxis.grid(True, which='major', alpha=0)
        ax.tick_params(axis='x', which='major', length=0)

    # minor label, major grid
    else:
        ax.minorticks_off()
        ax.set_xticks(center_positions(xticks_pos), minor=True)
        ax.set_xticks(xticks_pos, minor=False)
        ax.set_xticklabels(xticks_labels)
        ax.xaxis.grid(True, which='minor', alpha=0)
        ax.xaxis.grid(True, which='major', alpha=grid_alpha)

    # only show grid
    if only_grid:
        ax.set_xlabel("")
        ax.set_xticklabels([])
        ax.tick_params(axis='x', which='major', length=0)

    ax.set_xlim(xlim)



# ===================================================================================
# ===================================================================================
#        CLASS NEWGUI
# ===================================================================================
# ===================================================================================

class NewGUI():
    def __init__(self):

        # GUI variables
        self.root = tk.Tk()
        self.path = ""
        self.all_files = []
        self.timer = MyTimer()
        self.fontsize = 11
        self.default_font = tk.font.nametofont("TkDefaultFont")
        self.text_font = tk.font.nametofont("TkTextFont")

        # init timer
        self.timer.start()

        # window config
        self.root.config(bg='#fafafa')
        self.root.title(GUINAME + " (" + GUIVERSION + ")")
        self.root.geometry('800x400+100+100')
        self.root.protocol("WM_DELETE_WINDOW",  self.on_close)

        # fontsize
        self.default_font.configure(size=self.fontsize)
        self.text_font.configure(size=self.fontsize)

        # icon and DPI
        try:
            self.root.iconbitmap(GUINAME + ".ico")
            self.root.update() # important: recalculate the window dimensions
        except:
            print("Found no icon.")
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            print("No succeess of:    ctypes.windll.shcore.SetProcessDpiAwareness(1)")

        # bind actions
        self.root.bind('<Right>', self.replot_shift_p)
        self.root.bind('<Left>',  self.replot_shift_n)
        self.root.bind('<Alt-Right>', self.replot_min_shift_p)
        self.root.bind('<Alt-Left>',  self.replot_min_shift_n)
        self.root.bind('<Control-Right>', self.replot_reduce)
        self.root.bind('<Control-Left>',  self.replot_expand)
        self.root.bind('<Return>',  self.replot_reset_axes)
        self.root.bind('<Up>', self.decrease_cmt)
        self.root.bind('<Down>', self.increase_cmt)

        # positions
        x1 = pts(0.5*self.fontsize)
        x2 = pts(2.5*self.fontsize)
        y1 = pts(1.4*self.fontsize)
        ystep = pts(2*self.fontsize)
        yframe = pts(7.0*self.fontsize)
        h1 = pts(1.8*self.fontsize)
        
        # Don't want to have all positions as attributes (too many "self.")
        # class functions can access them anyway through this dictionary:
        self.wpos = {
            'x1': x1,
            'x2': x2,
            'y1': y1,
            'ystep': ystep,
            'yframe': yframe,
            'h1': h1,
        }

        # widget variables
        self.dropdown = []
        self.dropdown_menu = []
        self.remove_x = []
        self.check_xaxis = tk.BooleanVar()
        self.check_yaxis = tk.BooleanVar()
        self.check_today = tk.BooleanVar()
        self.check_distribute = tk.BooleanVar()
        self.check_horizontal = tk.BooleanVar()
        self.check_hold = tk.BooleanVar()
        self.check_betrag = tk.BooleanVar()
        self.check_style = tk.BooleanVar()
        self.check_shift = tk.BooleanVar()
        self.check_stack = tk.BooleanVar()
        self.check_norm = tk.BooleanVar()
        self.check_offset = tk.BooleanVar()
        self.radio_number = tk.StringVar(self.root)
        self.radio_cmt = tk.StringVar(self.root)
        self.radio_xlim = tk.StringVar(self.root)
        self.radio_ylim = tk.StringVar(self.root)

        # menu bars
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # load
        load = tk.Menu(menubar, tearoff=0)
        load.add_command(label="Pfad wählen", command=self.browse)
        load.add_command(label="Dateien aktualisieren", command=self.refresh_file_dropdowns)
        load.add_command(label="Grafik zurücksetzen", command=self.replot_reset_axes)
        load.add_command(label="Grafik aktualisieren", command=self.replot)
        load.add_command(label="Default Einstellungen", command=self.load_default)
        menubar.add_cascade(label="Laden", menu=load)

        # settings
        daten_menu = tk.Menu(menubar, tearoff=0)
        daten_menu.add_checkbutton(label="Daten an gleichen Tagen verteilen", onvalue=1, offvalue=0, variable=self.check_distribute, command=self.replot)
        daten_menu.add_checkbutton(label="Stapeln", onvalue=1, offvalue=0, variable=self.check_stack, command=self.replot)
        daten_menu.add_checkbutton(label="→ Übertrag von ausgeblendeten Mengen", onvalue=1, offvalue=0, variable=self.check_shift, command=self.replot)
        daten_menu.add_checkbutton(label="Normieren (ändert Stapeln)", onvalue=1, offvalue=0, variable=self.check_norm, command=self.toggle_stacking)
        daten_menu.add_checkbutton(label="→ Offset", onvalue=1, offvalue=0, variable=self.check_offset, command=self.replot)
        menubar.add_cascade(label="Daten", menu=daten_menu)

        # anzeige
        anzeige = tk.Menu(menubar, tearoff=0)
        anzeige.add_checkbutton(label="X-Achse", onvalue=1, offvalue=0, variable=self.check_xaxis, command=self.replot_reset_axes)
        anzeige.add_checkbutton(label="Y-Achse", onvalue=1, offvalue=0, variable=self.check_yaxis, command=self.replot_reset_axes)
        anzeige.add_checkbutton(label="X-Achse bis heute", onvalue=1, offvalue=0, variable=self.check_today, command=self.replot_reset_axes)
        anzeige.add_checkbutton(label="Horizontal bis zum nächsten Wert", onvalue=1, offvalue=0, variable=self.check_horizontal, command=self.replot)
        anzeige.add_checkbutton(label="Niveau halten nach letztem Punkt", onvalue=1, offvalue=0, variable=self.check_hold, command=self.replot)
        anzeige.add_checkbutton(label="Beträge", onvalue=1, offvalue=0, variable=self.check_betrag, command=self.replot)
        anzeige.add_checkbutton(label="Stil der Kommentare/Beträge nach Umsatz", onvalue=1, offvalue=0, variable=self.check_style, command=self.replot)
        menubar.add_cascade(label="Anzeige", menu=anzeige)

        # number
        number = tk.Menu(menubar, tearoff=0)
        options_number = [1,2,3,4,5,6]
        for opt in options_number:
            number.add_radiobutton(label=opt, value=opt, variable=self.radio_number, command=self.refresh_file_dropdowns)
        menubar.add_cascade(label="Anzahl", menu=number)

        # xlim
        zeitraum_menu = tk.Menu(menubar, tearoff=0)
        options_xlim = [
            "Auto",
            "Alle",
            "1 Woche",
            "2 Wochen",
            "1 Monat",
            "2 Monate",
            "4 Monate",
            "6 Monate",
            "1 Jahr",
            "2 Jahre",
            "4 Jahre",
            "10 Jahre",
        ]
        for opt in options_xlim:
            zeitraum_menu.add_radiobutton(label=opt, value=opt, variable=self.radio_xlim, command=self.replot_reset_axes)
        menubar.add_cascade(label="Zeitraum", menu=zeitraum_menu)

        # skala
        skala_menu = tk.Menu(menubar, tearoff=0)
        options_ylim = [
            "Auto",
            "Inklusive x-Achse",
            "Datenbereich",
        ]
        for opt in options_ylim:
            skala_menu.add_radiobutton(label=opt, value=opt, variable=self.radio_ylim, command=self.replot)
        menubar.add_cascade(label="Skala", menu=skala_menu)

        # Kommentare
        cmt_menu = tk.Menu(menubar, tearoff=0)
        self.cmt_options = [0,1,2,5,10,20,30,50,70,100]
        for opt in self.cmt_options:
            cmt_menu.add_radiobutton(label=opt, value=opt, variable=self.radio_cmt, command=self.replot)
        menubar.add_cascade(label="Kommentare", menu=cmt_menu)

        self.plot_frame = tk.Frame()
        self.plot_frame.place(relx=0.03, y=dropdown_y(y1, ystep, 3), relheight=1, height=pts('-', yframe, -4*self.fontsize), relwidth=0.94, anchor='nw')
        self.plot_window = Plotwindow(self, (18,12))
        self.timer.stop(text="Build GUI")

        # pre-init
        #self.radio_number.set(2)
        #self.refresh_file_dropdowns()

        # load config file
        self.load_config_file()

        self.root.mainloop()

    def search_files(self):
        self.all_files = load_files(self.path)

    def browse(self):
        thispath = tk.filedialog.askdirectory()
        thispath = thispath.replace("/",os.sep).replace("\\",os.sep)
        self.path = thispath
        self.search_files()
        self.refresh_file_dropdowns()

    def refresh_file_dropdowns(self):

        self.timer.start()
        old_selection = []
        for i in range(len(self.dropdown)):
            old_selection.append(self.dropdown[i].get())

        for i in range(len(self.dropdown_menu)):
            self.dropdown_menu[i].destroy()
            self.remove_x[i].destroy()

        x1 = self.wpos["x1"]
        x2 = self.wpos["x2"]
        y1 = self.wpos["y1"]
        yframe = self.wpos["yframe"]
        ystep = self.wpos["ystep"]
        h1 = self.wpos["h1"]

        self.dropdown = []
        self.dropdown_menu = []
        self.remove_x = []
        for i in range(int(self.radio_number.get())):
            self.dropdown.append(tk.StringVar(self.root))
            if i < len(old_selection):
                if old_selection[i] in self.all_files:
                    self.dropdown[i].set(old_selection[i])
            else:
                self.dropdown[i].set(self.all_files[0])
            self.dropdown_menu.append(tk.OptionMenu(self.root, self.dropdown[i], *self.all_files, command=self.replot_reset_axes))
            self.dropdown_menu[i].configure(fg=rgb_to_hex(LINECOLORS[i]), activeforeground=rgb_to_hex(LINECOLORS[i]), anchor='w')
            self.dropdown_menu[i].place(x=x2, y=dropdown_y(y1, ystep, i), height=h1, relwidth=1, width=pts("-", 4*self.fontsize), anchor='w')
            self.remove_x.append(tk.Button(self.root, text="X", anchor='c', command=partial(self.remove, i)))
            self.remove_x[i].configure(bg='#fafafa', fg=rgb_to_hex(LINECOLORS[i]), activeforeground=rgb_to_hex(LINECOLORS[i]), bd=0)
            self.remove_x[i].place(x=x1, y=dropdown_y(y1, ystep, i), height=h1, width=h1, anchor='w')
            self.remove_x[i].place_forget()

        self.plot_frame.place(relx=0.03, y=dropdown_y(y1, ystep, int(self.radio_number.get())), relheight=1, height=pts('-', dropdown_y(y1, ystep, int(self.radio_number.get())), -4*self.fontsize), relwidth=0.94, anchor='nw')

        self.timer.stop("Refresh file dropdowns")
        self.root.update()
        self.replot_reset_axes()

    def remove(self, i):
        self.dropdown[i].set(DEFAULT_FILENAME)
        self.remove_x[i].place_forget()
        self.root.title(GUINAME + " (" + GUIVERSION + ")")
        self.root.update()
        self.replot_reset_axes()

    def toggle_stacking(self, *args):
        if self.check_norm.get() == 1:
            self.check_stack.set(0)
        if self.check_norm.get() == 0:
            self.check_stack.set(1)
        self.replot()

    def replot_reset_axes(self, *args):
        self.load_and_plot(True, None, None)

    def replot(self, *args):
        self.load_and_plot(False, None, None)

    def replot_expand(self, *args):
        self.load_and_plot(True, -REL_ZOOM, REL_ZOOM)

    def replot_reduce(self, *args):
        self.load_and_plot(True, REL_ZOOM/2, -REL_ZOOM/2)

    def replot_shift_p(self, *args):
        self.load_and_plot(True, REL_SHIFT, REL_SHIFT)

    def replot_shift_n(self, *args):
        self.load_and_plot(True, -REL_SHIFT, -REL_SHIFT)

    def replot_min_shift_p(self, *args):
        self.load_and_plot(True, REL_SHIFT_MIN, REL_SHIFT_MIN)

    def replot_min_shift_n(self, *args):
        self.load_and_plot(True, -REL_SHIFT_MIN, -REL_SHIFT_MIN)

    def increase_cmt(self, *args):
        cmt_idx = self.cmt_options.index(int(self.radio_cmt.get()))
        if cmt_idx + 1 < len(self.cmt_options):
            self.radio_cmt.set(self.cmt_options[cmt_idx + 1])
        self.replot()

    def decrease_cmt(self, *args):
        cmt_idx = self.cmt_options.index(int(self.radio_cmt.get()))
        if cmt_idx - 1 >= 0:
            self.radio_cmt.set(self.cmt_options[cmt_idx - 1])
        self.replot()

    def load_and_plot(self, reset_axes, dx_left, dx_right, *args):
        if not reset_axes:
            old_xlims = self.plot_window.ax.get_xlim()
            old_ylims = self.plot_window.ax.get_ylim()
        elif dx_left is not None or dx_right is not None:
            old_xlims = self.plot_window.ax.get_xlim()
            old_ylims = []
        else:
            old_xlims = []
            old_ylims = []
        self.plot_window.clearplot()
        #os.system('cls') # clear console
        
        # load
        self.timer.start()
        data_input = []
        color_input = []
        for i in range(int(self.radio_number.get())):
            if not self.dropdown[i].get() == DEFAULT_FILENAME:
                color_input.append(LINECOLORS[i])
                data_input.append(load_csv_data(self.dropdown[i].get()))
        color_input = np.array(color_input)
        self.timer.stop("Load file")

        # plot
        if len(data_input) > 0:
            self.plot_window.stackplot(
                data_input,
                color_input,
                old_xlims,
                old_ylims,
                dx_left,
                dx_right
            )
            if not self.check_norm.get():
                this_radio_cmt = self.radio_cmt.get()
                self.plot_window.plot_comments(
                    data_input[-1],
                    self.plot_window.ax.get_xlim(),
                    self.plot_window.ax.get_ylim(),
                    int(this_radio_cmt) / 100)
        self.timer.stop("Plot file")

        # Entfernen-Kreuze aktualisieren
        for i in range(int(self.radio_number.get())):
            if self.dropdown[i].get() == DEFAULT_FILENAME:
                self.remove_x[i].place_forget()
            else:
                self.remove_x[i].place(x=self.wpos['x1'], y=dropdown_y(self.wpos['y1'], self.wpos['ystep'], i), height=self.wpos['h1'], width=self.wpos['h1'], anchor='w')

    def on_close(self):
        print("... save config file")
        print(self.root.winfo_geometry())
        config_object = ConfigParser()

        config_object["SETTINGS"] = {}
        config_object["SETTINGS"]["windowsize"] = self.root.winfo_geometry()
        config_object["SETTINGS"]["lastpath"] = self.path

        config_object["OPTIONS"] = {}
        config_object["OPTIONS"]["check_xaxis"]         = str(self.check_xaxis.get())
        config_object["OPTIONS"]["check_yaxis"]         = str(self.check_yaxis.get())
        config_object["OPTIONS"]["check_today"]         = str(self.check_today.get())
        config_object["OPTIONS"]["check_distribute"]    = str(self.check_distribute.get())
        config_object["OPTIONS"]["check_horizontal"]    = str(self.check_horizontal.get())
        config_object["OPTIONS"]["check_hold"]          = str(self.check_hold.get())
        config_object["OPTIONS"]["check_betrag"]        = str(self.check_betrag.get())
        config_object["OPTIONS"]["check_style"]         = str(self.check_style.get())
        config_object["OPTIONS"]["check_shift"]         = str(self.check_shift.get())
        config_object["OPTIONS"]["check_stack"]         = str(self.check_stack.get())
        config_object["OPTIONS"]["check_norm"]          = str(self.check_norm.get())
        config_object["OPTIONS"]["check_offset"]        = str(self.check_offset.get())

        config_object["RADIO"] = {}
        config_object["RADIO"]["radio_number"]      = self.radio_number.get()
        config_object["RADIO"]["radio_cmt"]         = self.radio_cmt.get()
        config_object["RADIO"]["radio_xlim"]        = self.radio_xlim.get()
        config_object["RADIO"]["radio_ylim"]        = self.radio_ylim.get()

        config_object["FILES"] = {}
        for i in range(int(self.radio_number.get())):
            config_object["FILES"]["dropdown" + str(i)] = self.dropdown[i].get()

        with open(GUINAME + ".conf", 'w') as conf:
            config_object.write(conf)

        self.root.destroy()

    def load_default(self):
        self.load_config_file(default=True)

    def load_config_file(self, default=False):
        self.timer.start()
        config_object = ConfigParser()

        # read
        if os.path.exists(GUINAME + ".conf") and not default:
            config_object.read(GUINAME + ".conf")

        # default
        else:
            config_object["SETTINGS"] = {
                "windowsize":  '850x500+300+300',
                "lastpath":     'V:' + os.sep,
            }
            config_object["OPTIONS"] = {
                "check_xaxis":          '1',
                "check_yaxis":          '1',
                "check_today":          '0',
                "check_distribute":     '1',
                "check_horizontal":     '1',
                "check_hold":           '1',
                "check_betrag":         '0',
                "check_style":          '1',
                "check_shift":          '1',
                "check_stack":          '1',
                "check_norm":           '0',
                "check_offset":         '1',
            }
            config_object["RADIO"] = {
                "radio_number":  '2',
                "radio_cmt":     '5',
                "radio_xlim":    "Auto",
                "radio_ylim":    "Auto",
            }
            config_object["FILES"] = {}
            for i in range(int(config_object["RADIO"]["radio_number"])):
                config_object["FILES"]["dropdown" + str(i)] = DEFAULT_FILENAME

        # apply
        self.root.geometry(             config_object["SETTINGS"]["windowsize"])
        self.path =                     config_object["SETTINGS"]["lastpath"]

        self.check_xaxis.set(           config_object["OPTIONS"]["check_xaxis"])
        self.check_yaxis.set(           config_object["OPTIONS"]["check_yaxis"])
        self.check_today.set(           config_object["OPTIONS"]["check_today"])
        self.check_distribute.set(      config_object["OPTIONS"]["check_distribute"])
        self.check_horizontal.set(      config_object["OPTIONS"]["check_horizontal"])
        self.check_hold.set(            config_object["OPTIONS"]["check_hold"])
        self.check_betrag.set(          config_object["OPTIONS"]["check_betrag"])
        self.check_style.set(           config_object["OPTIONS"]["check_style"])
        self.check_shift.set(           config_object["OPTIONS"]["check_shift"])
        self.check_stack.set(           config_object["OPTIONS"]["check_stack"])
        self.check_norm.set(            config_object["OPTIONS"]["check_norm"])
        self.check_offset.set(          config_object["OPTIONS"]["check_offset"])

        self.radio_number.set(          config_object["RADIO"]["radio_number"])
        self.radio_cmt.set(             config_object["RADIO"]["radio_cmt"])
        self.radio_xlim.set(            config_object["RADIO"]["radio_xlim"])
        self.radio_ylim.set(            config_object["RADIO"]["radio_ylim"])

        self.dropdown = []
        for i in range(int(self.radio_number.get())):
            self.dropdown.append(tk.StringVar(self.root))
            this_filename = config_object["FILES"]["dropdown" + str(i)]
            if os.path.isfile(this_filename):
                self.dropdown[i].set(this_filename)
            else:
                self.dropdown[i].set(DEFAULT_FILENAME)

        self.timer.stop(text="Config")
        self.search_files()
        self.refresh_file_dropdowns()



# =======================================================================================================
# =======================================================================================================
#        CLASS PLOTWINDOW
# =======================================================================================================
# =======================================================================================================
class Plotwindow():
    def __init__(self, root, size):

        # GUI variables
        self.root = root
        self.timer = MyTimer()
        self.fontsize = self.root.fontsize+2

        # init
        plt.rcParams['font.size'] = str(self.fontsize)

        # GUI widgets
        self.fig = mpl.figure.Figure(size, constrained_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = tkagg.FigureCanvasTkAgg(self.fig, master=root.plot_frame)
        toolbar = tkagg.NavigationToolbar2Tk(self.canvas, self.root.root)
        # print(toolbar.children.keys())
        # button:home, checkbutton-1:pan, checkbutton-2:zoom, button2:forward, button3:back, button4:settings, button5:save
        toolbar.children['!button2'].pack_forget()
        toolbar.children['!button3'].pack_forget()
        toolbar.children['!button4'].pack_forget()
        toolbar.children['!checkbutton-1'].pack_forget()
        toolbar.children['!button'].config(command=self.root.replot_reset_axes)
        toolbar.update()
        self.canvas.get_tk_widget().pack()
        cid = self.fig.canvas.mpl_connect('button_release_event', self.mouse_release)

    def mouse_release(self, event):
        self.root.replot()
        
    def plot_comments(self, input_data, xlims, ylims, comment_cutoff = 0):
        print("plot comments with cutoff", comment_cutoff)
        x = input_data[0]
        y = input_data[1]
        cmt_text = input_data[2]
        arraylength = len(x)

        cmt_x = []
        if self.root.check_distribute.get():
            cmt_x = distribute_x_at_same_day(x)
        else:
            cmt_x = x

        cmt_y = [y[0] / 2]
        for i in range(1,arraylength):
            cmt_y.append(y[i-1] + (y[i] - y[i-1])/2)

        cmt_diff = [0]
        for i in range(1,arraylength):
            cmt_diff.append(cmt_y[i] - cmt_y[i-1])

        max_y_diff = 0
        for i in range(arraylength):
            if cmt_x[i] > self.ax.get_xlim()[0] and cmt_x[i] < self.ax.get_xlim()[1] \
            and cmt_y[i] > self.ax.get_ylim()[0] and cmt_y[i] < self.ax.get_ylim()[1]:
                if abs(cmt_diff[i]) > max_y_diff:
                    max_y_diff = abs(cmt_diff[i])
        for i in range(arraylength):
            if cmt_x[i] > self.ax.get_xlim()[0] and cmt_x[i] < self.ax.get_xlim()[1] \
            and cmt_y[i] > self.ax.get_ylim()[0] and cmt_y[i] < self.ax.get_ylim()[1]\
            and abs(cmt_diff[i]) > comment_cutoff * max_y_diff \
            and len(cmt_text[i]) > 0:
                if self.root.check_style.get():
                    this_colorfactor = powerscale_between(abs(cmt_diff[i]) / max_y_diff, 0.7, 0, 0.7)
                    this_size = powerscale_between(abs(cmt_diff[i]) / max_y_diff, self.fontsize*0.6, self.fontsize, 0.7)
                else:
                    this_colorfactor = 0
                    this_size = self.fontsize
                this_color = this_colorfactor * np.array([1, 1, 1])
                if self.root.check_betrag.get():
                    this_label = str(cmt_text[i]) + " (" + '{0:.0f}'.format(abs(cmt_diff[i])) + ")"
                else:
                    this_label = str(cmt_text[i])
                if cmt_diff[i] > 0:
                    self.ax.text(cmt_x[i], cmt_y[i], this_label + "–", fontsize = str(this_size), va = 'center', ha = 'right', color = this_color, family='Arial Narrow')
                else:
                    self.ax.text(cmt_x[i], cmt_y[i], "–" + this_label, fontsize = str(this_size), va = 'center', ha = 'left', color = this_color, family='Arial Narrow')
        self.canvas.draw()

    def stackplot(self, input_data, color_input, xlims, ylims, dx_left, dx_right):
        linenumber = len(input_data)

        # prepare format (list of numpy 2d-arrays)
        line_data = []
        for i in range(linenumber):
            x = input_data[i][0]
            y = input_data[i][1]
            line_data.append(np.stack((x,y), axis=1))

        # load, sort and edit
        x_all = []
        y_all = []
        for i in range(linenumber):
            data = sort_array(line_data[i])
            if self.root.check_distribute.get():
                data[:,0] = distribute_x_at_same_day(data[:,0])
            if self.root.check_horizontal.get():
                data = repeat_y_in_between(data)
            x_all.append(data[:,0])
            y_all.append(data[:,1])

        # set axes if not empty
        if dx_left is not None and dx_right is not None:
            xdiff = xlims[1] - xlims[0]
            xlim = [xlims[0] + dx_left * xdiff, xlims[1] + dx_right * xdiff]
            if xlim[0] > xlim[1]:
                xlim = xlims
            else:
                ylim = ylims
        elif xlims and ylims:
            xlim = xlims
            ylim = ylims
        else:
            xlim = calc_x_limits(np.concatenate(x_all), self.root.radio_xlim.get(), self.root.check_today.get())

        # hold
        if self.root.check_hold.get():
            for i in range(linenumber):
                x_all[i] = np.append(x_all[i], xlim[1])
                y_all[i] = np.append(y_all[i], y_all[i][-1])

        # stack mode
        if self.root.check_stack.get() and linenumber > 1:
            lower_x_lim = min(x_all[0])
            upper_x_lim = max(x_all[0])
            for i in range(linenumber):
                if min(x_all[i]) < lower_x_lim:
                    lower_x_lim = min(x_all[i])
                if max(x_all[i]) > upper_x_lim:
                    upper_x_lim = max(x_all[i])

            interp_x = np.arange(lower_x_lim, upper_x_lim, TIMEDIFF_INTERPOLATION)
            interp_x = np.round(interp_x, 7)
            interp_y_all = []
            for i in range(linenumber):
                interp_y_all.append(np.interp(interp_x, x_all[i], y_all[i], 0, y_all[i][-1]))

            for i in range(linenumber-1,-1,-1):
                x_all[i] = interp_x
                if i==linenumber-1:
                    y_all[i] = interp_y_all[i]
                else:
                    y_all[i] = interp_y_all[i] + y_all[i+1]

            # temp y-limits
            # Wenn der erste Datensatz zu Limit y=0 führt -> kein Übertrag
            if not ylims:
                ylim = calc_y_limits(xlim, x_all[0], y_all[0], self.root.radio_ylim.get())

            # shift minimum
            if self.root.check_shift.get() and not ylim[0] == 0:
                for i in range(linenumber-1):
                    ymin1 = math.inf
                    ymax1 = -math.inf
                    for n in range(len(interp_x)):
                        if x_all[i][n] > xlim[0] and x_all[i][n] < xlim[1]:
                            if y_all[i][n] < ymin1:
                                ymin1 = y_all[i][n]
                            if y_all[i][n] > ymax1:
                                ymax1 = y_all[i][n]
                    ymin2 = math.inf
                    ymax2 = -math.inf
                    for n in range(len(interp_x)):
                        if x_all[i+1][n] > xlim[0] and x_all[i+1][n] < xlim[1]:
                            if y_all[i+1][n] < ymin2:
                                ymin2 = y_all[i+1][n]
                            if y_all[i+1][n] > ymax2:
                                ymax2 = y_all[i+1][n]
                    shift_amount = ymin1 - ymax2
                    if shift_amount < 0:
                        shift_amount = 0
                    else:
                        shift_amount = 0.95 * shift_amount
                    y_all[i+1] = y_all[i+1] + shift_amount

        # temp y-limits
        if not ylims:
            ylim = calc_y_limits(xlim, np.concatenate(x_all), np.concatenate(y_all), self.root.radio_ylim.get())

        # normalize
        if self.root.check_norm.get():
            if self.root.check_stack.get():
                norm_factor_all = norm_factor(np.concatenate(x_all), np.concatenate(y_all), xlim)
                for i in range(linenumber):
                    y_all[i] = y_all[i] * norm_factor_all
            else:
                for i in range(linenumber):
                    if self.root.check_offset.get() and not ylim[0] == 0:
                        y_all[i] = y_all[i] - min_within_x(x_all[i], y_all[i], xlim)
                    y_all[i] = y_all[i] * norm_factor(x_all[i], y_all[i], xlim)
                    if self.root.check_offset.get():
                        y_all[i] = y_all[i] + linenumber - 1 - i

        # y-limits
        if not ylims:
            ylim = calc_y_limits(xlim, np.concatenate(x_all), np.concatenate(y_all), self.root.radio_ylim.get())

        # add zeros for fill
        for i in range(linenumber):
            if self.root.check_norm.get() and self.root.check_offset.get() and not self.root.check_stack.get():
                arraylength = len(x_all[i])
                x_all[i] = np.append(x_all[i], x_all[i][arraylength - 1])
                y_all[i] = np.append(y_all[i], linenumber - 1 - i)
                x_all[i] = np.insert(x_all[i], 0, x_all[i][0])
                y_all[i] = np.insert(y_all[i], 0, linenumber - 1 - i)
            else:
                arraylength = len(x_all[i])
                x_all[i] = np.append(x_all[i], x_all[i][arraylength - 1])
                y_all[i] = np.append(y_all[i], 0)
                x_all[i] = np.insert(x_all[i], 0, x_all[i][0])
                y_all[i] = np.insert(y_all[i], 0, 0)

        # plot
        for i in range(linenumber):
            if self.root.check_stack.get():
                self.ax.fill(x_all[i], y_all[i], color=0.3 * color_input[i] + 0.7 * np.array([1, 1, 1]), linewidth=0.1, alpha=1)
            else:
                self.ax.fill(x_all[i], y_all[i], color=0.3 * color_input[i] + 0.7 * np.array([1, 1, 1]), linewidth=0.1, alpha=0.5)
            self.ax.plot(x_all[i], y_all[i], color=color_input[i], linewidth=1.1)

        # labels and ticks
        float_year_axis_labels(
            self.ax,
            xlim,
            fontsize=self.fontsize,
        )

        # axes visibility
        if not self.root.check_xaxis.get():
            self.ax.set_xticks([])
            self.ax.set_xlabel("")
        if not self.root.check_yaxis.get():
            self.ax.set_yticks([])
            self.ax.set_ylabel("")

        # limits
        if not xlim[0] is None:
            self.ax.set_xlim(left=xlim[0])
        if not xlim[1] is None:
            self.ax.set_xlim(right=xlim[1])
        if not ylim[0] is None:
            self.ax.set_ylim(bottom=ylim[0])
        if not ylim[1] is None:
            self.ax.set_ylim(top=ylim[1])

        # mouse position
        if self.root.check_xaxis.get():
            if self.root.check_yaxis.get():
                self.ax.format_coord=format_coord
            else:
                self.ax.format_coord=format_coord_x
        else:
            if self.root.check_yaxis.get():
                self.ax.format_coord=format_coord_y
            else:
                self.ax.format_coord=format_coord_empty

        # title
        if self.root.check_yaxis.get():
            y_title = y_all[0]
            y_title = y_title[np.logical_and(xlim[0] < x_all[0], x_all[0] < xlim[1])]
            self.root.root.title(GUINAME + " (" + GUIVERSION + ")   "
                + "  ← " + "{:.0f}".format(y_title[0])
                + "  ↑ " + "{:.0f}".format(np.max(y_title))
                + "  ↓ " + "{:.0f}".format(np.min(y_title[:-1]))
                + "  → " + "{:.0f}".format(y_title[-1])
            )
        else:
            self.root.root.title(GUINAME + " (" + GUIVERSION + ")")

        self.canvas.draw()

    def clearplot(self):
        self.ax.cla()
        self.canvas.draw()


class MyTimer():
    def __init__(self):
        self.timertime = dt.datetime.now()
    def start(self, text=None):
        if text:
            print(text, end=' ')
        self.timertime = dt.datetime.now()
    def stop(self, text=None):
        time_s = (dt.datetime.now() - self.timertime).total_seconds()
        if text:
            print(text, end=' ')
        if time_s >= 120:
            print("<" + myformat(time_s/60) + "min>")
        else:
            print("<" + myformat(time_s) + "s>")
        self.timertime = dt.datetime.now()



# ===================================================================================
# ===================================================================================
#        MAIN
# ===================================================================================
# ===================================================================================

if __name__ == '__main__':

    font_entry = font_manager.FontEntry(
        fname='Helvetica.ttf',
        name='Helvetica')
    font_manager.fontManager.ttflist.insert(0, font_entry)
    font_entry = font_manager.FontEntry(
        fname='ArialNarrow.ttf',
        name='Arial Narrow')
    font_manager.fontManager.ttflist.insert(0, font_entry)
    plt.rcParams['font.family'] = 'Helvetica'
    plt.rcParams['font.size'] = '11'
    plt.rcParams['axes.linewidth'] = 0.6
    locale.setlocale(locale.LC_TIME, "de_DE")
    new = NewGUI()
