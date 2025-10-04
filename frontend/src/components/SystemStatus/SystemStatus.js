import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Check, X, RefreshCw } from 'lucide-react';

const SystemStatus = () => {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [authStatus, setAuthStatus] = useState('checking');
  const [loading, setLoading] = useState(false);

  const checkBackendHealth = async () => {
    try {
      const response = await fetch(`${process.env.REACT_APP_BACKEND_URL}/api/health`);
      if (response.ok) {
        setBackendStatus('healthy');
      } else {
        setBackendStatus('unhealthy');
      }
    } catch (error) {
      console.error('Backend health check failed:', error);
      setBackendStatus('unreachable');
    }
  };

  const checkAuthStatus = () => {
    // Simple check if Firebase config is loaded
    if (process.env.REACT_APP_FIREBASE_API_KEY) {
      setAuthStatus('configured');
    } else {
      setAuthStatus('not-configured');
    }
  };

  const runAllChecks = async () => {
    setLoading(true);
    await Promise.all([
      checkBackendHealth(),
      checkAuthStatus()
    ]);
    setLoading(false);
  };

  useEffect(() => {
    runAllChecks();
  }, []);

  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy':
      case 'configured':
        return 'bg-green-100 text-green-800';
      case 'unhealthy':
      case 'unreachable':
      case 'not-configured':
        return 'bg-red-100 text-red-800';
      case 'checking':
      default:
        return 'bg-yellow-100 text-yellow-800';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'healthy':
      case 'configured':
        return <Check className="w-4 h-4" />;
      case 'unhealthy':
      case 'unreachable':
      case 'not-configured':
        return <X className="w-4 h-4" />;
      case 'checking':
      default:
        return <RefreshCw className="w-4 h-4 animate-spin" />;
    }
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          System Status
          <Button 
            onClick={runAllChecks} 
            disabled={loading}
            variant="outline"
            size="sm"
          >
            <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <span className="font-medium">Backend API</span>
            <Badge className={getStatusColor(backendStatus)}>
              {getStatusIcon(backendStatus)}
              <span className="ml-2 capitalize">{backendStatus}</span>
            </Badge>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="font-medium">Firebase Auth</span>
            <Badge className={getStatusColor(authStatus)}>
              {getStatusIcon(authStatus)}
              <span className="ml-2 capitalize">{authStatus}</span>
            </Badge>
          </div>

          <div className="text-sm text-gray-600 pt-2 border-t">
            <div>Backend URL: {process.env.REACT_APP_BACKEND_URL}</div>
            <div>Firebase Project: {process.env.REACT_APP_FIREBASE_PROJECT_ID}</div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

export default SystemStatus;