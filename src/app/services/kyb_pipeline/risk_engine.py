from datetime import datetime
from typing import Dict, List
from app.core.logging import get_logger

logger = get_logger(__name__)

def mask_content(value: str) -> str:
    """Simple mask for sensitive info (like company or doc names)."""
    if not value:
        return value
    return value[:2] + "*" * (len(value) - 4) + value[-2:]

class RiskEngine:

    def __init__(self):
        self.score = 0
        self.risk_drivers = []  
        self.exceptions = []
        
    def reset(self):
        """Reset all internal risk state for a new evaluation run."""
        self.score = 0
        self.risk_drivers = []
        self.exceptions = []
    # ------------------------------
    # HELPER METHODS
    # ------------------------------
    def add_risk(self, points: int, reason: str):
        self.score += points
        self.risk_drivers.append(reason)
        # Audit log for risk addition
        logger.info(
            "RISK_ADDED",
            extra={
                "audit": True,
                "event_type": "RISK_ADDED",
                "reason": reason,
                "points": points,
                "currentScore": self.score
            }
        )

    def add_exception(self, severity: str, fields: List[str], action: str):
        self.exceptions.append({
            "severity": severity,
            "impactedFields": fields,
            "requiredReviewerAction": action
        })
        # Audit log for exception
        logger.info(
            "EXCEPTION_ADDED",
            extra={
                "audit": True,
                "event_type": "EXCEPTION_ADDED",
                "severity": severity,
                "impactedFields": fields,
                "action": action
            }
        )

    # ------------------------------
    # FINANCIAL RISK EVALUATION
    # ------------------------------
    def evaluate_financial_risk(self, data: Dict):
        financials = data.get("financialIndicators", {})
        documents = data.get("documents", [])

        logger.info(
            "FINANCIAL_RISK_EVALUATION_STARTED",
            extra={
                "audit": True,
                "event_type": "FINANCIAL_RISK_EVALUATION_STARTED",
                "documents_count": len(documents),
                "financialFields_present": list(financials.keys())
            }
        )

        # Original evaluation logic
        if not financials:
            self.add_risk(40, "Missing financial statements (conservative default)")
            self.add_exception("High", ["financialIndicators"], "Obtain latest audited financial statements")
            return

        assets = financials.get("totalAssets", {}).get("value")
        liabilities = financials.get("totalLiabilities", {}).get("value")
        net_profit = financials.get("netProfit", {}).get("value")
        audit_status = financials.get("auditStatus", {}).get("value")
        period = financials.get("financialPeriod", {}).get("value")

        # Remaining evaluation logic as is
        if assets is None:
            self.add_risk(20, "Total assets missing (conservative default)")
            self.add_exception("High", ["totalAssets"], "Obtain total assets")
        if liabilities is None:
            self.add_risk(20, "Total liabilities missing (conservative default)")
            self.add_exception("High", ["totalLiabilities"], "Obtain total liabilities")
        if net_profit is None:
            self.add_risk(20, "Net profit missing (conservative default)")
            self.add_exception("High", ["netProfit"], "Obtain net profit/loss")
        if net_profit is not None and net_profit < 0:
            self.add_risk(30, "Net loss reported")
            self.add_exception("High", ["netProfit"], "Assess sustainability of business model")
        if assets is not None and liabilities is not None and liabilities > assets:
            self.add_risk(25, "Liabilities exceed assets")
            self.add_exception("High", ["totalAssets", "totalLiabilities"], "Review solvency position")
        if audit_status:
            if audit_status.upper() == "UNAUDITED":
                self.add_risk(15, "Financial statements unaudited")
                self.add_exception("Medium", ["auditStatus"], "Request audited statements")
        else:
            self.add_risk(20, "Audit status unknown (conservative default)")
            self.add_exception("Medium", ["auditStatus"], "Clarify audit status")
        if period:
            try:
                year = int(period)
                if datetime.utcnow().year - year > 1:
                    self.add_risk(20, "Outdated financial statements")
                    self.add_exception("Medium", ["financialPeriod"], "Obtain latest financial period")
            except:
                self.add_risk(10, "Financial period parse failed (conservative default)")
                self.add_exception("Medium", ["financialPeriod"], "Verify financial period")
        else:
            self.add_risk(15, "Financial period missing (conservative default)")
            self.add_exception("Medium", ["financialPeriod"], "Obtain latest financial period")

        logger.info(
            "FINANCIAL_RISK_EVALUATION_COMPLETED",
            extra={
                "audit": True,
                "event_type": "FINANCIAL_RISK_EVALUATION_COMPLETED",
                "currentScore": self.score
            }
        )

    # ------------------------------
    # DOCUMENT VALIDATION
    # ------------------------------
    def validate_documents(self, data: Dict):
        documents = data.get("documents", [])
        mandatory_types = ["Trade License", "Balance Sheet", "Profit & Loss"]
        present_types = [doc["classType"] for doc in documents]

        logger.info(
            "DOCUMENT_VALIDATION_STARTED",
            extra={
                "audit": True,
                "event_type": "DOCUMENT_VALIDATION_STARTED",
                "documents_count": len(documents),
                "present_types": present_types
            }
        )

        for required in mandatory_types:
            if required not in present_types:
                self.add_risk(30, f"Missing mandatory document: {mask_content(required)}")
                self.add_exception("High", [mask_content(required)], f"Obtain {mask_content(required)}")

        for doc in documents:
            expiry = doc.get("expiryDate")
            if expiry:
                expiry_date = datetime.fromisoformat(expiry)
                if expiry_date < datetime.utcnow():
                    self.add_risk(25, f"Expired document: {mask_content(doc['classType'])}")
                    self.add_exception("High", [mask_content(doc["classType"])], "Obtain renewed document")
            if doc.get("confidence", 1) < 0.6:
                self.add_risk(10, f"Low classification confidence: {mask_content(doc['classType'])}")
                self.add_exception("Low", [mask_content(doc["classType"])], "Manual verification required")

        logger.info(
            "DOCUMENT_VALIDATION_COMPLETED",
            extra={
                "audit": True,
                "event_type": "DOCUMENT_VALIDATION_COMPLETED",
                "currentScore": self.score
            }
        )

    # ------------------------------
    # FINALIZE RISK SCORE
    # ------------------------------
    def finalize(self):
        self.score = min(self.score, 100)
        if self.score <= 30:
            band = "Low"
        elif self.score <= 60:
            band = "Medium"
        else:
            band = "High"

        logger.info(
            "RISK_SCORE_FINALIZED",
            extra={
                "audit": True,
                "event_type": "RISK_SCORE_FINALIZED",
                "finalScore": self.score,
                "riskBand": band,
                "riskDrivers_count": len(self.risk_drivers),
                "exceptions_count": len(self.exceptions)
            }
        )

        return {
            "financialRiskScore": self.score,
            "riskBand": band,
            "riskDrivers": self.risk_drivers,
            "confidenceLevel": "High" if self.score < 40 else "Medium"
        }, self.exceptions