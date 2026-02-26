const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_API_URL

export async function loginUser(username: string, password: string) {
  const body = new URLSearchParams({
    grant_type: "password",
    username,
    password,
    scope: "",
    client_id: "string",
    client_secret: "string",
  })

  const res = await fetch(`${API_BASE_URL}/auth/login`, {
    method: "POST",
    headers: {
      accept: "application/json",
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body,
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Login failed")
  }

  return res.json() as Promise<{ access_token: string; token_type: string }>
}

export async function createCompany(token: string, name: string) {
  const res = await fetch(`${API_BASE_URL}/companies/`, {
    method: "POST",
    headers: {
      accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ name, status: "active" }),
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Failed to create company")
  }

  return res.json() as Promise<{
    name: string
    status: string
    id: number
    company_id: string
  }>
}

export async function uploadDocuments(
  token: string,
  companyId: string,
  files: File[]
) {
  const formData = new FormData()
  formData.append("company_id", companyId)
  for (const file of files) {
    formData.append("files", file)
  }

  const res = await fetch(`${API_BASE_URL}/documents/upload`, {
    method: "POST",
    headers: {
      accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Failed to upload documents")
  }

  return res.json() as Promise<{
    total: number
    uploaded: Array<{
      document_id: string
      filename: string
      status: string
    }>
  }>
}

export async function generateKYB(token: string, companyId: string) {
  const res = await fetch(`${API_BASE_URL}/companies/${companyId}/generate-kyb`, {
    method: "POST",
    headers: {
      accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Failed to generate KYB data")
  }

  return res.json()
}

export async function saveProfile(
  token: string,
  companyId: string,
  payload: { kyb_data: unknown; manual_edits: Array<{ fieldName: string; old_value: unknown; new_value: unknown }> }
) {
  const res = await fetch(`${API_BASE_URL}/companies/${companyId}/save_profile`, {
    method: "POST",
    headers: {
      accept: "application/json",
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Failed to save profile")
  }

  return res.json()
}

export async function getCompanies(token: string) {
  const res = await fetch(`${API_BASE_URL}/companies/`, {
    method: "GET",
    headers: {
      accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Failed to fetch companies")
  }

  return res.json() as Promise<
    Array<{
      name: string
      status: string
      id: number
      company_id: string
    }>
  >
}


export async function deleteCompany(token: string, companyId: string) {
  const res = await fetch(`${API_BASE_URL}/companies/${companyId}`, {
    method: "DELETE",
    headers: {
      accept: "application/json",
      Authorization: `Bearer ${token}`,
    },
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.detail || "Failed to delete company")
  }

  // typed response
  return res.json() as Promise<{ status: string; message: string }>
}