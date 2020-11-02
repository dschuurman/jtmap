# Connect to WSJTX and query QRZ.com to display contact details
# (C) 2020 Derek Schuurman
# License: GNU General Public License (GPL) v3
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import logging
import sys, os
import urllib.request
import json
import socket
import adif_io
import geopy.distance
import configparser
import datetime, time
import cartopy.crs as ccrs
from cartopy.feature.nightshade import Nightshade
import cartopy.feature
import matplotlib.pyplot as plt
import tkinter as tk
from select import select

VERSION=0.9

def get_latitude_longitude(gridsquare):
    ''' Converts four character gridsquare to latitude,longitude
    '''
    longitude = -180.0 + (ord(gridsquare[0]) - ord('A')) * 20.0
    latitude = -90.0 + (ord(gridsquare[1]) - ord('A')) * 10.0
    longitude += float(gridsquare[2]) * 2.0
    latitude += float(gridsquare[3])

    return latitude, longitude

# Read other constants from configuration file
# This file is assumed to be in the same folder as the program
conf = configparser.ConfigParser()
conf.read('jtmap.conf')

# If localhost is selected, then bind to local loopback only
if conf.getboolean('JTmap','LOCALHOST'):
    UDP_IP = "127.0.0.1"
else:
    UDP_IP = "0.0.0.0"   # otherwise bind to all local ports
UDP_PORT = conf.getint('jtmap','PORT')

# TO-DO: check if these are present, if not use gridsquare.
MY_LATITUDE = conf.getfloat('jtmap','LATITUDE')
MY_LONGITUDE = conf.getfloat('jtmap','LONGITUDE')
WEB_LOOKUP = conf.get('jtmap','WEB_LOOKUP')
logging.info('Using lookup database: {}'.format(WEB_LOOKUP))
LOGGING = conf.get('jtmap','LOG_LEVEL')
DISTANCE_UNITS = conf.get('jtmap','DISTANCE_UNITS')

# Set logging level
if LOGGING == 'debug':
    logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)
elif LOGGING == 'info':
    logging.basicConfig(stream=sys.stderr, level=logging.INFO)
else:
    logging.basicConfig(stream=sys.stderr, level=logging.ERROR)

# Disable annoying font messages
logging.getLogger('matplotlib.font_manager').disabled = True

# Create UDP server socket for listening to WSJT-X
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM) 
server.bind((UDP_IP, UDP_PORT))
server.setblocking(False)
logging.info('listening on {}:{}'.format(UDP_IP, UDP_PORT))

# main window with message and quit button
window = tk.Tk()
window.title("JTmap")
title = tk.Label(text="JTmap",font=("Arial Bold", 20))
title.pack()
info = tk.Label(text="by W8DCS version {:.2f}".format(VERSION),font=("Arial", 10))
info.pack()
status = tk.Label(text="Waiting for contacts from WSJT-X...",font=("Arial", 12))
status.pack()

# creating a button instance
button = tk.Button(master=window, text='Quit', command=lambda: os._exit(0))
button.pack(side=tk.BOTTOM)

