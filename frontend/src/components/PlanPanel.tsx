import { useState } from 'react'

import { generatePlan, getPlan } from '../api'
import type { SavedPlan } from '../api'

type PlanPanelProps = {
  requestId: string
}

export default function PlanPanel({ requestId }: PlanPanelProps) {
  const [plan, setPlan] = useState<SavedPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function handleLoadPlan() {
    if (loading) return

    setLoading(true)
    setError('')

    try {
      const result = plan
        ? await getPlan(requestId)
        : await generatePlan(requestId)

      setPlan(result)
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : 'Could not connect to the backend. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  return (
    <section className="card plan-panel" aria-labelledby="plan-heading">
      <div className="plan-header">
        <div>
          <p className="eyebrow">NEXT STEP</p>
          <h2 id="plan-heading">Onboarding plan</h2>
        </div>

        {plan && <span className="plan-status">{plan.status}</span>}
      </div>

      <p className="hint">
        Prepare tasks for HR, IT, and the hiring manager.
        Generating a plan does not execute its tasks.
      </p>

      <button
        type="button"
        onClick={handleLoadPlan}
        disabled={loading}
      >
        {loading
          ? 'Loading plan…'
          : plan
            ? 'Refresh saved plan'
            : 'Generate plan'}
      </button>

      <p className="hint" role="status">
        {loading ? 'Contacting the backend…' : ''}
      </p>

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}

      {plan && (
        <>
          <p className="hint">
            Plan ID: <span className="request-id">{plan.id}</span>
          </p>

          {plan.tasks.length === 0 ? (
            <p>This plan has no tasks.</p>
          ) : (
            <div
              className="table-scroll"
              role="region"
              aria-label="Onboarding tasks"
              tabIndex={0}
            >
              <table className="task-table">
                <caption>Tasks in the saved onboarding plan</caption>
                <thead>
                  <tr>
                    <th scope="col">Task</th>
                    <th scope="col">Owner</th>
                    <th scope="col">Due date</th>
                  </tr>
                </thead>
                <tbody>
                  {plan.tasks.map((task, index) => (
                    <tr key={`${plan.id}-${index}`}>
                      <td>{task.title}</td>
                      <td>{task.owner_team}</td>
                      <td>
                        <time dateTime={task.due_date}>
                          {task.due_date}
                        </time>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          <p className="hint">
            This plan uses demonstration rules. Dates are calendar dates.
          </p>
        </>
      )}
    </section>
  )
}