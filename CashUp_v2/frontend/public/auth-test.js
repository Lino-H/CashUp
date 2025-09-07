// CashUp_v2 认证测试脚本
// 在浏览器控制台中运行此脚本

const API_BASE = '/api';

// 测试登录函数
async function testLogin() {
    try {
        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                username: 'admin',
                password: 'admin123'
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            // 保存token
            if (data.session_id) {
                localStorage.setItem('access_token', data.session_id);
                console.log('✅ 登录成功！');
                console.log('Session ID:', data.session_id);
                console.log('用户信息:', data.user);
                return true;
            } else {
                console.error('❌ 登录成功但未返回 session_id');
                return false;
            }
        } else {
            console.error('❌ 登录失败:', data.detail || '未知错误');
            return false;
        }
    } catch (error) {
        console.error('❌ 网络错误:', error);
        return false;
    }
}

// 检查认证状态
function checkAuthStatus() {
    const token = localStorage.getItem('access_token');
    if (token) {
        console.log('✅ 已登录 (Token:', token.substring(0, 20) + '...)');
        return true;
    } else {
        console.log('❌ 未登录');
        return false;
    }
}

// 获取用户信息
async function getUserInfo() {
    const token = localStorage.getItem('access_token');
    if (!token) {
        console.error('❌ 请先登录');
        return null;
    }
    
    try {
        const response = await fetch(`${API_BASE}/auth/me`, {
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            }
        });
        
        const data = await response.json();
        
        if (response.ok) {
            console.log('✅ 获取用户信息成功:');
            console.log('用户信息:', data);
            return data;
        } else {
            console.error('❌ 获取用户信息失败:', data.detail || '未知错误');
            return null;
        }
    } catch (error) {
        console.error('❌ 网络错误:', error);
        return null;
    }
}

// 测试健康检查
async function testHealth() {
    try {
        const response = await fetch(`${API_BASE}/core/health`);
        const data = await response.json();
        
        if (response.ok) {
            console.log('✅ 健康检查成功:', data);
        } else {
            console.error('❌ 健康检查失败:', data.detail || '未知错误');
        }
    } catch (error) {
        console.error('❌ 网络错误:', error);
    }
}

// 完整测试流程
async function runFullTest() {
    console.log('🧪 开始 CashUp_v2 认证测试...');
    
    // 1. 检查当前状态
    console.log('\n1. 检查当前认证状态:');
    const isLoggedIn = checkAuthStatus();
    
    // 2. 测试登录
    console.log('\n2. 测试登录:');
    const loginSuccess = await testLogin();
    
    // 3. 获取用户信息
    console.log('\n3. 获取用户信息:');
    if (loginSuccess) {
        const userInfo = await getUserInfo();
        if (userInfo) {
            console.log('✅ 用户信息验证成功');
        }
    }
    
    // 4. 测试健康检查
    console.log('\n4. 测试健康检查:');
    await testHealth();
    
    console.log('\n🧪 测试完成！');
}

// 运行测试
runFullTest();