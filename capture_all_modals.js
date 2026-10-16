const { spawn } = require('child_process');
const fs = require('fs');

async function captureModals() {
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

  const modalActions = [
    { name: 'quick_clients', open: `openQuickModal('clients')`, close: `closeActionModal()` },
    { name: 'quick_compliance', open: `openQuickModal('compliance')`, close: `closeActionModal()` },
    { name: 'quick_replies', open: `openQuickModal('quick_replies')`, close: `closeActionModal()` },
    { name: 'quick_settings', open: `openQuickModal('settings')`, close: `closeActionModal()` },
    { name: 'action_tag', open: `openActionModal('tag')`, close: `closeActionModal()` },
    { name: 'action_transfer', open: `openActionModal('transfer')`, close: `closeActionModal()` },
    { name: 'action_close', open: `openActionModal('close')`, close: `closeActionModal()` },
    { name: 'action_reconcile', open: `openReconcileModal()`, close: `closeSmartModals()` },
    { name: 'action_turnover', open: `openTurnoverWaiverModal()`, close: `closeSmartModals()` },
    { name: 'action_retention', open: `openVipRetentionModal()`, close: `closeSmartModals()` },
    { name: 'action_antifraud', open: `checkAntiFraudRisk()`, close: `closeSmartModals()` },
    { name: 'action_qadetail', open: `openQaDetailModal('QA20261005001')`, close: `closeSmartModals()` },
    { name: 'action_addrule', open: `openAddRuleModal()`, close: `closeSmartModals()` }
  ];

  for (const m of modalActions) {
    try {
      await send('Runtime.evaluate', { expression: m.open });
      await new Promise(r => setTimeout(r, 400));
      const shot = await send('Page.captureScreenshot', { format: 'png' });
      fs.writeFileSync(`/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/modal_${m.name}.png`, Buffer.from(shot.data, 'base64'));
      console.log(`Saved modal_${m.name}.png`);
      await send('Runtime.evaluate', { expression: m.close });
      await new Promise(r => setTimeout(r, 300));
    } catch (e) {
      console.error(`Error capturing ${m.name}:`, e.message);
    }
  }

  ws.close();
  chrome.kill();
  console.log('All modals captured!');
}

captureModals().catch(console.error);
