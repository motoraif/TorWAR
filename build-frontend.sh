#!/bin/bash
cd frontend
npm install
npm run build
mkdir -p ../static/dist
cp -r dist/* ../static/dist/
