#!/usr/bin/env node
const port = Number(process.env.CDP_PROXY_PORT || 3456);
try {
  const response = await fetch(`http://127.0.0.1:${port}/shutdown`, {
    method: 'POST',
    signal: AbortSignal.timeout(5000),
  });
  if (!response.ok) throw new Error(`HTTP ${response.status}`);
  console.log(`CDP Proxy on port ${port} is shutting down.`);
} catch (error) {
  console.error(`Unable to stop CDP Proxy on port ${port}: ${error.message}`);
  process.exitCode = 1;
}
