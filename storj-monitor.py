#!/usr/bin/env python3
"""
Storj Multi-Node Monitor (Extended)
====================================
All-in-one: Proxy + Dashboard mit erweiterten Stats.

Start:  py storj-monitor.py
Browser: http://localhost:8080

Zeigt: Disk (used/free/total/trash mit Stack-Bar), Bandwidth (Ingress/Egress),
Earnings (current month + held + all-time), Satellite Scores, Wallet, uvm.
"""

import http.server
import socketserver
import urllib.request
import urllib.error
import json
import sys
from datetime import datetime
from urllib.parse import urlparse

LISTEN_PORT = 8080
LISTEN_HOST = "127.0.0.1"
NODE_HOST = "127.0.0.1"
REQUEST_TIMEOUT = 5

DASHBOARD_HTML = r"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Storj Multi-Node Monitor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;700&family=Space+Grotesk:wght@400;500;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg: #0a0e1a; --bg-card: #111726; --bg-card-hover: #161d30;
    --bg-deep: #060912;
    --border: #1f2a44; --border-accent: #2a3a5e;
    --text: #e8ecf5; --text-dim: #8892b0; --text-faint: #4a5673;
    --accent: #00d4aa; --accent-dim: #00a085;
    --gold: #f7c948; --gold-dim: #a8861a;
    --warning: #ffb84d; --danger: #ff5577; --info: #5b8cff;
    --grid-line: rgba(0, 212, 170, 0.05);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body {
    background: var(--bg); color: var(--text);
    font-family: 'Space Grotesk', sans-serif; min-height: 100vh;
    background-image:
      linear-gradient(var(--grid-line) 1px, transparent 1px),
      linear-gradient(90deg, var(--grid-line) 1px, transparent 1px);
    background-size: 40px 40px;
  }
  .wrap { max-width: 1700px; margin: 0 auto; padding: 28px 24px 80px; }
  header {
    display: flex; align-items: baseline; justify-content: space-between;
    flex-wrap: wrap; gap: 20px; margin-bottom: 28px; padding-bottom: 22px;
    border-bottom: 1px solid var(--border);
  }
  h1 { font-family: 'JetBrains Mono', monospace; font-size: 24px; font-weight: 700; letter-spacing: -0.02em; }
  h1 .brand { color: var(--accent); }
  h1 .sub { color: var(--text-faint); font-weight: 400; margin-left: 8px; font-size: 13px; }
  .controls { display: flex; align-items: center; gap: 16px; font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-dim); }
  .status-dot {
    display: inline-block; width: 8px; height: 8px; border-radius: 50%;
    background: var(--accent); box-shadow: 0 0 8px var(--accent);
    animation: pulse 2s ease-in-out infinite; margin-right: 6px;
  }
  @keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.4; } }
  button.refresh {
    background: var(--bg-card); border: 1px solid var(--border); color: var(--text);
    font-family: 'JetBrains Mono', monospace; font-size: 11px; padding: 7px 14px;
    border-radius: 4px; cursor: pointer; text-transform: uppercase;
    letter-spacing: 0.05em; transition: all 0.15s ease;
  }
  button.refresh:hover { background: var(--bg-card-hover); border-color: var(--accent); color: var(--accent); }

  .totals {
    display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
    gap: 12px; margin-bottom: 28px; padding: 22px;
    background: var(--bg-card); border: 1px solid var(--border-accent);
    border-radius: 8px; position: relative;
  }
  .totals::before {
    content: 'GESAMT'; position: absolute; top: -9px; left: 20px;
    background: var(--bg); padding: 0 10px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.2em; color: var(--accent);
  }
  .total-item { display: flex; flex-direction: column; gap: 6px; }
  .total-item .label {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint);
  }
  .total-item .value { font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 700; color: var(--text); }
  .total-item .value.earn { color: var(--gold); }
  .total-item .unit { font-size: 12px; color: var(--text-dim); font-weight: 400; margin-left: 4px; }

  .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(440px, 1fr)); gap: 18px; }
  .node {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 8px; padding: 22px; position: relative;
    transition: border-color 0.2s ease;
  }
  .node:hover { border-color: var(--border-accent); }
  .node.error { border-color: var(--danger); opacity: 0.7; }
  .node.error::after {
    content: 'OFFLINE'; position: absolute; top: 14px; right: 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.15em; color: var(--danger);
    padding: 3px 8px; border: 1px solid var(--danger); border-radius: 3px;
  }

  .node-head {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 16px; padding-bottom: 14px; border-bottom: 1px solid var(--border);
  }
  .node-head h2 { font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: var(--accent); }
  .node-head .port { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text-faint); margin-top: 4px; }
  .node-head .nodeid { font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-faint); margin-top: 3px; }
  .node-head .meta-right { text-align: right; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-dim); line-height: 1.6; }

  .earnings-block {
    background: linear-gradient(135deg, rgba(247, 201, 72, 0.08), rgba(247, 201, 72, 0.02));
    border: 1px solid rgba(247, 201, 72, 0.2);
    border-radius: 6px; padding: 14px 16px; margin-bottom: 14px;
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px;
  }

  .uptime-bar {
    display: flex; justify-content: space-between; align-items: center;
    background: var(--bg-deep); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 14px; margin-bottom: 14px;
  }
  .uptime-main { display: flex; align-items: center; gap: 10px; }
  .uptime-label {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.12em; color: var(--text-faint); text-transform: uppercase;
  }
  .uptime-value {
    font-family: 'JetBrains Mono', monospace; font-size: 14px;
    font-weight: 700; color: var(--accent);
  }
  .uptime-health {
    display: flex; align-items: center; gap: 6px;
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    font-weight: 500;
  }
  .earn-item { display: flex; flex-direction: column; gap: 3px; }
  .earn-item .label {
    font-family: 'JetBrains Mono', monospace; font-size: 9px;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--gold-dim);
  }
  .earn-item .value { font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 700; color: var(--gold); }
  .earn-item .sub { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--text-faint); }

  .disk-block {
    background: var(--bg-deep); border: 1px solid var(--border);
    border-radius: 6px; padding: 14px; margin-bottom: 14px;
  }
  .disk-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; }
  .disk-header .title {
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.12em; text-transform: uppercase; color: var(--text-faint);
  }
  .disk-header .total { font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text); }
  .disk-bar-stacked {
    height: 24px; display: flex; border-radius: 4px; overflow: hidden;
    background: var(--bg); margin-bottom: 10px;
  }
  .disk-seg {
    display: flex; align-items: center; justify-content: center;
    font-family: 'JetBrains Mono', monospace; font-size: 9px;
    color: var(--bg); font-weight: 700;
    transition: all 0.3s ease; min-width: 0; overflow: hidden;
  }
  .disk-seg.used { background: var(--accent); }
  .disk-seg.trash { background: var(--warning); }
  .disk-seg.free { background: #2a3a5e; color: var(--text-dim); }
  .disk-legend {
    display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
  }
  .disk-legend-item { display: flex; flex-direction: column; gap: 2px; }
  .disk-legend-item .lbl {
    color: var(--text-faint); text-transform: uppercase;
    letter-spacing: 0.05em; font-size: 9px;
    display: flex; align-items: center; gap: 4px;
  }
  .disk-legend-item .lbl::before {
    content: ''; width: 8px; height: 8px; border-radius: 2px; display: inline-block;
  }
  .disk-legend-item.used .lbl::before { background: var(--accent); }
  .disk-legend-item.trash .lbl::before { background: var(--warning); }
  .disk-legend-item.free .lbl::before { background: #2a3a5e; }
  .disk-legend-item.total .lbl::before { background: var(--text-dim); }
  .disk-legend-item .val { color: var(--text); font-size: 12px; font-weight: 500; }

  .bw-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px; margin-bottom: 14px; }
  .bw-item {
    background: var(--bg-deep); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 12px;
  }
  .bw-item .lbl {
    font-family: 'JetBrains Mono', monospace; font-size: 9px;
    letter-spacing: 0.1em; text-transform: uppercase; color: var(--text-faint);
    margin-bottom: 4px; display: flex; align-items: center; gap: 5px;
  }
  .bw-item .lbl.in .arrow { color: var(--info); }
  .bw-item .lbl.out .arrow { color: var(--accent); }
  .bw-item .val { font-family: 'JetBrains Mono', monospace; font-size: 14px; color: var(--text); font-weight: 500; }
  .bw-item .breakdown { font-family: 'JetBrains Mono', monospace; font-size: 9px; color: var(--text-faint); margin-top: 4px; }

  .meta-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px;
    margin-bottom: 14px;
    padding: 12px; background: var(--bg-deep); border-radius: 6px;
    border: 1px solid var(--border);
  }
  .meta-item { display: flex; flex-direction: column; gap: 3px; }
  .meta-item .lbl {
    font-family: 'JetBrains Mono', monospace; font-size: 9px;
    letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-faint);
  }
  .meta-item .val { font-family: 'JetBrains Mono', monospace; font-size: 11px; color: var(--text); }

  .wallet-box {
    background: var(--bg-deep); border: 1px solid var(--border);
    border-radius: 6px; padding: 10px 12px; margin-bottom: 14px;
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
  }
  .wallet-box .lbl { color: var(--text-faint); text-transform: uppercase; letter-spacing: 0.08em; font-size: 9px; margin-bottom: 3px; }
  .wallet-box .val { color: var(--text); word-break: break-all; }

  .satellites { display: flex; flex-direction: column; gap: 5px; font-family: 'JetBrains Mono', monospace; font-size: 11px; }
  .sat {
    display: grid; grid-template-columns: 1fr auto;
    align-items: center; gap: 10px;
    padding: 6px 10px; background: var(--bg-deep); border-radius: 4px;
    border-left: 2px solid var(--accent);
  }
  .sat.disq { border-left-color: var(--danger); }
  .sat.susp { border-left-color: var(--warning); }
  .sat-info { display: flex; flex-direction: column; gap: 2px; min-width: 0; }
  .sat-name { color: var(--text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .sat-meta { color: var(--text-faint); font-size: 9px; }
  .sat-scores { display: flex; gap: 8px; font-size: 10px; flex-shrink: 0; }
  .sat-scores span { color: var(--text-faint); }
  .sat-scores .ok { color: var(--accent); }
  .sat-scores .warn { color: var(--warning); }
  .sat-scores .bad { color: var(--danger); }

  .error-msg {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--text-faint); margin-top: 12px; padding: 10px;
    background: var(--bg); border-radius: 4px; border-left: 2px solid var(--danger);
  }
  .loading { text-align: center; padding: 60px 20px; font-family: 'JetBrains Mono', monospace; color: var(--text-dim); }
  footer { margin-top: 40px; text-align: center; font-family: 'JetBrains Mono', monospace; font-size: 10px; color: var(--text-faint); }

  .config-bar {
    background: var(--bg-card); border: 1px solid var(--border);
    border-radius: 6px; padding: 14px 18px; margin-bottom: 24px;
    display: flex; align-items: center; gap: 16px; flex-wrap: wrap;
  }
  .config-bar label {
    font-family: 'JetBrains Mono', monospace; font-size: 11px;
    color: var(--text-dim); text-transform: uppercase; letter-spacing: 0.08em;
  }
  .config-bar input, .config-bar select {
    background: var(--bg); border: 1px solid var(--border); color: var(--text);
    font-family: 'JetBrains Mono', monospace; font-size: 12px;
    padding: 7px 10px; border-radius: 4px;
  }
  .config-bar input { width: 220px; }
  .config-bar input:focus, .config-bar select:focus { outline: none; border-color: var(--accent); }

  details summary {
    cursor: pointer; color: var(--text-dim);
    font-family: 'JetBrains Mono', monospace; font-size: 10px;
    letter-spacing: 0.1em; text-transform: uppercase;
    padding: 6px 0; user-select: none;
  }
  details summary:hover { color: var(--accent); }
  details[open] summary { color: var(--accent); margin-bottom: 8px; }
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div><h1><span class="brand">STORJ</span> NODE MONITOR <span class="sub">// extended</span></h1></div>
    <div class="controls">
      <span><span class="status-dot"></span><span id="last-update">Lädt …</span></span>
      <button class="refresh" onclick="refreshAll()">↻ Aktualisieren</button>
    </div>
  </header>

  <div class="config-bar">
    <label>Ports:</label>
    <input id="ports-input" type="text" value="14002, 14003, 14004, 14005" />
    <label>Auto-Refresh:</label>
    <select id="refresh-interval">
      <option value="0">Aus</option>
      <option value="15">15s</option>
      <option value="30" selected>30s</option>
      <option value="60">60s</option>
      <option value="300">5min</option>
    </select>
    <button class="refresh" onclick="applyConfig()">Übernehmen</button>
  </div>

  <div class="totals" id="totals">
    <div class="total-item"><div class="label">Nodes Online</div><div class="value" id="t-online">– <span class="unit">/ –</span></div></div>
    <div class="total-item"><div class="label">⌀ Uptime</div><div class="value" id="t-uptime">– <span class="unit">Tage</span></div></div>
    <div class="total-item"><div class="label">Disk Total</div><div class="value" id="t-total">– <span class="unit">TB</span></div></div>
    <div class="total-item"><div class="label">Disk Used</div><div class="value" id="t-used">– <span class="unit">TB</span></div></div>
    <div class="total-item"><div class="label">Disk Free</div><div class="value" id="t-avail">– <span class="unit">TB</span></div></div>
    <div class="total-item"><div class="label">Bandwidth (Monat)</div><div class="value" id="t-bw">– <span class="unit">GB</span></div></div>
    <div class="total-item"><div class="label">Earnings bisher</div><div class="value earn" id="t-earn">– <span class="unit">USD</span></div></div>
    <div class="total-item"><div class="label">↗ Hochrechnung</div><div class="value earn" id="t-earn-proj">– <span class="unit">USD</span></div></div>
    <div class="total-item"><div class="label">Held Amount</div><div class="value earn" id="t-held">– <span class="unit">USD</span></div></div>
    <div class="total-item"><div class="label">Earnings (Total)</div><div class="value earn" id="t-earn-total">– <span class="unit">USD</span></div></div>
  </div>

  <div class="grid" id="grid"><div class="loading">Verbinde mit Storj Nodes …</div></div>

  <footer>Lokaler Proxy auf Port __LISTEN_PORT__ · Alle Daten bleiben auf deinem Rechner</footer>
</div>

<script>
  let PORTS = [14002, 14003, 14004, 14005];
  let refreshTimer = null;

  function fmtBytes(bytes) {
    if (bytes == null || isNaN(bytes)) return '–';
    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    let i = 0; let n = Number(bytes);
    while (n >= 1024 && i < units.length - 1) { n /= 1024; i++; }
    return n.toFixed(n < 10 ? 2 : n < 100 ? 1 : 0) + ' ' + units[i];
  }
  function fmtBytesAs(bytes, target) {
    if (bytes == null || isNaN(bytes)) return 0;
    const d = { GB: 1024**3, TB: 1024**4 };
    return Number(bytes) / d[target];
  }
  function fmtUSD(val) {
    // Storj earnings sind in cents oder microUSD je nach endpoint - normalize
    if (val == null || isNaN(val)) return '0.00';
    return Number(val).toFixed(2);
  }
  function scorePill(score) {
    if (score == null) return '<span>–</span>';
    const pct = (score * 100).toFixed(1);
    const cls = score >= 0.99 ? 'ok' : score >= 0.95 ? 'warn' : 'bad';
    return `<span class="${cls}">${pct}%</span>`;
  }
  function shortSatId(id) {
    if (!id) return '–';
    const known = {
      '12EayRS2V1kEsWESU9QMRseFhdxYxKicsiFmxrsLZHeLUtdps3S': 'US1',
      '12L9nCYHy3iE3pj66YHcL8gkBhrybQYAEFC9SCMfXctzKKnvkjW': 'EU1',
      '121RTSDpyNZVcEU84Ticf2L1ntiuUimbWgfATz21tuvgk3vzoA6': 'AP1',
      '1wFTAgs9DP5RSnCqKV1eLf6N9wtk4EAtmN5DpSxcs8EjT69tGE': 'SaltLake',
    };
    return known[id] || (id.slice(0, 8) + '…');
  }
  function daysSince(dateStr) {
    if (!dateStr) return null;
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return null;
    return Math.floor((Date.now() - d.getTime()) / (1000 * 60 * 60 * 24));
  }

  function formatUptime(dateStr) {
    if (!dateStr) return { text: '–', short: '–', days: null };
    const start = new Date(dateStr);
    if (isNaN(start.getTime())) return { text: '–', short: '–', days: null };
    const ms = Date.now() - start.getTime();
    const totalSec = Math.floor(ms / 1000);
    const days = Math.floor(totalSec / 86400);
    const hours = Math.floor((totalSec % 86400) / 3600);
    const mins = Math.floor((totalSec % 3600) / 60);

    let text;
    if (days > 0) text = `${days}d ${hours}h ${mins}m`;
    else if (hours > 0) text = `${hours}h ${mins}m`;
    else text = `${mins}m`;

    const short = days > 0 ? `${days}d` : `${hours}h`;
    return { text, short, days, hours, mins };
  }

  function timeSince(dateStr) {
    if (!dateStr) return '–';
    const d = new Date(dateStr);
    if (isNaN(d.getTime())) return '–';
    const sec = Math.floor((Date.now() - d.getTime()) / 1000);
    if (sec < 60) return `vor ${sec}s`;
    if (sec < 3600) return `vor ${Math.floor(sec/60)}min`;
    if (sec < 86400) return `vor ${Math.floor(sec/3600)}h`;
    return `vor ${Math.floor(sec/86400)}d`;
  }

  function projectedMonthEnd(currentEarnings) {
    // Hochrechnung: was wird am Monatsende sein, wenn das aktuelle Tempo so weitergeht?
    if (!currentEarnings || currentEarnings <= 0) return 0;
    const now = new Date();
    const dayOfMonth = now.getDate();
    const daysInMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0).getDate();
    if (dayOfMonth < 1) return currentEarnings;
    return (currentEarnings / dayOfMonth) * daysInMonth;
  }

  async function fetchNode(port) {
    try {
      const res = await fetch(`/api/node/${port}`, { cache: 'no-store' });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
        return { port, ok: false, error: err.error || `HTTP ${res.status}` };
      }
      const data = await res.json();
      return { port, ok: true, ...data };
    } catch (err) {
      return { port, ok: false, error: err.message };
    }
  }

  function parsePayout(payout) {
    // Storj payout endpoint returns values in different scales depending on version.
    // /api/sno/estimated-payout typically returns:
    //   { currentMonth: { payout: <microUSD>, held: <microUSD> }, previousMonth: {...}, currentMonthExpectations: <microUSD> }
    // We normalize to USD (float).
    if (!payout) return { current: 0, held: 0, total: 0 };

    const toUSD = (v) => {
      if (v == null || isNaN(v)) return 0;
      // microUSD heuristic: storj uses /10000 for cents-of-cent values
      // estimated-payout: in microUSD (1 USD = 1_000_000 microUSD? Actually 1 USD = 10000 in storj's "cents of cents")
      // Use /10000 as standard
      return Number(v) / 10000;
    };

    const current = toUSD(
      payout.currentMonth?.payout ??
      payout.currentMonthExpectations ??
      0
    );
    const held = toUSD(payout.currentMonth?.held ?? 0);

    let total = 0;
    if (Array.isArray(payout.previousMonth)) {
      // shouldn't happen but defensive
    }
    if (payout.previousMonth?.payout != null) {
      total += toUSD(payout.previousMonth.payout);
    }
    total += current;

    // If paystubs available, use them for more accurate all-time
    if (payout.paystubs && Array.isArray(payout.paystubs)) {
      const allTime = payout.paystubs.reduce((s, p) => s + (p.paid || 0) + (p.held || 0), 0);
      if (allTime > 0) total = allTime / 10000;
    }

    return { current, held, total };
  }

  function renderDiskBlock(d) {
    const used = d.diskSpace?.used || 0;
    const trash = d.diskSpace?.trash || 0;
    const avail = d.diskSpace?.available || 0;
    const overused = d.diskSpace?.overused || 0;
    const total = used + trash + avail;

    const pctUsed = total > 0 ? (used / total) * 100 : 0;
    const pctTrash = total > 0 ? (trash / total) * 100 : 0;
    const pctAvail = total > 0 ? (avail / total) * 100 : 0;

    return `
      <div class="disk-block">
        <div class="disk-header">
          <span class="title">⌬ Festplatte</span>
          <span class="total">${fmtBytes(total)} alloziert</span>
        </div>
        <div class="disk-bar-stacked">
          <div class="disk-seg used" style="width:${pctUsed}%">${pctUsed > 6 ? pctUsed.toFixed(0)+'%' : ''}</div>
          <div class="disk-seg trash" style="width:${pctTrash}%">${pctTrash > 6 ? pctTrash.toFixed(0)+'%' : ''}</div>
          <div class="disk-seg free" style="width:${pctAvail}%">${pctAvail > 6 ? pctAvail.toFixed(0)+'%' : ''}</div>
        </div>
        <div class="disk-legend">
          <div class="disk-legend-item used"><span class="lbl">Used</span><span class="val">${fmtBytes(used)}</span></div>
          <div class="disk-legend-item trash"><span class="lbl">Trash</span><span class="val">${fmtBytes(trash)}</span></div>
          <div class="disk-legend-item free"><span class="lbl">Frei</span><span class="val">${fmtBytes(avail)}</span></div>
          <div class="disk-legend-item total"><span class="lbl">Total</span><span class="val">${fmtBytes(total)}</span></div>
        </div>
        ${overused > 0 ? `<div style="margin-top:8px; font-family:'JetBrains Mono',monospace; font-size:10px; color:var(--danger);">⚠ Overused: ${fmtBytes(overused)}</div>` : ''}
      </div>
    `;
  }

  function renderBandwidth(d, sats) {
    const bwUsed = d.bandwidth?.used || 0;
    const bwAvail = d.bandwidth?.available || 0;

    let ingressTotal = 0, egressTotal = 0;
    (sats || []).forEach(s => {
      if (s.ingressSummary) ingressTotal += s.ingressSummary;
      if (s.egressSummary) egressTotal += s.egressSummary;
    });

    return `
      <div class="bw-grid">
        <div class="bw-item">
          <div class="lbl in"><span class="arrow">↓</span> Ingress (Monat)</div>
          <div class="val">${fmtBytes(ingressTotal)}</div>
          <div class="breakdown">eingehende Daten</div>
        </div>
        <div class="bw-item">
          <div class="lbl out"><span class="arrow">↑</span> Egress (Monat)</div>
          <div class="val">${fmtBytes(egressTotal)}</div>
          <div class="breakdown">ausgehende Daten</div>
        </div>
        <div class="bw-item" style="grid-column: span 2;">
          <div class="lbl"><span class="arrow">⇅</span> Gesamt-Bandbreite (Monat)</div>
          <div class="val">${fmtBytes(bwUsed)} <span style="color:var(--text-faint); font-size:11px">· verfügbar: ${fmtBytes(bwAvail)}</span></div>
        </div>
      </div>
    `;
  }

  function renderEarnings(earn) {
    const projected = projectedMonthEnd(earn.current);
    return `
      <div class="earnings-block">
        <div class="earn-item">
          <span class="label">⌬ Aktueller Monat</span>
          <span class="value">$${fmtUSD(earn.current)}</span>
          <span class="sub">bisher</span>
        </div>
        <div class="earn-item">
          <span class="label">↗ Hochrechnung</span>
          <span class="value">$${fmtUSD(projected)}</span>
          <span class="sub">am Monatsende</span>
        </div>
        <div class="earn-item">
          <span class="label">Held Amount</span>
          <span class="value">$${fmtUSD(earn.held)}</span>
          <span class="sub">einbehalten</span>
        </div>
        <div class="earn-item">
          <span class="label">Gesamt</span>
          <span class="value">$${fmtUSD(earn.total)}</span>
          <span class="sub">all-time</span>
        </div>
      </div>
    `;
  }

  function renderSatellites(sats) {
    if (!sats || !sats.length) return '';

    const rows = sats.map(s => {
      let cls = '';
      if (s.disqualified) cls = 'disq';
      else if (s.suspended) cls = 'susp';
      const joinedDays = s.joinedAt ? daysSince(s.joinedAt) : null;
      const meta = joinedDays !== null ? `seit ${joinedDays} Tagen` : '';
      return `<div class="sat ${cls}">
        <div class="sat-info">
          <span class="sat-name">${shortSatId(s.satelliteId)}</span>
          ${meta ? `<span class="sat-meta">${meta}</span>` : ''}
        </div>
        <div class="sat-scores">
          <span>A:${scorePill(s.auditScore)}</span>
          <span>S:${scorePill(s.suspensionScore)}</span>
          <span>O:${scorePill(s.onlineScore)}</span>
        </div>
      </div>`;
    }).join('');

    return `
      <details>
        <summary>▸ Satelliten (${sats.length}) — Audit / Suspension / Online</summary>
        <div class="satellites">${rows}</div>
      </details>
    `;
  }

  function renderNode(result) {
    if (!result.ok) {
      return `
        <div class="node error">
          <div class="node-head">
            <div><h2>NODE :${result.port}</h2><div class="port">127.0.0.1:${result.port}</div></div>
          </div>
          <div class="error-msg">
            Verbindung fehlgeschlagen: ${result.error}<br>
            <span style="color: var(--text-faint)">Läuft die Node? Ist der Port erreichbar?</span>
          </div>
        </div>`;
    }
    const d = result.dash;
    const sats = result.sats || [];
    const earn = parsePayout(result.payout);

    const wallet = d.wallet || '–';
    const nodeId = d.nodeID || '–';
    const upToDate = d.upToDate ? '<span style="color: var(--accent)">●</span> aktuell' : '<span style="color: var(--warning)">●</span> Update verfügbar';
    const quic = d.quicStatus === 'OK' ? '<span style="color: var(--accent)">QUIC OK</span>' : `<span style="color: var(--warning)">QUIC ${d.quicStatus || '?'}</span>`;
    const lastPing = d.lastPinged ? timeSince(d.lastPinged) : '–';

    // Uptime: bevorzuge startedAt, dann lastQuicPingedAt als Fallback
    const uptimeData = formatUptime(d.startedAt);
    const startedAtFull = d.startedAt ? new Date(d.startedAt).toLocaleString('de-DE') : '–';

    // Satellite stats
    const disqCount = sats.filter(s => s.disqualified).length;
    const suspCount = sats.filter(s => s.suspended).length;
    const healthySats = sats.length - disqCount - suspCount;

    // Health-Indikator: alle Satelliten gut?
    let healthIcon = '✓';
    let healthColor = 'var(--accent)';
    let healthText = 'gesund';
    if (disqCount > 0) {
      healthIcon = '✗';
      healthColor = 'var(--danger)';
      healthText = `${disqCount} disqualifiziert`;
    } else if (suspCount > 0) {
      healthIcon = '⚠';
      healthColor = 'var(--warning)';
      healthText = `${suspCount} suspendiert`;
    }

    return `
      <div class="node">
        <div class="node-head">
          <div>
            <h2>NODE :${result.port}</h2>
            <div class="port">${nodeId.slice(0, 20)}…</div>
          </div>
          <div class="meta-right">
            v${d.version || '?'}<br>
            ${upToDate}<br>
            ${quic}<br>
            <span style="color: var(--text-faint)">Last ping: ${lastPing}</span>
          </div>
        </div>

        <div class="uptime-bar">
          <div class="uptime-main">
            <span class="uptime-label">⏱ UPTIME</span>
            <span class="uptime-value">${uptimeData.text}</span>
          </div>
          <div class="uptime-health" style="color: ${healthColor}">
            <span style="font-size: 14px;">${healthIcon}</span>
            <span>${healthText}</span>
          </div>
        </div>

        ${renderEarnings(earn)}

        ${renderDiskBlock(d)}

        ${renderBandwidth(d, sats)}

        <div class="wallet-box">
          <div class="lbl">Wallet</div>
          <div class="val">${wallet}</div>
        </div>

        <div class="meta-grid">
          <div class="meta-item">
            <span class="lbl">Gestartet</span>
            <span class="val" title="${startedAtFull}">${startedAtFull}</span>
          </div>
          <div class="meta-item">
            <span class="lbl">Satelliten gesund</span>
            <span class="val">${healthySats} / ${sats.length}</span>
          </div>
          <div class="meta-item">
            <span class="lbl">Letzter Kontakt</span>
            <span class="val">${lastPing}</span>
          </div>
        </div>

        ${renderSatellites(sats)}
      </div>`;
  }

  function updateTotals(results) {
    const okResults = results.filter(r => r.ok);
    let totalUsed = 0, totalAvail = 0, totalTrash = 0, totalBw = 0;
    let totalEarn = 0, totalHeld = 0, totalAllTime = 0;
    let uptimeSum = 0, uptimeCount = 0;

    okResults.forEach(r => {
      totalUsed += r.dash.diskSpace?.used || 0;
      totalAvail += r.dash.diskSpace?.available || 0;
      totalTrash += r.dash.diskSpace?.trash || 0;
      totalBw += r.dash.bandwidth?.used || 0;
      const earn = parsePayout(r.payout);
      totalEarn += earn.current;
      totalHeld += earn.held;
      totalAllTime += earn.total;

      const ut = formatUptime(r.dash.startedAt);
      if (ut.days !== null) {
        uptimeSum += ut.days + (ut.hours || 0) / 24;
        uptimeCount++;
      }
    });

    const totalAlloc = totalUsed + totalAvail + totalTrash;
    const totalProjected = projectedMonthEnd(totalEarn);
    const avgUptime = uptimeCount > 0 ? (uptimeSum / uptimeCount) : 0;

    document.getElementById('t-online').innerHTML = `${okResults.length} <span class="unit">/ ${results.length}</span>`;
    document.getElementById('t-uptime').innerHTML = `${avgUptime.toFixed(1)} <span class="unit">Tage</span>`;
    document.getElementById('t-total').innerHTML = `${fmtBytesAs(totalAlloc, 'TB').toFixed(2)} <span class="unit">TB</span>`;
    document.getElementById('t-used').innerHTML = `${fmtBytesAs(totalUsed, 'TB').toFixed(2)} <span class="unit">TB</span>`;
    document.getElementById('t-avail').innerHTML = `${fmtBytesAs(totalAvail, 'TB').toFixed(2)} <span class="unit">TB</span>`;
    document.getElementById('t-bw').innerHTML = `${fmtBytesAs(totalBw, 'GB').toFixed(1)} <span class="unit">GB</span>`;
    document.getElementById('t-earn').innerHTML = `$${fmtUSD(totalEarn)} <span class="unit">USD</span>`;
    document.getElementById('t-earn-proj').innerHTML = `$${fmtUSD(totalProjected)} <span class="unit">USD</span>`;
    document.getElementById('t-held').innerHTML = `$${fmtUSD(totalHeld)} <span class="unit">USD</span>`;
    document.getElementById('t-earn-total').innerHTML = `$${fmtUSD(totalAllTime)} <span class="unit">USD</span>`;
  }

  async function refreshAll() {
    const grid = document.getElementById('grid');
    const results = await Promise.all(PORTS.map(p => fetchNode(p)));
    grid.innerHTML = results.map(renderNode).join('');
    updateTotals(results);
    document.getElementById('last-update').textContent = 'Aktualisiert: ' + new Date().toLocaleTimeString('de-DE');
  }

  function applyConfig() {
    const portsStr = document.getElementById('ports-input').value;
    PORTS = portsStr.split(',').map(s => parseInt(s.trim())).filter(n => !isNaN(n));
    if (refreshTimer) clearInterval(refreshTimer);
    const interval = parseInt(document.getElementById('refresh-interval').value);
    if (interval > 0) refreshTimer = setInterval(refreshAll, interval * 1000);
    refreshAll();
  }

  applyConfig();
