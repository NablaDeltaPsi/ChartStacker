import tkinter as tk
import tkinter.font
import numpy as np
import matplotlib as mpl
import glob
import os
import sys
import datetime
import locale
import math
import ctypes
from functools import partial
import matplotlib.pyplot as plt
import matplotlib.font_manager as font_manager
import matplotlib.ticker as tck
import matplotlib.backends.backend_tkagg as tkagg

GUINAME = 'ChartStacker'
GUIVERSION = '1.4'

# TIMEDIFF GLOBALS (<0.001 is same day)
TIMEDIFF_REPEATING      = 0.00001
TIMEDIFF_INTERPOLATION  = 0.0001
TIMEDIFF_SAME_DAY_DISTR = 0.0002
TIMEDIFF_AFTER_LAST     = 0.0004
TIMEDIFF_XLIM_DISTANCE  = 0.005

LINECOLORS = np.array([[1,.1,0],[0,.6,.2],[0,.2,.8],[.9,.6,0],[0,.6,.8],[1,0,.4]])
COMMENT_SUFFIXES = ["Kommentare", "comments"]

# ===========================================================
#        STATIC FUNCTIONS
# ===========================================================

def load_files(path):
    print(path)
    files_this = glob.glob(path + os.sep + "**" + os.sep + "*.csv", recursive=True)
    files_this.sort()
    print("\n".join(files_this))
    files_all = ["Choose file ..."] + files_this
    files_all_cmt_removed = []
    for i in range(len(files_all)):
        if not contains(files_all[i], ["_" + x + "." for x in COMMENT_SUFFIXES]):
            files_all_cmt_removed.append(files_all[i])
    return files_all_cmt_removed

def pts(*args):
    # accepts str, str+'p', int, float and returns sum as str+'p'
    # '-' sets the following argument negative
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
    thisdate = datetime.datetime.fromordinal(int(excel_nr) + 693594)
    dayfrac = excel_nr - int(excel_nr)
    thisyear = thisdate.year
    days_since_beginning = (thisdate - datetime.datetime(thisdate.year, 1, 1)).days
    days_this_year = (datetime.datetime(thisdate.year + 1, 1, 1) - datetime.datetime(thisdate.year, 1, 1)).days
    return thisyear + (days_since_beginning + dayfrac)/days_this_year

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
        return datetime_to_float_year(datetime.datetime(thisyear, thismonth, thisday))
    except:
        raise Exception('Date string could not be interpreted.')

def float_year_to_datetime(float_year):
    # 2022.86301 --> 12.11.2022
    days_this_year = (datetime.date(int(float_year)+1, 1, 1) - datetime.date(int(float_year), 1, 1)).days
    days_since_first = int(days_this_year * (float_year - int(float_year)))
    return datetime.date(int(float_year), 1, 1) + datetime.timedelta(days_since_first, 0)

def datetime_to_float_year(dt):
    # 12.11.2022 --> 2022.86301
    return excel_date_number_to_float_year(datetime_to_excel_date_number(dt))

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

def distribute_x_at_same_day(array_2d):
    # Problem: Werte am gleichen Tag (mit gleichem x) können nicht
    # interpoliert werden und werden nicht gezeichnet
    # Das Anzeigen von großen Sprüngen kann so von kleinen Buchungen
    # verhindert werden
    # Tag ist der gleiche wenn die dritte Nachkommastelle von
    # 2019.231 identisch ist
    # Prüfe auf gleiche Nachkommastellen und ändere dort die vierte und fünfte
    x = array_2d[:, 0]
    y = array_2d[:, 1]
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

    array_2d = np.stack((x, y), axis=1)
    return array_2d

