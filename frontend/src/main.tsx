import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { createBrowserRouter, RouterProvider } from 'react-router-dom'
import ProtectedRoute from './routes/ProtectedRoute'
import App from './App.tsx'
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
          { path: '/', element: <App /> },
          { path: '/friends', element: <div /> },
          { path: '/invitations', element: <div /> },
        ],
      },
    ],
  },
])

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <RouterProvider router={router} />
  </StrictMode>,
)
