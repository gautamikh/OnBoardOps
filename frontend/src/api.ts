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