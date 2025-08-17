import { type FormEvent, useState } from 'react'

export default function Login() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const onSubmit = (e: FormEvent) => {
    e.preventDefault()
    // Intentionally no API call yet; we'll wire it next step
  }

  return (
    <div
      style={{
        width: '100%',
        minHeight: '100dvh',
        backgroundColor: '#633D00',
        color: '#FAF0DC',
        fontFamily: 'Instrument Sans, ui-sans-serif, system-ui',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '3rem 2rem',
      }}
    >
      <div className="w-full max-w-xl px-6 py-11 flex flex-col items-center justify-center space-y-6">
        {/* Logo */}
        <div className="w-full flex justify-center">
          <img src="/images/logo.png" alt="HourglassED Logo" className="w-85 h-auto" />
        </div>

        {/* Login heading */}
        <h1 className="text-3xl font-bold">Login</h1>

        <form onSubmit={onSubmit} className="mt-2 flex flex-col items-center space-y-4">
          {/* Email field: label to the left of the input */}
          <div className="flex items-center gap-3 my-1">
            <label htmlFor="email" className="font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              className="w-80 rounded-md border px-4 py-2 text-[#FAF0DC] placeholder:text-[#FAF0DC]/70 bg-transparent focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]"
              required
            />
          </div>

          {/* Password field: label to the left of the input */}
          <div className="flex items-center gap-3 my-1">
            <label htmlFor="password" className="font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              className="w-80 rounded-md border px-4 py-2 text-[#FAF0DC] placeholder:text-[#FAF0DC]/70 bg-transparent focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]"
              required
            />
          </div>

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


