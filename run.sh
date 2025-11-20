#!/bin/bash
echo "Starting Smart Meeting Minutes API..."
uvicorn app:app --reload
