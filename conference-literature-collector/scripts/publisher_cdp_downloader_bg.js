const fs = require('fs');
const path = require('path');

const ROOT = process.cwd();
const METADATA = path.join(ROOT, process.env.METADATA_FILE || path.join('metadata', 'papers.json'));
const LOG_CSV = path.join(ROOT, process.env.DOWNLOAD_LOG || path.join('logs', 'download_report.csv'));
const OUT_CSV = path.join(ROOT, process.env.BROWSER_LOG || path.join('logs', 'browser_download_report.csv'));
const PAPERS = path.resolve(ROOT, process.env.PAPERS_DIR || 'papers');
const CDP_PORT = Number(process.env.CDP_PORT || '9333');
const MAX = Number(process.env.MAX || '0');
const START = Number(process.env.START || '0');
const DELAY_MS = Number(process.env.DELAY_MS || '700');
const FETCH_TIMEOUT_MS = Number(process.env.FETCH_TIMEOUT_MS || '90000');
const IDS = String(process.env.ONLY_IDS || '')
  .split(',')
  .map(s => s.trim())
  .filter(Boolean);

if (process.argv.includes('--help') || process.argv.includes('-h')) {
  console.log(`Usage: node publisher_cdp_downloader_bg.js

Download publisher PDFs through an existing isolated CDP browser.

Environment:
  CDP_PORT       CDP port from logs/browser_session.json, default 9333
  METADATA_FILE  metadata JSON path, default metadata/papers.json
  DOWNLOAD_LOG   prior download log CSV, default logs/download_report.csv
  BROWSER_LOG    output browser download log CSV, default logs/browser_download_report.csv
  PAPERS_DIR     PDF output directory, default papers
  ONLY_IDS       comma-separated paper IDs to retry
  MAX            maximum records to process
  START          starting record offset`);
  process.exit(0);
}

fs.mkdirSync(PAPERS, { recursive: true });

function slugify(value, maxLen = 72) {
  return (value || 'paper')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/-+/g, '-')
    .replace(/^-|-$/g, '')
    .slice(0, maxLen)
    .replace(/-$/, '') || 'paper';
}
function doiSafe(doi) { return String(doi || '').replace(/[^A-Za-z0-9.]+/g, '_').replace(/^_+|_+$/g, ''); }
function arnumberFromDoi(doi) { const m = String(doi || '').match(/\.(\d{7,})$/); return m ? m[1] : null; }
function csvEscape(v) { v = String(v ?? ''); return /[",\r\n]/.test(v) ? '"' + v.replace(/"/g, '""') + '"' : v; }
function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

function parseCsv(text) {
  text = text.replace(/^\uFEFF/, '');
  const rows = [];
  let row = [], cur = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) {
      if (c === '"' && text[i + 1] === '"') { cur += '"'; i++; }
      else if (c === '"') q = false;
      else cur += c;
    } else {
      if (c === '"') q = true;
      else if (c === ',') { row.push(cur); cur = ''; }
      else if (c === '\n') { row.push(cur.replace(/\r$/, '')); rows.push(row); row = []; cur = ''; }
      else cur += c;
    }
  }
  if (cur.length || row.length) { row.push(cur.replace(/\r$/, '')); rows.push(row); }
  const header = rows.shift() || [];
  return rows.filter(r => r.length && r.some(x => x)).map(r => Object.fromEntries(header.map((h, i) => [h, r[i] || ''])));
}

function writeCsv(file, rows, header) {
  const body = [header.join(','), ...rows.map(r => header.map(h => csvEscape(r[h])).join(','))].join('\n') + '\n';
  fs.writeFileSync(file, '\uFEFF' + body, 'utf8');
}

function isPdfFile(file) {
  try {
    const st = fs.statSync(file);
    if (st.size <= 10000) return false;
    const fd = fs.openSync(file, 'r');
    const b = Buffer.alloc(5);
    fs.readSync(fd, b, 0, 5, 0);
    fs.closeSync(fd);
    return b.toString() === '%PDF-';
  } catch {
    return false;
  }
}

