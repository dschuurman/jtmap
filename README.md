# jtmap
A program that listens for information sent from WSJT-X and shows a friendly map with information after each contact is confirmed.

## Installation
This program requires python ver. 3.x along with a few dependencies. 
Here are instructions for installing these dependencies on Win/OSX/Linux:

---
### For Linux

Python ver. 3.x is required. To install dependencies, 
type the following in a terminal:

```
sudo apt install libatlas-base-dev python3-cartopy
pip3 install adif_io geopy matplotlib scipy
```

---
### For OSX

Python ver. 3.x is required. To install dependencies, type the following 
in a terminal (assuming you are using the brew package manager):

```
pip3 install adif_io geopy matplotlib scipy
brew install proj geos
pip3 install cartopy
pip3 install --upgrade certificates
```

---
### For Windows

First, download Python ver. 3.x
Be sure to click "Add Python to PATH" during install so it can be
used easily run in a terminal window.

Open a terminal window and at the command prompt, type the following:

`pip3 install adif_io geopy matplotlib scipy`

*NOTE: Unfortunately, it seems cartopy has had some issues installing on Windows...
If this is the case, one could try installing these dependencies using Anaconda.*

---

## Setup

For all platforms ensure that jtmap.py and jtmap.conf are placed in the same folder.
The jtmap.conf file contains configuration information that you should setup before
launching the program (if unsure, it should work fine using the defaults).

Launch the program using python as 
follows:

`python3 jtmap.py`

Configure WSJT-X so that the UDP server is set to the IP address where JTmap
is running (if it's the same machine, use the local loopback interface: 127.0.0.1).
Launch JTmap and start WSJT-X and wait for contacts to be displayed in a pop-up
window showing a map of the contact.
