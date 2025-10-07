#! /bin/bash

# This script uses watchmedo to automatically restart the bot when Python files are modified.
# Use Only in development and testing.

source bot-env/bin/activate

watchmedo auto-restart \
  --directory=. \
  --pattern="*.py" \
  --recursive \
  -- python3 bot.py
