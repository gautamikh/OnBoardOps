import { useRef, useState } from 'react'

import { decidePlan, startPlanReview } from '../api'
import type { PlanReview, ReviewDecision, SavedPlan } from '../api'

type ReviewControlsProps = {
  plan: SavedPlan
  disabled: boolean
  onPlanUpdated: (plan: SavedPlan) => void
  onBusyChange: (busy: boolean) => void
}

export default function ReviewControls({
  plan,
  disabled,
  onPlanUpdated,
  onBusyChange,
}: ReviewControlsProps) {
  const [review, setReview] = useState<PlanReview | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const inFlight = useRef(false)

  const isFinal = plan.status !== 'draft'
  const waiting = review?.waiting_for_approval === true

  async function performAction(decision?: ReviewDecision) {
    if (inFlight.current || disabled || isFinal) return

    inFlight.current = true
    setBusy(true)
    onBusyChange(true)
    setError('')

    try {
      const result = decision
        ? await decidePlan(plan.id, decision)
        : await startPlanReview(plan.id)

      setReview(result)
      onPlanUpdated(result.plan)
    } catch (err) {
      // A failed response doesn't prove the decision failed to save.
      // Require a status check before allowing another decision.
      setReview(null)
      setError(
        err instanceof Error
          ? err.message
          : 'Could not confirm the result. Check the review status.',
      )
    } finally {
      inFlight.current = false
      setBusy(false)
      onBusyChange(false)
    }
  }

  return (
    <section className="review-section" aria-labelledby="review-heading">
      <h3 id="review-heading">Review this plan</h3>

      <p className="hint">
        Check the tasks, owners, and dates before deciding.
        Approval records your decision; it does not execute tasks.
      </p>

      <p className="review-message" role="status">
        {busy
          ? 'Saving or checking the review…'
          : isFinal
            ? `This plan is ${plan.status}.`
            : waiting
              ? 'Review started. This plan is waiting for your decision.'
              : 'Start or recover the review to continue.'}
      </p>

      {!isFinal && (
        <div className="review-actions">
          <button
            type="button"
            className="secondary-button"
            disabled={busy || disabled}
            onClick={() => performAction()}
          >
            {review || error ? 'Check review status' : 'Start review'}
          </button>

          {waiting && (
            <>
              <button
                type="button"
                disabled={busy || disabled}
                onClick={() => performAction('approve')}
              >
                Approve plan
              </button>

              <button
                type="button"
                className="reject-button"
                disabled={busy || disabled}
                onClick={() => performAction('reject')}
              >
                Reject plan
              </button>
            </>
          )}
        </div>
      )}

      {error && (
        <p className="error" role="alert">
          {error}
        </p>
      )}
    </section>
  )
}