#!/bin/bash

# Change to the directory containing your script
cd /Users/monilnarang/Documents/Repos/Pickleball_Booking

# Activate virtual environment if you're using one
source /Users/monilnarang/Documents/Repos/Pickleball_Booking/venv/bin/activate

# Run the script
python3 /Users/monilnarang/Documents/Repos/Pickleball_Booking/court_book.py

# Log output
echo "Script executed at $(date)" >> /Users/monilnarang/Documents/Repos/Pickleball_Booking/booking.log