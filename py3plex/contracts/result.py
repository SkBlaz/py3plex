"""Result container for contract evaluation."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import pandas as pd
from .failure_modes import FailureMode


@dataclass
class RepairPayload:
    """Repair payload for different conclusion types.
    
    Contains the repaired output and metadata about what was kept/removed.
    
    Attributes:
        repaired_ok: Whether repair succeeded
        conclusion_type: Type of conclusion ("top_k", "ranking", "community")
        stable_core: For top-k: set of items with freq >= threshold
        tiers: For ranking: list of tiers with stable ordering
        stable_nodes: For communities: nodes with low flip probability
        metadata: Additional repair metadata
    """
    repaired_ok: bool = False
    conclusion_type: Optional[str] = None
    stable_core: Optional[List[Any]] = None
    tiers: Optional[List[List[Any]]] = None
    stable_nodes: Optional[List[Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "repaired_ok": self.repaired_ok,
            "conclusion_type": self.conclusion_type,
            "stable_core": self.stable_core,
            "tiers": self.tiers,
            "stable_nodes": self.stable_nodes,
            "metadata": self.metadata,
        }


@dataclass
class Evidence:
    """Evidence from contract evaluation.
    
    Contains per-p metric summaries and predicate evaluation results.
    
    Attributes:
        predicate_results: List of (predicate, passed, evidence_dict) tuples
        per_p_summaries: Dictionary mapping p -> summary statistics
        curves: Full perturbation curves (optional, for evidence_frame())
    """
    predicate_results: List[tuple] = field(default_factory=list)
    per_p_summaries: Dict[float, Dict[str, Any]] = field(default_factory=dict)
    curves: Optional[Dict[str, List]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary."""
        return {
            "predicate_results": [
                {
                    "predicate": pred.get_name() if hasattr(pred, "get_name") else str(pred),
                    "passed": passed,
                    "evidence": ev
                }
                for pred, passed, ev in self.predicate_results
            ],
            "per_p_summaries": self.per_p_summaries,
        }
    
    def to_pandas(self) -> pd.DataFrame:
        """Convert curves to DataFrame for detailed inspection.
        
        Returns:
            DataFrame with columns: p, metric, value, sample_id
        """
        if self.curves is None:
            return pd.DataFrame()
        
        rows = []
        for metric_name, curve_data in self.curves.items():
            for entry in curve_data:
                rows.append({
                    "p": entry.get("p"),
                    "metric": metric_name,
                    "value": entry.get("value"),
                    "sample_id": entry.get("sample_id"),
                })
        
        return pd.DataFrame(rows)


class ContractResult:
    """Result of contract evaluation.
    
    This class wraps a QueryResult and adds contract-specific information:
    - Whether the contract passed or failed
    - Failure mode (if failed)
    - Evidence (per-p summaries, predicate results)
    - Repair payload (if repair was attempted)
    - Provenance (full contract spec and execution details)
    
    Attributes:
        baseline_result: Original QueryResult (if contract passed) or None
        contract_ok: Whether contract passed
        failure_mode: FailureMode enum value (if failed)
        message: Human-readable message
        details: Typed details dict
        evidence: Evidence object with per-p summaries
        repair: RepairPayload object (if repair was attempted)
        provenance: Full provenance dict
    """
    
    def __init__(
        self,
        baseline_result: Any = None,
        contract_ok: bool = False,
        failure_mode: Optional[FailureMode] = None,
        message: str = "",
        details: Optional[Dict[str, Any]] = None,
        evidence: Optional[Evidence] = None,
        repair: Optional[RepairPayload] = None,
        provenance: Optional[Dict[str, Any]] = None,
    ):
        """Initialize ContractResult.
        
        Args:
            baseline_result: QueryResult from baseline (unperturbed) query
            contract_ok: Whether contract passed
            failure_mode: FailureMode if contract failed
            message: Human-readable message
            details: Typed details dict
            evidence: Evidence object
            repair: RepairPayload object
            provenance: Full provenance dict
        """
        self.baseline_result = baseline_result
        self.contract_ok = contract_ok
        self.failure_mode = failure_mode
        self.message = message
        self.details = details or {}
        self.evidence = evidence or Evidence()
        self.repair = repair or RepairPayload()
        self.provenance = provenance or {}
    
    def to_dict(self, include_evidence: bool = False) -> Dict[str, Any]:
        """Serialize to dictionary.
        
        Args:
            include_evidence: Include full evidence (can be large)
            
        Returns:
            Dictionary representation
        """
        result = {
            "contract_ok": self.contract_ok,
            "failure_mode": self.failure_mode.value if self.failure_mode else None,
            "message": self.message,
            "details": self.details,
            "repair": self.repair.to_dict(),
            "provenance": self.provenance,
        }
        
        if include_evidence:
            result["evidence"] = self.evidence.to_dict()
        else:
            # Include minimal evidence summary
            result["evidence_summary"] = {
                "n_predicates": len(self.evidence.predicate_results),
                "n_perturbation_points": len(self.evidence.per_p_summaries),
            }
        
        return result
    
    def to_pandas(self, expand_contract: bool = True) -> pd.DataFrame:
        """Convert baseline result to pandas with contract columns.
        
        Args:
            expand_contract: Add contract-specific columns
            
        Returns:
            DataFrame with baseline results + contract columns
        """
        # Get baseline DataFrame
        if self.baseline_result is None:
            df = pd.DataFrame()
        elif hasattr(self.baseline_result, "to_pandas"):
            df = self.baseline_result.to_pandas()
        else:
            df = pd.DataFrame()
        
        if not expand_contract or len(df) == 0:
            return df
        
        # Add contract columns
        df["contract_ok"] = self.contract_ok
        df["failure_mode"] = self.failure_mode.value if self.failure_mode else None
        
        # Add repair-specific columns
        if self.repair.conclusion_type == "top_k" and self.repair.stable_core:
            # Add is_in_stable_core column
            stable_set = set(self.repair.stable_core)
            if "node" in df.columns:
                df["is_in_stable_core"] = df["node"].isin(stable_set)
            elif len(df.columns) > 0:
                df["is_in_stable_core"] = df[df.columns[0]].isin(stable_set)
        
        elif self.repair.conclusion_type == "ranking" and self.repair.tiers:
            # Add tier_id column
            tier_map = {}
            for tier_id, tier in enumerate(self.repair.tiers):
                for item in tier:
                    tier_map[item] = tier_id
            
            if "node" in df.columns:
                df["tier_id"] = df["node"].map(tier_map)
            elif len(df.columns) > 0:
                df["tier_id"] = df[df.columns[0]].map(tier_map)
        
        elif self.repair.conclusion_type == "community" and self.repair.stable_nodes:
            # Add is_stable_node column
            stable_set = set(self.repair.stable_nodes)
            if "node" in df.columns:
                df["is_stable_node"] = df["node"].isin(stable_set)
            elif len(df.columns) > 0:
                df["is_stable_node"] = df[df.columns[0]].isin(stable_set)
        
        return df
    
    def evidence_frame(self) -> pd.DataFrame:
        """Get full evidence curves as DataFrame.
        
        Returns:
            DataFrame with columns: p, metric, value, sample_id
        """
        return self.evidence.to_pandas()
    
    def __repr__(self) -> str:
        """String representation."""
        if self.contract_ok:
            return f"<ContractResult: PASS>"
        else:
            mode = self.failure_mode.value if self.failure_mode else "unknown"
            return f"<ContractResult: FAIL ({mode})>"