class CDP {
  constructor(wsUrl) {
    this.wsUrl = wsUrl;
    this.nextId = 1;
    this.pending = new Map();
    this.listeners = [];
  }
  async open() {
    this.ws = new WebSocket(this.wsUrl);
    this.ws.onmessage = ev => {
      const msg = JSON.parse(ev.data);
      if (msg.id && this.pending.has(msg.id)) {
        this.pending.get(msg.id)(msg);
        this.pending.delete(msg.id);
      }
      for (const fn of this.listeners) fn(msg);
    };
    await new Promise((resolve, reject) => {
      this.ws.onopen = resolve;
      this.ws.onerror = reject;
    });
  }
  on(fn) { this.listeners.push(fn); }
  send(method, params = {}, sessionId, timeoutMs = 90000) {
    const id = this.nextId++;
    const payload = { id, method, params };
    if (sessionId) payload.sessionId = sessionId;
    this.ws.send(JSON.stringify(payload));
    return new Promise((resolve, reject) => {
      const timer = setTimeout(() => {
        this.pending.delete(id);
        reject(new Error(`CDP timeout: ${method}`));
      }, timeoutMs);
      this.pending.set(id, msg => {
        clearTimeout(timer);
        resolve(msg);
      });
    });
  }
  close() { try { this.ws.close(); } catch {} }
}

function publisherFor(record) {
  const doi = String(record.doi || '');
  const publisher = String(record.publisher || '').toLowerCase();
  if (publisher.includes('ieee') || doi.startsWith('10.1109/')) return 'ieee';
  if (publisher.includes('acm') || doi.startsWith('10.1145/')) return 'acm';
  return 'other';
}

function recordId(record, index = 0) {
  return String(record.paper_id || record.id || record.session_paper_id || record.doi || `paper-${index + 1}`);
}

function collectionFor(record) {
  if (record.collection) return String(record.collection);
  const venue = record.venue_slug || record.conference || record.venue || 'venue';
  return `${slugify(String(venue))}-${record.year || 'unknown-year'}`;
}

function logKey(record) {
  return `${collectionFor(record)}::${recordId(record)}`;
}

function makeFilename(record) {
  const doiPart = doiSafe(record.doi);
  return `${slugify(recordId(record), 40)}__${slugify(record.title)}${doiPart ? `__${doiPart}` : ''}.pdf`;
}

function publisherDownloadExpression(filename) {
  return `(async()=>{
    const filename=${JSON.stringify(filename)};
    const timeoutMs=${FETCH_TIMEOUT_MS};
    async function fetchWithTimeout(url, opts={}) {
      const ctrl = new AbortController();
      const timer = setTimeout(() => ctrl.abort('timeout'), timeoutMs);
      try { return await fetch(url, {...opts, signal: ctrl.signal}); }
      finally { clearTimeout(timer); }
    }
    function absolute(url) { return new URL(url, location.href).href; }
    const meta = document.querySelector('meta[name="citation_pdf_url"]');
    const links = [...document.querySelectorAll('a[href]')].map(a => ({
      href: a.getAttribute('href') || '',
      text: (a.textContent || '').trim(),
      title: a.getAttribute('title') || '',
      aria: a.getAttribute('aria-label') || ''
    }));
    let candidates = [];
    if (meta && meta.content) candidates.push(meta.content);
    for (const link of links) {
      const hay = (link.text + ' ' + link.title + ' ' + link.aria).toLowerCase();
      if (/\\/doi\\/pdf\\//.test(link.href) || hay.includes('pdf') || hay.includes('download')) candidates.push(link.href);
    }
    candidates = [...new Set(candidates.filter(Boolean).map(absolute))];
    let pdfUrl = candidates.find(u => /\\/doi\\/pdf\\//.test(u)) || candidates[0] || '';
    if (!pdfUrl && /\\/doi\\//.test(location.pathname)) pdfUrl = absolute(location.pathname.replace('/doi/', '/doi/pdf/'));
    if (!pdfUrl) return {ok:false, reason:'no publisher PDF link found on page', url:location.href};
    const resp = await fetchWithTimeout(pdfUrl, {credentials:'include', headers:{Accept:'application/pdf,*/*'}});
    const contentType = resp.headers.get('content-type') || '';
    const blob = await resp.blob();
    if (!contentType.includes('pdf') || blob.size < 10000) {
      return {ok:false, reason:'publisher response was not a PDF', pdfUrl, status:resp.status, contentType, size:blob.size};
    }
    const objectUrl = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = objectUrl;
    a.download = filename;
    a.style.display = 'none';
    document.body.appendChild(a);
    a.click();
    setTimeout(() => { URL.revokeObjectURL(objectUrl); a.remove(); }, 30000);
    return {ok:true, pdfUrl, status:resp.status, contentType, size:blob.size};
  })()`;
}

