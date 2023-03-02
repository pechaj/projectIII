# Author: Jan Pecha

import struct
from tkinter import messagebox
from matplotlib.backends._backend_tk import NavigationToolbar2Tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from scipy import signal
from scipy.signal import lfilter
from scipy.signal import filtfilt
from scipy.signal import find_peaks
import pyspike as spk
import csv
from tkinter import *
from math import sin, pi

plt.style.use('seaborn-whitegrid')


class meaSignal:

    def __init__(self, length):
        self.length = length

    minsignal = 0
    spikecount = 0
    x = np.arange(0, 1320, 20).tolist()  # cas
    y = [0, 2.3, 2, -6, -12, -20, -30, -27, -20, -15, -6, 0, 2.5, 3.5, 2, 0] + [0] * 50  # amplituda

    xC = np.arange(0, 1320, 20).tolist()
    yC = [0, 2.3, 2, -6, -12, -20, -30, -27, -20, -15, -6, 0, 2.5, 3.5, 2, 0] + [0] * 50

    def signalload(self, path, length):
        meaSignal.x = []
        meaSignal.y = []

        def isfloat(num):
            try:
                float(num)
                return True
            except ValueError:
                return False

        with open(path, 'r') as data:
            for line in data:
                as_list = line.split("\t")

                try:
                    as_list[0] = float(as_list[0].replace(",", "."))
                    as_list[1] = float(as_list[1].replace(",", "."))
                except ValueError:
                    continue

                if isfloat(as_list[0]):

                    if as_list[2] == '':
                        break
                    meaSignal.x.append(as_list[0])
                    meaSignal.y.append(as_list[1])
                    if float(length) == as_list[0]:
                        break
        meaSignal.x = np.array(meaSignal.x)
        meaSignal.y = np.array(meaSignal.y)

        for i in meaSignal.y:
            if i < meaSignal.minsignal:
                meaSignal.minsignal = i


    def plot(self):

        fig = Figure(figsize=(5, 5))
        plot1 = fig.add_subplot(111)
        plot1.plot(meaSignal.x, meaSignal.y, '-b', label="Signal", linewidth=0.3)

        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack()

        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.update()
        canvas.get_tk_widget().pack()

        plot1.title("Graf signálu")
        plot1.xlabel("Time(ms)")
        plot1.ylabel("Signal(uV)")

    def butterWorthfilter(self, lowcut=150, highcut=4550):
        global peaks, filtered_data

        nyq = 16000 * 0.5

        low = lowcut / nyq
        high = highcut / nyq
        # Calculate coefficients
        [b, a] = signal.butter(4, Wn=low, btype='low', analog=False)
        [d, c] = signal.butter(4, Wn=high, btype='high', analog=False)

        # Filtered signal
        filtered_data = lfilter(b, a, meaSignal.y)
        filtered_data2 = filtfilt(d, c, meaSignal.y)

        peaks, locs = find_peaks(filtered_data, prominence=5)

        fig2 = Figure(figsize=(5, 5))
        plot2 = fig2.add_subplot(211)
        plot2.plot(meaSignal.x, filtered_data, '-g',
                       label='Butterworth filter(low)', linewidth=0.5)
        plot2.plot(meaSignal.x[peaks], filtered_data[peaks], 'rx')

        meaSignal.spikecount = len(peaks)

        canvas = FigureCanvasTkAgg(fig2, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(side=RIGHT)

        toolbar = NavigationToolbar2Tk(canvas, window)
        toolbar.update()
        canvas.get_tk_widget().pack(side=RIGHT)

        plot2.set_title("Lowpass")
        plot2.set_xlabel("Time(ms)")
        plot2.set_ylabel("Signal(uV)")
        plot2.set_xlim(0, meaSignal.x[-1])

        peaks2, locs2 = find_peaks(filtered_data2, prominence=2, height=1.3)
        plot3 = fig2.add_subplot(212)
        plot3.plot(meaSignal.x, filtered_data2, '-g',
                   label='Butterworth filter(high)', linewidth=0.5)
        plot3.plot(meaSignal.x[peaks2], filtered_data2[peaks2], 'rx')
        plot3.set_title("Highpass")
        plot3.set_xlabel("Time(ms)")
        plot3.set_ylabel("Signal(uV)")
        plot3.set_xlim(0, meaSignal.x[-1])
        plot3.set_ylim(-2, 2)

        fig2.suptitle("Comparison between lowpass and highpass Butterworth filter")
        fig2.tight_layout()

        plot2.show()
        plot3.show()


def info():
    global pop, filtered_data, peaks

    spike_train = []
    count = 0
    for i in filtered_data:
        if i == filtered_data[peaks[count]]:
            spike_train.append(1)
            count += 1
            if count == meaSignal.spikecount:
                break
        else:
            spike_train.append(0)

    spike_array = np.array(spike_train)
    spike_burst = []
    count2 = 0
    for i in spike_array:
        if i == 1:
            count3 = count2

            for j in spike_array[count2+1:count2+400]:

                if count3 >= len(meaSignal.x):
                    break
                if j == 1:
                    spike_burst.append([meaSignal.x[count2], meaSignal.x[count3]])
                    break
                count3 += 1
        count2 += 1

    sum = 0
    x = 0
    while x < len(spike_burst):
        sum += abs(spike_burst[x][0] - spike_burst[x][1])
        x += 1

    spike_burst_length = round(sum/len(spike_burst), 2)
    spike_burst_count_perminute = round(len(spike_burst) / (meaSignal.x[-1] / 60000), 2)

    pop = Toplevel(window)
    pop.title("Signal information")
    pop.geometry("600x550")
    pop.config(bg="grey")

    pop_label = Label(pop, text="Time [ms]: " + str(meaSignal.x[-1]) + "\nSpike count: " + str(meaSignal.spikecount)
                                + "\nLowest amplitude :" + str(round(meaSignal.minsignal, 2)) + " uV"
                                + "\nSpikes/s : " + str(round(meaSignal.spikecount / (meaSignal.x[-1] / 1000), 2))
                                + "\nFrequency of bursts/s: " + str(round(len(spike_burst)/(meaSignal.x[-1] / 1000), 2))
                                + "\nAverage length of bursts: " + str(spike_burst_length) + " ms"
                                + "\nSpike bursts/minute: " + str(spike_burst_count_perminute)
                                + "\nAverage time between APs in burst: " + str(spike_burst_length) + " ms",
                                bg="grey", fg="black")
    pop_label.pack(pady=10)
    my_frame = Frame(pop, bg="black")
    my_frame.pack(pady=5)
    fig, axs = plt.subplots(figsize=[6, 3])
    axs.vlines(meaSignal.x[peaks], 0, 1)

    canvas = FigureCanvasTkAgg(fig, master=pop)
    canvas.draw()
    canvas.get_tk_widget().pack()

    toolbar = NavigationToolbar2Tk(canvas, pop)
    toolbar.update()
    canvas.get_tk_widget().pack()

    axs.set_xlim([0, meaSignal.x[-1]])
    axs.set_xlabel('Time (ms)')

    axs.set_title('Neuronal Spike Times')

    plt.tight_layout()
    plt.show()

def click3():
    s.butterWorthfilter()
    Label(window, text="Butterworth filter applied!", bg="black", fg="white",
          font="none 15 bold") \
        .pack(side=TOP, pady=2)


def plot():
    fig = Figure(figsize=(6, 4))
    plot1 = fig.add_subplot(111)
    plot1.plot(meaSignal.x, meaSignal.y, '-b', label="Signal", linewidth=0.3)

    canvas = FigureCanvasTkAgg(fig, master=window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=LEFT, fill=BOTH)

    toolbar = NavigationToolbar2Tk(canvas, window)
    toolbar.update()
    canvas.get_tk_widget().pack(side=LEFT, fill=BOTH)

    plot1.set_title("Graph of loaded signal")
    plot1.set_xlabel("Time(ms)")
    plot1.set_ylabel("Signal(uV)")

    fig.tight_layout()
    plot1.show()


def click():
    entered_text = textentry.get()
    if not textentry.get():
        messagebox.showwarning(title="Error", message="User did not enter file destination! Try again")
    else:
        Label(window, text="Signal loaded successfully!", bg="black", fg="white",
              font="none 15 bold") \
            .pack(side=TOP, pady=2, fill=BOTH)#grid(row=3, column=0, sticky=W)

        butterworthBT = Button(window, text="Apply Butterworth filter", width=23, command=click3)
        butterworthBT.pack(side=TOP, pady=2)#grid(row=4, column=0, sticky=W)

        plotBT = Button(window, text="Plot", width=23, command=plot)
        plotBT.pack(side=TOP, pady=1)#grid(row=5, column=0, sticky=W)

        infoBT = Button(window, text="Signal information", width=23, command=info)
        infoBT.pack(side=TOP, pady=1)#grid(row=6, column=0, sticky=W)

        s.signalload(entered_text, '2000')


def _quit():
    window.quit()
    window.destroy()

# ---------------- main --------------------


window = Tk()
window.title("Neural signal processing")
window.configure(background="black")
window.geometry("900x700")

# Label:
Label(window, text="Enter absolute path to .txt file with signal coordinates:", bg="black", fg="white",
      font="none 12 bold") \
    .pack(side=TOP, pady=5)

# text entry box:
textentry = Entry(window, width=60, bg="white")
textentry.pack(side=TOP, pady=3)#grid(column=0, row=1, ipadx=2, pady=2)

# Button:
submit_button = Button(window, text="Submit", width=6, command=click)
submit_button.pack(side=TOP, pady=3)#grid(column=0, row=2, ipadx=5, pady=5)

exitBT = Button(master=window, text='Quit', width=5, command=_quit)
exitBT.pack(side=BOTTOM)

s = meaSignal(1)
window.mainloop()
# cesta k .txt: C:\Users\honzi\Desktop\Skola\ProjektI\MCD soubory\Data_set.txt
