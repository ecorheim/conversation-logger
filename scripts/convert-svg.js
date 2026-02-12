const puppeteer = require('puppeteer');
const fs = require('fs');
const path = require('path');

(async () => {
  const svgPath = path.join(__dirname, '../docs/infographic.svg');
  const pngPath = path.join(__dirname, '../docs/infographic.png');

  console.log('Reading SVG from:', svgPath);
  const svgContent = fs.readFileSync(svgPath, 'utf8');

  // Create HTML wrapper
  const html = `
    <!DOCTYPE html>
    <html>
      <head>
        <style>
          body {
            margin: 0;
            padding: 0;
            background: #0F172A;
            width: 1200px;
            height: 1600px;
          }
          svg {
            display: block;
          }
        </style>
      </head>
      <body>
        ${svgContent}
      </body>
    </html>
  `;

  console.log('Launching browser...');
  const browser = await puppeteer.launch({
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const page = await browser.newPage();

  // Set viewport to match SVG dimensions (2x for retina)
  await page.setViewport({
    width: 1200,
    height: 1600,
    deviceScaleFactor: 2
  });

  console.log('Loading SVG content...');
  await page.setContent(html, { waitUntil: 'networkidle0' });

  // Wait for any animations or fonts to load
  await new Promise(resolve => setTimeout(resolve, 2000));

  console.log('Taking screenshot...');
  await page.screenshot({
    path: pngPath,
    type: 'png',
    clip: { x: 0, y: 0, width: 1200, height: 1600 },
    omitBackground: false
  });

  await browser.close();

  console.log('✓ PNG generated successfully:', pngPath);

  // Get file size
  const stats = fs.statSync(pngPath);
  console.log('  File size:', Math.round(stats.size / 1024), 'KB');
})().catch(err => {
  console.error('Error:', err);
  process.exit(1);
});