def load_csv_data(filename):
    try:
        data = np.genfromtxt(filename, delimiter=';', usecols=(0,1), skip_header=1, dtype=str)
        x = data[:,0]
        y = data[:,1]
        x_ = []
        y_ = []
        for i in range(len(x)):
            new_x = date_string_to_float_year(x[i])
            x_.append(new_x)
            y_.append(float(y[i].replace(",",".")))
        x = np.array(x_)
        y = np.array(y_)
        new_data = np.stack((x,y), axis=1)
        return new_data
    except:
        raise Exception("Could not load data.")

def load_csv_comments(filename):
    cmt = [[],[],[],[]]
    for csuffix in COMMENT_SUFFIXES:
        try:
            data = np.genfromtxt(os.path.splitext(filename)[0] + "_" + csuffix + ".csv", delimiter=';', usecols=(0,1,2,3), skip_header=1, dtype=str)
            c1 = data[:,0]
            c2 = data[:,1]
            c3 = data[:,2]
            c4 = data[:,3]
            for i in range(len(c1)):
                cmt[0].append(date_string_to_float_year(c1[i]))
                cmt[1].append(float(c2[i].replace(",",".")))
                cmt[2].append(float(c3[i].replace(",",".")))
                cmt[3].append(c4[i])
        except:
            pass
        return cmt

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
    ylim = [-1, -1]
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
    if dropdown == "Inclusive x-axis":
        if y_min > 0:
             ylim = [0, y_max*1.02]
        else:
             ylim = [y_min-0.02*(y_max-y_min), y_max+0.02*(y_max-y_min)]
    elif dropdown == "Data range":
        ylim = [y_min-0.02*(y_max-y_min), y_max+0.02*(y_max-y_min)]
    return ylim

def calc_x_limits(x, dropdown, today):
    xlim = [-1, -1]
    x.sort()
    if today:
        float_jahr = datetime_to_float_year(datetime.datetime.now().date()+datetime.timedelta(days=1))
    else:
        float_jahr = max(x)
    thisyear = int(float_jahr)
    
    # Automatische
    if dropdown == "Auto": # min-max der letzten 365 Datenpunkte
        xlim = [min(x[-365:]), float_jahr]
    elif dropdown == "All":
        xlim = [min(x), float_jahr]
            
    # Fixe
    elif dropdown == "1 week":
        xlim = [float_jahr - 1 / 48, float_jahr]
    elif dropdown == "2 weeks":
        xlim = [float_jahr - 1 / 24, float_jahr]
    elif dropdown == "1 month":
        xlim = [float_jahr - 1 / 12, float_jahr]
    elif dropdown == "2 months":
        xlim = [float_jahr - 2 / 12, float_jahr]
    elif dropdown == "4 months":
        xlim = [float_jahr - 4 / 12, float_jahr]
    elif dropdown == "6 months":
        xlim = [float_jahr - 6 / 12, float_jahr]
    elif dropdown == "1 Jahr":
        xlim = [float_jahr - 1, float_jahr]
    elif dropdown == "2 years":
        xlim = [float_jahr - 2, float_jahr]
    elif dropdown == "4 years":
        xlim = [float_jahr - 4, float_jahr]
    elif dropdown == "10 years":
        xlim = [float_jahr - 10, float_jahr]
    return xlim

def center_positions(array):
    centers = []
    for i in range(1,len(array)):
        centers.append((array[i]+array[i-1])/2)
    centers.append(0)
    return centers

