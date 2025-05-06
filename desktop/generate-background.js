// A simple script to generate a basic background.png file for the DMG installer
const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

// Create a 540x380 background
const width = 540;
const height = 380;
const canvas = createCanvas(width, height);
const ctx = canvas.getContext('2d');

// Fill the background with a gradient
const gradient = ctx.createLinearGradient(0, 0, width, height);
gradient.addColorStop(0, '#f5f5f5');
gradient.addColorStop(1, '#e0e0e0');
ctx.fillStyle = gradient;
ctx.fillRect(0, 0, width, height);

// Add some subtle pattern
ctx.fillStyle = 'rgba(66, 133, 244, 0.03)';
for (let i = 0; i < width; i += 20) {
  for (let j = 0; j < height; j += 20) {
    ctx.beginPath();
    ctx.arc(i, j, 2, 0, Math.PI * 2);
    ctx.fill();
  }
}

// Add application name
ctx.font = 'bold 24px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
ctx.fillStyle = '#4285F4';
ctx.textAlign = 'center';
ctx.textBaseline = 'middle';
ctx.fillText('Smart Inbox Cleaner', width / 2, 50);

// Add instructions text
ctx.font = '14px -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif';
ctx.fillStyle = '#666';
ctx.fillText('Drag the application to the Applications folder to install', width / 2, height - 40);

// Draw arrows pointing to the icons
ctx.beginPath();
ctx.moveTo(270, 220);
ctx.lineTo(240, 220);
ctx.lineTo(255, 210);
ctx.moveTo(240, 220);
ctx.lineTo(255, 230);
ctx.strokeStyle = '#4285F4';
ctx.lineWidth = 2;
ctx.stroke();

// Save the generated image
const outputFile = path.join(__dirname, 'build', 'background.png');
const buffer = canvas.toBuffer('image/png');
fs.writeFileSync(outputFile, buffer);

console.log(`DMG background generated at: ${outputFile}`); 