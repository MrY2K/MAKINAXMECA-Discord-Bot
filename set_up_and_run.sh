# sudo dnf install python3-devel portaudio-devel

python -m venv bot-env

source bot-env/bin/activate

pip install -r requirements.txt

python3 bot.py