def set_labels_and_ticks(ax, xlim, fontsize, dropdown, x_axis_visible, y_axis_visible):

    # x-axis
    xdiff = xlim[1] - xlim[0]
    if xdiff > 8:
        ax.set_xlabel("Year", fontsize = fontsize)
        x_grid_minor_alpha = 0.0
        x_grid_major_alpha = 0.3
        ax.xaxis.set_major_locator(tck.MaxNLocator(integer=True))
    else:
        if xdiff > 8/12:
            ax.set_xlabel("Year", fontsize = fontsize)
            ax.tick_params(axis='x', which='major', length=0)
            ax.minorticks_on()
            x_grid_minor_alpha = 0.0
            x_grid_major_alpha = 0.0
            xticks_borderpos = np.arange(int(xlim[0])-1, int(xlim[1])+2, 1)
            xticks_pos = center_positions(xticks_borderpos)
            xticks_labels = [int(x) for x in xticks_borderpos]

            # ticklabels on major position in between
            ax.set_xticks(xticks_pos)
            ax.set_xticklabels(xticks_labels)

            # grid on minor position at beginning
            ax.set_xticks(xticks_borderpos, minor=True)

        elif xdiff*365 > 45:
            ax.set_xlabel("Month", fontsize = fontsize)
            ax.tick_params(axis='x', which='major', length=0)
            ax.minorticks_on()
            x_grid_minor_alpha = 0.3
            x_grid_major_alpha = 0.0
            xticks_borderpos = []
            xticks_labels = []
            for y in range(int(xlim[0])-1,int(xlim[1])+1):
                for m in range(1,13):
                    thisdate = datetime.date(y,m,1)
                    xticks_borderpos.append(datetime_to_float_year(thisdate))
                    xticks_labels.append(thisdate.strftime("%b %y"))
            xticks_pos = center_positions(xticks_borderpos)

            # ticklabels on major position in between
            ax.set_xticks(xticks_pos)
            ax.set_xticklabels(xticks_labels)

            # grid on minor position at beginning
            ax.set_xticks(xticks_borderpos, minor=True)

        elif xdiff*365 > 8:
            ax.set_xlabel("Day", fontsize = fontsize)
            ax.minorticks_on()
            x_grid_minor_alpha = 0.3
            x_grid_major_alpha = 0.3
            xticks_pos = []
            xticks_labels = []

            # ticklabels on major position
            for d in range(0,(int(xlim[1])-int(xlim[0])+1)*365+10,2):
                thisdate = datetime.date(int(xlim[0]),1,1) + datetime.timedelta(days=d)
                xticks_pos.append(datetime_to_float_year(thisdate))
                xticks_labels.append(str(thisdate.day))
            ax.set_xticks(xticks_pos)
            ax.set_xticklabels(xticks_labels)

            # grid on minor position at beginning
            for d in range(0,(int(xlim[1])-int(xlim[0])+1)*365+10,1):
                thisdate = datetime.date(int(xlim[0]),1,1) + datetime.timedelta(days=d)
                xticks_pos.append(datetime_to_float_year(thisdate))
            ax.set_xticks(xticks_pos, minor=True)

        else:
            ax.set_xlabel("Day", fontsize = fontsize)
            ax.tick_params(axis='x', which='major', length=0)
            ax.minorticks_on()
            x_grid_minor_alpha = 0.3
            x_grid_major_alpha = 0.0
            xticks_borderpos = []
            xticks_labels = []
            for d in range(0,(int(xlim[1])-int(xlim[0])+1)*365+10,1):
                thisdate = datetime.date(int(xlim[0]),1,1) + datetime.timedelta(days=d)
                xticks_borderpos.append(datetime_to_float_year(thisdate))
                xticks_labels.append(str(thisdate.day) + "." + str(thisdate.month) + "." + str(thisdate.year-2000))
            xticks_pos = center_positions(xticks_borderpos)

            # ticklabels on major position in between
            ax.set_xticks(xticks_pos)
            ax.set_xticklabels(xticks_labels)

            # grid on minor position at beginning
            ax.set_xticks(xticks_borderpos, minor=True)

    # if x-axis not visible
    if x_axis_visible == 0:
        ax.set_xlabel("")
        ax.set_xticks(np.arange(-5e9, 1e10, 1e10))
        ax.set_xticks(np.arange(-5e9, 1e10, 1e10), minor=True)

    # if y-axis not visible
    if y_axis_visible == 0:
        ax.set_ylabel("")
        ax.set_yticks(np.arange(-5e9, 1e10, 1e10))
        ax.set_yticks(np.arange(-5e9, 1e10, 1e10), minor=True)

    # no tick-label offset
    #ax.ticklabel_format(useOffset=False)

    # x grid
    ax.xaxis.grid(True, which='minor', alpha=x_grid_minor_alpha)
    ax.xaxis.grid(True, which='major', alpha=x_grid_major_alpha)

    # y grid
    y_grid_minor_alpha = 0.0
    y_grid_major_alpha = 0.2
    ax.yaxis.grid(True, which='minor', alpha=y_grid_minor_alpha)
    ax.yaxis.grid(True, which='major', alpha=y_grid_major_alpha)
        
