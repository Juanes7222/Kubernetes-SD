# 🧪 Microservices Testing Guide

Your microservices application is now fully configured and ready for testing! Here's how to test it comprehensively.

## ✅ Backend Services Status

All backend services are **HEALTHY** and **AUTHENTICATED**:

- **✅ Auth Service** (`auth-service:8000`) - Status: Healthy
- **✅ Tasks Service** (`tasks-service:8001`) - Status: Healthy  
- **✅ Collaborator Service** (`collaborator-service:8002`) - Status: Healthy
- **✅ Logs Service** (`logs-service:8003`) - Status: Healthy

## 🌐 Access Points

### Local Access (Recommended for Testing)
- **Frontend**: http://localhost:3000
- **Auth API**: http://localhost:8000 (if port-forward is active)

### Public Access
- **ngrok URL**: Check your ngrok terminal window for the public URL like `https://xxxxx.ngrok-free.app`

## 🔄 Step-by-Step Testing Process

### 1. **Frontend Access Test**
```bash
# Open your browser and go to:
http://localhost:3000
```
**Expected Result**: You should see the login/signup page

### 2. **Authentication Flow Test**

#### Test User Registration:
1. Click "Sign Up" 
2. Enter test credentials:
   - **Email**: `test@example.com`
   - **Password**: `TestPass123!`
3. Click "Create Account"

**Expected Result**: Should create account and redirect to main app

#### Test User Login:
1. Click "Sign In"
2. Enter the same credentials
3. Click "Sign In"

**Expected Result**: Should login and show the tasks dashboard

### 3. **Tasks Management Test**

Once logged in, test the core functionality:

#### Create a Task:
1. Click the "+" (Plus) button
2. Fill in task details:
   - **Title**: "Test Task 1" 
   - **Description**: "This is a test task"
   - **Due Date**: Select a future date
3. Click "Create Task"

**Expected Result**: Task appears in the task list

#### Update a Task:
1. Click the edit (pencil) icon on a task
2. Modify the title or description
3. Save changes

**Expected Result**: Task updates are reflected immediately

#### Toggle Task Completion:
1. Click the circle/check icon next to a task
2. Task should toggle between completed/incomplete

#### Delete a Task:
1. Click the trash icon on a task
2. Task should be removed from the list

### 4. **Collaborators Test**

#### Add a Collaborator:
1. Create a second test user account (different email)
2. From the first user, try to add the second user as a collaborator
3. Use the collaborator management features

**Expected Result**: Should be able to add/remove collaborators

### 5. **Search and Filter Test**

1. Create multiple tasks
2. Use the search box to filter tasks
3. Test different filter options (if available)

**Expected Result**: Tasks should filter correctly

## 🔍 API Testing (Advanced)

If you want to test the APIs directly:

### Health Checks
```bash
curl http://localhost:8000/health  # Auth Service
curl http://localhost:8001/health  # Tasks Service (if port-forwarded)
```

### Protected Endpoints (Need Authentication)
```bash
# These will return 401 without proper Firebase token
curl http://localhost:8000/api/auth/verify
curl http://localhost:8001/api/tasks
```

## 🚨 Expected Behaviors

### ✅ What Should Work:
- User registration and login via Firebase
- CRUD operations on tasks
- Real-time task updates
- Collaborator management
- Search and filtering
- Responsive design on different screen sizes

### ❌ What Might Not Work (Requires Further Configuration):
- Email notifications (requires SMTP setup)
- Real-time notifications (requires WebSocket setup)
- File uploads (requires file storage configuration)

## 🐛 Troubleshooting

### Frontend Issues:
- **White screen**: Check browser console for JavaScript errors
- **API errors**: Check if backend services are running
- **Authentication issues**: Verify Firebase configuration

### Backend Issues:
- **500 errors**: Check pod logs with `kubectl logs -n microservices-app <pod-name>`
- **Connection refused**: Verify services are running and port-forwarding is active

### Check Service Logs:
```bash
# Check individual service logs
kubectl logs -n microservices-app deployment/auth-service
kubectl logs -n microservices-app deployment/tasks-service
kubectl logs -n microservices-app deployment/collaborator-service
kubectl logs -n microservices-app deployment/logs-service
kubectl logs -n microservices-app deployment/frontend
```

## 🎯 Success Criteria

Your application is working correctly if you can:

1. ✅ Access the frontend without errors
2. ✅ Register and login with Firebase authentication  
3. ✅ Create, read, update, and delete tasks
4. ✅ Toggle task completion status
5. ✅ Search tasks (if implemented)
6. ✅ Add/remove collaborators (if implemented)
7. ✅ Navigate between different views
8. ✅ Maintain session across page refreshes

## 🚀 Ready for Production?

Once all tests pass, your application is ready for:
- Public deployment via ngrok (temporary)
- Cloud deployment (AWS, GCP, Azure)
- CI/CD pipeline integration
- Monitoring and logging setup

---

**Happy Testing!** 🎉

If you encounter any issues, check the service logs and verify that all environment variables are properly configured.
