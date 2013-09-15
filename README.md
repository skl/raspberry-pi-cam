raspberry-pi-cam
================

# Configuration

Take a look through the variables at the top of the `picam.py` file and change them to your liking.

## Installation

To install simply clone the repository to your Raspberry Pi and set the `picam` init script to start on boot:

```
git clone https://github.com/skl/raspberry-pi-cam.git
sudo -s
cp raspberry-pi-cam/picam /etc/init.d
update-rc.d picam defaults
```

### Credits

Originally by user "brainflakes" of http://www.raspberrypi.org/phpBB3/viewtopic.php?f=43&amp;t=45235
