(function () {
  'use strict';

  var splashEl = document.getElementById('splash');
  var loaderEl = document.getElementById('loader');
  var logContainer = document.getElementById('logContainer');
  var progressBar = document.getElementById('progressBar');
  var progressLabel = document.getElementById('progressLabel');
  var exploitEl = document.getElementById('exploit');
  var dashboardEl = document.getElementById('dashboard');
  var payloadSelectEl = document.getElementById('payloadSelect');
  var launchPayloadEl = document.getElementById('launchPayload');
  var autoJailbreakEl = document.getElementById('autoJailbreak');
  var showDetailsEl = document.getElementById('showDetails');
  var backToMenuEl = document.getElementById('backToMenu');
  var payloadGridEl = document.getElementById('payloadGrid');
  var riskDialogEl = document.getElementById('riskDialog');
  var riskMessageEl = document.getElementById('riskMessage');
  var riskCancelEl = document.getElementById('riskCancel');
  var riskContinueEl = document.getElementById('riskContinue');
  var goldenStateEl = document.getElementById('goldenState');
  var headerStateEl = document.getElementById('headerState');
  var firmwareValueEl = document.getElementById('firmwareValue');
  var exploitValueEl = document.getElementById('exploitValue');
  var payloadValueEl = document.getElementById('payloadValue');
  var uptimeValueEl = document.getElementById('uptimeValue');
  var modeValueEl = document.getElementById('modeValue');
  var modeNameEl = document.getElementById('modeName');
  var modeHelpEl = document.getElementById('modeHelp');
  var autoModeToggleEl = document.getElementById('autoModeToggle');
  var activityPayloadEl = document.getElementById('activityPayload');
  var detailsDrawerEl = document.getElementById('detailsDrawer');
  var retroStatusEl = document.querySelector('.retroLoader span');
  var retroBlocks = document.querySelectorAll('.retroBlocks i');
  var selectedPayload = 'etahen-2.6B.bin';
  var selectedLabel = 'etaHEN 2.6B';
  var pendingRiskLaunch = null;
  var SESSION_KEY = 'goldengames:v111-session-ready';
  var ACTIVE_PAYLOAD_KEY = 'goldengames:v111-active-payload';
  var AUTO_MODE_KEY = 'goldengames:v111-auto-mode';
  var AUTO_PAYLOAD_KEY = 'goldengames:v111-auto-payload';
  var queuedAutoPayload = null;
  var autoMode = false;
  var operationStartedAt = Date.now();

  function hasKnownSession() {
    try {
      return !!(sessionStorage.getItem(SESSION_KEY) || localStorage.getItem(SESSION_KEY));
    } catch (e) {
      return false;
    }
  }

  /* After a WebProcess crash the PS5 browser restores this page together with
     the iframe at its last URL — the armed exploit URL, which would auto-run
     the chain again. Blank it as early as possible (the iframe element is
     already in the DOM at script parse) so the chain only runs after the
     splash screen. */
  try {
    exploitEl.src = 'about:blank';
  } catch (e) { }

  var MAX_LOG_LINES = 80;
  var finished = false;
  var chainStarted = false;
  var mirroredLines = 0;
  var lastStageText = '';
  var lastStageCls = '';
  var lastSummaryText = '';
  var earlyLinesLogged = 0;
  var lastFrameUrl = '';
  var repairCount = 0;
  var mirrorTimer = 0;
  var retroAnimationTimer = 0;
  var retroAnimationFrame = 0;
  var reportedProgress = 0;

  function startRetroAnimation() {
    if (retroAnimationTimer) clearInterval(retroAnimationTimer);
    retroAnimationFrame = 0;
    var colors = ['#df2d32', '#f4c330', '#269c55', '#3475bd', '#df2d32'];
    retroAnimationTimer = setInterval(function () {
      retroAnimationFrame++;
      for (var i = 0; i < retroBlocks.length; i++) {
        var phase = (retroAnimationFrame + i) % 6;
        var height = phase < 3 ? 10 + phase * 9 : 10 + (5 - phase) * 9;
        retroBlocks[i].style.height = height + 'px';
        retroBlocks[i].style.opacity = String(0.38 + height / 48);
        retroBlocks[i].style.background = colors[i];
      }
      /* The colored bar grows with real exploit milestones. */
      progressBar.style.width = '100%';
      progressBar.style.left = '0';
      progressBar.style.webkitTransform = 'scaleX(' + reportedProgress / 100 + ')';
      progressBar.style.transform = 'scaleX(' + reportedProgress / 100 + ')';
    }, 140);
  }

  function stopRetroAnimation() {
    if (retroAnimationTimer) clearInterval(retroAnimationTimer);
    retroAnimationTimer = 0;
    progressBar.style.width = '100%';
    progressBar.style.left = '0';
    progressBar.style.webkitTransform = 'scaleX(' + reportedProgress / 100 + ')';
    progressBar.style.transform = 'scaleX(' + reportedProgress / 100 + ')';
  }

  /* The slopkit chains (poops 7.00-12.00, p2jb 12.02-12.70) keep a one-shot
     latch and their "stopped at …" marker in sessionStorage under shared
     "slopkit-poops:*" keys. On the PS5 browser the shortcut session can
     outlive a console reboot, so a previous interrupted run would otherwise
     block every retry with "the last run stopped at X but the latch is clear".
     Clear them right before arming so the full chain always restarts from
     the top (never a mid-chain resume). The iframe is same-origin, so this
     is exactly the storage both exploit pages read. */
  function clearSlopkitState() {
    try {
      sessionStorage.removeItem('slopkit-poops:next');
      sessionStorage.removeItem('slopkit-poops:latch');
    } catch (e) { }
  }

  /* Build-time exploit override: "auto" (firmware table), "umtx2", "poops"
     (7.00-12.00) or "p2jb" (12.02-12.70). Replaced by
     tools/gen_file_registry.py / build_host.py / dev_server.py from the
     FORCE_EXPLOIT env (default "auto"); left as the raw placeholder when
     served straight from source -> auto. A ?force= query on this page
     overrides it at runtime (handy for make dev). */
  var EXPLOIT_MODE = '[[EXPLOIT_MODE]]';
  if (EXPLOIT_MODE.indexOf('[[') === 0) EXPLOIT_MODE = 'auto';

  /* Firmwares supported by each exploit, keyed on the exact UA firmware
     string (/PlayStation 5/x.xx/). Keep in sync with the exploits' own lists:
     umtx2/document/en/ps5/main.js and slopkit/slopkit/main.js. */
  var UMTX2_FIRMWARES = ["1.00", "1.01", "1.02", "1.05", "1.10", "1.11", "1.12", "1.13", "1.14", "2.00", "2.20", "2.25", "2.26", "2.30", "2.50", "2.70", "3.00", "3.10", "3.20", "3.21", "4.00", "4.02", "4.03", "4.50", "4.51", "5.00", "5.02", "5.10", "5.50"];
  var POOPS_FIRMWARES = ["7.00", "7.01", "7.20", "7.40", "7.60", "7.61", "8.00", "8.20", "8.40", "8.60", "9.00", "9.05", "9.20", "9.40", "9.60", "10.00", "10.01", "10.20", "10.40", "10.60", "11.00", "11.20", "11.40", "11.60", "12.00"];
  var P2JB_FIRMWARES = ["12.02", "12.20", "12.40", "12.60", "12.70"];

  function umtx2Url(payload) {
    return 'umtx2/index.html?autoload=' + encodeURIComponent(payload) + '&v=2';
  }

  /* Keep in sync with EXPLOIT_IFRAME_URL in tools/gen_file_registry.py — the
     AppCache manifest lists these exact URLs so the console can serve them
     offline (AppCache matches URLs including the query string). */
  function poopsUrl(payload) {
    return 'slopkit/slopkit/poops.html?go=1&auto=1&production=1&trigger=netcontrol&attempts=8&only=ps0_preflight,ps1_prepare,ps3_stage0,ps4_validate,ps5_stage1,ps6_stage2,ps8_stage3,ps9_stage4,ps10_stage5&log=debug&payload=1&v=final&autoload=' + encodeURIComponent(payload);
  }
  function p2jbUrl(payload) {
    return 'slopkit/slopkit/p2jb.html?go=1&auto=1&production=1&log=debug&payload=1&v=final&autoload=' + encodeURIComponent(payload);
  }

  var EXPLOIT_URL = '';
  var exploitMode = null;

  function uiLog(message, type) {
    type = type || 'info';
    var entry = document.createElement('div');
    entry.className = 'line ' + type;
    entry.textContent = message;
    logContainer.appendChild(entry);
    while (logContainer.childElementCount > MAX_LOG_LINES) {
      logContainer.removeChild(logContainer.firstChild);
    }
    logContainer.parentNode.scrollTop = logContainer.parentNode.scrollHeight;
    return entry;
  }

  function updateProgress(percent, message) {
    reportedProgress = percent;
    progressBar.style.webkitTransform = 'scaleX(' + percent / 100 + ')';
    progressBar.style.transform = 'scaleX(' + percent / 100 + ')';
    if (message) {
      progressLabel.textContent = message;
      if (activityPayloadEl) activityPayloadEl.textContent = selectedLabel;
      if (retroStatusEl) retroStatusEl.textContent = String(message).toUpperCase();
      uiLog(message, 'info');
    }
  }

  window.uiLog = uiLog;
  window.updateProgress = updateProgress;

  function detectFirmware() {
    var m = /PlayStation 5\/(\d+\.\d+)/.exec(navigator.userAgent);
    if (!m) return null;
    return { str: m[1], num: parseFloat(m[1]) };
  }

  function setControlsDisabled(disabled) {
    if (autoModeToggleEl) autoModeToggleEl.disabled = disabled;
    var cards = document.querySelectorAll('.payloadCard');
    for (var i = 0; i < cards.length; i++) cards[i].disabled = disabled;
  }

  function formatUptime(ms) {
    var total = Math.max(0, Math.floor(ms / 1000));
    var h = Math.floor(total / 3600);
    var m = Math.floor((total % 3600) / 60);
    var s = total % 60;
    function pad(v) { return v < 10 ? '0' + v : String(v); }
    return pad(h) + ':' + pad(m) + ':' + pad(s);
  }

  function updateModeUi() {
    if (autoModeToggleEl) {
      autoModeToggleEl.classList.toggle('on', autoMode);
      autoModeToggleEl.setAttribute('aria-checked', autoMode ? 'true' : 'false');
      autoModeToggleEl.querySelector('span').textContent = autoMode ? 'AUTO ON' : 'AUTO OFF';
    }
    if (modeNameEl) modeNameEl.textContent = autoMode ? 'AUTO MODE' : 'MANUAL MODE';
    if (modeValueEl) modeValueEl.textContent = autoMode ? 'AUTO' : 'MANUAL';
    if (modeHelpEl) modeHelpEl.textContent = autoMode
      ? selectedLabel + ' will launch automatically when Goldengames opens.'
      : 'Press any payload button to jailbreak and launch it.';
  }

  function selectPayload(card) {
    var cards = document.querySelectorAll('.payloadCard');
    for (var i = 0; i < cards.length; i++) cards[i].classList.remove('selected');
    card.classList.add('selected');
    selectedPayload = card.getAttribute('data-payload');
    selectedLabel = card.getAttribute('data-label');
    if (payloadValueEl && hasKnownSession()) payloadValueEl.textContent = selectedLabel.toUpperCase();
    updateModeUi();
  }

  /* Choose which exploit to arm. Forced modes (build-time EXPLOIT_MODE or a
     ?force= query on this page) bypass the firmware table so a specific chain
     can be exercised on any firmware — the exploit page's own firmware guard
     still applies. Returns 'umtx2' | 'poops' | 'p2jb' | null. */
  function pickExploit() {
    var fw = detectFirmware();
    var forced = null;
    try {
      var q = new URLSearchParams(window.location.search).get('force');
      if (q === 'umtx2' || q === 'poops' || q === 'p2jb') forced = q;
    } catch (e) { }
    if (forced) {
      uiLog('[force] using ' + forced + ' on firmware ' + (fw ? fw.str : 'unknown'), 'warning');
      return forced;
    }
    if (EXPLOIT_MODE === 'umtx2' || EXPLOIT_MODE === 'poops'
      || EXPLOIT_MODE === 'p2jb') {
      uiLog('[force] using ' + EXPLOIT_MODE + ' on firmware ' + (fw ? fw.str : 'unknown'), 'warning');
      return EXPLOIT_MODE;
    }
    if (!fw) {
      uiLog('[ERROR] Not a PlayStation 5 browser.', 'error');
      return null;
    }
    if (UMTX2_FIRMWARES.indexOf(fw.str) !== -1) return 'umtx2';
    if (POOPS_FIRMWARES.indexOf(fw.str) !== -1) return 'poops';
    if (P2JB_FIRMWARES.indexOf(fw.str) !== -1) return 'p2jb';
    uiLog('[ERROR] Unsupported firmware ' + fw.str +
      ' (supported: 1.00-5.50 via umtx2, 7.00-12.00 via poops,'
      + ' 12.02-12.70 via p2jb).', 'error');
    return null;
  }

  function revealExploit() {
    startRetroAnimation();
    if (splashEl) splashEl.hidden = true;
    if (loaderEl) loaderEl.hidden = true;
    if (dashboardEl) dashboardEl.hidden = false;
    document.body.classList.add('running');
    setControlsDisabled(true);
  }

  function showDashboard() {
    stopRetroAnimation();
    if (splashEl) splashEl.hidden = true;
    if (loaderEl) loaderEl.hidden = true;
    if (dashboardEl) dashboardEl.hidden = false;
    document.body.classList.remove('running');
    var activeCards = document.querySelectorAll('.payloadCard.active-launch');
    for (var i = 0; i < activeCards.length; i++) activeCards[i].classList.remove('active-launch');
    setControlsDisabled(false);
  }

  function onAutoloadResult(data) {
    if (finished) return;
    finished = true;
    /* Success is terminal — stop mirroring so the page stays idle while the
       payload runs alongside it. On failure keep streaming the iframe's
       output into the log for diagnostics. */
    if (data.ok && mirrorTimer) {
      clearInterval(mirrorTimer);
      mirrorTimer = 0;
    }
    /* p2jb only: retire the stats panel (green 100% since the win) and
       restore the classic full-height log; no-op for the other chains. */
    collapseP2jbStats();
    if (data.ok) {
      try {
        sessionStorage.setItem(SESSION_KEY, String(Date.now()));
        sessionStorage.setItem(ACTIVE_PAYLOAD_KEY, selectedPayload);
        localStorage.setItem(SESSION_KEY, String(Date.now()));
        localStorage.setItem(ACTIVE_PAYLOAD_KEY, selectedPayload);
      } catch (e) { }

      /* Keep the runner iframe and the outer dashboard alive. Navigating the
         iframe to about:blank here could make the PS5 WebKit application
         disappear while a large HEN was still starting. */

      /* UMTX2 on 1.00-5.50 launches the small unified Payload Manager first.
         This stays invisible to the user: after memory settles, the exact
         payload card they pressed is sent without another kernel exploit. */
      if (queuedAutoPayload && selectedPayload === 'payload.elf') {
        var nextPayload = queuedAutoPayload;
        queuedAutoPayload = null;
        /* Retire only the hidden UMTX2 runner to release its memory. The
           visible Goldengames dashboard remains open and untouched. */
        try { exploitEl.src = 'about:blank'; } catch (e) { }
        if (goldenStateEl) goldenStateEl.textContent = 'JAILBREAK READY · PREPARING PAYLOAD';
        if (headerStateEl) headerStateEl.textContent = 'JAILBREAK COMPLETE';
        if (exploitValueEl) exploitValueEl.textContent = 'EXPLOIT OK';
        if (payloadValueEl) payloadValueEl.textContent = nextPayload.label.toUpperCase();
        updateProgress(62, 'Jailbreak complete · preparing ' + nextPayload.label + '...');
        setTimeout(function () {
          launchSelected(nextPayload.payload, nextPayload.label, false);
        }, 6500);
        return;
      }

      uiLog('Payload loaded (' + data.bytes + ' bytes sent to elfldr).', 'success');
      updateProgress(100, 'Payload launched successfully.');
      if (goldenStateEl) goldenStateEl.textContent = selectedLabel.toUpperCase() + ' READY';
      if (headerStateEl) headerStateEl.textContent = 'OPERATION COMPLETE';
      if (exploitValueEl) exploitValueEl.textContent = 'EXPLOIT OK';
      if (payloadValueEl) payloadValueEl.textContent = selectedLabel.toUpperCase();
    } else {
      queuedAutoPayload = null;
      stopRetroAnimation();
      var failureReason = data.why || 'unknown error';
      try {
        sessionStorage.removeItem(SESSION_KEY);
        sessionStorage.removeItem(ACTIVE_PAYLOAD_KEY);
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(ACTIVE_PAYLOAD_KEY);
      } catch (e) { }
      uiLog('[ERROR] Autoload failed: ' + failureReason, 'error');
      updateProgress(0, 'Failed: ' + failureReason);
      if (headerStateEl) headerStateEl.textContent = 'OPERATION FAILED';
      if (exploitValueEl) exploitValueEl.textContent = 'FAILED';
      if (goldenStateEl) goldenStateEl.textContent = 'PAYLOAD FAILED · TRY AGAIN';
      if (payloadValueEl) payloadValueEl.textContent = 'NOT LOADED';
    }
    setTimeout(function () {
      if (data.ok) uiLog('Payload running on the console.', 'success');
      showDashboard();
    }, 1500);
  }

  /* Mirror slopkit's live screen log (#scr) and stage text (#stage) from the
     same-origin exploit iframe into our own log view, so the UI shows what
     the chain is doing (and errors) instead of a generic progress message. */
  function mirrorSlopkit() {
    var doc;
    try {
      doc = exploitEl.contentDocument;
    } catch (e) {
      return;
    }
    if (!doc) return;

    /* Detect iframe navigation/reload: reset the mirror so a fresh document
       (or a crash restore) streams its log from the top. */
    var frameUrl = '';
    try {
      frameUrl = exploitEl.contentWindow.location.href;
    } catch (e) { }
    if (frameUrl !== lastFrameUrl) {
      lastFrameUrl = frameUrl;
      mirroredLines = 0;
      lastStageText = '';
      lastStageCls = '';
      lastSummaryText = '';
      earlyLinesLogged = 0;
    }
    /* The iframe is intentionally empty until the chain is armed — nothing
       to mirror yet. */
    if (!chainStarted) return;

    var scr = doc.getElementById('scr');
    if (!scr) {
      /* #scr is static HTML in poops.html — while it parses, #cat (earlier in
         the DOM) and <title> are already present, so a poll can briefly see
         "slopkit page without its screen". Same for the blank pre-navigation
         document. Never warn or re-arm during these windows: re-arming
         reloads the exploit a second time (and the log doubles). */
      var isArmedUrl = frameUrl.length > EXPLOIT_URL.length &&
        frameUrl.slice(-EXPLOIT_URL.length) === EXPLOIT_URL;
      if (frameUrl === 'about:blank' || doc.readyState !== 'complete'
        || isArmedUrl) {
        return;
      }
      /* Only reached when the iframe settled on a *different* page: slopkit's
         landing page (RUN button), a not-armed poops.html, or a 404. */
      var arm = doc.getElementById('arm');
      var cat = doc.getElementById('cat');
      var start = doc.getElementById('start');
      var title = doc.title || '';
      if (mirrorSlopkit.warned !== frameUrl) {
        mirrorSlopkit.warned = frameUrl;
        if (start) {
          uiLog('[iframe] slopkit landing page loaded (RUN button) — chain not started.', 'warning');
        } else if (arm && !arm.hidden) {
          uiLog('[iframe] slopkit page is NOT armed (?go=1 missing) — nothing will run.', 'warning');
        } else if (cat && title.indexOf('slopkit') !== -1) {
          uiLog('[iframe] slopkit page loaded without its screen (title="' + title + '").', 'warning');
        } else {
          uiLog('[iframe] page has no slopkit screen: title="' + title + '"', 'warning');
        }
      }
      /* Re-arm only for a wrong *slopkit* page (landing page or not-armed
         poops.html) — never for the armed URL itself. */
      var isSlopkitPage = !!start || (arm && !arm.hidden);
      if (chainStarted && isSlopkitPage && repairCount < 5) {
        repairCount++;
        uiLog('[iframe] re-arming (attempt ' + repairCount + '): ' + EXPLOIT_URL, 'info');
        try {
          exploitEl.src = EXPLOIT_URL;
        } catch (e) {
          uiLog('[iframe] re-arm failed: ' + (e && e.message ? e.message : e), 'error');
        }
      } else if (chainStarted && isSlopkitPage) {
        uiLog('[iframe] giving up after ' + repairCount + ' re-arm attempts.', 'error');
      }
      return;
    }

    var lines = scr.textContent.split('\n');
    /* If the screen shrank (slopkit caps its log at SCREEN_LINES and drops
       the oldest lines, or a fresh document replaced it), re-anchor the
       counter WITHOUT re-logging — the remaining lines were already streamed,
       and re-streaming them would double the log. A fresh document starts
       empty, so its new lines stream normally from here on. */
    if (lines.length < mirroredLines) {
      mirroredLines = lines.length;
    }
    for (; mirroredLines < lines.length; mirroredLines++) {
      var line = lines[mirroredLines].trim();
      if (!line) continue;
      /* Curated release log: surface the per-row progress ("> "), the
         milestone marks (STAGE / POOPS / LATCH / OFFSETS / ...), and
         anything that looks like a failure — never the full raw stream
         (that floods the UI and hides the actual result). */
      if (/^>/.test(line) || /^\[\+\]/.test(line)
        || /^(STAGE[0-5]|ALLPROC-CHECK|ALIASES-REPAIRED|POOPS-COMPLETE|POOPS-VERDICT|LATCH-HELD|LATCH-READ|OFFSETS-READY|WEBKIT-BASE|MODULE-BASES|SOCKETS|SPAWN|WAKEGATE)/.test(line)) {
        uiLog('[log] ' + line, 'info');
      } else if (/FAIL|ERROR|REFUSED|REBOOT|failed|panic|exception/i.test(line)
        || /^\[-\]/.test(line)) {
        uiLog('[log] ' + line, 'error');
      }
    }

    var stage = doc.getElementById('stage');
    if (stage && stage.textContent !== lastStageText) {
      lastStageText = stage.textContent;
      lastStageCls = stage.className || '';
      progressLabel.textContent = lastStageText;
      if (lastStageCls.indexOf('bad') !== -1) {
        uiLog('[stage] ' + lastStageText, 'error');
      } else if (lastStageCls.indexOf('ok') !== -1) {
        uiLog('[stage] ' + lastStageText, 'success');
      } else {
        uiLog('[stage] ' + lastStageText, 'info');
      }
    }

    /* Mirror the summary block (verdict/reboot details) when it changes. */
    var summary = doc.getElementById('summary');
    if (summary && summary.textContent && summary.textContent !== lastSummaryText) {
      var summaryLines = summary.textContent.split('\n');
      for (var i = 0; i < summaryLines.length; i++) {
        var sline = summaryLines[i].trim();
        if (sline && /FAIL|ERROR|REFUSED|REBOOT|failed|panic/i.test(sline)) {
          uiLog('[summary] ' + sline, 'error');
        }
      }
      lastSummaryText = summary.textContent;
    }

    /* Mirror the #early log (errors/notices written before the module chain
       runs — the earliest thing slopkit produces). slopkit only ever appends
       to #early, so log just the new tail — re-logging the whole buffer on
       every change doubled every early line. */
    var early = doc.getElementById('early');
    if (early && early.textContent) {
      var earlyLines = early.textContent.split('\n');
      if (earlyLines.length < earlyLinesLogged) {
        earlyLinesLogged = 0;
      }
      for (; earlyLinesLogged < earlyLines.length; earlyLinesLogged++) {
        var eline = earlyLines[earlyLinesLogged].trim();
        if (eline) {
          uiLog('[early] ' + eline, /ERROR|FAIL/i.test(eline) ? 'error' : 'info');
        }
      }
    }
  }

  /* Mirror umtx2's live #console log (#console > div, classed LOG-*) from the
     same-origin exploit iframe into our own log view, mapping its severity
     classes onto ours. umtx2 updates its last console line in place for
     progress logs (FLAG_TEMP, e.g. "Race attempt N-M"), so we update our
     matching last line in place too. */
  var umtx2MirroredLines = 0;
  var umtx2LastEntry = null;
  var umtx2LastText = '';
  function mirrorUmtx2() {
    var doc;
    try {
      doc = exploitEl.contentDocument;
    } catch (e) {
      return;
    }
    if (!doc || !chainStarted) return;
    var lines = doc.querySelectorAll('#console > div');
    if (lines.length < umtx2MirroredLines) {
      /* Iframe reloaded (#console recreated) — restart from a fresh document. */
      umtx2MirroredLines = lines.length;
      umtx2LastEntry = null;
      umtx2LastText = '';
    }
    for (; umtx2MirroredLines < lines.length; umtx2MirroredLines++) {
      var el = lines[umtx2MirroredLines];
      var text = (el.textContent || '').trim();
      if (!text) continue;
      var cls = el.className || '';
      var entry;
      if (/LOG-ERROR/.test(cls)) {
        entry = uiLog('[umtx2] ' + text, 'error');
      } else if (/LOG-WARN/.test(cls)) {
        entry = uiLog('[umtx2] ' + text, 'warning');
      } else if (/LOG-SUCCESS/.test(cls)) {
        entry = uiLog('[umtx2] ' + text, 'success');
      } else {
        entry = uiLog('[umtx2] ' + text, 'info');
      }
      umtx2LastEntry = entry;
      umtx2LastText = text;
    }
    /* Live-update the last mirrored line when umtx2 rewrites it in place. */
    if (lines.length > 0 && umtx2LastEntry
      && umtx2LastEntry === logContainer.lastChild) {
      var last = lines[lines.length - 1];
      var lastText = (last.textContent || '').trim();
      if (lastText && lastText !== umtx2LastText) {
        umtx2LastEntry.textContent = '[umtx2] ' + lastText;
        umtx2LastText = lastText;
      }
    }
  }

  /* Native rendering of p2jb's pinned #livestat readout. Upstream paints an
     ASCII status block once per second:
       "P2JB   total 00:12:03   leak 00:09:41\n<status text>\n"
       "[####....] 43.10%   0.31%/min   ETA 00:38:12 ...\n"
       "OVERALL [####....] 37.4%   step 3/7 (leak)   ~00:41:12 left ..."
     We parse it into the #p2jbStats panel (styled in style.css): phase +
     OVERALL bars, clocks, rate/ETA, worker bars, and detail counters. Every
     write is guarded — no-op DOM writes would only cost shared thread time. */
  var p2jbStats = null;

  function p2jbStatsDom() {
    if (!p2jbStats) {
      var root = document.getElementById('p2jbStats');
      if (!root) return null;
      p2jbStats = {
        root: root,
        stepChip: document.getElementById('p2jbStepChip'),
        clocks: document.getElementById('p2jbClocks'),
        status: document.getElementById('p2jbStatus'),
        detail: document.getElementById('p2jbDetail'),
        groupsBox: document.getElementById('p2jbGroups'),
        cells: null,
        phaseName: document.getElementById('p2jbPhaseName'),
        phasePct: document.getElementById('p2jbPhasePct'),
        phaseFill: document.getElementById('p2jbPhaseFill'),
        phaseMeta: document.getElementById('p2jbPhaseMeta'),
        overallPct: document.getElementById('p2jbOverallPct'),
        overallFill: document.getElementById('p2jbOverallFill'),
        overallMeta: document.getElementById('p2jbOverallMeta')
      };
    }
    return p2jbStats.root ? p2jbStats : null;
  }

  function statText(el, v) {
    if (el && el.textContent !== v) el.textContent = v;
  }

  function statFill(el, frac) {
    /* Quantize to 0.1% (upstream's reporting granularity): stable strings
       for the change-guard, no float noise like scaleX(0.4379999...). */
    var t = 'scaleX(' + Math.round(Math.max(0, Math.min(1, frac)) * 1000) / 1000 + ')';
    if (el.__transform !== t) {
      el.__transform = t;
      el.style.transform = t;
    }
  }

  /* Parse the #livestat text block. Layout (upstream render()):
     line 0        "P2JB   total HH:MM:SS   <phase> HH:MM:SS"
     lines 1..n    status text (multi-line; the leak feed adds byte counters
                   and a "per-core: 12.3% 45.6% ..." worker line)
     next          "[####....] 43.10% ..."   <- CURRENT phase progress
     last          "OVERALL [####....] 37.4% step i/N (phase) ~left"  */
  function parseLivestat(text) {
    var out = {};
    var lines = text.split('\n');
    var head = /^P2JB\s+total\s+(\d{2}:\d{2}:\d{2})\s+(\S+)\s+(\d{2}:\d{2}:\d{2})/
      .exec(lines[0] || '');
    if (head) {
      out.total = head[1];
      out.phaseKey = head[2];
      out.phaseTime = head[3];
    }
    for (var i = 1; i < lines.length; i++) {
      var line = lines[i].trim();
      if (!line) continue;
      if (/^OVERALL\s+\[[#.]*\]/.test(line)) {
        var mo = /OVERALL\s+\[[#.]*\]\s+(\d+(?:\.\d+)?)%\s+step\s+(\d+)\/(\d+)\s+\((\w+)\)\s+~(\d{2}:\d{2}:\d{2})\s+left(?:\s+done\s+~(\d{2}:\d{2}))?/.exec(line);
        if (mo) {
          out.overallPct = parseFloat(mo[1]);
          out.stepNum = parseInt(mo[2], 10);
          out.stepDen = parseInt(mo[3], 10);
          out.stepKey = mo[4];
          out.left = mo[5];
          out.doneClockOverall = mo[6] || '';
        }
      } else if (/^\[[#.]*\]\s+\d/.test(line)) {
        var mp = /\[[#.]*\]\s+(\d+(?:\.\d+)?)%(?:\s+(\d+(?:\.\d+)?)%\/min)?(?:\s+ETA\s+(\S+))?(?:\s+done\s+~(\S+))?(?:\s+\(no progress for (\d+)s\))?/.exec(line);
        if (mp) {
          out.phasePct = mp[1];
          out.ratePerMin = mp[2];
          out.eta = mp[3];
          out.doneClockPhase = mp[4];
          out.stallSecs = mp[5];
        }
      } else if (out.status === undefined) {
        out.status = line;
      } else {
        /* A "label: v v v ..." line of >= 2 percentages is a per-worker
           track (upstream's leak-feed "per-core:" line); anything else is
           detail text. */
        var mg = /^([A-Za-z][\w-]*)\s*:\s*(.+)$/.exec(line);
        if (mg) {
          var pcts = [];
          var gre = /(\d{1,3}(?:\.\d+)?)%/g;
          var gm = gre.exec(mg[2]);
          while (gm !== null) {
            pcts.push(parseFloat(gm[1]));
            gm = gre.exec(mg[2]);
          }
          if (pcts.length >= 2) {
            out.groups = pcts.slice(0, 24);
            continue;
          }
        }
        (out.details = out.details || []).push(line);
      }
    }
    return out;
  }

  function renderP2jbStats(text) {
    var d = p2jbStatsDom();
    if (!d) return;
    var s = parseLivestat(text);

    /* First real data: reveal the panel and shrink the log to the top half
       (body.p2jb-stats in style.css). */
    if (d.root.hidden) {
      d.root.hidden = false;
      document.body.classList.add('p2jb-stats');
    }

    statText(d.clocks, 'total ' + (s.total || '--:--:--')
      + (s.phaseKey ? ' · ' + s.phaseKey + ' ' + s.phaseTime : ''));
    statText(d.stepChip, 'STEP ' + (s.stepNum || '-') + '/' + (s.stepDen || 7));
    statText(d.status, s.status || '…');
    statText(d.phaseName, (s.phaseKey || 'phase').toUpperCase());
    statText(d.phasePct, s.phasePct !== undefined ? s.phasePct + '%' : '–');

    var meta = [];
    if (s.ratePerMin) meta.push(s.ratePerMin + '%/min');
    if (s.eta) meta.push('ETA ' + s.eta);
    if (s.doneClockPhase) meta.push('done ~' + s.doneClockPhase);
    if (s.stallSecs) meta.push('no progress for ' + s.stallSecs + 's');
    var metaCls = 'stats-meta' + (s.stallSecs ? ' stalled' : '');
    statText(d.phaseMeta, meta.join(' · ') || 'ETA --:--:--');
    if (d.phaseMeta.className !== metaCls) d.phaseMeta.className = metaCls;

    statText(d.overallPct, s.overallPct !== undefined
      ? s.overallPct.toFixed(1) + '%' : '–');
    var ometa = [];
    if (s.left) ometa.push('~' + s.left + ' left');
    if (s.doneClockOverall) ometa.push('done ~' + s.doneClockOverall);
    statText(d.overallMeta, ometa.join(' · ') || '– left');

    if (s.phasePct !== undefined) statFill(d.phaseFill, parseFloat(s.phasePct) / 100);
    if (s.overallPct !== undefined) statFill(d.overallFill, s.overallPct / 100);

    renderP2jbDetail(d, s.details);
    renderP2jbGroups(d, s.groups);

    if (s.stepKey && s.stepNum !== undefined) {
      var phaseStep = s.stepNum + '/' + (s.stepDen || 7) + ' ' + s.stepKey;
      if (phaseStep !== p2jbLastPhaseStep) {
        p2jbLastPhaseStep = phaseStep;
        uiLog('[p2jb] phase ' + s.stepKey + ' (step ' + s.stepNum
          + '/' + (s.stepDen || 7) + ') — overall ' + (s.overallPct !== undefined
            ? s.overallPct.toFixed(1) + '%' : '–')
          + (s.left ? ', ~' + s.left + ' left' : ''), 'info');
      }
    }
  }

  function renderP2jbDetail(d, details) {
    var text = details && details.length ? details.join('\n') : '';
    if (!text) {
      if (!d.detail.hidden) d.detail.hidden = true;
      return;
    }
    if (d.detail.hidden) d.detail.hidden = false;
    statText(d.detail, text);
  }

  /* Per-worker strip from upstream's leak-feed "per-core:" line: one bar
     per worker with its live percentage inside. Cells are rebuilt only when
     the worker count changes; every write is change-guarded. */
  function renderP2jbGroups(d, groups) {
    if (!groups || !groups.length) {
      d.cells = null;
      if (!d.groupsBox.hidden) d.groupsBox.hidden = true;
      return;
    }
    if (d.groupsBox.hidden) d.groupsBox.hidden = false;
    if (!d.cells || d.cells.length !== groups.length) {
      d.groupsBox.textContent = '';
      d.cells = [];
      for (var i = 0; i < groups.length; i++) {
        var cell = document.createElement('span');
        cell.className = 'group';
        var track = document.createElement('span');
        track.className = 'gtrack';
        var fill = document.createElement('span');
        fill.className = 'stats-fill';
        var pct = document.createElement('span');
        pct.className = 'gpct';
        track.appendChild(fill);
        track.appendChild(pct);
        cell.appendChild(track);
        d.groupsBox.appendChild(cell);
        d.cells.push({ fill: fill, pct: pct });
      }
    }
    for (var j = 0; j < d.cells.length; j++) {
      statFill(d.cells[j].fill, (groups[j] || 0) / 100);
      statText(d.cells[j].pct, (groups[j] || 0).toFixed(1) + '%');
    }
  }

  /* Win: pin the panel green at 100% until the autoload result lands
     (~4 s later), then collapseP2jbStats() restores the classic layout. */
  function completeP2jbStats() {
    var d = p2jbStatsDom();
    if (!d) return;
    document.body.classList.add('p2jb-done');
    d.status.className = 'stats-status';
    statText(d.status, 'ELF LOADER READY');
    statText(d.phaseName, 'COMPLETE');
    statText(d.phasePct, '100%');
    statText(d.overallPct, '100%');
    statText(d.phaseMeta, '');
    statText(d.overallMeta, 'elfldr ready — sending payload…');
    statFill(d.phaseFill, 1);
    statFill(d.overallFill, 1);
  }

  function collapseP2jbStats() {
    document.body.classList.remove('p2jb-stats');
    document.body.classList.remove('p2jb-done');
    if (p2jbStats && p2jbStats.root && !p2jbStats.root.hidden) {
      p2jbStats.root.hidden = true;
    }
  }

  /* Mirror p2jb's ~1 h run from the same-origin exploit iframe into our UI.
     p2jb renders a pinned progress readout (#livestat, repainted by
     upstream's 1 Hz ticker) with a per-phase bar and an OVERALL line:
       "P2JB   total 00:12:03   leak 00:09:41\n<phase text>\n"
       "[####....] 43.10%   0.31%/min   ETA 00:38:12 ...\n"
       "OVERALL [####....] 37.4%   step 3/7 (leak)   ~00:41:12 left ..."
     renderP2jbStats() mirrors it into #p2jbStats; screen/stage/summary/early
     mirroring works like the poops one, with a p2jb-specific curated mark
     filter (upstream's log=debug screen would otherwise flood us). */
  var p2jbMirroredLines = 0;
  var p2jbLastStageText = '';
  var p2jbLastStageCls = '';
  var p2jbLastSummaryText = '';
  var p2jbEarlyLinesLogged = 0;
  var p2jbLastPhaseStep = '';
  var p2jbComplete = false;
  function mirrorP2jb() {
    var doc;
    try {
      doc = exploitEl.contentDocument;
    } catch (e) {
      return;
    }
    if (!doc) return;

    /* Detect iframe navigation/reload: reset the mirrors so a fresh document
       (or a crash restore) streams its log from the top. */
    var frameUrl = '';
    try {
      frameUrl = exploitEl.contentWindow.location.href;
    } catch (e) { }
    if (frameUrl !== lastFrameUrl) {
      lastFrameUrl = frameUrl;
      p2jbMirroredLines = 0;
      p2jbLastStageText = '';
      p2jbLastStageCls = '';
      p2jbLastSummaryText = '';
      p2jbEarlyLinesLogged = 0;
      p2jbLastPhaseStep = '';
      p2jbComplete = false;
    }
    /* The iframe is intentionally empty until the chain is armed — nothing
       to mirror yet. */
    if (!chainStarted) return;

    var scr = doc.getElementById('scr');
    if (!scr) {
      /* #scr is static HTML in p2jb.html — while it parses, earlier elements
         and <title> are already present, so a poll can briefly see "p2jb
         page without its screen". Same for the blank pre-navigation
         document. Never warn or re-arm during these windows: re-arming
         reloads the exploit a second time (and the log doubles). */
      var isArmedUrl = frameUrl.length > EXPLOIT_URL.length &&
        frameUrl.slice(-EXPLOIT_URL.length) === EXPLOIT_URL;
      if (frameUrl === 'about:blank' || doc.readyState !== 'complete'
        || isArmedUrl) {
        return;
      }
      /* Only reached when the iframe settled on a *different* page: slopkit's
         landing page, a not-armed p2jb.html, or a 404. */
      var arm = doc.getElementById('arm');
      var runP2jb = doc.getElementById('run-p2jb');
      var title = doc.title || '';
      if (mirrorP2jb.warned !== frameUrl) {
        mirrorP2jb.warned = frameUrl;
        if (runP2jb) {
          uiLog('[iframe] slopkit landing page loaded — chain not started.', 'warning');
        } else if (arm && !arm.hidden) {
          uiLog('[iframe] p2jb page is NOT armed (?go=1 missing) — nothing will run.', 'warning');
        } else if (title.indexOf('slopkit') !== -1) {
          uiLog('[iframe] p2jb page loaded without its screen (title="' + title + '").', 'warning');
        } else {
          uiLog('[iframe] page has no p2jb screen: title="' + title + '"', 'warning');
        }
      }
      /* Re-arm only for a wrong *slopkit* page (landing page or not-armed
         p2jb.html) — never for the armed URL itself. */
      var isSlopkitPage = !!runP2jb || (arm && !arm.hidden);
      if (chainStarted && isSlopkitPage && repairCount < 5) {
        repairCount++;
        uiLog('[iframe] re-arming (attempt ' + repairCount + '): ' + EXPLOIT_URL, 'info');
        try {
          exploitEl.src = EXPLOIT_URL;
        } catch (e) {
          uiLog('[iframe] re-arm failed: ' + (e && e.message ? e.message : e), 'error');
        }
      } else if (chainStarted && isSlopkitPage) {
        uiLog('[iframe] giving up after ' + repairCount + ' re-arm attempts.', 'error');
      }
      return;
    }

    /* Live progress: mirror #livestat into our native stats panel. The
       element only exists once the first real phase starts; before that the
       stage text carries the status. Upstream's 1 Hz ticker keeps repainting
       #livestat even after the win, so stop once the chain is complete and
       let the stage/autoload messages own the UI again. */
    var live = doc.getElementById('livestat');
    if (live && live.textContent && !p2jbComplete) {
      renderP2jbStats(live.textContent);
    }

    var lines = scr.textContent.split('\n');
    /* If the screen shrank (p2jb caps its log at 12 lines and drops the
       oldest ones, or a fresh document replaced it), re-anchor the counter
       WITHOUT re-logging — the remaining lines were already streamed. */
    if (lines.length < p2jbMirroredLines) {
      p2jbMirroredLines = lines.length;
    }
    for (; p2jbMirroredLines < lines.length; p2jbMirroredLines++) {
      var line = lines[p2jbMirroredLines].trim();
      if (!line) continue;
      /* Curated release log: milestone marks and failures only. The verbose
         debug stream (LEAK-/SPRAY-/TRIPLET/PROGRESS every 15 s, ...) stays
         off our log — the livestat bar above carries the live progress. */
      if (/^(POOPS-BOOT|OFFSETS-READY|TRIGGER-ARMED|TRIGGER-FIRED|LATCH-SET|LATCH-ESCALATE|LATCH-CLEAR|LATCH-HELD|LATCH-RELEASED|POOPS-LATCHED|POOPS-STALLED|BOOT-STALLED|CHAIN-DEAD|STAGE5-DONE|POOPS-COMPLETE|POOPS-FAILED|ELFLDR-MENU-VISIBLE|ELFLDR-UP|ELF-SENT|ELF-SEND-FAILED|ELF-SENDER-BLOCKED|KEXP-JOIN|KEXP-JOIN-PRE|KEXP-SPAWN|KEXP-ELF|AUTOLOAD-OK|AUTOLOAD-FAILED)/.test(line)) {
        uiLog('[log] ' + line, 'info');
      } else if (/FAIL|ERROR|REFUSED|REBOOT|failed|panic|exception/i.test(line)
        || /^\[-\]/.test(line)) {
        uiLog('[log] ' + line, 'error');
      }
    }

    var stage = doc.getElementById('stage');
    if (stage && stage.textContent !== p2jbLastStageText) {
      p2jbLastStageText = stage.textContent;
      p2jbLastStageCls = stage.className || '';
      /* The panel owns progress while it is up (the slim bar is hidden via
         body.p2jb-stats); before livestat exists (early boot) and after the
         collapse, mirror the stage text into our label instead. */
      if (!live || p2jbComplete) {
        progressLabel.textContent = p2jbLastStageText;
      }
      /* showWin() fires on every win path (KEXP-JOIN detection and the
         already-jailbroken shortcut) — latch completion here so the
         autoload flow owns the UI from this point on. */
      if (!p2jbComplete && p2jbLastStageText.indexOf('ELF LOADER READY') !== -1) {
        p2jbComplete = true;
        progressBar.style.transform = 'scaleX(1)';
        uiLog('[p2jb] exploit complete — elfldr ready.', 'success');
        /* Pin the panel green at 100% until the autoload result lands, then
           onAutoloadResult collapses back to the classic full-height log.
           The iframe stays loaded — it holds the ROP workers/threads. */
        completeP2jbStats();
      }
      if (p2jbLastStageCls.indexOf('bad') !== -1) {
        uiLog('[stage] ' + p2jbLastStageText, 'error');
        /* Tint the panel status red so a mid-run failure is visible there
           too (the panel stays up for diagnostics on failures). */
        if (p2jbStats && p2jbStats.status) {
          p2jbStats.status.className = 'stats-status bad';
        }
      } else if (p2jbLastStageCls.indexOf('ok') !== -1) {
        uiLog('[stage] ' + p2jbLastStageText, 'success');
      } else {
        uiLog('[stage] ' + p2jbLastStageText, 'info');
      }
    }

    /* Mirror the summary block (verdict details) when it changes. */
    var summary = doc.getElementById('summary');
    if (summary && summary.textContent && summary.textContent !== p2jbLastSummaryText) {
      var summaryLines = summary.textContent.split('\n');
      for (var i = 0; i < summaryLines.length; i++) {
        var sline = summaryLines[i].trim();
        if (sline && /FAIL|ERROR|REFUSED|REBOOT|failed|panic/i.test(sline)) {
          uiLog('[summary] ' + sline, 'error');
        }
      }
      p2jbLastSummaryText = summary.textContent;
    }

    /* Mirror the #early log (errors/notices written before the module chain
       runs). p2jb only ever appends to #early, so log just the new tail. */
    var early = doc.getElementById('early');
    if (early && early.textContent) {
      var earlyLines = early.textContent.split('\n');
      if (earlyLines.length < p2jbEarlyLinesLogged) {
        p2jbEarlyLinesLogged = 0;
      }
      for (; p2jbEarlyLinesLogged < earlyLines.length; p2jbEarlyLinesLogged++) {
        var eline = earlyLines[p2jbEarlyLinesLogged].trim();
        if (eline) {
          uiLog('[early] ' + eline, /ERROR|FAIL/i.test(eline) ? 'error' : 'info');
        }
      }
    }
  }

  function mirrorExploit() {
    if (exploitMode === 'umtx2') {
      mirrorUmtx2();
      return;
    }
    if (exploitMode === 'p2jb') {
      mirrorP2jb();
      return;
    }
    mirrorSlopkit();
  }

  function launchSelected(payload, label, forceJailbreak) {
    selectedPayload = payload;
    selectedLabel = label;
    var activeCard = document.querySelector('.payloadCard[data-payload="' + payload + '"]');
    if (activeCard) activeCard.classList.add('active-launch');
    finished = false;
    chainStarted = false;
    mirroredLines = 0;
    repairCount = 0;
    if (goldenStateEl) goldenStateEl.textContent = forceJailbreak ? 'JAILBREAK IN PROGRESS' : 'LAUNCHING · ' + label.toUpperCase();
    if (headerStateEl) headerStateEl.textContent = forceJailbreak ? 'JAILBREAK RUNNING' : 'PAYLOAD RUNNING';
    if (exploitValueEl) exploitValueEl.textContent = forceJailbreak ? 'RUNNING' : (hasKnownSession() ? 'EXPLOIT OK' : 'STARTING');
    if (payloadValueEl) payloadValueEl.textContent = label.toUpperCase();
    var initialProgress = !forceJailbreak && hasKnownSession() ? 68 : 4;
    updateProgress(initialProgress, forceJailbreak
      ? (autoMode ? 'Preparing Auto Jailbreak...' : 'Preparing Jailbreak...')
      : 'Preparing ' + label + '...');

    var picked = pickExploit();
    if (!picked) {
      updateProgress(0, 'Unsupported firmware.');
      return;
    }
    exploitMode = picked;
    EXPLOIT_URL = picked === 'umtx2' ? umtx2Url(selectedPayload)
      : picked === 'p2jb' ? p2jbUrl(selectedPayload)
        : poopsUrl(selectedPayload);

    if (mirrorTimer) clearInterval(mirrorTimer);
    mirrorTimer = setInterval(mirrorExploit, picked === 'p2jb' ? 1000 : 500);
    try {
      if (picked === 'umtx2') {
        var senderOnly = !forceJailbreak && hasKnownSession();
        sessionStorage.setItem('on_load_autorun', senderOnly ? 'wkonly' : 'kernel');
        sessionStorage.setItem('wkal_autoload', selectedPayload);
      } else {
        sessionStorage.removeItem('on_load_autorun');
        sessionStorage.removeItem('wkal_autoload');
      }
      if (forceJailbreak) {
        sessionStorage.removeItem(SESSION_KEY);
        sessionStorage.removeItem(ACTIVE_PAYLOAD_KEY);
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(ACTIVE_PAYLOAD_KEY);
      }
    } catch (e) { }

    chainStarted = true;
    if (picked === 'poops' || picked === 'p2jb') clearSlopkitState();
    try { exploitEl.src = EXPLOIT_URL; } catch (e) { }
    revealExploit();
  }

  function beginPayloadLaunch(payload, label, forceJailbreak) {
    if (forceJailbreak && payload !== 'payload.elf' && pickExploit() === 'umtx2') {
      queuedAutoPayload = { payload: payload, label: label };
      launchSelected('payload.elf', 'Jailbreak Stage', true);
      return;
    }
    queuedAutoPayload = null;
    launchSelected(payload, label, forceJailbreak);
  }

  function closeRiskDialog() {
    pendingRiskLaunch = null;
    if (riskDialogEl) riskDialogEl.hidden = true;
  }

  function requestPayloadLaunch(payload, label, risk, forceJailbreak) {
    if (!risk) {
      beginPayloadLaunch(payload, label, !!forceJailbreak);
      return;
    }
    var active = '';
    try { active = sessionStorage.getItem(ACTIVE_PAYLOAD_KEY) || localStorage.getItem(ACTIVE_PAYLOAD_KEY) || ''; } catch (e) { }
    pendingRiskLaunch = { payload: payload, label: label, force: !!forceJailbreak };
    if (riskMessageEl) {
      if (risk === 'kstuff') {
        riskMessageEl.textContent = (active.indexOf('etahen') !== -1
          ? 'etaHEN appears to be active. Do not stack Kstuff over etaHEN. Fully reboot the PS5 first, reopen Goldengames, then continue only if this is a fresh session.'
          : 'Kstuff modifies the active kernel session. Fully reboot before switching between etaHEN, Kstuff and Kstuff Lite. Continue only from a fresh session.');
      } else if (risk === 'kernel') {
        riskMessageEl.textContent = 'Another HEN or kernel payload may already be active. Fully reboot before switching between etaHEN, OnionHEN, PIZZA-HEN, or Kstuff. Continue only from a fresh session.';
      } else {
        riskMessageEl.textContent = 'Linux Loader can conflict with etaHEN or Kstuff. Use a fresh console session and do not launch it after another kernel payload.';
      }
    }
    if (riskContinueEl) riskContinueEl.textContent = (risk === 'kstuff' || risk === 'kernel') ? '× I REBOOTED · CONTINUE' : '× FRESH SESSION · CONTINUE';
    if (riskDialogEl) riskDialogEl.hidden = false;
    if (riskCancelEl) riskCancelEl.focus();
  }

  function start() {
    uiLog('Goldengames PS5 Jailbreak v1.1.1', 'success');
    updateProgress(0, 'Ready.');
    /* A page reload between the lightweight stage and the final payload must
       never be displayed as a completed jailbreak session. */
    try {
      var restoredPayload = sessionStorage.getItem(ACTIVE_PAYLOAD_KEY)
        || localStorage.getItem(ACTIVE_PAYLOAD_KEY) || '';
      if (restoredPayload === 'payload.elf') {
        sessionStorage.removeItem(SESSION_KEY);
        sessionStorage.removeItem(ACTIVE_PAYLOAD_KEY);
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(ACTIVE_PAYLOAD_KEY);
      }
    } catch (e) { }
    var detected = detectFirmware();
    if (firmwareValueEl) firmwareValueEl.textContent = detected ? detected.str : 'UNKNOWN';
    updateModeUi();
    setInterval(function () {
      if (uptimeValueEl) uptimeValueEl.textContent = formatUptime(Date.now() - operationStartedAt);
    }, 1000);

    window.addEventListener('message', function (event) {
      var data = event.data;
      if (!data) return;
      /* send-complete is diagnostic only. Firmware 5.10 remains inside the
         active sender at that point; cleanup waits for the final WKAL result. */
      if (data.type === 'goldengames-diag') return;
      if (data.type !== 'wkal') return;
      if (data.kind === 'autoload') {
        onAutoloadResult(data);
      }
    });

    /* No iframe 'load' listener: its mirroredLines reset re-streamed the
       whole screen mid-run (doubling the log), and the other state resets
       are already handled by the URL-diff branch in mirrorSlopkit() plus
       the shrink re-anchor (fresh documents start with an empty screen,
       so their lines stream normally). */

    if (payloadSelectEl) payloadSelectEl.addEventListener('change', function () {
      selectedPayload = this.value;
      selectedLabel = this.options[this.selectedIndex].text;
    });
    if (launchPayloadEl) launchPayloadEl.addEventListener('click', function () {
      var opt = payloadSelectEl.options[payloadSelectEl.selectedIndex];
      var value = payloadSelectEl.value;
      var risk = value.indexOf('kstuff') !== -1 ? 'kstuff' : value.indexOf('linux-loader') !== -1 ? 'linux' : '';
      requestPayloadLaunch(value, opt.text, risk, false);
    });
    if (autoJailbreakEl) autoJailbreakEl.addEventListener('click', function () {
      startAutoJailbreak();
    });
    if (showDetailsEl) showDetailsEl.addEventListener('click', function () {
      document.body.classList.toggle('details-open');
      this.textContent = document.body.classList.contains('details-open') ? '□ HIDE DETAILS' : '□ SHOW DETAILS';
    });
    if (backToMenuEl) backToMenuEl.addEventListener('click', function () {
      document.body.classList.remove('details-open');
      if (showDetailsEl) showDetailsEl.textContent = '□ SHOW DETAILS';
    });
    if (autoModeToggleEl) autoModeToggleEl.addEventListener('click', function () {
      autoMode = !autoMode;
      try {
        localStorage.setItem(AUTO_MODE_KEY, autoMode ? '1' : '0');
        localStorage.setItem(AUTO_PAYLOAD_KEY, selectedPayload);
      } catch (e) { }
      updateModeUi();
    });
    var launchCards = document.querySelectorAll('.payloadCard[data-payload]');
    for (var c = 0; c < launchCards.length; c++) {
      launchCards[c].addEventListener('click', function () {
        selectPayload(this);
        try { localStorage.setItem(AUTO_PAYLOAD_KEY, selectedPayload); } catch (e) { }
        requestPayloadLaunch(selectedPayload, selectedLabel, this.getAttribute('data-risk') || '', !hasKnownSession());
      });
    }
    if (riskCancelEl) riskCancelEl.addEventListener('click', closeRiskDialog);
    if (riskContinueEl) riskContinueEl.addEventListener('click', function () {
      var pending = pendingRiskLaunch;
      if (!pending) return closeRiskDialog();
      pendingRiskLaunch = null;
      if (riskDialogEl) riskDialogEl.hidden = true;
      try {
        sessionStorage.removeItem(SESSION_KEY);
        sessionStorage.removeItem(ACTIVE_PAYLOAD_KEY);
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(ACTIVE_PAYLOAD_KEY);
      } catch (e) { }
      beginPayloadLaunch(pending.payload, pending.label, pending.force);
    });

    if (hasKnownSession()) {
      if (exploitValueEl) exploitValueEl.textContent = 'EXPLOIT OK';
      if (goldenStateEl) goldenStateEl.textContent = 'PAYLOADS READY';
      updateProgress(100, 'Session ready.');
    }
    try {
      autoMode = localStorage.getItem(AUTO_MODE_KEY) === '1';
      var savedPayload = localStorage.getItem(AUTO_PAYLOAD_KEY);
      var savedCard = savedPayload && document.querySelector('.payloadCard[data-payload="' + savedPayload + '"]');
      if (savedCard) selectPayload(savedCard);
    } catch (e) { }
    updateModeUi();
    setTimeout(showDashboard, 150);
    if (autoMode) {
      setTimeout(function () {
        requestPayloadLaunch(selectedPayload, selectedLabel,
          (document.querySelector('.payloadCard.selected') || {}).getAttribute
            ? document.querySelector('.payloadCard.selected').getAttribute('data-risk') || ''
            : '', !hasKnownSession());
      }, 1400);
    }
  }

  window.addEventListener('load', start);
})();
