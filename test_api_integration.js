/**
 * 前后端API对接测试
 * 验证API客户端和后端服务的集成情况
 */

// 测试API基础URL
const API_BASE_URL = 'http://localhost:8001'

// 测试功能1: 订阅源搜索
async function testSubscriptionSearch() {
    console.log('=== 测试订阅源搜索 ===')
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/subscription-search/search?query=bilibili`)
        const data = await response.json()
        
        console.log('✅ 搜索API响应正常')
        console.log(`- 找到 ${data.total} 个结果`)
        console.log(`- 第一个结果: ${data.results[0]?.template_name}`)
        console.log(`- 表单字段数: ${data.results[0]?.required_params?.length}`)
        
        return data
    } catch (error) {
        console.error('❌ 搜索API测试失败:', error.message)
        return null
    }
}

// 测试功能2: 用户订阅列表
async function testSubscriptionList() {
    console.log('\n=== 测试订阅列表 ===')
    
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/subscriptions/`)
        const data = await response.json()
        
        console.log('✅ 订阅列表API响应正常')
        console.log(`- 订阅数量: ${data.length}`)
        if (data.length > 0) {
            console.log(`- 第一个订阅: ${data[0].name}`)
            console.log(`- 平台: ${data[0].platform}`)
            console.log(`- 状态: ${data[0].is_active ? '活跃' : '未激活'}`)
        }
        
        return data
    } catch (error) {
        console.error('❌ 订阅列表API测试失败:', error.message)
        return null
    }
}

// 测试功能3: 创建新订阅
async function testCreateSubscription() {
    console.log('\n=== 测试创建订阅 ===')
    
    try {
        const newSubscription = {
            platform: 'bilibili',
            subscription_type: 'precise',
            name: '测试订阅',
            description: '这是一个测试订阅',
            config: {
                user_id: '123456'
            }
        }
        
        const response = await fetch(`${API_BASE_URL}/api/v1/subscriptions/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(newSubscription)
        })
        
        const data = await response.json()
        
        console.log('✅ 创建订阅API响应正常')
        console.log(`- 订阅ID: ${data.subscription_id}`)
        console.log(`- RSS URL: ${data.rss_url}`)
        
        return data
    } catch (error) {
        console.error('❌ 创建订阅API测试失败:', error.message)
        return null
    }
}

// 测试字段兼容性
function testFieldCompatibility(searchResult, subscriptionItem) {
    console.log('\n=== 测试字段兼容性 ===')
    
    if (searchResult && searchResult.results && searchResult.results.length > 0) {
        const template = searchResult.results[0]
        console.log('搜索结果字段检查:')
        console.log(`- template_id: ${template.template_id ? '✅' : '❌'}`)
        console.log(`- template_name: ${template.template_name ? '✅' : '❌'}`)
        console.log(`- required_params: ${template.required_params ? '✅' : '❌'}`)
    }
    
    if (subscriptionItem && subscriptionItem.length > 0) {
        const subscription = subscriptionItem[0]
        console.log('订阅项字段检查:')
        console.log(`- subscription_id: ${subscription.subscription_id ? '✅' : '❌'}`)
        console.log(`- platform: ${subscription.platform ? '✅' : '❌'}`)
        console.log(`- is_active: ${subscription.is_active !== undefined ? '✅' : '❌'}`)
    }
}

// 运行所有测试
async function runAllTests() {
    console.log('🚀 开始API集成测试...\n')
    
    const searchResult = await testSubscriptionSearch()
    const subscriptionList = await testSubscriptionList()
    const createResult = await testCreateSubscription()
    
    testFieldCompatibility(searchResult, subscriptionList)
    
    console.log('\n📊 测试完成总结:')
    console.log(`- 搜索API: ${searchResult ? '✅ 正常' : '❌ 异常'}`)
    console.log(`- 订阅列表API: ${subscriptionList ? '✅ 正常' : '❌ 异常'}`)
    console.log(`- 创建订阅API: ${createResult ? '✅ 正常' : '❌ 异常'}`)
    
    if (searchResult && subscriptionList && createResult) {
        console.log('\n🎉 前后端API对接状态: 良好')
    } else {
        console.log('\n⚠️  前后端API对接状态: 存在问题')
    }
}

// 如果是Node.js环境则运行测试
if (typeof module !== 'undefined' && module.exports) {
    // Node.js环境需要安装node-fetch
    const fetch = require('node-fetch')
    runAllTests()
} else {
    // 浏览器环境
    window.runAPITests = runAllTests
} 