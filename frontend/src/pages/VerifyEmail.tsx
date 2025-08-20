import { type FormEvent, useMemo, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import type { TokenWithUserResponse } from '../types/api'
import api from '../lib/api'

export default function VerifyEmail() {
  const location = useLocation()
  const navigate = useNavigate()
  const stateEmail = (location.state as any)?.email as string | undefined
  const statePassword = (location.state as any)?.password as string | undefined
  const qsEmail = new URLSearchParams(location.search).get('email') || ''
  const initialEmail = stateEmail ?? qsEmail

  const [otpDigits, setOtpDigits] = useState<string[]>(['', '', '', '', '', ''])
  const [error, setError] = useState<string>('')
  const inputsRef = useRef<Array<HTMLInputElement | null>>([])

  const otpString = useMemo(() => otpDigits.join(''), [otpDigits])

  const handleChange = (index: number, value: string) => {
    setError('')
    const clean = value.replace(/\D/g, '').slice(0, 1)
    setOtpDigits((prev) => {
      const next = [...prev]
      next[index] = clean
      return next
    })
    if (clean && index < 5) {
      inputsRef.current[index + 1]?.focus()
    }
  }

  const handleKeyDown = (index: number, e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Backspace' && !otpDigits[index] && index > 0) {
      inputsRef.current[index - 1]?.focus()
    }
    if (e.key === 'ArrowLeft' && index > 0) {
      e.preventDefault()
      inputsRef.current[index - 1]?.focus()
    }
    if (e.key === 'ArrowRight' && index < 5) {
      e.preventDefault()
      inputsRef.current[index + 1]?.focus()
    }
  }

  const onSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (otpString.length !== 6 || otpDigits.some((d) => d === '')) {
      setError('Please enter the 6-digit code.')
      return
    }
    try {
      await api.post('/auth/verify-email-otp', {
        email: initialEmail,
        otp: otpString,
      })
      // After verification, automatically log in and go to calendar
      if (initialEmail && statePassword) {
        const { data } = await api.post<TokenWithUserResponse>('/auth/login', {
          email: initialEmail,
          password: statePassword,
        })
        localStorage.setItem('access_token', data.access_token)
        navigate('/', { replace: true })
      } else {
        // Fallback: send to login if password wasn't available in state
        navigate('/login', { replace: true })
      }
    } catch (err: any) {
      const detail = err?.response?.data?.detail
      setError(detail || 'Invalid or expired OTP. Please try again.')
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
        <h1 className="text-3xl font-bold text-center">OTP Verification</h1>
        {initialEmail && (
          <>
            <p className="text-sm opacity-90 text-center">One Time Passcode (OTP) has been sent via Email to {initialEmail}</p>
            <p className="text-xs opacity-80 text-center">make sure to check your spam</p>
          </>
        )}

        <form onSubmit={onSubmit} className="mt-2 flex flex-col items-center space-y-6 w-full">
          <div className="flex items-center justify-center gap-3">
            {otpDigits.map((digit, idx) => (
              <input
                key={idx}
                ref={(el) => {
                  inputsRef.current[idx] = el
                }}
                inputMode="numeric"
                autoComplete="one-time-code"
                pattern="[0-9]*"
                maxLength={1}
                value={digit}
                onChange={(e) => handleChange(idx, e.target.value)}
                onKeyDown={(e) => handleKeyDown(idx, e)}
                className="w-12 h-14 text-center text-xl rounded-md border-2 border-[#FAF0DC] bg-transparent text-[#FAF0DC] focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]"
              />
            ))}
          </div>

          {error && <p className="text-red-300 text-sm">{error}</p>}

          <button
            type="submit"
            className="w-80 rounded-md mt-3 bg-[#FAF0DC] text-[#633D00] font-semibold py-2 hover:opacity-90 focus:outline-none focus:ring-2 focus:ring-[#FAF0DC]/50"
          >
            Verify OTP
          </button>

          <div className="mt-2 flex items-center gap-2 text-sm">
            <span className="text-[#FAF0DC]">Resend code?</span>
            <button
              type="button"
              className="underline text-[#FAF0DC] hover:opacity-90"
              onClick={async () => {
                if (!initialEmail) {
                  setError('Missing email. Please go back and enter your email again.')
                  return
                }
                try {
                  await api.post('/auth/resend-otp', null, { params: { email: initialEmail } })
                  alert('OTP resent. Please check your email.')
                } catch (err: any) {
                  const detail = err?.response?.data?.detail
                  setError(detail || 'Failed to resend OTP. Please try again later.')
                }
              }}
            >
              Resend
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}


