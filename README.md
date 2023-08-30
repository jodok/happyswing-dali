# MQTT -> DALI bridge for happyswing on Raspberry Pi

## Raspberry Pi setup and prerequisites

- Flash Raspberry Pi OS Lite to SD card, using the Raspberry Pi Imager
  <https://www.raspberrypi.org/software/>

- On the SD card, create a file named `ssh` in the boot partition - this will
  enable SSH on the Raspberry Pi for headless setup

- On the SD card, create a file named `userconf` in the boot partition with the
  following content:

  ```bash
  pi:encyptedpassword
  ```

  where `pi` is the username (feel free to use any username) and
  `encryptedpassword` is the output of the following command:

  ```bash
  echo 'mypassword' | openssl passwd -6 -stdin
  ```

- Bonus tip: copy your public SSH key as one line in `~/.ssh/authorized_keys` to
  allow passwordless login (also helpful for VS Code remote SSH).

- ideally, configure the DHCP server to assign a static IP address to the
  Raspberry Pi based on its MAC address. In our case we use `192.168.1.252`.

- configure udev to allow access to the USB DALI bus gateway. Download the file
  <https://github.com/sde1000/python-dali/blob/master/examples/50-dali-hid.rules>
  and copy it to `/etc/udev/rules.d``. Reboot.

- Connect the USB DALI bus gateway to the Raspberry Pi. When running `sudo dmesg -T`
  you should see that the DALI device was connected.

- Install required packages:

  ```bash
  sudo apt update
  sudo apt-get install git python3-venv
  ```

## Install software enviroment

- To allow GitHub operations from the Raspberry Pi you want to use SSH agent
  forwarding. On your local machine, run `ssh-add` to add your SSH key to the
  agent. Then connect to the Raspberry Pi using `ssh -A pi@192.168.1.252`.

- Clone the GithHub repository and bootstrap it:

  ```bash
  cd
  git clone git@github.com:jodok/happyswing-dali.git --recurse-submodules
  cd happyswing-dali
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```

## Development

- The used library, <https://github.com/sde1000/python-dali> doesn't have a
  recent release, that's why it is included as a git submodule. To update it,
  run:

  ```bash
  git submodule update --remote
  ```

- It turned out to be very helpful to develop with the VSCode remote SSH
  extension. It's easy to connect if you already added your ssh keys as
  described above.

## Examples

- Simple example that lets the DALI devices blink a few times:
  <https://github.com/sde1000/python-dali/blob/master/examples/async-flash.py>

- Next steps: Instead of sending a broadcast like this:

  ```python
  await dev.send(RecallMaxLevel(Broadcast()))
  ```

  use this command to send the dim level for device `a1`:

  ```python
  await driver.send(DAPC(GearShort(1), 120))
  ```

  where `120` is the dim level. `255` is the maximum dim level for 100%.
  You can use any value down to the minimal physical dim-level. The
  physial minimum is device specific (e.g. 1% = 86).


## Auto start after boot

We use `systemd` to autostart the happyswing service after boot. 

First the `service` needs to be put in the right directory. 

```bash 
  sudo cp happyswing.service  /lib/systemd/system/happyswing.service
```

After that the service can be enabled with 

```bash 
  sudo systemctl daemon-reload
  sudo systemctl enable happyswing
  sudo systemctl start happyswing
```

Now the the service run automatcally when the Raspberry Pi started. 


To stop the service run 

```bash 
  sudo systemctl stop happyswing
```


To look at the logs of the service use 

```bash 
  journalctl -u happyswing
```




