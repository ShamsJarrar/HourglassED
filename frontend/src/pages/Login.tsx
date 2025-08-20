import { type FormEvent, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import api from '../lib/api'
import type { TokenWithUserResponse } from '../types/api'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const navigate = useNavigate()
  const location = useLocation() as { state?: { from?: Location } }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      const { data } = await api.post<TokenWithUserResponse>('/auth/login', {
        email,
        password,
      })
      localStorage.setItem('access_token', data.access_token)
      const from = (location.state as any)?.from?.pathname || '/'
      navigate(from, { replace: true })
    } catch (err: any) {
      const status = err?.response?.status
      const detail = err?.response?.data?.detail
      if (status === 403) {
        // Not verified → send to OTP page with email and password for auto-login after verification
        navigate('/verify-email', { replace: true, state: { email, password } })
        return
      }
      alert(detail || 'Login failed. Please check your credentials.')
    }
  }

  return (
    <div
      style={{
        width: '100%',
        minHeight: '100dvh',
        backgroundColor: '#FAF0DC',
        color: '#633D00',
        fontFamily: 'Instrument Sans, ui-sans-serif, system-ui',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 2rem',
        position: 'relative',
      }}
    >
      {/* Top-left logo outside the card */}
      <div className="absolute top-6 left-6">
        <img src="/images/logo.png" alt="HourglassED Logo" className="w-65 h-auto" />
      </div>

      <div className="w-full max-w-md px-8 py-12 flex flex-col items-center justify-center space-y-6 bg-[#633D00] text-[#FAF0DC] rounded-2xl shadow-2xl shadow-black/45">

        {/* Login heading */}
        <h1 className="text-3xl font-bold">Login</h1>

        <form onSubmit={onSubmit} className="mt-2 flex flex-col items-center space-y-4">
          {/* Email field: label to the left of the input */}
          <div className="flex flex-col items-start gap-1 my-1 w-full">
            <label htmlFor="email" className="font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-80 rounded-md border-2 border-[#FAF0DC] px-4 py-2 text-[#FAF0DC] placeholder:text-[#FAF0DC]/70 bg-transparent focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]"
              required
            />
          </div>

          {/* Password field: label to the left of the input */}
          <div className="flex flex-col items-start gap-1 my-1 w-full">
            <label htmlFor="password" className="font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-80 rounded-md border-2 border-[#FAF0DC] px-4 py-2 text-[#FAF0DC] placeholder:text-[#FAF0DC]/70 bg-transparent focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]"
              required
            />
          </div>

          {/* Login button */}
          <button
            type="submit"
            className="w-80 rounded-md bg-[#FAF0DC] text-[#633D00] font-semibold mt-6 py-2 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]/50"
          >
            Login
          </button>

          {/* Sign up: prompt text to the left of the link */}
          <div className="mt-4 flex items-center gap-2">
            <span>Have not created an account yet?</span>
            <a href="/signup" className="underline">
              Sign up
            </a>
          </div>
        </form>
      </div>
    </div>
  )
}


