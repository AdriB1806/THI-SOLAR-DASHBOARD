#!/bin/bash

# Git initialization script for THI PV Dashboard

echo "Initializing Git repository for THI PV Dashboard..."

# Initialize git repository
git init

# Add all files
git add .

# Initial commit
git commit -m "Initial commit: THI Photovoltaic Dashboard

- Streamlit-based dashboard matching THI PV design
- Real-time power monitoring with gauge display
- Daily production curve visualization
- Energy metrics and environmental impact tracking
- Live-only FTP data source integration (pvdaten/pv.csv)
- Local SQLite history storage (pv_data.db)
- Responsive layout with custom styling"

echo ""
echo "Repository initialized successfully!"
echo ""
echo "Next steps:"
echo "1. Add your THI logo as 'thi_logo.png' in the project directory"
echo "2. Create a new repository on GitHub under the 'shendi' account"
echo "3. Run these commands to push to GitHub:"
echo ""
echo "   git remote add origin https://github.com/shendi/thi-pv-dashboard.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "Dashboard is running at: http://localhost:8501"
