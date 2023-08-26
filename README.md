Configure Raspberry: copy <https://github.com/sde1000/python-dali/blob/master/examples/50-dali-hid.rules> to /etc/udev/rules.d and reboot

# Install enviroment

ssh -A pi@192.168.1.254

git clone <git@github.com>:jodok/happyswing-dali.git --recurse-submodules

python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
