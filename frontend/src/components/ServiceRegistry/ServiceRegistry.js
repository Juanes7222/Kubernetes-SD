import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Alert, AlertDescription } from '../ui/alert';
import { RefreshCw, Activity, Server, Globe, Database, Shield, Monitor, ArrowRightLeft, CheckCircle2, XCircle, Clock } from 'lucide-react';
import { useToast } from '../../hooks/use-toast';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

// Extraer el host del BACKEND_URL para mostrarlo en la UI
const getBackendHost = () => {
  try {
    const url = new URL(BACKEND_URL);
    return url.hostname;
  } catch {
    return 'localhost';
  }
};

const ServiceRegistry = () => {
  const [backendStatus, setBackendStatus] = useState('checking');
  const [frontendStatus, setFrontendStatus] = useState('active');
  const [firebaseStatus, setFirebaseStatus] = useState('checking');
  const [metrics, setMetrics] = useState({
    totalRequests: 0,
    avgLatency: 0,
    lastRequest: null
  });
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  useEffect(() => {
    checkSystemHealth();
    // Actualizar cada 10 segundos
    const interval = setInterval(checkSystemHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const checkSystemHealth = async () => {
    // Check Backend
    try {
      const startTime = Date.now();
      const response = await fetch(`${BACKEND_URL}/health`);
      const latency = Date.now() - startTime;
      
      if (response.ok) {
        setBackendStatus('healthy');
        setMetrics(prev => ({
          totalRequests: prev.totalRequests + 1,
          avgLatency: Math.round((prev.avgLatency + latency) / 2),
          lastRequest: new Date().toLocaleTimeString()
        }));
      } else {
        setBackendStatus('unhealthy');
      }
    } catch (error) {
      setBackendStatus('offline');
    }

    // Check Firebase (simulado basado en si tenemos token)
    const hasFirebaseToken = localStorage.getItem('authToken');
    setFirebaseStatus(hasFirebaseToken ? 'connected' : 'disconnected');
  };

  const handleRefresh = async () => {
    setLoading(true);
    await checkSystemHealth();
    setLoading(false);
    toast({
      title: "Sistema actualizado",
      description: "Estado de componentes verificado"
    });
  };

  const getStatusIcon = (status) => {
    switch(status) {
      case 'healthy':
      case 'active':
      case 'connected':
        return <CheckCircle2 className="w-5 h-5 text-green-600" />;
      case 'unhealthy':
      case 'disconnected':
        return <XCircle className="w-5 h-5 text-red-600" />;
      case 'checking':
        return <Clock className="w-5 h-5 text-yellow-600 animate-pulse" />;
      default:
        return <XCircle className="w-5 h-5 text-gray-600" />;
    }
  };

  const getStatusColor = (status) => {
    switch(status) {
      case 'healthy':
      case 'active':
      case 'connected':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'unhealthy':
      case 'disconnected':
        return 'bg-red-100 text-red-800 border-red-200';
      case 'checking':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-start">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Monitor className="w-6 h-6" />
            Arquitectura Cliente-Servidor Distribuida
          </h2>
          <p className="text-gray-600 mt-1">
            Monitoreo en tiempo real de componentes del sistema
          </p>
        </div>
        <Button onClick={handleRefresh} disabled={loading} variant="outline">
          <RefreshCw className={`w-4 h-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
          Actualizar Estado
        </Button>
      </div>

      {/* Arquitectura Overview */}
      <Card className="bg-gradient-to-br from-blue-50 to-indigo-50 border-2 border-blue-200">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="w-5 h-5" />
            Componentes del Sistema Distribuido
          </CardTitle>
          <CardDescription>
            Visualización de la arquitectura cliente-servidor y servicios externos
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {/* Cliente */}
            <Card className="border-2 border-blue-300">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Globe className="w-5 h-5 text-blue-600" />
                    <span>CLIENTE</span>
                  </div>
                  {getStatusIcon(frontendStatus)}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Tecnología:</span>
                    <span className="text-gray-600">React.js</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Puerto:</span>
                    <span className="text-gray-600">3000</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Ubicación:</span>
                    <span className="text-gray-600">
                      {window.location.hostname}
                    </span>
                  </div>
                </div>
                <Badge className={getStatusColor(frontendStatus)}>
                  {frontendStatus === 'active' ? 'Activo' : 'Inactivo'}
                </Badge>
                <div className="text-xs text-gray-600 bg-white p-2 rounded border">
                  <strong>Rol:</strong> Interfaz de usuario, envía requests al servidor
                </div>
              </CardContent>
            </Card>

            {/* Comunicación */}
            <div className="flex items-center justify-center">
              <Card className="w-full border-2 border-purple-300 bg-purple-50">
                <CardContent className="py-8">
                  <div className="text-center space-y-3">
                    <ArrowRightLeft className="w-12 h-12 mx-auto text-purple-600" />
                    <h3 className="font-bold text-lg">COMUNICACIÓN</h3>
                    <div className="space-y-2 text-sm">
                      <div className="bg-white p-2 rounded">
                        <strong>Protocolo:</strong> HTTP/REST
                      </div>
                      <div className="bg-white p-2 rounded">
                        <strong>Formato:</strong> JSON
                      </div>
                      <div className="bg-white p-2 rounded">
                        <strong>Auth:</strong> JWT Tokens
                      </div>
                      {metrics.avgLatency > 0 && (
                        <div className="bg-white p-2 rounded">
                          <strong>Latencia:</strong> {metrics.avgLatency}ms
                        </div>
                      )}
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Servidor */}
            <Card className="border-2 border-green-300">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Server className="w-5 h-5 text-green-600" />
                    <span>SERVIDOR</span>
                  </div>
                  {getStatusIcon(backendStatus)}
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Tecnología:</span>
                    <span className="text-gray-600">FastAPI</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Puerto:</span>
                    <span className="text-gray-600">8001</span>
                  </div>
                  <div className="flex justify-between text-sm">
                    <span className="font-medium">Ubicación:</span>
                    <span className="text-gray-600">{getBackendHost()}</span>
                  </div>
                </div>
                <Badge className={getStatusColor(backendStatus)}>
                  {backendStatus === 'healthy' ? 'Saludable' : 
                   backendStatus === 'checking' ? 'Verificando...' : 'No disponible'}
                </Badge>
                <div className="text-xs text-gray-600 bg-white p-2 rounded border">
                  <strong>Rol:</strong> Lógica de negocio, procesa requests, gestiona datos
                </div>
              </CardContent>
            </Card>
          </div>
        </CardContent>
      </Card>

      {/* Servicios Externos */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Shield className="w-5 h-5 text-orange-600" />
              Servicio de Autenticación
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Firebase Authentication</div>
                <div className="text-sm text-gray-600">Gestión de usuarios y sesiones</div>
              </div>
              {getStatusIcon(firebaseStatus)}
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="font-medium">Proveedor:</span>
                <span className="text-gray-600">Google Firebase</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Protocolo:</span>
                <span className="text-gray-600">HTTPS</span>
              </div>
            </div>
            <Badge className={getStatusColor(firebaseStatus)}>
              {firebaseStatus === 'connected' ? 'Conectado' : 
               firebaseStatus === 'checking' ? 'Verificando...' : 'Desconectado'}
            </Badge>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-600" />
              Base de Datos Distribuida
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="font-medium">Cloud Firestore</div>
                <div className="text-sm text-gray-600">Almacenamiento de tareas</div>
              </div>
              {getStatusIcon(firebaseStatus)}
            </div>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="font-medium">Tipo:</span>
                <span className="text-gray-600">NoSQL (Documentos)</span>
              </div>
              <div className="flex justify-between">
                <span className="font-medium">Región:</span>
                <span className="text-gray-600">us-central1</span>
              </div>
            </div>
            <Badge className={getStatusColor(firebaseStatus)}>
              {firebaseStatus === 'connected' ? 'Conectado' : 
               firebaseStatus === 'checking' ? 'Verificando...' : 'Desconectado'}
            </Badge>
          </CardContent>
        </Card>
      </div>

      {/* Métricas del Sistema */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5" />
            Métricas del Sistema Distribuido
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="text-center p-4 bg-blue-50 rounded-lg border border-blue-200">
              <div className="text-3xl font-bold text-blue-600">{metrics.totalRequests}</div>
              <div className="text-sm text-gray-600 mt-1">Requests Totales</div>
              <div className="text-xs text-gray-500 mt-2">Cliente → Servidor</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg border border-green-200">
              <div className="text-3xl font-bold text-green-600">
                {metrics.avgLatency > 0 ? `${metrics.avgLatency}ms` : '---'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Latencia Promedio</div>
              <div className="text-xs text-gray-500 mt-2">Tiempo de respuesta</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg border border-purple-200">
              <div className="text-2xl font-bold text-purple-600">
                {metrics.lastRequest || '---'}
              </div>
              <div className="text-sm text-gray-600 mt-1">Última Comunicación</div>
              <div className="text-xs text-gray-500 mt-2">Hora del último request</div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ServiceRegistry;