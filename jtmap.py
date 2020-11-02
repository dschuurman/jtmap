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
if conf.getboolean('jtmap','LOCALHOST'):
    UDP_IP = "127.0.0.1"
else:
    UDP_IP = "0.0.0.0"   # otherwise bind to all local ports
UDP_PORT = conf.getint('jtmap','PORT')

# Use latitude/longitude of present, otherwise use gridsquare reported in WSJT-X
if conf.has_option('jtmap','LATITUDE'):
    my_latitude = conf.getfloat('jtmap','LATITUDE')
else:
    my_latitude = None
if conf.has_option('jtmap','LONGITUDE'):
    my_longitude = conf.getfloat('jtmap','LONGITUDE')
else:
    my_longitude = None
WEB_LOOKUP = conf.get('jtmap','WEB_LOOKUP')
logging.info('Using lookup database: {}'.format(WEB_LOOKUP))
LOGGING = conf.get('jtmap','LOG_LEVEL')
if conf.has_option('jtmap','DISTANCE_UNITS'):
    DISTANCE_UNITS = conf.get('jtmap','DISTANCE_UNITS')
else:
    DISTANCE_UNITS = 'miles'

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

    # Proceed only if a QSO is completed (indicated by byte in header)
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
    
    # If no home station latitude/longitude was specified in conf file, 
    # use center of my_gridsquare reported in WSJT-X to approximate my latitude/longitude
    if my_latitude == None:
        my_gridsquare = qso['MY_GRIDSQUARE']
        my_latitude, my_longitude = get_latitude_longitude(my_gridsquare)
        my_longitude += 0.5
        my_latitude += 1.0
    
    # Use the remote station's gridsquare to get approximate latitude/longitude
    # This will be refined if station is found in an online database.
    gridsquare = qso['GRIDSQUARE']
    # If no gridsquare was sent from WSJT-X, skip map and loop again (this should be rare)
    if gridsquare == '':
        continue
    latitude, longitude = get_latitude_longitude(gridsquare)

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
    ## TO-DO: Add other open online databases?

    logging.info('QSO completed!')
    logging.info('call: {}\nname: {}\nQTH: {}\nGridsquare: {}'.format(callsign,name,qth,gridsquare))

    # TO-DO: check units for distance between stations
    if DISTANCE_UNITS == 'kilometers' or DISTANCE_UNITS == 'km':
        distance = geopy.distance.distance((latitude, longitude), (my_latitude,my_longitude)).kilometers
        units = 'km'
        logging.info("distance: {:.0f} km\n\n".format(distance))
    else:
        distance = geopy.distance.distance((latitude, longitude), (my_latitude,my_longitude)).miles
        units = 'miles'
        logging.info("distance: {:.0f} miles\n\n".format(distance))

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
    ax.set_extent([min(longitude,my_longitude)-5, max(longitude,my_longitude)+5, min(latitude,my_latitude)-5, max(latitude,my_latitude)+5],crs=ccrs.PlateCarree())

    ax.add_feature(cartopy.feature.OCEAN)
    ax.add_feature(cartopy.feature.LAND, edgecolor='black')
    ax.add_feature(cartopy.feature.LAKES, edgecolor='black')
    ax.add_feature(Nightshade(datetime.datetime.utcnow(), alpha=0.2))

    # show contact details in the text box if it was found in database
    if name != None:
        contact_details = 'call: {}\nname: {}\n{}\ndistance: {:.0f} {}'.format(callsign,name,qth,distance,units)
        plt.figtext(0.5, 0.00, contact_details, ha="center", fontsize=12, bbox={"facecolor":"white", 'edgecolor':'none', "alpha":0.5, "pad":5})

    at_x, at_y = ax.projection.transform_point(my_longitude, my_latitude, src_crs=ccrs.PlateCarree())
    plt.annotate(my_callsign, xy=(at_x, at_y), color='green', ha='left', fontweight='bold')

    at_x, at_y = ax.projection.transform_point(longitude, latitude, src_crs=ccrs.PlateCarree())
    plt.annotate(callsign, xy=(at_x, at_y), color='green', ha='right', fontweight='bold')

    plt.plot([my_longitude, longitude], [my_latitude, latitude],
         color='blue', linewidth=2, marker='o', transform=ccrs.Geodetic())

    # This will draw and fit things nicely in the window
    # Note: tight_layout() must be called after draw()
    fig.canvas.draw()
    fig.tight_layout()
 
    #plt.ioff()   # Turning interactive mode off
    plt.show(block = False)
