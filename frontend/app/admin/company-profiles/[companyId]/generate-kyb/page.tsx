"use client"

import { useState, useCallback, useRef, use } from "react"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/auth-context"
import { generateKYB, saveProfile } from "@/lib/api"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Separator } from "@/components/ui/separator"
import { Input } from "@/components/ui/input"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Loader2,
  ShieldCheck,
  ArrowLeft,
  FileSearch,
  Building2,
  CreditCard,
  FileText,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ScrollText,
  TrendingUp,
  AlertCircle,
  CircleAlert,
  Info,
  Save,
  Pencil,
  Undo2,
} from "lucide-react"
import { toast } from "sonner"

// --- Types ---

interface ExtractedField {
  value: string | number | null
  sourceDocument: string
  confidence: number
  extractionMethod: string
}

interface DocumentInfo {
  fileName: string
  classType: string
  confidence: number
  issueDate: string | null
  expiryDate: string | null
  processedAt: string
}

interface RiskAssessment {
  financialRiskScore: number
  riskBand: string
  riskDrivers: string[]
  confidenceLevel: string
}

interface ComplianceException {
  type: string
  message: string
  severity: string
  impactedFields: string[]
  requiredAction: string
}

interface KYBResponse {
  status: string
  company_id: string
  kyb_result: {
    status: string
    company_id: string
    unified_company: {
      companyProfile: Record<string, ExtractedField>
      licenseDetails: Record<string, ExtractedField>
      addresses: Record<string, unknown>
      shareholders: unknown[]
      ubos: unknown[]
      documents: DocumentInfo[]
      signatories: unknown[]
      financialIndicators: Record<string, ExtractedField>
      riskAssessment: RiskAssessment
      complianceIndicators: {
        exceptions: ComplianceException[]
      }
      missingFields: string[]
    }
  }
}

interface ManualEdit {
  fieldName: string
  old_value: string | number | null
  new_value: string | number | null
}

// --- Helpers ---

function formatKey(key: string): string {
  return key
    .replace(/_/g, " ")
    .replace(/([A-Z])/g, " $1")
    .replace(/\b\w/g, (l) => l.toUpperCase())
    .trim()
}

function confidenceBadge(confidence: number) {
  const pct = Math.round(confidence * 100)
  if (pct >= 90)
    return (
      <Badge className="bg-emerald-100 text-emerald-800 text-[10px] px-1.5 py-0">
        {pct}%
      </Badge>
    )
  if (pct >= 70)
    return (
      <Badge className="bg-amber-100 text-amber-800 text-[10px] px-1.5 py-0">
        {pct}%
      </Badge>
    )
  return (
    <Badge className="bg-red-100 text-red-800 text-[10px] px-1.5 py-0">
      {pct}%
    </Badge>
  )
}

function riskBadge(band: string) {
  const lower = band.toLowerCase()
  if (lower === "low")
    return (
      <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">
        Low Risk
      </Badge>
    )
  if (lower === "medium")
    return (
      <Badge className="bg-amber-100 text-amber-800 border-amber-200">
        Medium Risk
      </Badge>
    )
  return (
    <Badge className="bg-red-100 text-red-800 border-red-200">
      High Risk
    </Badge>
  )
}

function severityBadge(severity: string) {
  const lower = severity.toLowerCase()
  if (lower === "high")
    return (
      <Badge variant="destructive" className="text-xs">
        High
      </Badge>
    )
  if (lower === "medium")
    return (
      <Badge className="bg-amber-100 text-amber-800 text-xs">Medium</Badge>
    )
  return (
    <Badge variant="secondary" className="text-xs">
      Low
    </Badge>
  )
}

function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value)
}

// --- Editable Field Row ---

