import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import ProtectedRoute from './routes/ProtectedRoute'
import Calendar from './pages/Calendar'
import { ToastProvider } from './components/Toast'
import Invitations from './pages/Invitations'
import Friends from './pages/Friends'
import Login from './pages/Login'
import Signup from './pages/Signup'
import VerifyEmail from './pages/VerifyEmail'
import LoaderLayout from './routes/LoaderLayout'

const router = createBrowserRouter([
  {
    element: <LoaderLayout />,
    children: [
      { path: '/login', element: <Login /> },
      { path: '/signup', element: <Signup /> },
      { path: '/verify-email', element: <VerifyEmail /> },
      {
        element: <ProtectedRoute />,
        children: [
          { path: '/', element: <Calendar /> },
          { path: '/friends', element: <Friends /> },
          { path: '/invitations', element: <Invitations /> },
        ],
      },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <ToastProvider>
      <RouterProvider router={router} />
    </ToastProvider>
  </StrictMode>,
)

