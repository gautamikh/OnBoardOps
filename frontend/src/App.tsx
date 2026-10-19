import { useState } from 'react'
import type { FormEvent } from 'react'

import { createOnboardingRequest } from './api'
import type { OnboardingInput, OnboardingRequest } from './api'
import './App.css'

const fields = [
  { name: 'employee_name', label: 'Employee name', maxLength: 120 },
  { name: 'job_title', label: 'Job title', maxLength: 120 },
  { name: 'department', label: 'Department', maxLength: 80 },
  { name: 'location', label: 'Location', maxLength: 80 },
] as const

function App() {
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState('')
  const [savedRequest, setSavedRequest] =
    useState<OnboardingRequest | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (saving || savedRequest) return

    const form = event.currentTarget
    const data = new FormData(form)

    const input: OnboardingInput = {
      employee_name: String(data.get('employee_name') ?? '').trim(),
      job_title: String(data.get('job_title') ?? '').trim(),
      department: String(data.get('department') ?? '').trim(),
      location: String(data.get('location') ?? '').trim(),
      start_date: String(data.get('start_date') ?? ''),
    }

    setError('')

    if (Object.values(input).some((value) => value.length === 0)) {
      setError('Please complete every field.')
      return
    }

    setSaving(true)

    try {
      const result = await createOnboardingRequest(input)
      setSavedRequest(result)
    } catch (err) {
      setError(
        err instanceof Error ? err.message : 'Something went wrong.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="page">
      <header className="page-header">
        <span className="brand">OnboardOps</span>
        <span className="environment">Local workspace</span>
      </header>

      <section className="intro">
        <p className="eyebrow">EMPLOYEE ONBOARDING</p>
        <h1>A thoughtful start for every new joiner.</h1>
        <p>Create a request, prepare a plan, and coordinate the next steps.</p>
      </section>

      <section className="card" aria-labelledby="request-heading">
        <div className="card-heading">
          <h2 id="request-heading">New onboarding request</h2>
          <p>Use fictional employee details while developing.</p>
        </div>

        <form onSubmit={handleSubmit}>
          <fieldset disabled={saving || savedRequest !== null}>
            <div className="form-grid">
              {fields.map((field) => (
                <label key={field.name} htmlFor={field.name}>
                  {field.label}
                  <input
                    id={field.name}
                    name={field.name}
                    type="text"
                    required
                    maxLength={field.maxLength}
                  />
                </label>
              ))}

              <label htmlFor="start_date">
                Start date
                <input
                  id="start_date"
                  name="start_date"
                  type="date"
                  required
                />
              </label>
            </div>

            <button type="submit">
              {saving
                ? 'Saving request…'
                : savedRequest
                  ? 'Request saved'
                  : 'Create request'}
            </button>
          </fieldset>

          {error && (
            <p className="error" role="alert">
              {error}
            </p>
          )}
        </form>

        {savedRequest && (
          <section className="success" role="status">
            <h3>Request saved</h3>
            <p>
              Onboarding for <strong>{savedRequest.employee_name}</strong>{' '}
              has been recorded.
            </p>
            <dl>
              <dt>Status</dt>
              <dd>{savedRequest.status}</dd>
              <dt>Request ID</dt>
              <dd className="request-id">{savedRequest.id}</dd>
            </dl>
            <p className="hint">
              Keep this ID to retrieve the request and generate its plan.
            </p>
          </section>
        )}
      </section>
    </main>
  )
}

export default App