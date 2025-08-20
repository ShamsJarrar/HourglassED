import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../lib/api'
import type { UserResponse } from '../types/api'

export default function Signup() {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    try {
      await api.post<UserResponse>('/auth/register', { name, email, password })
      // Redirect to OTP verification with the user's email and password for auto-login
      navigate('/verify-email', { replace: true, state: { email, password } })
    } catch (err) {
      alert('Sign up failed. Email may already be registered.')
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
        {/* Heading */}
        <h1 className="text-3xl font-bold">Sign up</h1>

        <form onSubmit={onSubmit} className="mt-2 flex flex-col items-center space-y-4">
          {/* Name */}
          <div className="flex flex-col items-start gap-1 my-1 w-full">
            <label htmlFor="name" className="font-medium">
              Name
            </label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Enter your name"
              className="w-80 rounded-md border-2 border-[#FAF0DC] px-4 py-2 text-[#FAF0DC] placeholder:text-[#FAF0DC]/70 bg-transparent focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]"
              required
            />
          </div>

          {/* Email */}
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

          {/* Password */}
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

          {/* Submit */}
          <button
            type="submit"
            className="w-80 rounded-md bg-[#FAF0DC] text-[#633D00] font-semibold mt-6 py-2 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]/50"
          >
            Sign up
          </button>

          {/* Switch to login */}
          <div className="mt-4 flex items-center gap-2">
            <span className="text-[#FAF0DC]">Already have an account?</span>
            <a href="/login" className="underline text-[#FAF0DC]">
              Login
            </a>
          </div>
        </form>
      </div>
    </div>
  )
}