def contains(text, substrings, booltype='any', ignore_case=True):
    if not type(substrings) is list:
        substrings = [substrings]
    if ignore_case:
        text = text.lower()
        substrings = [substr.lower() for substr in substrings]
    contains_any = False
    contains_all = True
    for substr in substrings:
        if text.find(substr) > 0:
            contains_any = True
        else:
            contains_all = False
    if booltype == 'any':
        return contains_any
    else:
        return contains_all

# ===================================================================================
# ===================================================================================
#        CLASS NEWGUI
# ===================================================================================
# ===================================================================================

class NewGUI():
    def __init__(self):

        self.root = tk.Tk()
        self.root.config(bg='#fafafa')
        self.root.title(GUINAME + " (" + GUIVERSION + ")")

        # get fontsize
        self.fontsize = 11
        self.default_font = tk.font.nametofont("TkDefaultFont")
        self.text_font = tk.font.nametofont("TkTextFont")
        self.default_font.configure(size=self.fontsize)
        self.text_font.configure(size=self.fontsize)

        # reset saved window position and path
        if os.path.isfile(GUINAME + ".conf"):
            with open(GUINAME + ".conf", "r") as conf:
                lines = conf.readlines()
                self.root.geometry(lines[0].strip())
                self.path = lines[1].strip()
        else:
            self.path = "Q:" + os.sep
            self.root.geometry('850x500+300+300')
        self.root.protocol("WM_DELETE_WINDOW",  self.on_close)

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
        self.root.bind('<Right>', self.replot_expand_p)
        self.root.bind('<Left>',  self.replot_expand_n)
        self.root.bind('<Control-Right>', self.replot_shift_p)
        self.root.bind('<Control-Left>',  self.replot_shift_n)
        self.root.bind('<Alt-Right>', self.replot_reduce_p)
        self.root.bind('<Alt-Left>',  self.replot_reduce_n)
        self.root.bind('<Return>',  self.replot_reset_axes)

        all_files = load_files(self.path)

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

        self.dropdown = []
        self.dropdown_menu = []
        self.remove_x = []
        for i in range(3):
            self.dropdown.append(tk.StringVar(self.root))
            self.dropdown[i].set(all_files[0])
            self.dropdown_menu.append(tk.OptionMenu(self.root, self.dropdown[i], *all_files, command=self.replot_reset_axes))
            self.dropdown_menu[i].configure(fg=rgb_to_hex(LINECOLORS[i]), activeforeground=rgb_to_hex(LINECOLORS[i]), anchor='w')
            self.dropdown_menu[i].place(x=x2, y=dropdown_y(y1, ystep, i), height=h1, relwidth=1, width=pts("-", 4*self.fontsize), anchor='w')
            self.remove_x.append(tk.Button(self.root, text="X", anchor='c', command=partial(self.remove, i)))
            self.remove_x[i].configure(bg='#fafafa', fg=rgb_to_hex(LINECOLORS[i]), activeforeground=rgb_to_hex(LINECOLORS[i]), bd=0)
            self.remove_x[i].place(x=x1, y=dropdown_y(y1, ystep, i), height=h1, width=h1, anchor='w')
            self.remove_x[i].place_forget()

        self.check_xaxis = tk.BooleanVar()
        self.check_yaxis = tk.BooleanVar()
        self.check_today = tk.BooleanVar()
        self.check_distribute = tk.BooleanVar()
        self.check_horizontal = tk.BooleanVar()
        self.check_hold = tk.BooleanVar()
        self.check_comments = tk.BooleanVar()
        self.check_betrag = tk.BooleanVar()
        self.check_style = tk.BooleanVar()
        self.check_shift = tk.BooleanVar()
        self.check_stack = tk.BooleanVar()
        self.check_norm = tk.BooleanVar()
        self.check_offset = tk.BooleanVar()

        self.check_xaxis.set(1)
        self.check_yaxis.set(1)
        self.check_today.set(0)
        self.check_distribute.set(1)
        self.check_horizontal.set(1)
        self.check_hold.set(1)
        self.check_comments.set(0)
        self.check_betrag.set(0)
        self.check_style.set(1)
        self.check_shift.set(1)
        self.check_stack.set(1)
        self.check_norm.set(0)
        self.check_offset.set(1)
        
        # menu bars
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # load
        load = tk.Menu(menubar, tearoff=0)
        load.add_command(label="Choose path", command=self.browse)
        load.add_command(label="Update files", command=self.refresh)
        load.add_command(label="Reset graph", command=self.replot_reset_axes)
        load.add_command(label="Update graph", command=self.replot_leave_axes)
        menubar.add_cascade(label="Load", menu=load)

        # anzeige
        anzeige = tk.Menu(menubar, tearoff=0)
        anzeige.add_checkbutton(label="X-axis", onvalue=1, offvalue=0, variable=self.check_xaxis, command=self.replot_leave_axes)
        anzeige.add_checkbutton(label="Y-axis", onvalue=1, offvalue=0, variable=self.check_yaxis, command=self.replot_leave_axes)
        anzeige.add_checkbutton(label="X-axis until today", onvalue=1, offvalue=0, variable=self.check_today, command=self.replot_reset_axes)
        anzeige.add_checkbutton(label="Horizontal to next value", onvalue=1, offvalue=0, variable=self.check_horizontal, command=self.replot_reset_axes)
        anzeige.add_checkbutton(label="Hold level after last point", onvalue=1, offvalue=0, variable=self.check_hold, command=self.replot_reset_axes)
        anzeige.add_checkbutton(label="Comments", onvalue=1, offvalue=0, variable=self.check_comments, command=self.replot_leave_axes)
        anzeige.add_checkbutton(label="Amounts", onvalue=1, offvalue=0, variable=self.check_betrag, command=self.replot_leave_axes)
        anzeige.add_checkbutton(label="Stile of comments/amounts by volume", onvalue=1, offvalue=0, variable=self.check_style, command=self.replot_leave_axes)
        menubar.add_cascade(label="View", menu=anzeige)

        # settings
        settings = tk.Menu(menubar, tearoff=0)
        settings.add_checkbutton(label="Distribute data for same day", onvalue=1, offvalue=0, variable=self.check_distribute, command=self.replot_reset_axes)
        settings.add_checkbutton(label="Stack", onvalue=1, offvalue=0, variable=self.check_stack, command=self.replot_reset_axes)
        settings.add_checkbutton(label="→ Transfer of hidden parts", onvalue=1, offvalue=0, variable=self.check_shift, command=self.replot_reset_axes)
        settings.add_checkbutton(label="Normalize (toggles Stacking)", onvalue=1, offvalue=0, variable=self.check_norm, command=self.toggle_stacking)
        settings.add_checkbutton(label="→ Offset", onvalue=1, offvalue=0, variable=self.check_offset, command=self.replot_reset_axes)
        menubar.add_cascade(label="Settings", menu=settings)

        # number
        number = tk.Menu(menubar, tearoff=0)
        self.radio_number = tk.StringVar(self.root)
        options_number = [1,2,3,4,5,6]
        self.radio_number.set(3)
        for opt in options_number:
            number.add_radiobutton(label=opt, value=opt, variable=self.radio_number, command=self.refresh)
        menubar.add_cascade(label="Dropdowns", menu=number)

        # xlim
        zeitraum = tk.Menu(menubar, tearoff=0)
        self.radio_xlim = tk.StringVar(self.root)
        options_xlim = [
            "Auto",
            "All",
            "1 week",
            "2 weeks",
            "1 month",
            "2 months",
            "4 months",
            "6 months",
            "1 year",
            "2 years",
            "4 years",
            "10 years",
        ]
        self.radio_xlim.set("Auto")
        for opt in options_xlim:
            zeitraum.add_radiobutton(label=opt, value=opt, variable=self.radio_xlim, command=self.replot_reset_axes)
        menubar.add_cascade(label="Period", menu=zeitraum)

        # skala
        skala = tk.Menu(menubar, tearoff=0)
        self.radio_ylim = tk.StringVar(self.root)
        options_ylim = [
            "Auto",
            "Inclusive x-axis",
            "Data range",
        ]
        self.radio_ylim.set("Auto")
        for opt in options_ylim:
            skala.add_radiobutton(label=opt, value=opt, variable=self.radio_ylim, command=self.replot_reset_axes)
        menubar.add_cascade(label="Scale", menu=skala)

        self.plot_frame = tk.Frame()
        self.plot_frame.place(relx=0.03, y=dropdown_y(y1, ystep, 3), relheight=1, height=pts('-', yframe, -4*self.fontsize), relwidth=0.94, anchor='nw')
        self.plot_window = Plotwindow(self, (18,12))

        self.root.mainloop()

    def browse(self):
        thispath = tk.filedialog.askdirectory()
        thispath = thispath.replace("/",os.sep).replace("\\",os.sep)
        self.path = thispath
        self.refresh()

    def refresh(self):

        old_selection = []
        for i in range(len(self.dropdown_menu)):
            old_selection.append(self.dropdown[i].get())

        all_files = load_files(self.path)

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
                if old_selection[i] in all_files:
                    self.dropdown[i].set(old_selection[i])
            else:
                self.dropdown[i].set(all_files[0])
            self.dropdown_menu.append(tk.OptionMenu(self.root, self.dropdown[i], *all_files, command=self.replot_reset_axes))
            self.dropdown_menu[i].configure(fg=rgb_to_hex(LINECOLORS[i]), activeforeground=rgb_to_hex(LINECOLORS[i]), anchor='w')
            self.dropdown_menu[i].place(x=x2, y=dropdown_y(y1, ystep, i), height=h1, relwidth=1, width=pts("-", 4*self.fontsize), anchor='w')
            self.remove_x.append(tk.Button(self.root, text="X", anchor='c', command=partial(self.remove, i)))
            self.remove_x[i].configure(bg='#fafafa', fg=rgb_to_hex(LINECOLORS[i]), activeforeground=rgb_to_hex(LINECOLORS[i]), bd=0)
            self.remove_x[i].place(x=x1, y=dropdown_y(y1, ystep, i), height=h1, width=h1, anchor='w')
            self.remove_x[i].place_forget()

        self.plot_frame.place(relx=0.03, y=dropdown_y(y1, ystep, int(self.radio_number.get())), relheight=1, height=pts('-', dropdown_y(y1, ystep, int(self.radio_number.get())), -4*self.fontsize), relwidth=0.94, anchor='nw')

        self.root.update()
        self.replot_reset_axes()

    def remove(self, i):
        self.dropdown[i].set("Choose file ...")
        self.remove_x[i].place_forget()
        self.root.title(GUINAME + " (" + GUIVERSION + ")")
        self.root.update()
        self.replot_reset_axes()

    def toggle_stacking(self, *args):
        if self.check_norm.get() == 1:
            self.check_stack.set(0)
        if self.check_norm.get() == 0:
            self.check_stack.set(1)
        self.replot_reset_axes()

    def replot_reset_axes(self, *args):
        self.load_and_plot(1, None, None)

    def replot_leave_axes(self, *args):
        self.load_and_plot(0, None, None)

    def replot_expand_p(self, *args):
        self.load_and_plot(1, 0, 1/12)

    def replot_expand_n(self, *args):
        self.load_and_plot(1, -1/12, 0)

    def replot_shift_p(self, *args):
        self.load_and_plot(1, 1/12, 1/12)

    def replot_shift_n(self, *args):
        self.load_and_plot(1, -1/12, -1/12)

    def replot_reduce_p(self, *args):
        self.load_and_plot(1, 1/12, 0)

    def replot_reduce_n(self, *args):
        self.load_and_plot(1, 0, -1/12)

    def load_and_plot(self, reset_axes, dx_left, dx_right, *args):
        if reset_axes == 0:
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
        data_input = []
        color_input = []
        for i in range(int(self.radio_number.get())):
            if not self.dropdown[i].get() == "Choose file ...":
                color_input.append(LINECOLORS[i])
                data_input.append(load_csv_data(self.dropdown[i].get()))
                cmt = load_csv_comments(self.dropdown[i].get())
        color_input = np.array(color_input)
        
        # plot
        if data_input:
            self.plot_window.stackplot(data_input, color_input, old_xlims, old_ylims, dx_left, dx_right)
            if (self.check_comments.get() or self.check_betrag.get()) and not self.check_norm.get():
                self.plot_window.plot_comments(cmt, self.plot_window.ax.get_xlim(), self.plot_window.ax.get_ylim())

        # Entfernen-Kreuze aktualisieren
        for i in range(int(self.radio_number.get())):
            if self.dropdown[i].get() == "Choose file ...":
                self.remove_x[i].place_forget()
            else:
                self.remove_x[i].place(x=self.wpos['x1'], y=dropdown_y(self.wpos['y1'], self.wpos['ystep'], i), height=self.wpos['h1'], width=self.wpos['h1'], anchor='w')

    def on_close(self):
        with open(GUINAME + ".conf", "w") as conf:
            conf.write(self.root.geometry() + "\n")
            conf.write(self.path)
        self.root.destroy()