function ieeeStampLinkExpression(ar) {
  return `(() => {
    const links = [...document.querySelectorAll('a[href]')].map(a => ({
      href: a.getAttribute('href') || '',
      text: (a.textContent || '').trim(),
      title: a.getAttribute('title') || '',
      aria: a.getAttribute('aria-label') || ''
    }));
    let stampUrl = '';
    for (const link of links) {
      const hay = (link.text + ' ' + link.title + ' ' + link.aria).toLowerCase();
      if (link.href && link.href.toLowerCase().includes('/stamp/stamp.jsp') && (hay.includes('pdf') || hay.includes('download'))) {
        stampUrl = new URL(link.href, location.href).href;
        break;
      }
    }
    if (!stampUrl) stampUrl = 'https://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber=' + encodeURIComponent(${JSON.stringify(ar)});
    return { ok: !!stampUrl, stampUrl, pageUrl: location.href, title: document.title };
  })()`;
}

function ieeePdfFromStampExpression() {
  return `(async()=>{
    let pdfUrl = '';
    const iframe = [...document.querySelectorAll('iframe[src]')].find(f => /pdf|getpdf|stamp/i.test(f.src)) || document.querySelector('iframe[src]');
    if (iframe && iframe.src) pdfUrl = iframe.src;
    if (!pdfUrl) {
      const links = [...document.querySelectorAll('a[href]')].map(a => ({
        href: a.getAttribute('href') || '',
        text: (a.textContent || '').trim(),
        title: a.getAttribute('title') || '',
        aria: a.getAttribute('aria-label') || ''
      }));
      for (const link of links) {
        const hay = (link.text + ' ' + link.title + ' ' + link.aria + ' ' + link.href).toLowerCase();
        if (link.href && (hay.includes('pdf') || hay.includes('download'))) {
          pdfUrl = new URL(link.href, location.href).href;
          if (pdfUrl.toLowerCase().includes('.pdf') || pdfUrl.toLowerCase().includes('getpdf') || pdfUrl.toLowerCase().includes('pdf')) break;
        }
      }
    }
    if (!pdfUrl) return {ok:false, reason:'no_iframe_or_pdf_link', url:location.href, title:document.title, sample:document.documentElement.outerHTML.slice(0,500)};
    pdfUrl = new URL(pdfUrl.replace(/&amp;/g,'&'), location.href).href;
    const resp=await fetch(pdfUrl,{credentials:'include',headers:{Accept:'application/pdf,*/*'}});
    const contentType=resp.headers.get('content-type')||'';
    const blob=await resp.blob();
    if(!contentType.includes('pdf') || blob.size < 10000) return {ok:false, reason:'not_pdf', status:resp.status, contentType, size:blob.size, pdfUrl};
    const buf=await blob.arrayBuffer();
    let binary='';
    const bytes=new Uint8Array(buf);
    const chunk=0x8000;
    for(let i=0;i<bytes.length;i+=chunk){ binary += String.fromCharCode(...bytes.subarray(i, i+chunk)); }
    const base64=btoa(binary);
    window.__pdfStore = { base64, pdfUrl, size: blob.size };
    return {ok:true, pdfUrl, size:blob.size, len:base64.length};
  })()`;
}

async function pullStoredBase64(cdp, sessionId, chunkSize = 400000) {
  const metaResp = await cdp.send('Runtime.evaluate', {
    expression: `window.__pdfStore ? ({ len: window.__pdfStore.base64.length, pdfUrl: window.__pdfStore.pdfUrl, size: window.__pdfStore.size }) : null`,
    returnByValue: true
  }, sessionId, 30000);
  const meta = metaResp.result && metaResp.result.result && metaResp.result.result.value;
  if (!meta || !meta.len) throw new Error('window.__pdfStore was not populated');
  const parts = [];
  for (let offset = 0; offset < meta.len; offset += chunkSize) {
    const sliceResp = await cdp.send('Runtime.evaluate', {
      expression: `window.__pdfStore.base64.slice(${offset}, ${offset + chunkSize})`,
      returnByValue: true
    }, sessionId, 30000);
    const part = sliceResp.result && sliceResp.result.result && sliceResp.result.result.value;
    if (typeof part !== 'string') throw new Error(`invalid base64 slice at offset ${offset}`);
    parts.push(part);
  }
  await cdp.send('Runtime.evaluate', { expression: 'window.__pdfStore = null; true', returnByValue: true }, sessionId, 30000);
  return { pdfUrl: meta.pdfUrl, size: meta.size, base64: parts.join('') };
}

