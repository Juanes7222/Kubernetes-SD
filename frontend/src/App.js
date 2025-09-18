import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import LoginForm from "./components/Auth/LoginForm";
import SignupForm from "./components/Auth/SignupForm";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Card, CardContent } from "./components/ui/card";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "./components/ui/dialog";
import { Badge } from "./components/ui/badge";
import { Search, Plus, Calendar, CheckCircle2, Circle, Edit3, Trash2, LogOut, User } from "lucide-react";
import { format } from "date-fns";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios interceptor to add auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

const AuthPage = () => {
  const [isLogin, setIsLogin] = useState(true);

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {isLogin ? (
          <LoginForm onToggleMode={() => setIsLogin(false)} />
        ) : (
          <SignupForm onToggleMode={() => setIsLogin(true)} />
        )}
      </div>
    </div>
  );
};

const TodoApp = () => {
  const { user, logout, getIdToken } = useAuth();
  const [tasks, setTasks] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [loading, setLoading] = useState(true);

  // Form states
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    due_date: ""
  });

  // Update auth token when user changes
  useEffect(() => {
    const updateAuthToken = async () => {
      if (user) {
        const token = await getIdToken();
        localStorage.setItem('authToken', token);
      } else {
        localStorage.removeItem('authToken');
      }
    };

    updateAuthToken();
  }, [user, getIdToken]);

  // Fetch tasks
  const fetchTasks = async (search = "") => {
    try {
      const params = search ? { search } : {};
      const response = await axios.get(`${API}/tasks`, { params });
      setTasks(response.data);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      if (error.response?.status === 401) {
        logout();
      }
    } finally {
      setLoading(false);
    }
  };

  // Create task
  const createTask = async (taskData) => {
    try {
      const response = await axios.post(`${API}/tasks`, taskData);
      setTasks(prev => [response.data, ...prev]);
      resetForm();
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error("Error creating task:", error);
    }
  };

  // Update task
  const updateTask = async (taskId, updateData) => {
    try {
      const response = await axios.put(`${API}/tasks/${taskId}`, updateData);
      setTasks(prev => prev.map(task => 
        task.id === taskId ? response.data : task
      ));
      resetForm();
      setEditingTask(null);
    } catch (error) {
      console.error("Error updating task:", error);
    }
  };

  // Delete task
  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`);
      setTasks(prev => prev.filter(task => task.id !== taskId));
    } catch (error) {
      console.error("Error deleting task:", error);
    }
  };

  // Toggle task completion
  const toggleTaskCompletion = async (taskId) => {
    try {
      const response = await axios.patch(`${API}/tasks/${taskId}/toggle`);
      setTasks(prev => prev.map(task => 
        task.id === taskId ? response.data : task
      ));
    } catch (error) {
      console.error("Error toggling task:", error);
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      due_date: ""
    });
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    const taskData = {
      ...formData,
      due_date: formData.due_date || null
    };

    if (editingTask) {
      updateTask(editingTask.id, taskData);
    } else {
      createTask(taskData);
    }
  };

  // Start editing task
  const startEditing = (task) => {
    setEditingTask(task);
    setFormData({
      title: task.title,
      description: task.description,
      due_date: task.due_date || ""
    });
  };

  // Format date for display
  const formatDate = (dateString) => {
    if (!dateString) return null;
    try {
      return format(new Date(dateString), "MMM dd, yyyy");
    } catch {
      return dateString;
    }
  };

  // Check if task is overdue
  const isOverdue = (dateString) => {
    if (!dateString) return false;
    const dueDate = new Date(dateString);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return dueDate < today;
  };

  // Handle logout
  const handleLogout = async () => {
    try {
      await logout();
    } catch (error) {
      console.error("Error logging out:", error);
    }
  };

  // Initial load
  useEffect(() => {
    if (user) {
      fetchTasks();
    }
  }, [user]);

  // Search functionality
  useEffect(() => {
    if (user) {
      const timeoutId = setTimeout(() => {
        fetchTasks(searchQuery);
      }, 500);

      return () => clearTimeout(timeoutId);
    }
  }, [searchQuery, user]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Cargando tareas...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Header with user info */}
        <div className="mb-8 flex justify-between items-start">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-2">Lista de Tareas</h1>
            <p className="text-gray-600">Organiza y gestiona tus tareas diarias</p>
          </div>
          
          <div className="flex items-center gap-4">
            <div className="text-right">
              <div className="text-sm text-gray-500">Bienvenido</div>
              <div className="font-medium text-gray-900">
                {user?.displayName || user?.email}
              </div>
            </div>
            <Button
              variant="outline"
              size="sm"
              onClick={handleLogout}
              className="flex items-center gap-2"
            >
              <LogOut className="h-4 w-4" />
              Salir
            </Button>
          </div>
        </div>

        {/* Search and Add */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
            <Input
              placeholder="Buscar tareas..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-10 bg-white border-gray-200"
            />
          </div>
          
          <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
            <DialogTrigger asChild>
              <Button className="bg-gray-900 hover:bg-gray-800 text-white">
                <Plus className="h-4 w-4 mr-2" />
                Nueva Tarea
              </Button>
            </DialogTrigger>
            <DialogContent className="bg-white">
              <DialogHeader>
                <DialogTitle>Crear Nueva Tarea</DialogTitle>
              </DialogHeader>
              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <Input
                    placeholder="Título de la tarea"
                    value={formData.title}
                    onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                    required
                    className="border-gray-200"
                  />
                </div>
                <div>
                  <Textarea
                    placeholder="Descripción (opcional)"
                    value={formData.description}
                    onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                    className="border-gray-200 min-h-[80px]"
                  />
                </div>
                <div>
                  <Input
                    type="date"
                    value={formData.due_date}
                    onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                    className="border-gray-200"
                  />
                </div>
                <div className="flex gap-2 pt-2">
                  <Button type="submit" className="bg-gray-900 hover:bg-gray-800 text-white">
                    Crear Tarea
                  </Button>
                  <Button 
                    type="button" 
                    variant="outline" 
                    onClick={() => setIsCreateDialogOpen(false)}
                    className="border-gray-200"
                  >
                    Cancelar
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        </div>

        {/* Edit Dialog */}
        <Dialog open={!!editingTask} onOpenChange={() => setEditingTask(null)}>
          <DialogContent className="bg-white">
            <DialogHeader>
              <DialogTitle>Editar Tarea</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <Input
                  placeholder="Título de la tarea"
                  value={formData.title}
                  onChange={(e) => setFormData(prev => ({ ...prev, title: e.target.value }))}
                  required
                  className="border-gray-200"
                />
              </div>
              <div>
                <Textarea
                  placeholder="Descripción (opcional)"
                  value={formData.description}
                  onChange={(e) => setFormData(prev => ({ ...prev, description: e.target.value }))}
                  className="border-gray-200 min-h-[80px]"
                />
              </div>
              <div>
                <Input
                  type="date"
                  value={formData.due_date}
                  onChange={(e) => setFormData(prev => ({ ...prev, due_date: e.target.value }))}
                  className="border-gray-200"
                />
              </div>
              <div className="flex gap-2 pt-2">
                <Button type="submit" className="bg-gray-900 hover:bg-gray-800 text-white">
                  Guardar Cambios
                </Button>
                <Button 
                  type="button" 
                  variant="outline" 
                  onClick={() => setEditingTask(null)}
                  className="border-gray-200"
                >
                  Cancelar
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>

        {/* Tasks List */}
        <div className="space-y-3">
          {tasks.length === 0 ? (
            <Card className="bg-white border-gray-200">
              <CardContent className="p-8 text-center">
                <div className="text-gray-400 mb-2">
                  <Circle className="h-12 w-12 mx-auto mb-4" />
                </div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {searchQuery ? "No se encontraron tareas" : "No hay tareas"}
                </h3>
                <p className="text-gray-500">
                  {searchQuery 
                    ? "Intenta con diferentes términos de búsqueda" 
                    : "Crea tu primera tarea para comenzar"
                  }
                </p>
              </CardContent>
            </Card>
          ) : (
            tasks.map((task) => (
              <Card key={task.id} className="bg-white border-gray-200 hover:border-gray-300 transition-colors">
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <button
                      onClick={() => toggleTaskCompletion(task.id)}
                      className="mt-1 text-gray-400 hover:text-gray-600 transition-colors"
                    >
                      {task.completed ? (
                        <CheckCircle2 className="h-5 w-5 text-green-600" />
                      ) : (
                        <Circle className="h-5 w-5" />
                      )}
                    </button>
                    
                    <div className="flex-1 min-w-0">
                      <div className={`text-lg font-medium ${task.completed ? 'line-through text-gray-500' : 'text-gray-900'}`}>
                        {task.title}
                      </div>
                      
                      {task.description && (
                        <p className={`mt-1 text-sm ${task.completed ? 'text-gray-400' : 'text-gray-600'}`}>
                          {task.description}
                        </p>
                      )}
                      
                      <div className="flex items-center gap-2 mt-2">
                        {task.due_date && (
                          <Badge 
                            variant="outline"
                            className={`text-xs ${
                              isOverdue(task.due_date) && !task.completed
                                ? 'border-red-200 text-red-700 bg-red-50'
                                : 'border-gray-200 text-gray-600'
                            }`}
                          >
                            <Calendar className="h-3 w-3 mr-1" />
                            {formatDate(task.due_date)}
                          </Badge>
                        )}
                        
                        {task.completed && (
                          <Badge variant="outline" className="text-xs border-green-200 text-green-700 bg-green-50">
                            Completada
                          </Badge>
                        )}
                      </div>
                    </div>
                    
                    <div className="flex gap-1">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => startEditing(task)}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        <Edit3 className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => deleteTask(task.id)}
                        className="text-gray-400 hover:text-red-600"
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </div>

        {/* Footer */}
        <div className="mt-12 text-center text-sm text-gray-500">
          <p>Total de tareas: {tasks.length}</p>
          <p>Completadas: {tasks.filter(t => t.completed).length} | Pendientes: {tasks.filter(t => !t.completed).length}</p>
        </div>
      </div>
    </div>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

const AppContent = () => {
  const { user } = useAuth();
  
  return (
    <div className="App">
      {user ? <TodoApp /> : <AuthPage />}
    </div>
  );
};

export default App;