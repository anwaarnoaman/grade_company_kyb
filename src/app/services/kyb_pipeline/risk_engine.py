from datetime import datetime
from typing import Dict, List

class RiskEngine:

    def __init__(self):
        self.score = 0
        self.risk_drivers = []  # ← track all risk drivers
        self.exceptions = []

    # ------------------------------
    # HELPER METHODS
    # ------------------------------

    def add_risk(self, points: int, reason: str):
        self.score += points
        self.risk_drivers.append(reason)

    def add_exception(self, severity: str, fields: List[str], action: str):
        self.exceptions.append({
            "severity": severity,
            "impactedFields": fields,
            "requiredReviewerAction": action
        })

    # ------------------------------
    # FINANCIAL RISK EVALUATION
    # ------------------------------

    def evaluate_financial_risk(self, data: Dict):

        financials = data.get("financialIndicators", {})
        documents = data.get("documents", [])

        # 1️⃣ Conservative default for missing financials
        if not financials:
            self.add_risk(40, "Missing financial statements (conservative default)")
            self.add_exception(
                "High",
                ["financialIndicators"],
                "Obtain latest audited financial statements"
            )
            return

        assets = financials.get("totalAssets", {}).get("value")
        liabilities = financials.get("totalLiabilities", {}).get("value")
        net_profit = financials.get("netProfit", {}).get("value")
        audit_status = financials.get("auditStatus", {}).get("value")
        period = financials.get("financialPeriod", {}).get("value")

        # 2️⃣ Conservative default for missing numeric values
        if assets is None:
            self.add_risk(20, "Total assets missing (conservative default)")
            self.add_exception("High", ["totalAssets"], "Obtain total assets")
        if liabilities is None:
            self.add_risk(20, "Total liabilities missing (conservative default)")
            self.add_exception("High", ["totalLiabilities"], "Obtain total liabilities")
        if net_profit is None:
            self.add_risk(20, "Net profit missing (conservative default)")
            self.add_exception("High", ["netProfit"], "Obtain net profit/loss")

        # 3️⃣ Rule-based scoring
        if net_profit is not None and net_profit < 0:
            self.add_risk(30, "Net loss reported")
            self.add_exception(
                "High",
                ["netProfit"],
                "Assess sustainability of business model"
            )

        if assets is not None and liabilities is not None and liabilities > assets:
            self.add_risk(25, "Liabilities exceed assets")
            self.add_exception(
                "High",
                ["totalAssets", "totalLiabilities"],
                "Review solvency position"
            )

        if audit_status:
            if audit_status.upper() == "UNAUDITED":
                self.add_risk(15, "Financial statements unaudited")
                self.add_exception(
                    "Medium",
                    ["auditStatus"],
                    "Request audited statements"
                )
        else:
            self.add_risk(20, "Audit status unknown (conservative default)")
            self.add_exception(
                "Medium",
                ["auditStatus"],
                "Clarify audit status"
            )

        if period:
            try:
                year = int(period)
                if datetime.utcnow().year - year > 1:
                    self.add_risk(20, "Outdated financial statements")
                    self.add_exception(
                        "Medium",
                        ["financialPeriod"],
                        "Obtain latest financial period"
                    )
            except:
                self.add_risk(10, "Financial period parse failed (conservative default)")
                self.add_exception(
                    "Medium",
                    ["financialPeriod"],
                    "Verify financial period"
                )
        else:
            self.add_risk(15, "Financial period missing (conservative default)")
            self.add_exception(
                "Medium",
                ["financialPeriod"],
                "Obtain latest financial period"
            )

    # ------------------------------
    # DOCUMENT VALIDATION
    # ------------------------------

    def validate_documents(self, data: Dict):
        documents = data.get("documents", [])
        mandatory_types = ["Trade License", "Balance Sheet", "Profit & Loss"]
        present_types = [doc["classType"] for doc in documents]

        # Missing mandatory documents → conservative high risk
        for required in mandatory_types:
            if required not in present_types:
                self.add_risk(30, f"Missing mandatory document: {required}")
                self.add_exception(
                    "High",
                    [required],
                    f"Obtain {required}"
                )

        # Expired documents
        for doc in documents:
            expiry = doc.get("expiryDate")
            if expiry:
                expiry_date = datetime.fromisoformat(expiry)
                if expiry_date < datetime.utcnow():
                    self.add_risk(25, f"Expired document: {doc['classType']}")
                    self.add_exception(
                        "High",
                        [doc["classType"]],
                        "Obtain renewed document"
                    )

        # Low confidence → conservative addition
        for doc in documents:
            if doc.get("confidence", 1) < 0.6:
                self.add_risk(10, f"Low classification confidence: {doc['classType']}")
                self.add_exception(
                    "Low",
                    [doc["classType"]],
                    "Manual verification required"
                )

    # ------------------------------
    # FINALIZE RISK SCORE
    # ------------------------------

    def finalize(self):
        # Cap score to 100
        self.score = min(self.score, 100)

        # Risk band
        if self.score <= 30:
            band = "Low"
        elif self.score <= 60:
            band = "Medium"
        else:
            band = "High"

        return {
            "financialRiskScore": self.score,
            "riskBand": band,
            "riskDrivers": self.risk_drivers,  # ✅ fully explainable
            "confidenceLevel": "High" if self.score < 40 else "Medium"
        }, self.exceptions