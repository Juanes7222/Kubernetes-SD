const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

class ServiceRegistryAPI {
  constructor() {
    this.baseURL = `${API_BASE_URL}/api/services`;
  }

  async makeRequest(url, options = {}) {
    const token = localStorage.getItem('authToken');
    
    const defaultOptions = {
      headers: {
        'Content-Type': 'application/json',
        ...(token && { 'Authorization': `Bearer ${token}` })
      }
    };

    const response = await fetch(url, { ...defaultOptions, ...options });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
    }
    
    return response.json();
  }

  async getAllServices(tag = null, status = null) {
    let url = `${this.baseURL}/`;
    const params = new URLSearchParams();
    
    if (tag) params.append('tag', tag);
    if (status) params.append('status', status);
    
    if (params.toString()) {
      url += `?${params.toString()}`;
    }
    
    return this.makeRequest(url);
  }

  async getService(serviceName) {
    return this.makeRequest(`${this.baseURL}/${serviceName}`);
  }

  async registerService(serviceData) {
    return this.makeRequest(`${this.baseURL}/register`, {
      method: 'POST',
      body: JSON.stringify(serviceData)
    });
  }

  async updateService(serviceName, updateData) {
    return this.makeRequest(`${this.baseURL}/${serviceName}`, {
      method: 'PUT',
      body: JSON.stringify(updateData)
    });
  }

  async removeService(serviceName) {
    return this.makeRequest(`${this.baseURL}/${serviceName}`, {
      method: 'DELETE'
    });
  }

  async getServicesByTag(tag) {
    return this.makeRequest(`${this.baseURL}/tag/${tag}`);
  }

  async healthCheckAll() {
    return this.makeRequest(`${this.baseURL}/health-check`, {
      method: 'POST'
    });
  }

  async getServiceDiscoveryConfig() {
    return this.makeRequest(`${this.baseURL}/discovery/config`);
  }
}

export const serviceRegistryAPI = new ServiceRegistryAPI();