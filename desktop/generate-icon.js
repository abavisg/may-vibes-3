// A simple script to generate a basic icon.png file
const fs = require('fs');
const path = require('path');
const { createCanvas } = require('canvas');

// Create a 512x512 icon
const size = 512;
const canvas = createCanvas(size, size);
const ctx = canvas.getContext('2d');

// Fill the background with Gmail-like red
ctx.fillStyle = '#DB4437';
ctx.fillRect(0, 0, size, size);

// Draw a white envelope shape
ctx.fillStyle = '#FFFFFF';
ctx.beginPath();

// Envelope shape
const margin = size * 0.15;
const width = size - (2 * margin);
const height = width * 0.75;
const x = margin;
const y = (size - height) / 2;

// Base rectangle
ctx.rect(x, y, width, height);

// Top part (envelope flap)
ctx.moveTo(x, y);
ctx.lineTo(x + (width / 2), y - (height * 0.2));
ctx.lineTo(x + width, y);

ctx.fill();

// Draw a lightning bolt or check mark to represent organization/sorting
ctx.fillStyle = '#4285F4'; // Gmail blue
ctx.beginPath();

// Simple check mark inside the envelope
const checkX = x + width * 0.3;
const checkY = y + height * 0.5;
const checkWidth = width * 0.4;
const checkHeight = height * 0.25;

ctx.lineWidth = size * 0.08;
ctx.strokeStyle = '#4285F4';
ctx.moveTo(checkX, checkY);
ctx.lineTo(checkX + checkWidth * 0.4, checkY + checkHeight);
ctx.lineTo(checkX + checkWidth, checkY - checkHeight * 0.5);
ctx.stroke();

// Save the generated image
const outputFile = path.join(__dirname, 'build', 'icon.png');
const buffer = canvas.toBuffer('image/png');
fs.writeFileSync(outputFile, buffer);

console.log(`Icon generated at: ${outputFile}`); 