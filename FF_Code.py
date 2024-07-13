# -*- coding: utf-8 -*-
# Python for Test and Measurement
# Requires VISA installed on controlling PC, 'http://pyvisa.sourceforge.net/pyvisa/'
# Keysight IO Libraries 18.1.22x 32-Bit Keysight VISA (as primary)
# Anaconda Python 4.4.0 32 bit
# pyvisa 3.6.x
# Keysight N9952A 50GHz FieldFox Handheld portable combination analyzer 
# running A.10.17 application code
##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
## Copyright © 2018 Keysight Technologies Inc. All rights reserved.
##
## You have a royalty-free right to use, modify, reproduce and distribute this
## example / files (and/or any modified version) in any way you find useful, provided
## that you agree that Keysight has no warranty, obligations or liability for any
## Sample Application / Files.
##
##"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Example Description: 
 
# A python sample program utilizing pyvisa to connect and control a Keysight FieldFox 
# Family Combination Analyzer. 
# 
# The application performs the following:
 
# Imports the pyvisa libraries and operating system dependent functionality;
# Establishes a visa resource manager;
# Opens a connection to the FieldFox based on the instrument's VISA address as
# acquired via Keysight Connection Expert
# Sets the visa time out (increasing the timeout as compared to the default). 
# Clears the event status register and thus clears the error queue;
# Defines an error check function and checks the system error queue;
# Presets the FieldFox unit; performs a *IDN?, sets the analyzer to Spectrum Analyzer 
# mode, 
# then queries the number of points, start frequency and stop frequency.
# Executes a synchronized single sweep. 
# Queries the spectrum analyzer trace data, builds a linear array to compute the 
# stimulus array, 
# and plots the stimulus - response data as an X-Y trace. 
# 
# Import the visa, csv, and math libraries 
import pyvisa as visa
import os as os
import csv
import time
import math as m
# The numpy is imported as it is helpful for a linear ramp creation for the stimulus 
# array
import numpy as npStimulusArray
# import module for plotting
import matplotlib.pyplot as stimulusResponsePlot
# A variable to control various events and testing during development. 
# by uncommenting the #debug True line, debug will occur, for efficiency, during 
# development. 
debug = True
#debug = True
print("Debug flag set to " + str(debug))
 
# Set variables for ease of change - assumes 'debug is true. 
# If debug is set to false then Spectrum Analyzer preset defaults for
# start frequency, stop frequency and number of points are utilized. 
numPoints = 401
startFreq = 9950000000
stopFreq = 10050000000
# Number of sweeps to perform
num_sweeps = 50  # Adjust as needed
# Open a VISA resource manager pointing to the installation folder for the Keysight 
# Visa libraries. 
rm = visa.ResourceManager() 
 
# Based on the resource manager, open a session to a specific VISA resource string as 
# provided via
# Keysight Connection Expert
# ALTER LINE BELOW - Updated VISA resource string to match your specific configuration
myFieldFox = rm.open_resource("TCPIP0::169.254.15.18::inst0::INSTR") 
#Set Timeout - 10 seconds
myFieldFox.timeout = 10000
# Clear the event status registers and empty the error queue
myFieldFox.write("*CLS")
# Query identification string *IDN? 
myFieldFox.write("*IDN?")
print (myFieldFox.read())
# Define Error Check Function
def Errcheck():
 myError = []
 ErrorList = myFieldFox.query("SYST:ERR?").split(',')
 Error = ErrorList[0]
 if int(Error) == 0:
    print ("+0, No Error!")
 else:
    while int(Error)!=0:
         print ("Error #: " + ErrorList[0])
         print ("Error Description: " + ErrorList[1])
         myError.append(ErrorList[0])
         myError.append(ErrorList[1])
         ErrorList = myFieldFox.query("SYST:ERR?").split(',')
         Error = ErrorList[0]
         myError = list(myError)
         return myError
 
# Call and print error check results 
print (Errcheck())
# Preset the FieldFox and wait for operation complete via the *OPC?, i.e. 
# the operation complete query. 
myFieldFox.write("SYST:PRES;*OPC?")
print ("Preset complete, *OPC? returned : " + myFieldFox.read())
# Set mode to Spectrum Analyzer and wait for operation complete via the *OPC?, i.e. 
# the operation complete query.
myFieldFox.write("INST:SEL 'SA';*OPC?")
myFieldFox.read()
# If debug is true then user setting of start frequency, stop frequency and number of 
# points
if debug:
 myFieldFox.write("SENS:SWE:POIN " + str(numPoints))
 myFieldFox.write("SENS:FREQ:START " + str(startFreq))
 myFieldFox.write("SENS:FREQ:STOP " + str(stopFreq))