function EditableFieldRow({
  label,
  field,
  fieldPath,
  editedValue,
  onEdit,
  onRevert,
}: {
  label: string
  field: ExtractedField
  fieldPath: string
  editedValue: string | number | null | undefined
  onEdit: (fieldPath: string, originalValue: string | number | null, newValue: string | number | null) => void
  onRevert: (fieldPath: string) => void
}) {
  const [isEditing, setIsEditing] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const isModified = editedValue !== undefined
  const displayValue = isModified ? editedValue : field.value

  const handleStartEdit = () => {
    setIsEditing(true)
    setTimeout(() => inputRef.current?.focus(), 0)
  }

  const handleBlur = () => {
    setIsEditing(false)
    if (inputRef.current) {
      const rawValue = inputRef.current.value
      const originalValue = field.value

      // Parse numeric values
      let newValue: string | number | null = rawValue
      if (typeof originalValue === "number") {
        const parsed = parseFloat(rawValue)
        newValue = isNaN(parsed) ? rawValue : parsed
      }

      if (newValue === originalValue || rawValue === String(originalValue)) {
        onRevert(fieldPath)
      } else {
        onEdit(fieldPath, originalValue, newValue)
      }
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      inputRef.current?.blur()
    }
    if (e.key === "Escape") {
      setIsEditing(false)
      onRevert(fieldPath)
    }
  }

  return (
    <div
      className={`flex items-start justify-between gap-4 py-2.5 border-b border-border/50 last:border-0 rounded-sm transition-colors ${
        isModified ? "bg-amber-50/60 -mx-2 px-2" : ""
      }`}
    >
      <div className="flex flex-col gap-0.5 min-w-0 shrink-0">
        <span className="text-sm text-muted-foreground">{label}</span>
        <span className="text-[11px] text-muted-foreground/60">
          Source: {field.sourceDocument}
        </span>
      </div>
      <div className="flex items-center gap-2 text-right min-w-0">
        {isEditing ? (
          <Input
            ref={inputRef}
            defaultValue={displayValue !== null ? String(displayValue) : ""}
            onBlur={handleBlur}
            onKeyDown={handleKeyDown}
            className="h-7 text-sm w-48 text-right"
          />
        ) : (
          <button
            type="button"
            onClick={handleStartEdit}
            className="group flex items-center gap-1.5 text-sm font-medium text-foreground hover:text-primary transition-colors cursor-text"
            title="Click to edit"
          >
            <span className="truncate max-w-[240px]">
              {displayValue !== null ? String(displayValue) : "N/A"}
            </span>
            <Pencil className="size-3 text-muted-foreground/40 group-hover:text-primary shrink-0 transition-colors" />
          </button>
        )}
        {isModified && !isEditing && (
          <button
            type="button"
            onClick={() => onRevert(fieldPath)}
            className="text-muted-foreground hover:text-destructive transition-colors"
            title="Revert to original"
          >
            <Undo2 className="size-3.5" />
          </button>
        )}
        {confidenceBadge(field.confidence)}
      </div>
    </div>
  )
}

// --- Sub-components ---

function CompanyProfileCard({
  profile,
  edits,
  onEdit,
  onRevert,
}: {
  profile: Record<string, ExtractedField>
  edits: Map<string, string | number | null>
  onEdit: (fieldPath: string, originalValue: string | number | null, newValue: string | number | null) => void
  onRevert: (fieldPath: string) => void
}) {
  const entries = Object.entries(profile)
  if (entries.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Building2 className="size-5 text-primary" />
          Company Profile
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        {entries.map(([key, field]) => {
          const fieldPath = `companyProfile.${key}.value`
          return (
            <EditableFieldRow
              key={key}
              label={formatKey(key)}
              field={field}
              fieldPath={fieldPath}
              editedValue={edits.get(fieldPath)}
              onEdit={onEdit}
              onRevert={onRevert}
            />
          )
        })}
      </CardContent>
    </Card>
  )
}

function LicenseDetailsCard({
  details,
  edits,
  onEdit,
  onRevert,
}: {
  details: Record<string, ExtractedField>
  edits: Map<string, string | number | null>
  onEdit: (fieldPath: string, originalValue: string | number | null, newValue: string | number | null) => void
  onRevert: (fieldPath: string) => void
}) {
  const entries = Object.entries(details)
  if (entries.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <ScrollText className="size-5 text-primary" />
          License Details
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        {entries.map(([key, field]) => {
          const fieldPath = `licenseDetails.${key}.value`
          return (
            <EditableFieldRow
              key={key}
              label={formatKey(key)}
              field={field}
              fieldPath={fieldPath}
              editedValue={edits.get(fieldPath)}
              onEdit={onEdit}
              onRevert={onRevert}
            />
          )
        })}
      </CardContent>
    </Card>
  )
}

function FinancialIndicatorsCard({
  indicators,
  edits,
  onEdit,
  onRevert,
}: {
  indicators: Record<string, ExtractedField>
  edits: Map<string, string | number | null>
  onEdit: (fieldPath: string, originalValue: string | number | null, newValue: string | number | null) => void
  onRevert: (fieldPath: string) => void
}) {
  const entries = Object.entries(indicators)
  if (entries.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <TrendingUp className="size-5 text-primary" />
          Financial Indicators
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        {entries.map(([key, field]) => {
          const fieldPath = `financialIndicators.${key}.value`
          return (
            <EditableFieldRow
              key={key}
              label={formatKey(key)}
              field={field}
              fieldPath={fieldPath}
              editedValue={edits.get(fieldPath)}
              onEdit={onEdit}
              onRevert={onRevert}
            />
          )
        })}
      </CardContent>
    </Card>
  )
}

