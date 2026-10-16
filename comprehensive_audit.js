const { spawn } = require('child_process');
const fs = require('fs');

async function fullAudit() {
  console.log('🚀 Starting Chrome Full End-to-End Audit...');
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

  const consoleErrors = [];
  const pageErrors = [];

  ws.addEventListener('message', (event) => {
    const data = JSON.parse(event.data);
    if (data.method === 'Runtime.consoleAPICalled') {
      if (data.params.type === 'error') {
        consoleErrors.push(data.params.args.map(a => a.value || a.description).join(' '));
      }
    }
    if (data.method === 'Runtime.exceptionThrown') {
      pageErrors.push(data.params.exceptionDetails.text + ' ' + (data.params.exceptionDetails.exception?.description || ''));
    }
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

  await new Promise(r => setTimeout(r, 1200));

  const runTest = async (testName, actionJs) => {
    try {
      const evalRes = await send('Runtime.evaluate', {
        expression: `
          (async () => {
            try {
              ${actionJs}
              return { success: true };
            } catch (e) {
              return { success: false, error: e.toString() };
            }
          })()
        `,
        awaitPromise: true,
        returnByValue: true
      });
      const res = evalRes?.result?.value;
      if (res && res.success) {
        console.log(`  ✅ [PASS] ${testName}`);
        return true;
      } else {
        console.error(`  ❌ [FAIL] ${testName}:`, res?.error || 'Unknown error');
        return false;
      }
    } catch (e) {
      console.error(`  ❌ [FAIL] ${testName}:`, e.message);
      return false;
    }
  };

  const results = [];

  console.log('\n--- 1. 顶部模式/语言/状态交互 ---');
  results.push(await runTest('模式切换 (Auto-Pilot)', `switchSystemMode('auto_pilot');`));
  results.push(await runTest('模式切换 (Copilot)', `switchSystemMode('copilot');`));
  results.push(await runTest('语言切换 (English)', `setLanguage('en');`));
  results.push(await runTest('语言切换 (中文)', `setLanguage('zh');`));
  results.push(await runTest('坐席状态切换 (busy)', `setAgentStatus('busy');`));
  results.push(await runTest('坐席状态切换 (online)', `setAgentStatus('online');`));

  console.log('\n--- 2. 会话队列与仿真交互 ---');
  results.push(await runTest('切换会话 lucky_tiger_99', `switchActiveUser('u1002');`));
  results.push(await runTest('切换回会话 vip_player_88', `switchActiveUser('u1001');`));
  results.push(await runTest('刷新队列 refreshQueue', `refreshQueue();`));

  console.log('\n--- 3. 聊天输入与 AI Copilot ---');
  results.push(await runTest('采纳 AI 草稿到输入框', `applyDraftToEditor();`));
  results.push(await runTest('清空输入框', `clearEditor();`));
  results.push(await runTest('输入自定义文本并发送', `
    const editor = document.getElementById('agentEditor');
    editor.value = '您好，这边正在为您核验链上流水，请稍候。';
    submitAgentReply();
  `));
  results.push(await runTest('重新生成草稿', `regenerateCopilotDraft();`));
  results.push(await runTest('切换回复语气为温和安抚', `selectTone('empathetic', '温和安抚');`));
  results.push(await runTest('展开/收起草稿详情与动作', `toggleCopilotCollapse(); toggleCopilotCollapse();`));

  console.log('\n--- 4. 右侧 CRM 看板与全渠道漫游 ---');
  results.push(await runTest('切换至全渠道旅程 Tab', `switchCrmTab('journey');`));
  results.push(await runTest('敏感数据脱敏查看申请', `requestUnmaskAudit('bank_card');`));
  results.push(await runTest('切回财务档案 Tab', `switchCrmTab('billing');`));
  results.push(await runTest('收起右侧看板', `toggleCrmSidebar();`));
  results.push(await runTest('展开右侧看板', `toggleCrmSidebar();`));

  console.log('\n--- 5. 核心业务弹窗与操作测试 ---');
  results.push(await runTest('打标签弹窗 (打开与关闭)', `
    openActionModal('tag');
    closeActionModal();
  `));
  results.push(await runTest('转接弹窗 (打开与关闭)', `
    openActionModal('transfer');
    closeActionModal();
  `));
  results.push(await runTest('结束会话弹窗 (打开与关闭)', `
    openActionModal('close');
    closeActionModal();
  `));
  results.push(await runTest('掉单核验弹窗 (打开与关闭)', `
    openReconcileModal();
    closeActionModal();
  `));
  results.push(await runTest('流水冲正弹窗 (打开与关闭)', `
    openTurnoverWaiverModal();
    closeActionModal();
  `));
  results.push(await runTest('VIP礼金弹窗 (打开与关闭)', `
    openVipRetentionModal();
    closeActionModal();
  `));
  results.push(await runTest('快速工单弹窗 (打开与关闭)', `
    openQuickCreateTicketModal();
    closeActionModal();
  `));
  results.push(await runTest('反欺诈风险排查', `checkAntiFraudRisk();`));

  console.log('\n--- 6. 顶部快速窗口 ---');
  results.push(await runTest('客户列表弹窗', `openQuickModal('clients'); closeActionModal();`));
  results.push(await runTest('合规风控弹窗', `openQuickModal('compliance'); closeActionModal();`));
  results.push(await runTest('常用语弹窗', `openQuickModal('quick_replies'); closeActionModal();`));
  results.push(await runTest('系统设置弹窗', `openQuickModal('settings'); closeActionModal();`));

  console.log('\n--- 7. 主视图页面导航切换 ---');
  results.push(await runTest('切换到仪表盘', `switchMainView('dashboard');`));
  results.push(await runTest('切换到智能质检', `switchMainView('qa');`));
  results.push(await runTest('切换到工单对账', `switchMainView('orders');`));
  results.push(await runTest('切换到知识飞轮', `switchMainView('knowledge');`));
  results.push(await runTest('切换到渠道网关', `switchMainView('channels');`));
  results.push(await runTest('切回工作台', `switchMainView('workspace');`));

  // Take a final screenshot of workspace
  const finalScreen = await send('Page.captureScreenshot', { format: 'png' });
  fs.writeFileSync('/Users/king/.gemini/antigravity-ide/brain/e74f09df-8f9d-4825-b910-8ae27f418b62/scratch/final_audit_render.png', Buffer.from(finalScreen.data, 'base64'));

  await new Promise(r => setTimeout(r, 500));

  console.log('\n--- 8. 错误日志汇总 ---');
  console.log(`Console Errors (${consoleErrors.length}):`, consoleErrors);
  console.log(`Page Unhandled Exceptions (${pageErrors.length}):`, pageErrors);

  const passedCount = results.filter(Boolean).length;
  console.log(`\n🎉 Audit Summary: ${passedCount} / ${results.length} tests passed.`);

  ws.close();
  chrome.kill();
}

fullAudit().catch(console.error);
