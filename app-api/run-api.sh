#!/bin/bash

echo "Starting the server..."
sudo uvicorn mainAPI:app --reload --host 0.0.0.0
