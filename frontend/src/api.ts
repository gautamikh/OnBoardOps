export type OnboardingInput = {
  employee_name: string
  job_title: string
  department: string
  location: string
  start_date: string
}

export type OnboardingRequest = OnboardingInput & {
  id: string
  status: string
  created_at: string
}

export async function createOnboardingRequest(
  input: OnboardingInput,
): Promise<OnboardingRequest> {
  let response: Response

  try {
    response = await fetch('/api/onboarding-requests', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(input),
    })
  } catch {
    throw new Error(
      'Could not confirm whether the request was saved. Check the backend before submitting again.',
    )
  }

  if (!response.ok) {
    if (response.status === 422) {
      throw new Error('Check that all fields contain valid values.')
    }

    throw new Error(
      `Could not confirm the save (HTTP ${response.status}). Check the backend before retrying.`,
    )
  }

  return response.json()
}
export type PlanTask = {
  title: string
  owner_team: string
  due_date: string
}

export type SavedPlan = {
  id: string
  request_id: string
  status: 'draft' | 'approved' | 'rejected'
  tasks: PlanTask[]
  created_at: string
}

async function requestPlan(
  requestId: string,
  method: 'GET' | 'POST',
): Promise<SavedPlan> {
  const response = await fetch(
    `/api/onboarding-requests/${encodeURIComponent(requestId)}/plan`,
    { method },
  )

  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('The request or saved plan could not be found.')
    }

    throw new Error(
      `Could not load the plan (HTTP ${response.status}). Please try again.`,
    )
  }

  return response.json()
}

export function generatePlan(requestId: string): Promise<SavedPlan> {
  return requestPlan(requestId, 'POST')
}

export function getPlan(requestId: string): Promise<SavedPlan> {
  return requestPlan(requestId, 'GET')
}

export type ReviewDecision = 'approve' | 'reject'

export type PlanReview = {
  plan: SavedPlan
  workflow_status: 'awaiting_approval' | 'approved' | 'rejected'
  waiting_for_approval: boolean
}

async function sendReviewRequest(
  planId: string,
  decision?: ReviewDecision,
): Promise<PlanReview> {
  const action = decision ? 'decision' : 'review'

  const response = await fetch(
    `/api/plans/${encodeURIComponent(planId)}/${action}`,
    {
      method: 'POST',
      headers: decision
        ? { 'Content-Type': 'application/json' }
        : undefined,
      body: decision ? JSON.stringify({ decision }) : undefined,
    },
  )

  if (!response.ok) {
    if (response.status === 409) {
      throw new Error(
        'The review state has changed. Check the review status before continuing.',
      )
    }

    if (response.status === 404) {
      throw new Error('This plan could not be found.')
    }

    throw new Error(
      `Could not confirm the review result (HTTP ${response.status}). Check its status before continuing.`,
    )
  }

  return response.json()
}

export function startPlanReview(planId: string): Promise<PlanReview> {
  return sendReviewRequest(planId)
}

export function decidePlan(
  planId: string,
  decision: ReviewDecision,
): Promise<PlanReview> {
  return sendReviewRequest(planId, decision)
}