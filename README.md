# JTmap
A program that listens for information sent from [WSJT-X](http://physics.princeton.edu/pulsar/K1JT/wsjtx.html)
and displays a friendly map with additional information after each contact is confirmed.

## Installation
The program requires python ver. 3.x. Before running the program a few dependencies need to be installed.
Here are instructions for installing these dependencies on Windows/OSX/Linux:

---
### For Linux

Python version 3.x is required (tested using Python 3.8.x under Ubuntu 20.04).
To install dependencies, type the following in a terminal:

```
sudo apt install libatlas-base-dev python3-cartopy
pip3 install adif_io geopy matplotlib scipy
```

---
### For OSX

Python ver. 3.x is required. To install dependencies, type the following 
in a terminal (assuming you are using the Homebrew package manager):

```
pip3 install adif_io geopy matplotlib scipy
brew install proj geos
pip3 install cartopy
pip3 install --upgrade certificates
```

---
### For Windows

*NOTE: Unfortunately, it seems the cartopy package has had some issues installing on Windows
which will prevent JTmap from working with Windows until this is resolved... 
However, it may be possible to install these dependencies using Anaconda (not tested).*

First, download and install Python ver. 3.x.
Be sure to click "Add Python to PATH" during install so it can be
easily run in a terminal window.

Open a terminal window and at the command prompt, type the following:

`pip3 install adif_io geopy matplotlib scipy cartopy`

---

### Configuring WSJT-X

Configure WSJT-X so that the UDP server is set to the IP address where JTmap
is running (if it's the same machine, use the default which is the local loopback interface: 127.0.0.1).
Launch JTmap and start WSJT-X then wait for contacts to be displayed in a pop-up
window showing a map of the contact.


### Downloading and running

To download the program folder from guthub, use the following command line:

`git clone https://github.com/dschuurman/jtmap.git`

Next, enter the project folder and launch the program as follows:

```
cd jtmap
python3 jtmap.py
```

Note that `jtmap.py` and `jtmap.conf` should be placed in the same folder.
The `jtmap.conf` file contains configuration information that should be setup before
launching the program (if unsure, it should work "out of the box" using the defaults).