</script>
</body>
</html>
"""


def http_get_json(url, timeout=REQUEST_TIMEOUT):
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_node_data(port):
    base = f"http://{NODE_HOST}:{port}"
    result = {"dash": None, "sats": [], "payout": None}

    try:
        result["dash"] = http_get_json(f"{base}/api/sno")
    except Exception as e:
        return None, str(e)

    try:
        sats_data = http_get_json(f"{base}/api/sno/satellites")
        result["sats"] = sats_data.get("audits", [])
    except Exception:
        pass

    try:
        result["payout"] = http_get_json(f"{base}/api/sno/estimated-payout")
    except Exception:
        pass

    # Versuche, paystubs für all-time earnings zu holen
    try:
        paystubs = http_get_json(f"{base}/api/heldamount/paystubs")
        if result["payout"] is None:
            result["payout"] = {}
        result["payout"]["paystubs"] = paystubs
    except Exception:
        pass

    return result, None


class Handler(http.server.BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        try:
            line = fmt % args
            if "/api/node/" in line:
                return
        except Exception:
            pass
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path

        if path == "/" or path == "/index.html":
            html = DASHBOARD_HTML.replace("__LISTEN_PORT__", str(LISTEN_PORT))
            body = html.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        if path.startswith("/api/node/"):
            try:
                port = int(path.split("/")[-1])
            except ValueError:
                self._json(400, {"error": "Invalid port"})
                return

            data, err = fetch_node_data(port)
            if err:
                self._json(502, {"error": err, "port": port})
                return
            self._json(200, data)
            return

        self.send_response(404)
        self.end_headers()
        self.wfile.write(b"Not Found")

    def _json(self, status, obj):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)


class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    print()
    print("  ╔════════════════════════════════════════════╗")
    print("  ║   STORJ MULTI-NODE MONITOR (extended)      ║")
    print("  ╠════════════════════════════════════════════╣")
    print(f"  ║   Dashboard: http://localhost:{LISTEN_PORT}        ║")
    print("  ║                                            ║")
    print("  ║   Beenden mit Strg+C                       ║")
    print("  ╚════════════════════════════════════════════╝")
    print()

    try:
        with ThreadingServer((LISTEN_HOST, LISTEN_PORT), Handler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Beendet.")
    except OSError as e:
        if "Address already in use" in str(e) or getattr(e, 'errno', None) in (98, 48, 10048):
            print(f"  Fehler: Port {LISTEN_PORT} ist bereits belegt.")
            print(f"  Tipp: Im Script LISTEN_PORT ändern (oben in der Datei).")
        else:
            print(f"  Fehler: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
