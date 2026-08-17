(function () {
  'use strict';

  var UMTX2 = ['1.00','1.01','1.02','1.05','1.10','1.11','1.12','1.13','1.14','2.00','2.20','2.25','2.26','2.30','2.50','2.70','3.00','3.10','3.20','3.21','4.00','4.02','4.03','4.50','4.51','5.00','5.02','5.10','5.50'];
  var SLOPKIT = ['9.00','9.05','9.20','9.40','9.60','10.00','10.01','10.20','10.40','10.60','11.00','11.20','11.40','11.60','12.00'];

  var PAYLOADS = {
    etahen: { file: 'etahen-2.5B.bin', label: 'etaHEN 2.5B' },
    kstuff: { file: 'kstuff-1.10.elf', label: 'Kstuff Lite 1.10' },
    manager: { file: 'payload.elf', label: 'Payload Manager' }
  };

  var splash = document.getElementById('splash');
  var dashboard = document.getElementById('dashboard');
  var loader = document.getElementById('loader');
  var exploit = document.getElementById('exploit');
  var firmwareValue = document.getElementById('firmwareValue');
  var exploitValue = document.getElementById('exploitValue');
  var statusValue = document.getElementById('statusValue');
  var runTitle = document.getElementById('runTitle');
  var runSubtitle = document.getElementById('runSubtitle');
  var logContainer = document.getElementById('logContainer');
  var progressBar = document.getElementById('progressBar');
  var progressLabel = document.getElementById('progressLabel');

  function log(message, cls) {
    var line = document.createElement('div');
    line.className = 'line ' + (cls || 'info');
    line.textContent = message;
    logContainer.appendChild(line);
    logContainer.parentNode.scrollTop = logContainer.parentNode.scrollHeight;
  }

  function progress(percent, text) {
    progressBar.style.transform = 'scaleX(' + (percent / 100) + ')';
    progressLabel.textContent = text;
  }

  function firmware() {
    var match = /PlayStation 5\/(\d+\.\d+)/.exec(navigator.userAgent);
    return match ? match[1] : null;
  }

  function exploitForFirmware(fw) {
    if (UMTX2.indexOf(fw) !== -1) return 'umtx2';
    if (SLOPKIT.indexOf(fw) !== -1) return 'slopkit';
    return null;
  }

  function buildExploitUrl(mode, payload) {
    var encoded = encodeURIComponent(payload);
    if (mode === 'umtx2') {
      return 'umtx2/index.html?autoload=' + encoded + '&v=2';
    }
    return 'slopkit/slopkit/poops.html?go=1&auto=1&production=1&trigger=netcontrol&attempts=8&only=ps0_preflight,ps1_prepare,ps3_stage0,ps4_validate,ps5_stage1,ps6_stage2,ps8_stage3,ps9_stage4,ps10_stage5&log=debug&payload=1&autoload=' + encoded + '&v=final';
  }

  function showDashboard() {
    splash.classList.add('hide');
    setTimeout(function () {
      splash.hidden = true;
      dashboard.hidden = false;
      scheduleAutoJailbreak();
    }, 350);
  }

  function scheduleAutoJailbreak() {
    var fw = firmware();
    var mode = fw ? exploitForFirmware(fw) : null;
    var alreadyStarted = false;

    try {
      alreadyStarted = sessionStorage.getItem('goldengames:auto-started') === '1';
    } catch (e) {}

    if (!mode || alreadyStarted) return;

    statusValue.textContent = 'AUTO START';
    setTimeout(function () {
      try {
        sessionStorage.setItem('goldengames:auto-started', '1');
      } catch (e) {}
      startPayload('etahen', true);
    }, 900);
  }

  function startPayload(key, autoMode) {
    var fw = firmware();
    var mode = fw ? exploitForFirmware(fw) : null;
    var item = PAYLOADS[key];

    if (!fw) {
      statusValue.textContent = 'NOT PS5';
      return;
    }
    if (!mode) {
      statusValue.textContent = 'UNSUPPORTED';
      return;
    }

    dashboard.hidden = true;
    loader.hidden = false;
    exploitValue.textContent = mode === 'umtx2' ? 'UMTX2' : 'SlopKit';
    statusValue.textContent = 'RUNNING';
    runTitle.textContent = autoMode ? 'AUTO JAILBREAK' : item.label;
    runSubtitle.textContent = 'Firmware ' + fw + ' via ' + exploitValue.textContent;
    log('Firmware detected: ' + fw, 'success');
    log('Exploit selected: ' + exploitValue.textContent, 'info');
    log('Payload selected: ' + item.file, 'info');
    if (autoMode && key === 'etahen') {
      log('AUTO target locked: etaHEN 2.5B only. External Kstuff is not requested.', 'success');
    }
    progress(15, 'Starting exploit...');

    try {
      sessionStorage.removeItem('slopkit-poops:next');
      sessionStorage.removeItem('slopkit-poops:latch');
      sessionStorage.setItem('wkal_autoload', item.file);
    } catch (e) {}

    exploit.hidden = true;
    exploit.src = buildExploitUrl(mode, item.file);
    progress(30, 'Exploit armed. Waiting for payload chain...');
  }

  window.addEventListener('message', function (event) {
    var data = event.data || {};

    if (data.type === 'goldengames-diag') {
      if (data.stage === 'autoload-route') {
        log('UMTX2 route: ' + data.payload + ' -> port ' + data.port + ' (' + data.loader + ')', 'info');
        progress(70, 'etaHEN route selected: port ' + data.port);
      } else if (data.stage === 'autoload-dispatch') {
        log('Dispatching etaHEN to port ' + data.port + '...', 'info');
        progress(80, 'Sending etaHEN 2.5B...');
      }
      return;
    }

    var isAutoloadResult = data.type === 'autoload-result' ||
      data.type === 'ps5-autoload' ||
      (data.type === 'wkal' && data.kind === 'autoload');

    if (isAutoloadResult) {
      if (data.ok) {
        log('etaHEN payload sent successfully' + (data.bytes ? ' (' + data.bytes + ' bytes).' : '.'), 'success');
        progress(100, 'etaHEN sent successfully.');
        statusValue.textContent = 'ETAHEN SENT';
      } else {
        log('etaHEN autoload failed: ' + (data.why || 'unknown error'), 'error');
        progress(0, 'etaHEN autoload failed.');
        statusValue.textContent = 'FAILED';
      }
    }
  });

  document.getElementById('autoJailbreak').addEventListener('click', function () {
    startPayload('etahen', true);
  });

  var tiles = document.querySelectorAll('[data-payload]');
  for (var i = 0; i < tiles.length; i++) {
    tiles[i].addEventListener('click', function () {
      startPayload(this.getAttribute('data-payload'), false);
    });
  }

  var fw = firmware();
  var mode = fw ? exploitForFirmware(fw) : null;
  firmwareValue.textContent = fw || 'Unknown';
  exploitValue.textContent = mode === 'umtx2' ? 'UMTX2' : mode === 'slopkit' ? 'SlopKit' : 'Unsupported';
  statusValue.textContent = mode ? 'READY' : 'UNSUPPORTED';

  setTimeout(showDashboard, 900);
}());
