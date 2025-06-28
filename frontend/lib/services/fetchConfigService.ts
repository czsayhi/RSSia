/**
 * 订阅频率配置API服务
 * 负责与后端fetch接口的交互
 */

// 类型定义
export interface FetchConfig {
  user_id: number;
  auto_fetch_enabled: boolean;
  frequency: 'daily' | 'three_days' | 'weekly';
  preferred_hour: number;
  timezone: string;
  daily_limit: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface UpdateConfigRequest {
  auto_fetch_enabled?: boolean;
  frequency?: 'daily' | 'three_days' | 'weekly';
  preferred_hour?: number;
  daily_limit?: number;
}

// 数据格式转换工具函数
export const formatUtils = {
  /**
   * 将时间字符串转换为小时数
   * @param timeString 格式："09:00"
   * @returns 小时数 (0-23)
   */
  timeStringToHour: (timeString: string): number => {
    const hour = parseInt(timeString.split(':')[0]);
    return Math.max(0, Math.min(23, hour));
  },

  /**
   * 将小时数转换为时间字符串
   * @param hour 小时数 (0-23)
   * @returns 格式："09:00"
   */
  hourToTimeString: (hour: number): string => {
    const validHour = Math.max(0, Math.min(23, hour));
    return `${validHour.toString().padStart(2, '0')}:00`;
  },

  /**
   * 获取当前用户ID - 从localStorage中的认证信息获取
   */
  getCurrentUserId: (): number => {
    try {
      const userStr = localStorage.getItem('rss_user_info');
      if (userStr) {
        const user = JSON.parse(userStr);
        return user.user_id;
      }
    } catch (error) {
      console.error('获取用户ID失败:', error);
    }
    
    // 如果无法获取用户ID，抛出错误而不是返回默认值
    throw new Error('用户未登录或认证信息无效');
  }
};

// API调用函数
export const fetchConfigService = {
  /**
   * 获取用户的订阅频率配置
   */
  async getUserConfig(): Promise<FetchConfig> {
    const userId = formatUtils.getCurrentUserId();
    const response = await fetch(`/api/v1/fetch/config/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`获取配置失败: ${response.status}`);
    }

    return await response.json();
  },

  /**
   * 更新用户的订阅频率配置
   * @param config 要更新的配置项
   */
  async updateUserConfig(config: UpdateConfigRequest): Promise<FetchConfig> {
    const userId = formatUtils.getCurrentUserId();
    const response = await fetch(`/api/v1/fetch/config/${userId}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new Error(`更新配置失败: ${response.status}`);
    }

    return await response.json();
  },

  /**
   * 获取用户的拉取配额信息
   */
  async getUserQuota() {
    const userId = formatUtils.getCurrentUserId();
    const response = await fetch(`/api/v1/fetch/quota/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`获取配额信息失败: ${response.status}`);
    }

    return await response.json();
  },

  /**
   * 检查是否可以手动拉取
   */
  async checkCanFetch() {
    const userId = formatUtils.getCurrentUserId();
    const response = await fetch(`/api/v1/fetch/can-fetch/${userId}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`检查拉取权限失败: ${response.status}`);
    }

    return await response.json();
  },

  /**
   * 手动拉取RSS内容
   */
  async manualFetch(): Promise<{
    success: boolean;
    message: string;
    quota_after?: any;
    fetch_results?: any;
  }> {
    const userId = formatUtils.getCurrentUserId();
    const response = await fetch('/api/v1/fetch/manual-fetch', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        user_id: userId,
      }),
    });

    if (!response.ok) {
      throw new Error(`手动拉取失败: ${response.status}`);
    }

    return await response.json();
  }
}; 