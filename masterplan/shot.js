// Render HTML files to PNG (preview) or PDF (print): node shot.js png in.html out.png [width]
//                                                     node shot.js pdf in.html out.pdf
const { chromium } = require('playwright');
(async () => {
  const [mode, src, dst, width] = process.argv.slice(2);
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: parseInt(width || '2400'), height: 900 } });
  await page.goto('file://' + require('path').resolve(src));
  await page.waitForTimeout(300);
  if (mode === 'pdf') {
    await page.pdf({ path: dst, preferCSSPageSize: true, printBackground: true });
  } else {
    await page.screenshot({ path: dst, fullPage: true });
  }
  await browser.close();
})();
