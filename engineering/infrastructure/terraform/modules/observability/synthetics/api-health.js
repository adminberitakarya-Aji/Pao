const https = require('https');
const http = require('http');

exports.handler = async (event) => {
  const urls = [
    process.env.API_HEALTH_URL || 'https://api.pao.ai/health',
    process.env.AUTH_HEALTH_URL || 'https://api.pao.ai/auth/health',
  ];

  const results = [];
  const startTime = Date.now();

  for (const url of urls) {
    try {
      const result = await checkUrl(url);
      results.push(result);
    } catch (error) {
      results.push({
        url,
        status: 'error',
        error: error.message,
        timestamp: new Date().toISOString(),
      });
    }
  }

  const duration = Date.now() - startTime;
  const hasFailures = results.some(r => r.status !== 'ok');

  console.log(JSON.stringify({
    duration_ms: duration,
    checks: results,
    overall_status: hasFailures ? 'failed' : 'passed',
  }));

  if (hasFailures) {
    throw new Error('Health check failed');
  }

  return {
    statusCode: 200,
    body: JSON.stringify({ status: 'ok', checks: results }),
  };
};

function checkUrl(url) {
  return new Promise((resolve, reject) => {
    const client = url.startsWith('https') ? https : http;
    const startTime = Date.now();

    const req = client.get(url, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        const latency = Date.now() - startTime;
        const status = res.statusCode >= 200 && res.statusCode < 300 ? 'ok' : 'error';
        resolve({
          url,
          status,
          statusCode: res.statusCode,
          latency_ms: latency,
          timestamp: new Date().toISOString(),
        });
      });
    });

    req.on('error', (err) => {
      const latency = Date.now() - startTime;
      reject({
        url,
        status: 'error',
        error: err.message,
        latency_ms: latency,
        timestamp: new Date().toISOString(),
      });
    });

    req.setTimeout(10000, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
  });
}