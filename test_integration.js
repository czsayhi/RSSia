const https = require('https');
const http = require('http');

function makeRequest(url, options = {}) {
  return new Promise((resolve, reject) => {
    const lib = url.startsWith('https') ? https : http;
    const req = lib.request(url, options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({
            status: res.statusCode,
            data: res.headers['content-type']?.includes('json') ? JSON.parse(data) : data
          });
        } catch (e) {
          resolve({ status: res.statusCode, data });
        }
      });
    });
    
    if (options.body) {
      req.write(options.body);
    }
    
    req.on('error', reject);
    req.end();
  });
}

async function testIntegration() {
  console.log('=== 前后端对接功能测试 ===\n');
  
  // 测试1: 后端搜索API
  console.log('1. 测试订阅源搜索API');
  try {
    const searchRes = await makeRequest('http://localhost:8001/api/v1/subscription-search/search?query=bilibili');
    if (searchRes.status === 200) {
      console.log('   ✅ 搜索API: 找到', searchRes.data.total, '个结果');
      console.log('   - 第一个结果:', searchRes.data.results[0]?.template_name);
    } else {
      console.log('   ❌ 搜索API: HTTP', searchRes.status);
    }
  } catch (err) {
    console.log('   ❌ 搜索API失败:', err.message);
  }
  
  // 测试2: 后端订阅列表API
  console.log('\n2. 测试订阅列表API');
  try {
    const listRes = await makeRequest('http://localhost:8001/api/v1/subscriptions/');
    if (listRes.status === 200) {
      console.log('   ✅ 订阅列表API: 找到', listRes.data.length, '个订阅');
      if (listRes.data.length > 0) {
        console.log('   - 第一个订阅:', listRes.data[0].template_name);
        console.log('   - 订阅状态:', listRes.data[0].is_active ? '激活' : '未激活');
      }
    } else {
      console.log('   ❌ 订阅列表API: HTTP', listRes.status);
    }
  } catch (err) {
    console.log('   ❌ 订阅列表API失败:', err.message);
  }
  
  // 测试3: 前端页面
  console.log('\n3. 测试前端页面访问');
  try {
    const frontendRes = await makeRequest('http://localhost:3000');
    console.log('   ✅ 前端页面: HTTP', frontendRes.status, frontendRes.status === 200 ? '正常访问' : '访问异常');
  } catch (err) {
    console.log('   ❌ 前端页面失败:', err.message);
  }
  
  console.log('\n=== 测试完成 ===');
}

testIntegration().catch(console.error); 