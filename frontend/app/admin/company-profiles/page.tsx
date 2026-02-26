"use client"

import { useState } from "react"
import { useAuth } from "@/lib/auth-context"
import { createCompany, getCompanies, deleteCompany } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Building2,
  Plus,
  Loader2,
  AlertCircle,
  ArrowRight,
  FileJson,
} from "lucide-react"
import { useRouter } from "next/navigation"
import { toast } from "sonner"
import useSWR from "swr"

export default function CompanyProfilesPage() {
  const { token } = useAuth()
  const router = useRouter()

  const [dialogOpen, setDialogOpen] = useState(false)
  const [companyName, setCompanyName] = useState("")
  const [creating, setCreating] = useState(false)

  const [kybDialogOpen, setKybDialogOpen] = useState(false)
  const [selectedKybData, setSelectedKybData] = useState<any>(null)

  const {
    data: companies,
    error: fetchError,
    isLoading,
    mutate,
  } = useSWR(
    token ? "companies" : null,
    () => getCompanies(token!),
    { revalidateOnFocus: false }
  )

  const handleCreateCompany = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!token || !companyName.trim()) return
    setCreating(true)

    try {
      const company = await createCompany(token, companyName.trim())
      toast.success(`Company "${company.name}" created successfully`)
      setDialogOpen(false)
      setCompanyName("")
      mutate()
      router.push(
        `/admin/company-profiles/${company.company_id}/upload-documents`
      )
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to create company"
      )
    } finally {
      setCreating(false)
    }
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-foreground">
            Company Profiles
          </h1>
          <p className="text-sm text-muted-foreground">
            Manage your company profiles and KYB verification
          </p>
        </div>

        {/* Create Company Dialog */}
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="size-4" />
              New Company
            </Button>
          </DialogTrigger>

          <DialogContent>
            <form onSubmit={handleCreateCompany}>
              <DialogHeader>
                <DialogTitle>Create Company Profile</DialogTitle>
                <DialogDescription>
                  Enter the company name to create a new KYB profile.
                </DialogDescription>
              </DialogHeader>

              <div className="flex flex-col gap-2 py-4">
                <Label htmlFor="company-name">Company Name</Label>
                <Input
                  id="company-name"
                  placeholder="e.g. Acme Corporation"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  required
                  autoFocus
                />
              </div>

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setDialogOpen(false)}
                >
                  Cancel
                </Button>

                <Button type="submit" disabled={creating || !companyName.trim()}>
                  {creating ? (
                    <>
                      <Loader2 className="size-4 animate-spin" />
                      Creating...
                    </>
                  ) : (
                    "Create Company"
                  )}
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Companies Table */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Building2 className="size-5" />
            All Companies
          </CardTitle>
          <CardDescription>
            A list of all company profiles in the system
          </CardDescription>
        </CardHeader>

        <CardContent>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="size-6 animate-spin text-muted-foreground" />
            </div>
          ) : fetchError ? (
            <div className="flex flex-col items-center justify-center gap-2 py-12 text-muted-foreground">
              <AlertCircle className="size-8" />
              <p className="text-sm">Failed to load companies</p>
              <Button variant="outline" size="sm" onClick={() => mutate()}>
                Retry
              </Button>
            </div>
          ) : !companies || companies.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 py-12 text-muted-foreground">
              <Building2 className="size-10 opacity-50" />
              <p className="text-sm">No companies found</p>
              <p className="text-xs">
                Create a new company to get started with KYB verification.
              </p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>ID</TableHead>
                  <TableHead>Name</TableHead>
                  <TableHead>Company ID</TableHead>
                      <TableHead>Exceptions</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>

 

              <TableBody>
                {companies.map((company: any) => (
                  <TableRow key={company.id}>
                    <TableCell className="font-mono text-xs">
                      {company.id}
                    </TableCell>

                    <TableCell className="font-medium">
                      {company.name}
                    </TableCell>

                    <TableCell className="font-mono text-xs text-muted-foreground">
                      {company.company_id}
                    </TableCell>

             <TableCell>
  <div className="flex flex-wrap gap-1">
    {company.kyb_data?.complianceIndicators?.exceptions?.length > 0 ? (
      company.kyb_data.complianceIndicators.exceptions.map(
        (exception: any, index: number) => (
          <Badge
            key={index}
            variant={
              exception.severity === "High"
                ? "destructive"
                : exception.severity === "Medium"
                ? "secondary"
                : "outline"
            }
            className="text-xs"
          >
            {exception.message}
          </Badge>
        )
      )
    ) : (
      <Badge variant="outline" className="text-xs">
        None
      </Badge>
    )}
  </div>
</TableCell>

                    <TableCell className="text-right flex justify-end gap-2">
                                            {/* Upload Docs */}
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          router.push(
                            `/admin/company-profiles/${company.company_id}/upload-documents`
                          )
                        }
                      >
                        Upload Docs
                        <ArrowRight className="size-3" />
                      </Button>

                                            {/* KYB Data */}
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setSelectedKybData(company.kyb_data || {})
                          setKybDialogOpen(true)
                        }}
                      >
                        <FileJson className="size-3 mr-1" />
                        Show Profile
                      </Button>



                      {/* Delete */}
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={async () => {
                          if (!token) return
                          const confirmDelete = confirm(
                            `Are you sure you want to delete "${company.name}"?`
                          )
                          if (!confirmDelete) return

                          try {
                            const result = await deleteCompany(
                              token,
                              company.company_id
                            )
                            toast.success(result.message)
                            mutate()
                          } catch (err) {
                            toast.error(
                              err instanceof Error
                                ? err.message
                                : "Failed to delete company"
                            )
                          }
                        }}
                      >
                        Delete
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* KYB Data Dialog */}
      <Dialog open={kybDialogOpen} onOpenChange={setKybDialogOpen}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>KYB Data</DialogTitle>
            <DialogDescription>
              Raw KYB verification data for this company.
            </DialogDescription>
          </DialogHeader>

          <div className="max-h-[500px] overflow-auto rounded-md bg-muted p-4">
            <pre className="text-xs whitespace-pre-wrap break-words">
              {selectedKybData && Object.keys(selectedKybData).length > 0
                ? JSON.stringify(selectedKybData, null, 2)
                : "No KYB data available"}
            </pre>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setKybDialogOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}