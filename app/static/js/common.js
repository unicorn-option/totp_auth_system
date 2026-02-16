/**
 * 共用 JavaScript 工具函数
 * 适用于 Vue 和 React 模板
 */

// API 基础配置
const API_BASE_URL = '';

/**
 * 工具函数：设置 Cookie
 * @param {string} name - Cookie 名称
 * @param {string} value - Cookie 值
 * @param {number} days - 过期天数
 */
function setCookie(name, value, days = 7) {
    const date = new Date();
    date.setTime(date.getTime() + (days * 24 * 60 * 60 * 1000));
    const expires = "expires=" + date.toUTCString();
    document.cookie = name + "=" + value + ";" + expires + ";path=/;samesite=lax";
}

/**
 * 工具函数：删除 Cookie
 * @param {string} name - Cookie 名称
 */
function deleteCookie(name) {
    document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 UTC;path=/;";
}

/**
 * 工具函数：显示加载状态
 * @param {boolean} isLoading - 是否加载中
 * @param {string} elementId - 加载状态元素 ID
 */
function showLoading(isLoading, elementId = 'loading') {
    const loadingElement = document.getElementById(elementId);
    if (loadingElement) {
        loadingElement.style.display = isLoading ? 'block' : 'none';
    }
}

/**
 * 工具函数：显示错误消息
 * @param {string} errorMessage - 错误消息
 * @param {string} elementId - 错误消息元素 ID
 */
function showError(errorMessage, elementId = 'error-message') {
    const errorElement = document.getElementById(elementId);
    if (errorElement) {
        errorElement.textContent = errorMessage;
        errorElement.style.display = errorMessage ? 'block' : 'none';
    }
}

/**
 * 通用的 API POST 请求
 * @param {string} url - API 端点
 * @param {Object} data - 表单数据
 * @param {boolean} includeCredentials - 是否包含凭证
 * @returns {Promise} - 返回响应数据
 */
async function apiPost(url, data, includeCredentials = true) {
    const formData = new FormData();
    
    // 转换对象为 FormData
    for (const key in data) {
        if (data.hasOwnProperty(key)) {
            formData.append(key, data[key]);
        }
    }
    
    const response = await fetch(`${API_BASE_URL}${url}`, {
        method: 'POST',
        body: formData,
        credentials: includeCredentials ? 'include' : 'omit'
    });
    
    if (!response.ok) {
        // 如果是 401 错误，重定向到登录页
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * 通用的 API GET 请求
 * @param {string} url - API 端点
 * @param {boolean} includeCredentials - 是否包含凭证
 * @returns {Promise} - 返回响应数据
 */
async function apiGet(url, includeCredentials = true) {
    const response = await fetch(`${API_BASE_URL}${url}`, {
        method: 'GET',
        credentials: includeCredentials ? 'include' : 'omit'
    });
    
    if (!response.ok) {
        // 如果是 401 错误，重定向到登录页
        if (response.status === 401) {
            window.location.href = '/login';
            return;
        }
        
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `API request failed: ${response.status}`);
    }
    
    return response.json();
}

/**
 * 登录函数
 * @param {string} username - 用户名
 * @param {string} totpCode - TOTP 验证码
 * @returns {Promise<Object>} - 返回用户信息和重定向 URL
 */
async function login(username, totpCode) {
    const data = await apiPost('/auth/login', {
        username,
        totp_code: totpCode
    });
    
    // 设置 Cookie
    setCookie('access_token', data.access_token, 0.5); // 30分钟
    setCookie('refresh_token', data.refresh_token, 7); // 7天
    
    // 计算重定向 URL
    const redirectUrl = data.user.role === 'super_admin' ? '/admin' : '/user';
    
    return {
        user: data.user,
        token: data.access_token,
        refreshToken: data.refresh_token,
        redirectUrl
    };
}

/**
 * 登出函数
 * @returns {Promise<void>}
 */
async function logout() {
    try {
        // 直接使用 fetch 调用，不使用 apiPost，因为不需要处理 JSON 响应
        await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
    } catch (error) {
        console.error('Logout failed:', error);
    } finally {
        // 删除 Cookie
        deleteCookie('access_token');
        deleteCookie('refresh_token');
        window.location.href = '/login';
    }
}

/**
 * 获取用户列表
 * @param {number} page - 页码
 * @param {number} limit - 每页数量
 * @returns {Promise<Object>} - 返回用户列表和分页信息
 */
async function fetchUsers(page = 1, limit = 10) {
    return apiGet(`/api/users?page=${page}&limit=${limit}`, true);
}

/**
 * 创建新用户
 * @param {string} username - 用户名
 * @returns {Promise<Object>} - 返回用户信息和 QR 码 URI
 */
async function createUser(username) {
    return apiPost('/admin/users', { username }, true);
}

/**
 * 删除用户
 * @param {number} userId - 用户 ID
 * @returns {Promise<Object>} - 返回操作结果
 */
async function deleteUser(userId) {
    return apiPost(`/admin/users/${userId}/disable`, {}, true);
}

/**
 * 旋转 TOTP 密钥
 * @returns {Promise<Object>} - 返回新的 TOTP URI
 */
async function rotateTotp() {
    return apiPost('/user/totp/rotate', {}, true);
}

/**
 * 生成 TOTP QR 码
 * @returns {Promise<Object>} - 返回 TOTP URI
 */
async function generateTotpQrCode() {
    return apiPost('/user/totp/qr', {}, true);
}

/**
 * 生成 QR 码
 * @param {string} uri - TOTP URI
 * @returns {Promise<string>} - 返回 QR 码的 Data URL
 */
async function generateQRCode(uri) {
    // 确保 qrcode.js 库已加载
    if (typeof QRCode === 'undefined') {
        throw new Error('QRCode library is not loaded');
    }
    
    const canvas = document.createElement('canvas');
    await QRCode.toCanvas(canvas, uri, {
        width: 200,
        margin: 1
    });
    
    return canvas.toDataURL('image/png');
}

// 导出这些函数，使其在全局可用
if (typeof window !== 'undefined') {
    // 添加到 window 对象，确保在所有地方都能访问
    window.logout = logout;
    window.setCookie = setCookie;
    window.deleteCookie = deleteCookie;
    
    // ApiUtils 对象
    window.ApiUtils = {
        apiPost,
        apiGet,
        login,
        logout,
        fetchUsers,
        createUser,
        deleteUser,
        rotateTotp,
        generateTotpQrCode,
        generateQRCode,
        showLoading,
        showError,
        setCookie,
        deleteCookie
    };
}