function RiskAssessmentCard({
  assessment,
}: {
  assessment: RiskAssessment
}) {
  const scoreColor =
    assessment.financialRiskScore <= 40
      ? "text-emerald-600"
      : assessment.financialRiskScore <= 70
        ? "text-amber-600"
        : "text-red-600"

  const progressColor =
    assessment.financialRiskScore <= 40
      ? "bg-emerald-500"
      : assessment.financialRiskScore <= 70
        ? "bg-amber-500"
        : "bg-red-500"

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <AlertTriangle className="size-5 text-primary" />
          Risk Assessment
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4 flex flex-col gap-4">
        <div className="flex items-center justify-between">
          <div className="flex flex-col gap-1">
            <span className="text-sm text-muted-foreground">Risk Band</span>
            {riskBadge(assessment.riskBand)}
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className="text-sm text-muted-foreground">Confidence</span>
            <Badge variant="outline">{assessment.confidenceLevel}</Badge>
          </div>
        </div>

        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">
              Financial Risk Score
            </span>
            <span className={`text-2xl font-bold ${scoreColor}`}>
              {assessment.financialRiskScore}
              <span className="text-sm font-normal text-muted-foreground">
                /100
              </span>
            </span>
          </div>
          <div className="h-2 rounded-full bg-muted overflow-hidden">
            <div
              className={`h-full rounded-full transition-all ${progressColor}`}
              style={{ width: `${assessment.financialRiskScore}%` }}
            />
          </div>
        </div>

        {assessment.riskDrivers.length > 0 && (
          <div className="flex flex-col gap-2">
            <span className="text-sm font-medium text-foreground">
              Risk Drivers
            </span>
            <div className="flex flex-col gap-1.5">
              {assessment.riskDrivers.map((driver, i) => (
                <div
                  key={i}
                  className="flex items-start gap-2 rounded-md bg-muted/50 px-3 py-2"
                >
                  <CircleAlert className="size-4 text-amber-500 shrink-0 mt-0.5" />
                  <span className="text-sm text-muted-foreground">
                    {driver}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function DocumentsCard({ documents }: { documents: DocumentInfo[] }) {
  if (documents.length === 0) return null

  return (
    <Card className="md:col-span-2">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <FileText className="size-5 text-primary" />
          Processed Documents
          <Badge variant="secondary" className="ml-1 text-xs">
            {documents.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>File Name</TableHead>
              <TableHead>Classification</TableHead>
              <TableHead>Confidence</TableHead>
              <TableHead>Issue Date</TableHead>
              <TableHead>Expiry Date</TableHead>
              <TableHead>Processed At</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {documents.map((doc) => (
              <TableRow key={doc.fileName}>
                <TableCell className="font-medium">{doc.fileName}</TableCell>
                <TableCell>
                  <Badge variant="outline">{doc.classType}</Badge>
                </TableCell>
                <TableCell>{confidenceBadge(doc.confidence)}</TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.issueDate || "---"}
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {doc.expiryDate || "---"}
                </TableCell>
                <TableCell className="text-muted-foreground text-xs">
                  {new Date(doc.processedAt).toLocaleString()}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

function ComplianceCard({
  exceptions,
}: {
  exceptions: ComplianceException[]
}) {
  if (exceptions.length === 0) return null

  return (
    <Card className="md:col-span-2 border-destructive/30">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg text-destructive">
          <AlertCircle className="size-5" />
          Compliance Exceptions
          <Badge variant="destructive" className="ml-1 text-xs">
            {exceptions.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Type</TableHead>
              <TableHead>Message</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Impacted Fields</TableHead>
              <TableHead>Required Action</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {exceptions.map((exc, i) => (
              <TableRow key={i}>
                <TableCell className="font-medium">{exc.type}</TableCell>
                <TableCell>{exc.message}</TableCell>
                <TableCell>{severityBadge(exc.severity)}</TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {exc.impactedFields.map((f) => (
                      <Badge key={f} variant="secondary" className="text-xs">
                        {f}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-muted-foreground">
                  {exc.requiredAction}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

function MissingFieldsCard({ fields }: { fields: string[] }) {
  if (fields.length === 0) return null

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Info className="size-5 text-amber-500" />
          Missing Fields
          <Badge className="bg-amber-100 text-amber-800 ml-1 text-xs">
            {fields.length}
          </Badge>
        </CardTitle>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4 flex flex-col gap-2">
        {fields.map((field) => (
          <div
            key={field}
            className="flex items-center gap-2 rounded-md bg-amber-50 px-3 py-2"
          >
            <AlertCircle className="size-4 text-amber-500 shrink-0" />
            <span className="text-sm text-amber-800 font-mono">{field}</span>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}

// --- Edit Summary Panel ---

function EditSummaryPanel({ edits }: { edits: ManualEdit[] }) {
  if (edits.length === 0) return null

  return (
    <Card className="md:col-span-2 border-primary/30 bg-primary/[0.02]">
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Pencil className="size-5 text-primary" />
          Pending Changes
          <Badge className="bg-primary/10 text-primary ml-1 text-xs">
            {edits.length}
          </Badge>
        </CardTitle>
        <CardDescription>
          These fields have been manually edited and will be submitted with the review.
        </CardDescription>
      </CardHeader>
      <Separator />
      <CardContent className="pt-4">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Field</TableHead>
              <TableHead>Original Value</TableHead>
              <TableHead>New Value</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {edits.map((edit) => (
              <TableRow key={edit.fieldName}>
                <TableCell className="font-mono text-xs text-muted-foreground">
                  {edit.fieldName}
                </TableCell>
                <TableCell className="line-through text-muted-foreground">
                  {edit.old_value !== null ? String(edit.old_value) : "N/A"}
                </TableCell>
                <TableCell className="font-medium text-primary">
                  {edit.new_value !== null ? String(edit.new_value) : "N/A"}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}

// --- Confirmation Dialog ---

function SubmitConfirmationDialog({
  open,
  onOpenChange,
  onConfirm,
  submitting,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  onConfirm: () => void
  submitting: boolean
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <ShieldCheck className="size-5 text-primary" />
            Attestation Confirmation
          </DialogTitle>
          <DialogDescription className="pt-3 text-sm leading-relaxed text-foreground">
            I confirm that I have reviewed the extracted information, supporting
            documents, and risk indicators. I understand that submission
            constitutes an attestation for regulatory purposes.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={submitting}
          >
            Cancel
          </Button>
          <Button onClick={onConfirm} disabled={submitting}>
            {submitting ? (
              <>
                <Loader2 className="size-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <ShieldCheck className="size-4" />
                Submit
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

// --- Main Page ---

export default function GenerateKYBPage({
  params,
}: {
  params: Promise<{ companyId: string }>
}) {
  const { companyId } = use(params)
  const { token } = useAuth()
  const router = useRouter()
  const [generating, setGenerating] = useState(false)
  const [kybData, setKybData] = useState<KYBResponse | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const [confirmOpen, setConfirmOpen] = useState(false)

  // Track edits: fieldPath -> newValue
  const [editMap, setEditMap] = useState<Map<string, string | number | null>>(new Map())
  // Track original values: fieldPath -> originalValue
  const [originalMap, setOriginalMap] = useState<Map<string, string | number | null>>(new Map())

  const handleEdit = useCallback(
    (fieldPath: string, originalValue: string | number | null, newValue: string | number | null) => {
      setEditMap((prev) => {
        const next = new Map(prev)
        next.set(fieldPath, newValue)
        return next
      })
      setOriginalMap((prev) => {
        const next = new Map(prev)
        if (!next.has(fieldPath)) {
          next.set(fieldPath, originalValue)
        }
        return next
      })
    },
    []
  )

  const handleRevert = useCallback((fieldPath: string) => {
    setEditMap((prev) => {
      const next = new Map(prev)
      next.delete(fieldPath)
      return next
    })
    setOriginalMap((prev) => {
      const next = new Map(prev)
      next.delete(fieldPath)
      return next
    })
  }, [])

  const manualEdits: ManualEdit[] = Array.from(editMap.entries()).map(
    ([fieldName, new_value]) => ({
      fieldName,
      old_value: originalMap.get(fieldName) ?? null,
      new_value,
    })
  )

  const handleGenerate = async () => {
    if (!token) return
    setGenerating(true)

    try {
      const data = await generateKYB(token, companyId)
      setKybData(data as KYBResponse)
      toast.success("KYB report generated successfully")
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to generate KYB data"
      )
    } finally {
      setGenerating(false)
    }
  }

  const handleSaveClick = () => {
    setConfirmOpen(true)
  }

  const handleConfirmSubmit = async () => {
    if (!token || !kybData) return
    setSubmitting(true)

    try {
      const payload = {
        kyb_data: kybData,
        manual_edits: manualEdits,
      }
      await saveProfile(token, companyId, payload)
      toast.success("Profile saved and submitted successfully")
      setConfirmOpen(false)
      router.push("/admin/company-profiles")
    } catch (err) {
      toast.error(
        err instanceof Error ? err.message : "Failed to save profile"
      )
    } finally {
      setSubmitting(false)
    }
  }

  if (kybData) {
    const uc = kybData.kyb_result.unified_company
    const companyName =
      uc.companyProfile?.legalName?.value || "Unknown Company"

    return (
      <div className="flex flex-col gap-6">
        {/* Sticky Header Bar */}
        <div className="flex items-center justify-between sticky top-0 z-10 bg-background/95 backdrop-blur-sm -mx-1 px-1 py-3 border-b border-border/40">
          <div className="flex flex-col gap-1">
            <div className="flex items-center gap-3">
              <h1 className="text-2xl font-bold tracking-tight text-foreground text-balance">
                {companyName}
              </h1>
              <Badge className="bg-emerald-100 text-emerald-800 border-emerald-200">
                <CheckCircle2 className="size-3 mr-1" />
                {kybData.status}
              </Badge>
              {manualEdits.length > 0 && (
                <Badge className="bg-amber-100 text-amber-800 border-amber-200">
                  <Pencil className="size-3 mr-1" />
                  {manualEdits.length} edit{manualEdits.length !== 1 ? "s" : ""}
                </Badge>
              )}
            </div>
            <p className="text-sm text-muted-foreground">
              Company ID:{" "}
              <span className="font-mono text-xs">{kybData.company_id}</span>
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => router.push("/admin/company-profiles")}
            >
              <ArrowLeft className="size-4" />
              Back to Companies
            </Button>
            <Button onClick={handleSaveClick}>
              <Save className="size-4" />
              Save Data
            </Button>
          </div>
        </div>

        {/* Edit Summary at the top if edits exist */}
        {manualEdits.length > 0 && (
          <EditSummaryPanel edits={manualEdits} />
        )}

        {/* Cards Grid */}
        <div className="grid gap-4 md:grid-cols-2">
          <CompanyProfileCard
            profile={uc.companyProfile}
            edits={editMap}
            onEdit={handleEdit}
            onRevert={handleRevert}
          />
          <LicenseDetailsCard
            details={uc.licenseDetails}
            edits={editMap}
            onEdit={handleEdit}
            onRevert={handleRevert}
          />
          <FinancialIndicatorsCard
            indicators={uc.financialIndicators}
            edits={editMap}
            onEdit={handleEdit}
            onRevert={handleRevert}
          />
          <RiskAssessmentCard assessment={uc.riskAssessment} />
          <DocumentsCard documents={uc.documents} />
          <ComplianceCard
            exceptions={uc.complianceIndicators.exceptions}
          />
          <MissingFieldsCard fields={uc.missingFields} />
        </div>

        {/* Confirmation Dialog */}
        <SubmitConfirmationDialog
          open={confirmOpen}
          onOpenChange={setConfirmOpen}
          onConfirm={handleConfirmSubmit}
          submitting={submitting}
        />
      </div>
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Generate KYB Report
        </h1>
        <p className="text-sm text-muted-foreground">
          Company ID: <span className="font-mono">{companyId}</span>
        </p>
      </div>

      <Card className="max-w-lg">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShieldCheck className="size-5" />
            KYB Analysis
          </CardTitle>
          <CardDescription>
            Generate a comprehensive Know Your Business report by analyzing the
            uploaded documents. This process will extract and verify business
            information, ownership structure, financial data, and compliance
            details.
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div className="flex flex-col gap-2 rounded-lg border bg-muted/50 p-4">
            <div className="flex items-center gap-2 text-sm font-medium text-foreground">
              <Clock className="size-4 text-amber-500" />
              What will be analyzed:
            </div>
            <ul className="ml-6 flex flex-col gap-1 text-sm text-muted-foreground list-disc">
              <li>Company registration and legal documents</li>
              <li>Ownership and directorship information</li>
              <li>Financial statements and bank details</li>
              <li>Trade licenses and VAT certificates</li>
              <li>Identity verification of key persons</li>
            </ul>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => router.push("/admin/company-profiles")}
            >
              <ArrowLeft className="size-4" />
              Back
            </Button>
            <Button onClick={handleGenerate} disabled={generating}>
              {generating ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Generating KYB Report...
                </>
              ) : (
                <>
                  <FileSearch className="size-4" />
                  Generate KYB Data
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
