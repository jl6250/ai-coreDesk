const { spawn } = require('child_process');
const fs = require('fs');

async function testQaAndResponsive() {
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

  // 1. Switch to QA view and open QA Detail modal
  await send('Emulation.setDeviceMetricsOverride', { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });
  await send('Runtime.evaluate', { expression: `switchMainView('qa')` });
  await new Promise(r => setTimeout(r, 800));

  // Trigger openQaDetailModal with real first record
  await send('Runtime.evaluate', {
    expression: `
      (() => {
        if (currentQaRecords && currentQaRecords.length > 0) {
          openQaDetailModal(currentQaRecords[0].qa_id);
        }
      })()
    `
  });
  await new Promise(r => setTimeout(r, 400));
  const shotQa = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/modal_qa_radar_opened.png', Buffer.from(shotQa.data, 'base64'));
  console.log('Saved modal_qa_radar_opened.png');

  // Close QA modal and return to workspace
  await send('Runtime.evaluate', { expression: `closeQaDetailModal(); switchMainView('workspace');` });
  await new Promise(r => setTimeout(r, 500));

  // 2. Test 1920x1080 (Desktop Wide Screen)
  await send('Emulation.setDeviceMetricsOverride', { width: 1920, height: 1080, deviceScaleFactor: 1, mobile: false });
  await new Promise(r => setTimeout(r, 500));
  const shot1080p = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/workspace_1920x1080.png', Buffer.from(shot1080p.data, 'base64'));
  console.log('Saved workspace_1920x1080.png');

  // 3. Test 1280x800 (Compact Laptop Screen)
  await send('Emulation.setDeviceMetricsOverride', { width: 1280, height: 800, deviceScaleFactor: 1, mobile: false });
  await new Promise(r => setTimeout(r, 500));
  const shotCompact = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/workspace_1280x800.png', Buffer.from(shotCompact.data, 'base64'));
  console.log('Saved workspace_1280x800.png');

  // 4. Test Toast position
  await send('Runtime.evaluate', { expression: `showToast('测试右下角浮层提示', 'success')` });
  await new Promise(r => setTimeout(r, 400));
  const shotToast = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/toast_position.png', Buffer.from(shotToast.data, 'base64'));
  console.log('Saved toast_position.png');

  ws.close();
  chrome.kill();
  console.log('All tests completed successfully!');
}

testQaAndResponsive().catch(console.error);