async function waitForDownload(downloads, filename, before, timeoutMs = 180000) {
  const start = Date.now();
  while (Date.now() - start < timeoutMs) {
    for (const d of downloads.values()) {
      if (d.startedAt >= before && (d.suggestedFilename === filename || d.filename === filename)) {
        if (d.state === 'completed') return d;
        if (d.state === 'canceled') throw new Error(`download canceled: ${filename}`);
      }
    }
    await sleep(500);
  }
  throw new Error(`download event timeout: ${filename}`);
}

async function main() {
  const metadata = JSON.parse(fs.readFileSync(METADATA, 'utf8'));
  const candidates = metadata
    .map((record, index) => ({ ...record, paper_id: recordId(record, index) }))
    .filter(r => r.doi || r.doi_url || r.ee_url || r.citation_pdf_url);
  const slice = IDS.length > 0
    ? candidates.filter(r => IDS.includes(recordId(r)))
    : (MAX > 0 ? candidates.slice(START, START + MAX) : candidates.slice(START));

  const version = await (await fetch(`http://127.0.0.1:${CDP_PORT}/json/version`)).json();
  const cdp = new CDP(version.webSocketDebuggerUrl);
  await cdp.open();
  const downloads = new Map();
  cdp.on(msg => {
    if (msg.method === 'Browser.downloadWillBegin') {
      downloads.set(msg.params.guid, {
        guid: msg.params.guid,
        suggestedFilename: msg.params.suggestedFilename,
        startedAt: Date.now(),
        state: 'started'
      });
    }
    if (msg.method === 'Browser.downloadProgress') {
      const d = downloads.get(msg.params.guid) || { guid: msg.params.guid, startedAt: Date.now() };
      d.state = msg.params.state;
      downloads.set(msg.params.guid, d);
    }
  });
  await cdp.send('Browser.setDownloadBehavior', { behavior: 'allow', downloadPath: PAPERS, eventsEnabled: true });
  const target = await cdp.send('Target.createTarget', { url: 'about:blank' });
  const targetId = target.result.targetId;
  const attached = await cdp.send('Target.attachToTarget', { targetId, flatten: true });
  const sessionId = attached.result.sessionId;
  await cdp.send('Page.enable', {}, sessionId);
  await cdp.send('Runtime.enable', {}, sessionId);

  const header = ['collection', 'paper_id', 'title', 'doi', 'doi_url', 'ee_url', 'source_url', 'download_status', 'pdf_path', 'failure_reason'];
  let browserRows = [];
  if (fs.existsSync(OUT_CSV)) browserRows = parseCsv(fs.readFileSync(OUT_CSV, 'utf8'));
  const byId = new Map(browserRows.map(r => [logKey(r), r]));

  function flushLogs() {
    const ordered = Array.from(byId.values()).sort((a, b) => String(a.paper_id).localeCompare(String(b.paper_id), undefined, { numeric: true }));
    writeCsv(OUT_CSV, ordered, header);
    if (fs.existsSync(LOG_CSV)) {
      const mainRows = parseCsv(fs.readFileSync(LOG_CSV, 'utf8'));
      const byMainId = new Map(ordered.map(r => [logKey(r), r]));
      for (const row of mainRows) {
        const hit = byMainId.get(logKey(row));
        if (hit && hit.download_status.startsWith('downloaded_')) {
          row.source_url = hit.source_url;
          row.download_status = hit.download_status;
          row.pdf_path = hit.pdf_path;
          row.failure_reason = '';
        }
      }
      writeCsv(LOG_CSV, mainRows, header);
    }
  }

  for (let i = 0; i < slice.length; i++) {
    const rec = slice[i];
    const publisher = publisherFor(rec);
    const collection = collectionFor(rec);
    const paperId = recordId(rec);
    const filename = makeFilename(rec);
    const file = path.join(PAPERS, filename);
    const doiUrl = rec.doi_url || (rec.doi ? `https://doi.org/${rec.doi}` : '');
    const landingUrl = rec.citation_pdf_url || doiUrl || rec.ee_url || rec.official_url || '';
    if (isPdfFile(file)) {
      const doneStatus = publisher === 'ieee' ? 'downloaded_ieee_xplore' : publisher === 'acm' ? 'downloaded_acm_dl' : 'downloaded_open_access';
      byId.set(logKey(rec), {
        collection,
        paper_id: paperId,
        title: rec.title,
        doi: rec.doi,
        doi_url: rec.doi_url || '',
        ee_url: rec.ee_url || '',
        source_url: landingUrl,
        download_status: doneStatus,
        pdf_path: path.relative(ROOT, file),
        failure_reason: ''
      });
      flushLogs();
      console.log(`[skip] ${i + 1}/${slice.length} ${rec.paper_id} exists`);
      continue;
    }

    console.log(`[download] ${i + 1}/${slice.length} ${rec.paper_id} ${rec.title}`);
    let row;
    try {
      let value;
      if (publisher === 'ieee' && rec.doi && arnumberFromDoi(rec.doi)) {
        if (!landingUrl) throw new Error('no publisher landing or PDF URL');
        await cdp.send('Page.navigate', { url: landingUrl }, sessionId, 120000);
        await sleep(6000);
        const ar = arnumberFromDoi(rec.doi);
        const stampResult = await cdp.send('Runtime.evaluate', {
          expression: ieeeStampLinkExpression(ar),
          returnByValue: true
        }, sessionId, 60000);
        if (stampResult.result && stampResult.result.exceptionDetails) throw new Error(JSON.stringify(stampResult.result.exceptionDetails).slice(0, 1000));
        const stampValue = stampResult.result && stampResult.result.result && stampResult.result.result.value;
        if (!stampValue || !stampValue.ok || !stampValue.stampUrl) throw new Error(JSON.stringify(stampValue || stampResult).slice(0, 1000));
        await cdp.send('Page.navigate', { url: stampValue.stampUrl }, sessionId, 120000);
        await sleep(5000);
        const evalResult = await cdp.send('Runtime.evaluate', {
          expression: ieeePdfFromStampExpression(),
          awaitPromise: true,
          returnByValue: true
        }, sessionId, 600000);
        if (evalResult.result && evalResult.result.exceptionDetails) throw new Error(JSON.stringify(evalResult.result.exceptionDetails).slice(0, 1000));
        value = evalResult.result && evalResult.result.result && evalResult.result.result.value;
        if (!value || !value.ok || !value.len) throw new Error(JSON.stringify(value || evalResult).slice(0, 1000));
        const stored = await pullStoredBase64(cdp, sessionId);
        fs.writeFileSync(file, Buffer.from(stored.base64, 'base64'));
        value = stored;
      } else {
        const before = Date.now();
        if (!landingUrl) throw new Error('no publisher landing or PDF URL');
        await cdp.send('Page.navigate', { url: landingUrl }, sessionId, 120000);
        await sleep(6000);
        const evalResult = await cdp.send('Runtime.evaluate', {
          expression: publisherDownloadExpression(filename),
          awaitPromise: true,
          returnByValue: true
        }, sessionId, FETCH_TIMEOUT_MS + 30000);
        if (evalResult.result && evalResult.result.exceptionDetails) throw new Error(JSON.stringify(evalResult.result.exceptionDetails).slice(0, 1000));
        value = evalResult.result && evalResult.result.result && evalResult.result.result.value;
        if (!value || !value.ok) throw new Error(JSON.stringify(value || evalResult).slice(0, 1000));
        await waitForDownload(downloads, filename, before, 180000);
        for (let tries = 0; tries < 30 && !isPdfFile(file); tries++) await sleep(500);
      }
      if (!isPdfFile(file)) throw new Error(`download completed but file missing or invalid: ${filename}`);
      row = {
        collection,
        paper_id: paperId,
        title: rec.title,
        doi: rec.doi,
        doi_url: rec.doi_url || '',
        ee_url: rec.ee_url || '',
        source_url: value.pdfUrl || doiUrl || rec.ee_url || '',
        download_status: publisher === 'ieee' ? 'downloaded_ieee_xplore' : publisher === 'acm' ? 'downloaded_acm_dl' : 'downloaded_publisher_pdf',
        pdf_path: path.relative(ROOT, file),
        failure_reason: ''
      };
      console.log(`[ok] ${rec.paper_id} ${row.pdf_path}`);
    } catch (e) {
      row = {
        collection,
        paper_id: paperId,
        title: rec.title,
        doi: rec.doi,
        doi_url: rec.doi_url || '',
        ee_url: rec.ee_url || '',
        source_url: landingUrl,
        download_status: 'browser_download_failed',
        pdf_path: '',
        failure_reason: e.stack || e.message || String(e)
      };
      console.log(`[fail] ${rec.paper_id} ${row.failure_reason.slice(0, 240)}`);
    }
    byId.set(logKey(rec), row);
    flushLogs();
    await sleep(DELAY_MS);
  }

  try { await cdp.send('Target.closeTarget', { targetId }); } catch {}
  cdp.close();
  console.log(JSON.stringify({ attempted: slice.length, report: OUT_CSV }, null, 2));
}

main().catch(err => {
  console.error(err.stack || err);
  process.exit(1);
});