while True:
    # Loop to wait for a UDP packet; service figure event loop while waiting
    while True:
        # Wait for packets
        # Note that tkinter and matplotlib prefer to run in the main thread
        # so use a timeout after 50ms and service any pending events
        ready = select([server],[],[],0.05)
        if ready[0]:
            data,addr = server.recvfrom(2048)  # buffer size is 2 kbytes
            logging.debug('Recv UDP: {}'.format(data))
            break
        # Service event loop on figure (if presemt)
        if len(plt.get_fignums()) != 0:
            fig.canvas.draw_idle()
            fig.canvas.flush_events()

        # Update tkinter GUI (run this periodically rather than using a blocking mainloop)
        window.update()

    # Proceed only if a QSO is completed (indicated in header)
    if data[11] != 0x0c:
        continue
    
    # Parse completed QSO and extract ADIF payload
    header = data[:16]
    adif = data[26:].decode('utf-8')
    logging.debug("WSJT-X header:", header)
    logging.debug("WSJT-X ADIF payload:", adif)

    # Parse ADIF data
    qsos, header =  adif_io.read_from_string(adif)
    qso = qsos[0]
    logging.info("ADIF data: {}\nADIF Header: {}\n".format(qsos, header))
    
    # Extract call from ADIF data
    callsign = qso['CALL']
    my_callsign = qso['STATION_CALLSIGN']
    gridsquare = qso['GRIDSQUARE']
    latitude, longitude = get_latitude_longitude(gridsquare)  # use the gridsquare to approximate latitude/longitude

    # Lookup callsign in an online database
    logging.info('Looking up: '+callsign)
    if WEB_LOOKUP == "callbook.info":
        response = urllib.request.urlopen('http://callook.info/{}/json'.format(callsign))
        json_data = response.read().decode("utf-8")
        logging.debug('JSON: ',json_data)
        contact = json.loads(json_data)
        if contact['status'] == 'INVALID':
            logging.info('callsign {} not found in {}.'.format(callsign,WEB_LOOKUP))
            name = None
        else:
            callsign = contact['current']['callsign']
            name = contact['name']
            qth = contact['address']['line2']
            gridsquare = contact['location']['gridsquare']
            latitude = float(contact['location']['latitude'])
            longitude = float(contact['location']['longitude'])
    elif WEB_LOOKUP == "hamdb.org":
        response = urllib.request.urlopen('http://api.hamdb.org/{}/json/JTmap'.format(callsign))
        json_data = response.read().decode("utf-8") 
        logging.debug('JSON:',json_data)
        contact = json.loads(json_data)
        if contact['hamdb']['callsign']['call'] == 'NOT_FOUND':
            logging.info('callsign {} not found in {}.'.format(callsign,WEB_LOOKUP))
            name = None

        else:  # Get contact details and a more accurate latitute/longitude
            callsign = contact['hamdb']['callsign']['call']
            name = contact['hamdb']['callsign']['fname'] + ' ' + contact['hamdb']['callsign']['name']
            qth = contact['hamdb']['callsign']['addr2'] + ', ' + contact['hamdb']['callsign']['state'] + ', ' + contact['hamdb']['callsign']['country']
            gridsquare = contact['hamdb']['callsign']['grid']
            latitude = float(contact['hamdb']['callsign']['lat'])
            longitude = float(contact['hamdb']['callsign']['lon'])

    logging.info('QSO completed!')
    logging.info('call: {}\nname: {}\nQTH: {}\nGridsquare: {}'.format(callsign,name,qth,gridsquare))

    # TO-DO: check units for distance between stations
    distance = geopy.distance.distance((latitude, longitude), (MY_LATITUDE,MY_LONGITUDE)).km
    logging.info("distance: {:.0f} km\n\n".format(distance))

    # Plot communication on a map

    # close the current plot and create a new figure
    plt.close()
    fig = plt.figure()
    fig.canvas.set_window_title('WSJT-X QSO confirmed')

    ax = plt.axes(projection=ccrs.PlateCarree())
    ax.set_global()

    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M") 
    ax.set_title('WSJT-X QSO confirmed on {}'.format(date))

    # Zoom in on region of interest on map
    ax.set_extent([min(longitude,MY_LONGITUDE)-5, max(longitude,MY_LONGITUDE)+5, min(latitude,MY_LATITUDE)-5, max(latitude,MY_LATITUDE)+5],crs=ccrs.PlateCarree())

    ax.add_feature(cartopy.feature.OCEAN)
    ax.add_feature(cartopy.feature.LAND, edgecolor='black')
    ax.add_feature(cartopy.feature.LAKES, edgecolor='black')
    ax.add_feature(Nightshade(datetime.datetime.utcnow(), alpha=0.2))

    # show contact details in the text box if it was found in database
    if name != None:
        contact_details = 'call: {}\nname: {}\n{}\ndistance: {:.0f} km'.format(callsign,name,qth,distance)
        plt.figtext(0.5, 0.00, contact_details, ha="center", fontsize=12, bbox={"facecolor":"white", 'edgecolor':'none', "alpha":0.5, "pad":5})

    at_x, at_y = ax.projection.transform_point(MY_LONGITUDE, MY_LATITUDE, src_crs=ccrs.PlateCarree())
    plt.annotate(my_callsign, xy=(at_x, at_y), color='green', ha='left', fontweight='bold')

    at_x, at_y = ax.projection.transform_point(longitude, latitude, src_crs=ccrs.PlateCarree())
    plt.annotate(callsign, xy=(at_x, at_y), color='green', ha='right', fontweight='bold')

    plt.plot([MY_LONGITUDE, longitude], [MY_LATITUDE, latitude],
         color='blue', linewidth=2, marker='o', transform=ccrs.Geodetic())

    # This will draw and fit things nicely in the window
    # Note: tight_layout() must be called after draw()!
    fig.canvas.draw()
    fig.tight_layout()
 
    #plt.ioff()   # Turning interactive mode off
    plt.show(block = False)

    #plt.pause(3)

