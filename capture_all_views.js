const { spawn } = require('child_process');
const fs = require('fs');

async function captureViews() {
  const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
    '--headless=new',
    '--remote-debugging-port=9222',
    '--disable-gpu',
    '--no-sandbox',
    'http://localhost:8000'
  ]);

  await new Promise(r => setTimeout(r, 1500));
  const listRes = await fetch('http://127.0.0.1:9222/json');
  const tabs = await listRes.json();
  const pageTab = tabs.find(t => t.type === 'page');

  const ws = new WebSocket(pageTab.webSocketDebuggerUrl);
  let id = 1;
  const send = (method, params = {}) => new Promise((resolve) => {
    const curId = id++;
    const handler = (event) => {
      const data = JSON.parse(event.data);
      if (data.id === curId) {
        ws.removeEventListener('message', handler);
        resolve(data.result);
      }
    };
    ws.addEventListener('message', handler);
    ws.send(JSON.stringify({ id: curId, method, params }));
  });

  await new Promise(r => ws.addEventListener('open', r));

  await send('Runtime.enable');
  await send('Page.enable');

  await send('Emulation.setDeviceMetricsOverride', {
    width: 1440,
    height: 900,
    deviceScaleFactor: 1,
    mobile: false
  });

  await new Promise(r => setTimeout(r, 1000));

  const views = [
    { name: 'workspace', fn: `switchMainView('workspace')` },
    { name: 'dashboard', fn: `switchMainView('dashboard')` },
    { name: 'qa', fn: `switchMainView('qa')` },
    { name: 'orders', fn: `switchMainView('orders')` },
    { name: 'knowledge', fn: `switchMainView('knowledge')` },
    { name: 'channels', fn: `switchMainView('channels')` }
  ];

  for (const v of views) {
    await send('Runtime.evaluate', { expression: v.fn });
    await new Promise(r => setTimeout(r, 600));
    const shot = await send('Page.captureScreenshot', { format: 'png' });
    fs.writeFileSync(`/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/view_${v.name}.png`, Buffer.from(shot.data, 'base64'));
    console.log(`Captured view_${v.name}.png`);
  }

  ws.close();
  chrome.kill();
  console.log('All 6 main views captured!');
}

captureViews().catch(console.error);