# Determine, i.e. query, number of points in trace for ASCII transfer - query
myFieldFox.write("SENS:SWE:POIN?")
numPoints = myFieldFox.read()
print ("Number of trace points " + numPoints)
# Determine, i.e. query, start and stop frequencies, i.e. stimulus begin and end points
myFieldFox.write("SENS:FREQ:START?")
startFreq = myFieldFox.read()
myFieldFox.write("SENS:FREQ:STOP?")
stopFreq = myFieldFox.read()
print ("FieldFox start frequency = " + startFreq + " stop frequency = " + stopFreq)
# Set trigger mode to hold for trigger synchronization
myFieldFox.write("INIT:CONT OFF;*OPC?")
myFieldFox.read()
# Use of Python numpy import to comupte linear step size of stimulus array
# based on query of the start frequency - stop frequency and number of points. 
# 'Other' analyzers support a SCPI "SENSe:X?" query which will provide the stimulus
# array as a SCPI query. 
stimulusArray = npStimulusArray.linspace(float(startFreq),float(stopFreq),int(numPoints)).tolist()
print (stimulusArray)
# Initialize all lists used for grabbing data
ff_SA_Trace_Data_Array = []
reltime = []
formatted = []
# Set the number of sweeps performed in a single trigger to the number of sweeps specfied
# by 'num_sweeps'
myFieldFox.write("SENS:SWE:COUN " + str(num_sweeps))
# Assert a single trigger and wait for trigger complete via *OPC? output of a 1
myFieldFox.write("INIT:IMM;*OPC?")
print ("Single Trigger complete, *OPC? returned : " + myFieldFox.read())
# query the amount of sweeps performed by VNA and then read amount to ensure congruity
myFieldFox.write("CALC:DATA:NSW:COUN?")
count = myFieldFox.read()
# Query the amount of time the trigger took to perform ******NEEDS MORE VERIFICATION*******
myFieldFox.write("SENS:SWE:TIME?")
time_total = float(myFieldFox.read())
print(count)
# Query the FieldFox response data for each sweep specified by 'num_sweeps'
for j in range(num_sweeps):
   myFieldFox.write("CALC:DATA:NSW? SDAT," + str(num_sweeps - j))
   ff_SA_Trace_Data = myFieldFox.read()
   ff_SA_Trace_Data_Array.append(list(map(float,ff_SA_Trace_Data.split(","))))
print (ff_SA_Trace_Data_Array[1]) # This is one long comma separated string list of 
# values. Each point is represented by a complex number with a real and imaginary part.
# Calculate change in time between each sweep
dt = time_total / num_sweeps
reltime = []
for k in range(num_sweeps):
# Make a list of time of each sweep performed   
   reltime.append(k * dt)
   for i in range(0,len(ff_SA_Trace_Data_Array[k]),2):
# Change data from complex number to a dB reading
      formatted.append(20 * m.log10(m.sqrt(ff_SA_Trace_Data_Array[k][i]**2 + ff_SA_Trace_Data_Array[k][i+1]**2)))
   ff_SA_Trace_Data_Array[k] = formatted
   formatted = []
# Use split to turn long string to an array of values,map and float to convert each value
# from string to float, and list turn the array of values into a list.

# Now plot the x - y data
maxResponseVal = max(ff_SA_Trace_Data_Array)
minResponseVal = min(ff_SA_Trace_Data_Array)
#if debug:
#print ("Max value = " + maxResponseVal + " Min Value = " + minResponseVal)

stimulusResponsePlot.title ("Keysight FieldFox Spectrum Trace Data via Python - PyVisa - SCPI")
stimulusResponsePlot.xlabel("Frequency")
stimulusResponsePlot.ylabel("Amplitude (dBm)")
stimulusResponsePlot.plot(stimulusArray,ff_SA_Trace_Data_Array[num_sweeps-1])
stimulusResponsePlot.autoscale(True, True, True) 
stimulusResponsePlot.show()
filename = 'multi_set_spectrum_data.csv'
with open(filename, 'w', newline='') as csvfile:
   writer = csv.writer(csvfile)

# Write header for frequency columns
   header_row = ['Frequency (Hz)']
   for set_number in range(0, num_sweeps):
      header_row.append(f'Amplitude (dB) - Set {set_number}')
   writer.writerow(header_row)
# Write frequency of each point
   writer.writerow(stimulusArray)
# Write dB reading of each point for each sweep with the sweeps time of performance.
   for i in range(0,num_sweeps):
      ff_SA_Trace_Data_Array[i].insert(0,reltime[i])
      writer.writerow(ff_SA_Trace_Data_Array[i])
# Return the FieldFox back to free run trigger mode
myFieldFox.write("INIT:CONT ON")
# Send a corrupt SCPI command end of application as a debug test
if debug:
 myFieldFox.write("INIT:CONT OOOOOOOOOO")
# Call the ErrCheck function and ensure no errors occurred between start of program
# (first Errcheck() call and end of program (last Errcheck() call. 
print (Errcheck())
# On exit clean a few items up.
myFieldFox.clear()
myFieldFox.close()