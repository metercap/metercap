#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Ausfuehrender User muss berechtigt sein:
# sudo usermod -a -G dialout $USER
#
import time
import datetime
import sys
import os
import cgi, cgitb
import serial

class CgiSerial:
    
    # Initialize
    def __init__(self):
        self.port = 'ttyUSB0'                   # Port des seriellen Anschlusses (ohne /dev/)
        self.baud_handshake = 0                 # Baudrate für den Handshake
        self.baud_data = 9600                   # (Default) Baudrate für die Datenübertragung
        self.databits = serial.SEVENBITS        # Daten-Bits
        self.stopbits = serial.STOPBITS_ONE     # Stop-Bits
        self.parity = serial.PARITY_EVEN        # Parity
        self.flowcontrol = None                 # Flow Control
        self.pull_sequence_hex = None           # Pull Sequenz (Hexadezimal)
        self.send_pull_sleep_after = 0          # Sleep nach Absetzen der Pullsequenz
        self.ack_sequence_hex = None            # ACK Sequenz (Hexadezimal)
        self.change_baud_sleep_before = 0       # Sleep vor Umschalten auf die Datenübertragung
        self.change_baud_sleep_after = 0        # Sleep nach Umschalten auf die Datenübertragung
        self.timeout = 10                       # Timeout zum Aufbau der seriellen Verbindung
        self.data_begin = '/'                   # Anfang des Datensatzes
        self.data_end = '!'                     # Ende des Datensatzes
        self.data_raw = False                   # Übertragung der Rohdaten
        self.close_serial_sleep_after = 0       # Sleep nach Beendigung der seriellen Verbindung
        self.readdata = ''                      # Gelesene Daten
        self.output = ''                        # Ausgabe Daten
        self.ser = None                         # Objekt Serielle Verbindung
        self.baud = 0                           # Aktuelle Baudrate der seriellen Verbindung
        self.readstart = False                  # Startpunkt der auszulesenden Daten erreicht
        self.readstop = False                   # Stoppunkt der auszulesenden Daten erreicht
        self.outputhtml = False                 # Ausgabe HTML (sonst Text ohne HTML Tags)
        self.lineflush = False                  # Zeilenweise Ausgabe (sonst kompletter Block)
        self.cgimode = False                    # Wird Script als CGI ausgeführt?
        self.energy_consumption = None          # Ausgelesener Wert Energie Verbrauch kWh
        self.energy_production = None           # Ausgelesener Wert Energie Produktion kWh
        self.power = None
        pass

    # Delete des CgiSerial Obejekts
    def __del__(self):
        if self.ser:
            self.CloseSerial()
        pass

    # Serielle Verbindung aufbauen
    def OpenSerial(self):
        try:
            self.ser = serial.Serial(
                port = '/dev/' + self.port,
                baudrate = self.baud_data,
                parity = self.parity,
                stopbits = self.stopbits,
                bytesize = self.databits,
                timeout = self.timeout
            )
            #self.output += "OpenSerial() successful"
            #self.FlushOutput()
        except:
            self.output += "Error: OpenSerial() failed"
            self.FlushOutput()
            sys.exit()
        pass
    
    # Handshake durchfuehren
    def SerialHandshake(self):
        self.ser.baudrate = self.baud_handshake
        # Flush Output / Input
        self.ser.flushOutput()
        self.ser.flushInput()
        # Pull Sequence
        if len(self.pull_sequence_hex) > 0:
            pull_sequence_decoded = self.pull_sequence_hex.decode("hex")
            self.ser.write(pull_sequence_decoded)
            while 1 and self.readstop == False:
                line = self.ser.readline().strip()
                self.readdata += str(line) + "\n"
                self.output += str(line) + "\n"
                if self.lineflush:
                    self.FlushOutput()
                if len(line) > 3:
                    self.readstop = True
            time.sleep(self.send_pull_sleep_after)
        # ACK Sequence
        if len(self.ack_sequence_hex) > 0:
            ack_sequence_decoded = self.ack_sequence_hex.decode("hex")
            self.readstart = True
            self.readstop = False
            self.ser.write(ack_sequence_decoded)
            if self.change_baud_sleep_before > 0:
                time.sleep(self.change_baud_sleep_before)
            # Baudrate für Nutzdaten setzen
            self.ser.baudrate = self.baud_data
            if self.change_baud_sleep_after > 0:
                time.sleep(self.change_baud_sleep_after)
        pass

    # Serielle Verbindung schliessen
    def CloseSerial(self):
        # Serielle Verbindung flushen
        self.ser.flushOutput()
        self.ser.flushInput()
        # Serielle Verbindung schliessen
        self.ser.close()
        try:
            sys.stdout.flush()
            sys.stdout.close()
        except:
            pass
        try:
            sys.stderr.flush()
            sys.stderr.close()
        except:
            pass
        time.sleep(self.close_serial_sleep_after)
        pass

    # Daten auslesen
    def GetData(self):
        # Nutzdaten laden
        data_begin_len = len(self.data_begin)
        # Output / Input Buffer Flush
        if self.baud_handshake == 0:
            self.ser.flushOutput()
            self.ser.flushInput()
        # Endlosschleife bis Stopsequenz erreicht
        while True and self.readstop == False:
            # Eine Zeile von der seriellen Verbindung lesen
            line = self.ser.readline().decode("utf-8").strip()
            # Im DataRaw Modus werden alle Start/Stopppunkte ignoriert: endloses Lesen
            if self.data_raw == True:
                self.readdata += str(line) + "\n"
                self.output += str(line) + "\n"
                if self.lineflush:
                    self.FlushOutput()
            else:
                # Sofern Startpunkt noch nicht erreicht
                if not self.readstart:
                    # Wenn Eröffnungssequenz gefunden wurde: Lese Daten
                    if line[:data_begin_len] == self.data_begin:
                        self.readstart = True
                        self.readdata += str(line) + "\n"
                        self.output += str(line) + "\n"
                        if self.lineflush:
                            self.FlushOutput()
                else:
                    # Startpunkt wurde bereits erreicht: Lese Daten und prüfe auf Stoppunkt
                    self.readdata += str(line) + "\n"
                    self.output += str(line) + "\n"
                    if line == self.data_end:
                        self.readstop = True
                    if self.lineflush:
                        self.FlushOutput()
        pass

    def OutputToHtml(self):
        # HTML Zeilenumbruch hinzufügen
        #self.output.replace("\n", "<br>\n")
        pass

    def SendHTTPHeader(self):
        # HTTP Header senden
        print('Content-Type: text/html')
        print('Cache-Control: no-cache, no-store, must-revalidate')
        print('Pragma: no-cache')
        print('Expires: 0')
        print('')

    def FlushOutput(self):
        if self.outputhtml == True:
            self.OutputToHtml()
        print(str(self.output.strip()))
        sys.stdout.flush()
        self.output = ''
        pass

    def CompactOutput(self):
        print('A+*' + self.energy_consumption)
        print('A-*' + self.energy_production)
        print('P*' + self.power)
        sys.stdout.flush()
        pass
    
    def ParseSML(self):
        self.energy_consumption = None
        self.energy_production = None
        self.power = None
        line_array = self.readdata.split("\n")
        for line in line_array:
            record_array = line.split('(')
            if ':1.8.0' in record_array[0] or record_array[0] == '1.8.0':
                self.energy_consumption = str(float(record_array[1].split('*')[0]))
            if ':2.8.0' in record_array[0] or record_array[0] == '2.8.0':
                self.energy_production = str(float(record_array[1].split('*')[0]))
            if ':1.7.0' in record_array[0] or ':16.7.0' in record_array[0] or record_array[0] == '16.7':
                self.power = str(float(record_array[1].split('*')[0]))
        pass

    def WriteToDisk(self):
        path_currentdir = os.path.realpath(__file__)
        today = datetime.date.today()
        year = today.strftime("%Y")
        month = today.strftime("%m")
        day = today.strftime("%d")
        if not os.path.exists(path_currentdir + '/data/' + year):
            os.mkdir(path_currentdir + '/data/' + year)
        if not os.path.exists(path_currentdir + '/data/' + year + '/' + month):
            os.mkdir(path_currentdir + '/data/' + year + '/' + month)
        datafile = path_currentdir + '/data/' + year + '/' + month + '/' + day + '.txt'
        line_array = self.readdata.split("\n")
        with open(datafile, 'a') as f:
            for line in line_array:
                f.write("%s\n" % line)
        pass


    def ExecuteRequest(self):
        # HTTP Header senden
        if self.outputhtml:
            self.SendHTTPHeader()
        self.OpenSerial()
        # Durchführen des Handshakes (falls Handshake Baudrate gesetzt)
        if self.baud_handshake:
            self.SerialHandshake()
        self.GetData()
        
    
# cgiserial Instanz anlegen und initialisieren
cgiserial = CgiSerial()
cgiserial.outputhtml = True
# Ausführen der Datenabfrage
cgiserial.ExecuteRequest()
# Ausgabe der Daten
#cgiserial.FlushOutput()
cgiserial.ParseSML()
cgiserial.CompactOutput()

