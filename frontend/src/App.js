import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import LoginForm from "./components/Auth/LoginForm";
import SignupForm from "./components/Auth/SignupForm";
import ServiceRegistry from "./components/ServiceRegistry/ServiceRegistry";
import SystemStatus from "./components/SystemStatus/SystemStatus";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Textarea } from "./components/ui/textarea";
import { Card, CardContent } from "./components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./components/ui/dialog";
import { Badge } from "./components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./components/ui/tabs";
import { useToast } from "./hooks/use-toast";
import { Toaster } from "./components/ui/toaster";
import {
  Search,
  Plus,
  Calendar,
  CheckCircle2,
  Circle,
  Edit3,
  Trash2,
  LogOut,
  User,
  Server,
  ListTodo,
} from "lucide-react";
import { format } from "date-fns";
import logger from "./lib/logger";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

// Configure axios interceptor to add auth token
axios.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem("authToken");
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
  const { toast } = useToast();
  const [tasks, setTasks] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [taskFilter, setTaskFilter] = useState("all"); // all, owned, collaborator, assigned
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shareTask, setShareTask] = useState(null);
  const [shareUid, setShareUid] = useState("");
  const [activeTab, setActiveTab] = useState("tasks"); // tasks, services
  const currentUserUidRef = useRef(user?.uid); // Ref para rastrear el UID actual
  

  // Form states
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    due_date: "",
  });

  // Helper function to extract error message from backend response
  const getErrorMessage = (error) => {
    if (error.response?.data?.detail) {
      // FastAPI returns detail field
      if (typeof error.response.data.detail === 'string') {
        return error.response.data.detail;
      }
      // Sometimes detail is an array
      if (Array.isArray(error.response.data.detail)) {
        return error.response.data.detail.map(e => e.msg || e.message).join(', ');
      }
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return 'Ha ocurrido un error inesperado';
  };

  // Update auth token when user changes
  useEffect(() => {
    const updateAuthToken = async () => {
      if (user) {
        const token = await getIdToken();
        localStorage.setItem("authToken", token);
      } else {
        localStorage.removeItem("authToken");
      }
    };

    updateAuthToken();
  }, [user, getIdToken]);

  // Fetch tasks
  const fetchTasks = async (search = "", filter = taskFilter) => {
    try {
      const params = {};
      if (search) params.search = search;
      if (filter !== "all") params.filter_by = filter;
      
      const response = await axios.get(`${API}/tasks`, { params });
      const tasksData = response.data || [];

      // Enrich owners: if task.owner is missing but owner_id present, resolve via backend
      const ownerCache = {};
      const ownersToFetch = new Set();
      tasksData.forEach((t) => {
        if ((!t.owner || !t.owner.email) && t.owner_id) {
          ownersToFetch.add(t.owner_id);
        }
      });

      // Fetch owners in parallel
      const ownerFetchPromises = Array.from(ownersToFetch).map((uid) =>
        axios
          .get(`${API}/auth/users/${encodeURIComponent(uid)}`)
          .then((r) => ({ uid, info: r.data }))
          .catch(() => ({ uid, info: null }))
      );

      const ownerResults = await Promise.all(ownerFetchPromises);
      ownerResults.forEach(({ uid, info }) => {
        if (info) ownerCache[uid] = info;
      });

      const enriched = tasksData.map((t) => {
        if ((!t.owner || !t.owner.email) && t.owner_id && ownerCache[t.owner_id]) {
          t.owner = ownerCache[t.owner_id];
        }
        return t;
      });

      // Solo actualizar tareas si el usuario no ha cambiado durante el fetch
      if (currentUserUidRef.current === user?.uid) {
        setTasks(enriched);
      }
    } catch (error) {
      console.error("Error fetching tasks:", error);
      logger.error(
        `Error fetching tasks: ${error?.message || error}`,
        user?.email,
        { status: error?.response?.status }
      );
      if (error.response?.status === 401) {
        logout();
        toast({
          title: "Sesión expirada",
          description: "Por favor, inicia sesión nuevamente",
          variant: "destructive"
        });
      } else {
        toast({
          title: "❌ Error al cargar tareas",
          description: getErrorMessage(error),
          variant: "destructive"
        });
      }
    } finally {
      setLoading(false);
    }
  };

  // Create task
  const createTask = async (taskData) => {
    try {
      const response = await axios.post(`${API}/tasks`, taskData);
      const newTask = response.data;
      
      // Enriquecer la tarea con la información del owner (usuario actual)
      if (user && (!newTask.owner || !newTask.owner.uid)) {
        newTask.owner = {
          uid: user.uid,
          email: user.email,
          display_name: user.displayName || user.email
        };
      }
      
      setTasks((prev) => [newTask, ...prev]);
      resetForm();
      setIsCreateDialogOpen(false);
      
      toast({
        title: "✅ Tarea creada",
        description: "La tarea se ha creado exitosamente"
      });
    } catch (error) {
      console.error("Error creating task:", error);
      logger.error(
        `Error creating task: ${error?.message || error}`,
        user?.email,
        { status: error?.response?.status }
      );
      
      toast({
        title: "❌ Error al crear tarea",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
  };

  // Update task
  const updateTask = async (taskId, updateData) => {
    try {
      const response = await axios.put(`${API}/tasks/${taskId}`, updateData);
      const updatedTask = response.data;
      
      // Preservar o enriquecer la información del owner
      setTasks((prev) =>
        prev.map((task) => {
          if (task.id === taskId) {
            // Si la tarea actualizada no tiene owner info, preservar la anterior
            if ((!updatedTask.owner || !updatedTask.owner.uid) && task.owner) {
              updatedTask.owner = task.owner;
            }
            return updatedTask;
          }
          return task;
        })
      );
      resetForm();
      setEditingTask(null);
      
      toast({
        title: "✅ Tarea actualizada",
        description: "Los cambios se han guardado correctamente"
      });
    } catch (error) {
      console.error("Error updating task:", error);
      logger.error(
        `Error updating task: ${error?.message || error}`,
        user?.email,
        { taskId, status: error?.response?.status }
      );
      
      toast({
        title: "❌ Error al actualizar tarea",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
  };

  // Delete task
  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`);
      setTasks((prev) => prev.filter((task) => task.id !== taskId));
      
      toast({
        title: "✅ Tarea eliminada",
        description: "La tarea se ha eliminado correctamente"
      });
    } catch (error) {
      console.error("Error deleting task:", error);
      logger.error(
        `Error deleting task: ${error?.message || error}`,
        user?.email,
        { taskId, status: error?.response?.status }
      );
      
      toast({
        title: "❌ Error al eliminar tarea",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
  };

  // Toggle task completion
  const toggleTaskCompletion = async (taskId) => {
    try {
      const response = await axios.patch(`${API}/tasks/${taskId}/toggle`);
      const updatedTask = response.data;
      
      setTasks((prev) =>
        prev.map((task) => {
          if (task.id === taskId) {
            // Preservar owner info si no viene en la respuesta
            if ((!updatedTask.owner || !updatedTask.owner.uid) && task.owner) {
              updatedTask.owner = task.owner;
            }
            return updatedTask;
          }
          return task;
        })
      );
    } catch (error) {
      console.error("Error toggling task:", error);
      logger.error(
        `Error toggling task: ${error?.message || error}`,
        user?.email,
        { taskId, status: error?.response?.status }
      );
      
      toast({
        title: "❌ Error al cambiar estado",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
  };

  // Reset form
  const resetForm = () => {
    setFormData({
      title: "",
      description: "",
      due_date: "",
    });
  };

  // Handle form submission
  const handleSubmit = (e) => {
    e.preventDefault();
    const taskData = {
      ...formData,
      due_date: formData.due_date || null,
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
      due_date: task.due_date || "",
    });
  };

  // Open share dialog for a task
  const openShareDialog = (task) => {
    setShareTask(task);
    setShareUid("");
  };

  const closeShareDialog = () => setShareTask(null);

  // Add collaborator
  const addCollaborator = async () => {
    if (!shareTask || !shareUid) return;
    try {
      const resp = await axios.post(
        `${API}/tasks/${shareTask.id}/collaborators`,
        { email: shareUid }
      );
      const updatedTask = resp.data;
      
      // Preservar owner info si no viene en la respuesta
      if ((!updatedTask.owner || !updatedTask.owner.uid) && shareTask.owner) {
        updatedTask.owner = shareTask.owner;
      }
      
      setTasks((prev) =>
        prev.map((t) => (t.id === shareTask.id ? updatedTask : t))
      );
      setShareUid("");
      // update local shareTask reference
      setShareTask(updatedTask);
      
      toast({
        title: "✅ Colaborador agregado",
        description: "El colaborador se ha añadido exitosamente"
      });
    } catch (error) {
      console.error("Error adding collaborator:", error);
      
      toast({
        title: "❌ Error al agregar colaborador",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
  };

  // Remove collaborator
  const removeCollaborator = async (identifier) => {
    if (!shareTask) return;
    try {
      const resp = await axios.delete(
        `${API}/tasks/${shareTask.id}/collaborators/${encodeURIComponent(
          identifier
        )}`
      );
      const updatedTask = resp.data;
      
      // Preservar owner info si no viene en la respuesta
      if ((!updatedTask.owner || !updatedTask.owner.uid) && shareTask.owner) {
        updatedTask.owner = shareTask.owner;
      }
      
      setTasks((prev) =>
        prev.map((t) => (t.id === shareTask.id ? updatedTask : t))
      );
      setShareTask(updatedTask);
      
      toast({
        title: "✅ Colaborador eliminado",
        description: "El colaborador se ha removido correctamente"
      });
    } catch (error) {
      console.error("Error removing collaborator:", error);
      
      toast({
        title: "❌ Error al eliminar colaborador",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
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
      toast({
        title: "Sesión cerrada",
        description: "Has cerrado sesión exitosamente"
      });
    } catch (error) {
      console.error("Error logging out:", error);
      logger.error(
        `Error logging out: ${error?.message || error}`,
        user?.email
      );
      
      toast({
        title: "❌ Error al cerrar sesión",
        description: getErrorMessage(error),
        variant: "destructive"
      });
    }
  };

  // Cargar tareas cuando el usuario cambia o cambia el filtro
  useEffect(() => {
    // Actualizar la referencia del usuario actual
    currentUserUidRef.current = user?.uid;
    
    // Limpiar tareas inmediatamente al cambiar de usuario
    setTasks([]);
    
    if (user) {
      setLoading(true);
      // Fetch de las nuevas tareas
      fetchTasks();
    } else {
      setLoading(false);
    }
  }, [user?.uid, taskFilter]); // user?.uid detecta cambios de cuenta

  // Search functionality
  useEffect(() => {
    if (user) {
      const timeoutId = setTimeout(() => {
        fetchTasks(searchQuery, taskFilter);
      }, 500);

      return () => clearTimeout(timeoutId);
    }
  }, [searchQuery, taskFilter]); // Removido 'user' para evitar duplicación

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-gray-500">Cargando tareas...</div>
      </div>
    );
  }

  return (
    <>
      <div className="min-h-screen bg-gray-50">
        <div className="max-w-6xl mx-auto px-4 py-8">
          {/* Header with user info */}
          <div className="mb-8 flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Gestor de Tareas colaborativo
              </h1>
              <p className="text-gray-600">
                Gestiona tareas y servicios desde un solo lugar
              </p>
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

          {/* System Status - shown once for the entire app */}
          <SystemStatus />

          {/* Navigation Tabs */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-2 lg:w-400">
              <TabsTrigger value="tasks" className="flex items-center space-x-2">
                <ListTodo className="w-4 h-4" />
                <span>Tareas</span>
              </TabsTrigger>
              <TabsTrigger value="services" className="flex items-center space-x-2">
                <Server className="w-4 h-4" />
                <span>Service Registry</span>
              </TabsTrigger>
            </TabsList>

            {/* Tasks Tab */}
            <TabsContent value="tasks" className="space-y-6">
              {/* Search and Add */}
              <div className="flex flex-col sm:flex-row gap-4">
                <div className="relative flex-1">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    placeholder="Buscar tareas..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-10 bg-white border-gray-200"
                  />
                </div>

                {/* Filtros de tareas */}
                <div className="flex gap-2">
                  <Button
                    variant={taskFilter === "all" ? "default" : "outline"}
                    onClick={() => setTaskFilter("all")}
                    size="sm"
                  >
                    Todas
                  </Button>
                  <Button
                    variant={taskFilter === "owned" ? "default" : "outline"}
                    onClick={() => setTaskFilter("owned")}
                    size="sm"
                  >
                    Propias
                  </Button>
                  <Button
                    variant={taskFilter === "collaborator" ? "default" : "outline"}
                    onClick={() => setTaskFilter("collaborator")}
                    size="sm"
                  >
                    Colaboración
                  </Button>
                </div>

                <Dialog
                  open={isCreateDialogOpen}
                  onOpenChange={setIsCreateDialogOpen}
                >
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
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              title: e.target.value,
                            }))
                          }
                          required
                          className="border-gray-200"
                        />
                      </div>
                      <div>
                        <Textarea
                          placeholder="Descripción (opcional)"
                          value={formData.description}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              description: e.target.value,
                            }))
                          }
                          className="border-gray-200 min-h-[80px]"
                        />
                      </div>
                      <div>
                        <Input
                          type="date"
                          value={formData.due_date}
                          onChange={(e) =>
                            setFormData((prev) => ({
                              ...prev,
                              due_date: e.target.value,
                            }))
                          }
                          className="border-gray-200"
                        />
                      </div>
                      <div className="flex gap-2 pt-2">
                        <Button
                          type="submit"
                          className="bg-gray-900 hover:bg-gray-800 text-white"
                        >
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
              <Dialog
                open={!!editingTask}
                onOpenChange={() => setEditingTask(null)}
              >
                <DialogContent className="bg-white">
                  <DialogHeader>
                    <DialogTitle>Editar Tarea</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                      <Input
                        placeholder="Título de la tarea"
                        value={formData.title}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            title: e.target.value,
                          }))
                        }
                        required
                        className="border-gray-200"
                      />
                    </div>
                    <div>
                      <Textarea
                        placeholder="Descripción (opcional)"
                        value={formData.description}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            description: e.target.value,
                          }))
                        }
                        className="border-gray-200 min-h-[80px]"
                      />
                    </div>
                    <div>
                      <Input
                        type="date"
                        value={formData.due_date}
                        onChange={(e) =>
                          setFormData((prev) => ({
                            ...prev,
                            due_date: e.target.value,
                          }))
                        }
                        className="border-gray-200"
                      />
                    </div>
                    <div className="flex gap-2 pt-2">
                      <Button
                        type="submit"
                        className="bg-gray-900 hover:bg-gray-800 text-white"
                      >
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
                          : "Crea tu primera tarea para comenzar"}
                      </p>
                    </CardContent>
                  </Card>
                ) : (
                  tasks.map((task) => (
                    <Card
                      key={task.id}
                      className="bg-white border-gray-200 hover:border-gray-300 transition-colors"
                    >
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
                            <div
                              className={`text-lg font-medium ${
                                task.completed
                                  ? "line-through text-gray-500"
                                  : "text-gray-900"
                              }`}
                            >
                              {task.title}
                            </div>

                            {task.description && (
                              <p
                                className={`mt-1 text-sm ${
                                  task.completed ? "text-gray-400" : "text-gray-600"
                                }`}
                              >
                                {task.description}
                              </p>
                            )}

                            <div className="flex items-center gap-2 mt-2">
                              {task.due_date && (
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${
                                    isOverdue(task.due_date) && !task.completed
                                      ? "border-red-200 text-red-700 bg-red-50"
                                      : "border-gray-200 text-gray-600"
                                  }`}
                                >
                                  <Calendar className="h-3 w-3 mr-1" />
                                  {formatDate(task.due_date)}
                                </Badge>
                              )}

                              {task.completed && (
                                <Badge
                                  variant="outline"
                                  className="text-xs border-green-200 text-green-700 bg-green-50"
                                >
                                  Completada
                                </Badge>
                              )}

                              {/* Mostrar si la tarea fue compartida contigo */}
                              {task.invited_by && (
                                <Badge
                                  variant="outline"
                                  className="text-xs border-purple-200 text-purple-700 bg-purple-50"
                                >
                                  Compartida por {task.invited_by.invited_by_name || task.invited_by.invited_by_email}
                                </Badge>
                              )}

                              {/* Mostrar owner */}
                              {task.owner && (
                                <Badge
                                  variant="outline"
                                  className="text-xs border-blue-200 text-blue-700 bg-blue-50"
                                >
                                  <User className="h-3 w-3 mr-1" />
                                  Creada por {task.owner.display_name || task.owner.email}
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
                            
                            {/* Mostrar botones de eliminar y compartir solo para el propietario */}
                            {(task.owner?.uid === user?.uid) && (
                              <>
                               <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => openShareDialog(task)}
                                    className="text-gray-400 hover:text-gray-600"
                                    title="Compartir"
                                  >
                                    <User className="h-4 w-4" />
                                  </Button>
                                
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => deleteTask(task.id)}
                                  className="text-gray-400 hover:text-red-600"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              </>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))
                )}
              </div>
            </TabsContent>

            {/* Services Tab */}
            <TabsContent value="services">
              <ServiceRegistry />
            </TabsContent>
          </Tabs>

          {/* Footer para la tab de tareas */}
          {activeTab === "tasks" && (
            <div className="mt-12 text-center text-sm text-gray-500">
              <p>Total de tareas: {tasks.length}</p>
              <p>
                Completadas: {tasks.filter((t) => t.completed).length} |
                Pendientes: {tasks.filter((t) => !t.completed).length}
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Share Task Dialog */}
      <Dialog open={!!shareTask} onOpenChange={closeShareDialog}>
        <DialogContent className="bg-white">
          <DialogHeader>
            <DialogTitle>Compartir tarea</DialogTitle>
          </DialogHeader>
          {shareTask && (
            <div className="space-y-6">
              {/* Información de la tarea */}
              <div className="pb-4 border-b">
                <div className="text-sm font-medium">{shareTask.title}</div>
                {shareTask.description && (
                  <div className="text-xs text-gray-500 mt-1">
                    {shareTask.description}
                  </div>
                )}
                {shareTask.due_date && (
                  <div className="text-xs text-gray-400 mt-1">
                    Vence: {formatDate(shareTask.due_date)}
                  </div>
                )}
              </div>

              {/* Información del creador */}
              <div>
                <div className="text-sm font-medium mb-2 text-blue-700">Creador de la tarea</div>
                <div className="border rounded p-3 bg-blue-50">
                  <div className="text-sm">
                    <div className="font-medium flex items-center gap-2">
                      <User className="h-4 w-4 text-blue-600" />
                      {shareTask.owner?.display_name || 
                       shareTask.owner?.email || 
                       shareTask.owner?.uid || 
                       'Usuario desconocido'}
                    </div>
                    {shareTask.owner?.email && (
                      <div className="text-xs text-gray-600 mt-1">
                        {shareTask.owner.email}
                      </div>
                    )}
                    <div className="text-xs text-blue-600 mt-1 font-medium">
                      Propietario
                    </div>
                  </div>
                </div>
              </div>

              {/* Información de quién te agregó como colaborador */}
              {shareTask.invited_by && (
                <div>
                  <div className="text-sm font-medium mb-2 text-green-700">Te agregó como colaborador</div>
                  <div className="border rounded p-3 bg-green-50">
                    <div className="text-sm">
                      <div className="font-medium flex items-center gap-2">
                        <User className="h-4 w-4 text-green-600" />
                        {shareTask.invited_by.invited_by_name || 
                         shareTask.invited_by.invited_by_email || 
                         'Usuario desconocido'}
                      </div>
                      {shareTask.invited_by.invited_by_email && (
                        <div className="text-xs text-gray-600 mt-1">
                          {shareTask.invited_by.invited_by_email}
                        </div>
                      )}
                      {shareTask.invited_by.invited_at && (
                        <div className="text-xs text-green-600 mt-1">
                          Invitado el: {new Date(shareTask.invited_by.invited_at).toLocaleDateString()}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}

              {/* Añadir colaborador */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Añadir colaborador por correo electrónico
                </label>
                <div className="flex gap-2">
                  <Input
                    value={shareUid}
                    onChange={(e) => setShareUid(e.target.value)}
                    placeholder="correo@ejemplo.com"
                    className="border-gray-200"
                  />
                  <Button
                    onClick={addCollaborator}
                    className="bg-gray-900 text-white hover:bg-gray-800"
                  >
                    Invitar
                  </Button>
                </div>
              </div>

              {/* Lista de colaboradores */}
              <div>
                <div className="text-sm font-medium mb-2">Colaboradores</div>
                {!shareTask.collaborators ||
                shareTask.collaborators.length === 0 ? (
                  <div className="text-xs text-gray-500 p-3 border rounded bg-gray-50">
                    No hay colaboradores añadidos
                  </div>
                ) : (
                  <div className="flex flex-col gap-2">
                    {shareTask.collaborators.map((c) => (
                      <div
                        key={c.uid}
                        className="flex items-center justify-between gap-2 border rounded p-3 bg-white"
                      >
                        <div className="text-sm">
                          <div className="font-medium">
                            {c.display_name || c.email || c.uid}
                          </div>
                          <div className="text-xs text-gray-500">
                            {c.email || c.uid}
                          </div>
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => removeCollaborator(c.uid)}
                          className="text-red-600 hover:text-red-700 hover:bg-red-50"
                        >
                          Eliminar
                        </Button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Botones de acción */}
              <div className="flex justify-end pt-4 border-t">
                <Button variant="outline" onClick={closeShareDialog}>
                  Cerrar
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>      
    </>
  );
};

function App() {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster />
    </AuthProvider>
  );
}

const AppContent = () => {
  const { user } = useAuth();

  return <div className="App">{user ? <TodoApp /> : <AuthPage />}</div>;
};

export default App;
