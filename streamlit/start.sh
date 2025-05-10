#!/bin/bash

# Start cron
cron

# Start Streamlit in the foreground
exec streamlit run /streamlit/Home.py --server.port="${SERVER_PORT}"
