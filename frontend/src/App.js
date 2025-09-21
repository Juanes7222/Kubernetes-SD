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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "./components/ui/dialog";
import { Badge } from "./components/ui/badge";
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
  const [tasks, setTasks] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [taskFilter, setTaskFilter] = useState("all"); // all, owned, collaborator, assigned
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [editingTask, setEditingTask] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shareTask, setShareTask] = useState(null);
  const [shareUid, setShareUid] = useState("");
  const [assignTask, setAssignTask] = useState(null);
  const [assigneeInput, setAssigneeInput] = useState("");

  // Form states
  const [formData, setFormData] = useState({
    title: "",
    description: "",
    due_date: "",
  });

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
      setTasks(response.data);
    } catch (error) {
      console.error("Error fetching tasks:", error);
      logger.error(
        `Error fetching tasks: ${error?.message || error}`,
        user?.email,
        { status: error?.response?.status }
      );
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
      setTasks((prev) => [response.data, ...prev]);
      resetForm();
      setIsCreateDialogOpen(false);
    } catch (error) {
      console.error("Error creating task:", error);
      logger.error(
        `Error creating task: ${error?.message || error}`,
        user?.email,
        { status: error?.response?.status }
      );
    }
  };

  // Update task
  const updateTask = async (taskId, updateData) => {
    try {
      const response = await axios.put(`${API}/tasks/${taskId}`, updateData);
      setTasks((prev) =>
        prev.map((task) => (task.id === taskId ? response.data : task))
      );
      resetForm();
      setEditingTask(null);
    } catch (error) {
      console.error("Error updating task:", error);
      logger.error(
        `Error updating task: ${error?.message || error}`,
        user?.email,
        { taskId, status: error?.response?.status }
      );
    }
  };

  // Delete task
  const deleteTask = async (taskId) => {
    try {
      await axios.delete(`${API}/tasks/${taskId}`);
      setTasks((prev) => prev.filter((task) => task.id !== taskId));
    } catch (error) {
      console.error("Error deleting task:", error);
      logger.error(
        `Error deleting task: ${error?.message || error}`,
        user?.email,
        { taskId, status: error?.response?.status }
      );
    }
  };

  // Toggle task completion
  const toggleTaskCompletion = async (taskId) => {
    try {
      const response = await axios.patch(`${API}/tasks/${taskId}/toggle`);
      setTasks((prev) =>
        prev.map((task) => (task.id === taskId ? response.data : task))
      );
    } catch (error) {
      console.error("Error toggling task:", error);
      logger.error(
        `Error toggling task: ${error?.message || error}`,
        user?.email,
        { taskId, status: error?.response?.status }
      );
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
      setTasks((prev) =>
        prev.map((t) => (t.id === shareTask.id ? resp.data : t))
      );
      setShareUid("");
      // update local shareTask reference
      setShareTask(resp.data);
    } catch (error) {
      console.error("Error adding collaborator:", error);
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
      setTasks((prev) =>
        prev.map((t) => (t.id === shareTask.id ? resp.data : t))
      );
      setShareTask(resp.data);
    } catch (error) {
      console.error("Error removing collaborator:", error);
    }
  };

  // Assign task
  const assignTaskToUser = async () => {
    if (!assigneeInput.trim()) return;
    
    try {
      const resp = await axios.post(
        `${API}/tasks/${assignTask.id}/assign`,
        {
          assignee_email: assigneeInput.includes("@") ? assigneeInput : null,
          assignee_uid: !assigneeInput.includes("@") ? assigneeInput : null,
        }
      );
      setTasks((prev) =>
        prev.map((t) => (t.id === assignTask.id ? resp.data : t))
      );
      setAssignTask(null);
      setAssigneeInput("");
      fetchTasks(searchQuery, taskFilter);
    } catch (error) {
      console.error("Error assigning task:", error);
    }
  };

  // Unassign task
  const unassignTask = async (taskId) => {
    try {
      const resp = await axios.delete(`${API}/tasks/${taskId}/assign`);
      setTasks((prev) =>
        prev.map((t) => (t.id === taskId ? resp.data : t))
      );
      fetchTasks(searchQuery, taskFilter);
    } catch (error) {
      console.error("Error unassigning task:", error);
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
    } catch (error) {
      console.error("Error logging out:", error);
      logger.error(
        `Error logging out: ${error?.message || error}`,
        user?.email
      );
    }
  };

  // Initial load
  useEffect(() => {
    if (user) {
      fetchTasks();
    }
  }, [user, taskFilter]);

  // Search functionality
  useEffect(() => {
    if (user) {
      const timeoutId = setTimeout(() => {
        fetchTasks(searchQuery, taskFilter);
      }, 500);

      return () => clearTimeout(timeoutId);
    }
  }, [searchQuery, user, taskFilter]);

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
        <div className="max-w-4xl mx-auto px-4 py-8">
          {/* Header with user info */}
          <div className="mb-8 flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Lista de Tareas
              </h1>
              <p className="text-gray-600">
                Organiza y gestiona tus tareas diarias
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
              <Button
                variant={taskFilter === "assigned" ? "default" : "outline"}
                onClick={() => setTaskFilter("assigned")}
                size="sm"
              >
                Asignadas
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

                          {/* Mostrar responsable asignado */}
                          {task.assignee && (
                            <Badge
                              variant="outline"
                              className="text-xs border-blue-200 text-blue-700 bg-blue-50"
                            >
                              <User className="h-3 w-3 mr-1" />
                              Asignada a {task.assignee.display_name || task.assignee.email}
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
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setAssignTask(task)}
                          className="text-gray-400 hover:text-blue-600"
                          title="Asignar responsable"
                        >
                          <User className="h-4 w-4" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => openShareDialog(task)}
                          className="text-gray-400 hover:text-gray-600"
                          title="Compartir"
                        >
                          <User className="h-4 w-4" />
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
            <p>
              Completadas: {tasks.filter((t) => t.completed).length} |
              Pendientes: {tasks.filter((t) => !t.completed).length}
            </p>
          </div>
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

      {/* Diálogo de asignación */}
      <Dialog open={!!assignTask} onOpenChange={() => setAssignTask(null)}>
        <DialogContent className="bg-white">
          <DialogHeader>
            <DialogTitle>Asignar Responsable</DialogTitle>
          </DialogHeader>
          {assignTask && (
            <div className="space-y-4">
              <div>
                <p className="text-sm text-gray-600 mb-2">
                  Tarea: <span className="font-medium">{assignTask.title}</span>
                </p>
                
                {assignTask.assignee && (
                  <div className="mb-4 p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm text-blue-800">
                      <strong>Responsable actual:</strong> {assignTask.assignee.display_name || assignTask.assignee.email}
                    </p>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => unassignTask(assignTask.id)}
                      className="mt-2"
                    >
                      Desasignar
                    </Button>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Email o UID del responsable
                </label>
                <Input
                  type="text"
                  value={assigneeInput}
                  onChange={(e) => setAssigneeInput(e.target.value)}
                  placeholder="correo@ejemplo.com"
                  className="w-full"
                />
              </div>

              <div className="flex justify-end gap-2 pt-4 border-t">
                <Button variant="outline" onClick={() => setAssignTask(null)}>
                  Cancelar
                </Button>
                <Button
                  onClick={assignTaskToUser}
                  disabled={!assigneeInput.trim()}
                >
                  Asignar
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
    </AuthProvider>
  );
}

const AppContent = () => {
  const { user } = useAuth();

  return <div className="App">{user ? <TodoApp /> : <AuthPage />}</div>;
};

export default App;