# =======================================================================================================
# =======================================================================================================
#        CLASS PLOTWINDOW
# =======================================================================================================
# =======================================================================================================
        
class Plotwindow():
    def __init__(self, root, size):
        self.root = root
        self.fontsize = self.root.fontsize+2
        plt.rcParams['font.size'] = str(self.fontsize)
        self.fig = mpl.figure.Figure(size, constrained_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = tkagg.FigureCanvasTkAgg(self.fig, master=root.plot_frame)
        toolbar = tkagg.NavigationToolbar2Tk(self.canvas, self.root.root)
        toolbar.update()
        self.canvas.get_tk_widget().pack()
        cid = self.fig.canvas.mpl_connect('button_release_event', self.mouse_release)

    def mouse_release(self, event):
        self.root.replot_leave_axes()

    def plot_simple(self, x, y):
        self.ax.plot(x,y)
        self.canvas.draw()
        
    def plot_comments(self, cmt, xlims, ylims):
        cmt_x = cmt[0]
        cmt_y = cmt[1]
        cmt_diff = cmt[2]
        cmt_text = cmt[3]
        max_y_diff = 0
        for i in range(len(cmt_text)):
            if cmt_x[i] > self.ax.get_xlim()[0] and cmt_x[i] < self.ax.get_xlim()[1] \
            and cmt_y[i] > self.ax.get_ylim()[0] and cmt_y[i] < self.ax.get_ylim()[1]:
                if abs(cmt_diff[i]) > max_y_diff:
                    max_y_diff = abs(cmt_diff[i])
        for i in range(len(cmt_text)):
            if cmt_x[i] > self.ax.get_xlim()[0] and cmt_x[i] < self.ax.get_xlim()[1] \
            and cmt_y[i] > self.ax.get_ylim()[0] and cmt_y[i] < self.ax.get_ylim()[1]:
                if self.root.check_style.get():
                    this_colorfactor = powerscale_between(abs(cmt_diff[i]) / max_y_diff, 0.7, 0, 0.7)
                    this_size = powerscale_between(abs(cmt_diff[i]) / max_y_diff, self.fontsize*0.6, self.fontsize, 0.7)
                else:
                    this_colorfactor = 0
                    this_size = self.fontsize
                this_color = this_colorfactor * np.array([1, 1, 1])
                if self.root.check_comments.get() and self.root.check_betrag.get():
                    this_label = str(cmt_text[i]) + " (" + '{0:.0f}'.format(abs(cmt_diff[i])) + ")"
                elif self.root.check_comments.get():
                    this_label = str(cmt_text[i])
                else:
                    this_label = '{0:.0f}'.format(abs(cmt_diff[i]))
                if cmt_diff[i] > 0:
                    self.ax.text(cmt_x[i], cmt_y[i], this_label + "–", fontsize = str(this_size), va = 'center', ha = 'right', color = this_color, family='Arial Narrow')
                else:
                    self.ax.text(cmt_x[i], cmt_y[i], "–" + this_label, fontsize = str(this_size), va = 'center', ha = 'left', color = this_color, family='Arial Narrow')
        self.canvas.draw()

    def stackplot(self, alldata, color_input, xlims, ylims, dx_left, dx_right):
        
        linenumber = len(alldata)
        x_all = []
        y_all = []

        # load and edit
        for i in range(linenumber):
            data = sort_array(alldata[i])
            if self.root.check_distribute.get():
                data = distribute_x_at_same_day(data)
            if self.root.check_horizontal.get():
                data = repeat_y_in_between(data)
            x_all.append(data[:,0])
            y_all.append(data[:,1])

        # set axes if not empty
        if dx_left is not None and dx_right is not None:
            if xlims[1] + dx_right > xlims[0] + dx_left + 1.5/12:
                xlim = [xlims[0] + dx_left, xlims[1] + dx_right]
            else:
                xlim = xlims
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
        set_labels_and_ticks(self.ax, xlim, self.fontsize, self.root.radio_ylim.get(), self.root.check_xaxis.get(), self.root.check_yaxis.get())

        # limits
        if not xlim[0] == -1:
            self.ax.set_xlim(left=xlim[0])
        if not xlim[1] == -1:
            self.ax.set_xlim(right=xlim[1])
        if not ylim[0] == -1:
            self.ax.set_ylim(bottom=ylim[0])
        if not ylim[1] == -1:
            self.ax.set_ylim(top=ylim[1])

        # mouse position
        self.ax.format_coord=format_coord
        
        # title
        if self.root.check_yaxis.get():
            try:
                dt_end = float_year_to_datetime(x_all[0][-1])
                float_year_jahreserster = datetime_to_float_year(datetime.date(dt_end.year, 1, 1))
                float_year_monatserster = datetime_to_float_year(datetime.date(dt_end.year, dt_end.month, 1))
                diff_jahreserster = [np.abs(x - float_year_jahreserster) for x in x_all[0]]
                diff_monatserster = [np.abs(x - float_year_monatserster) for x in x_all[0]]
                if min(diff_jahreserster) < 3*1/365 and min(diff_monatserster) < 3*1/365:
                    index_jahreserster = np.argmin(diff_jahreserster)
                    index_monatserster = np.argmin(diff_monatserster)
                    self.root.root.title(GUINAME
                                         + " | " + "{:.2f}".format(y_all[0][index_jahreserster])
                                         + " > " + "{:.2f}".format(y_all[0][index_monatserster])
                                         + " > " + "{:.2f}".format(y_all[0][-2]))
                else:
                    self.root.root.title(GUINAME
                                         + " | " + "{:.2f}".format(y_all[0][-2]))
            except:
                pass
        else:
            self.root.root.title(GUINAME)

        self.canvas.draw()

    def clearplot(self):
        self.ax.cla()
        self.canvas.draw()






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
