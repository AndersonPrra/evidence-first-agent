from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class EvidenceState(str, Enum):
    """
    Estado da sustentação de uma afirmação.
    """

    VERIFIED = "VERIFIED"
    SUPPORTED = "SUPPORTED"
    UNCERTAIN = "UNCERTAIN"
    UNSUPPORTED = "UNSUPPORTED"


class EvidenceLevel(str, Enum):
    """
    Hierarquia epistemológica das afirmações.
    """

    OBSERVATION = "OBSERVATION"
    ASSOCIATION = "ASSOCIATION"
    INFERENCE = "INFERENCE"
    CAUSALITY = "CAUSALITY"


class EvidenceClaim(BaseModel):
    """
    Uma afirmação que poderá aparecer no relatório final.

    O agente não deve simplesmente produzir texto.
    Toda afirmação relevante deve possuir evidência rastreável.
    """

    claim_id: str = Field(..., description="Identificador único da afirmação.")
    statement: str = Field(..., description="Texto da afirmação.")
    level: EvidenceLevel = Field(..., description="Nível da afirmação.")
    state: EvidenceState = Field(..., description="Estado de sustentação da afirmação.")
    tool_used: str = Field(..., description="Ferramenta determinística responsável pelo resultado.")

    parameters_used: Dict[str, Any] = Field(default_factory=dict)
    result_summary: Dict[str, Any] = Field(default_factory=dict)

    validation_method: str | None = Field(None, description="Método utilizado para verificar o resultado.")
    source_tables: List[str] = Field(default_factory=list, description="Tabelas utilizadas para produzir a evidência.")
    limitations: List[str] = Field(default_factory=list, description="Ressalvas e limites de inferência.")


class AnalyticalRefusal(BaseModel):
    """
    Registra uma análise que o sistema decidiu não realizar
    ou não transformar em conclusão.
    """

    question: str
    reason: str
    affected_stage: str
    recommended_action: str | None = None


class ExecutionManifest(BaseModel):
    """
    Manifesto completo de uma execução do sistema.
    """

    execution_id: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    question: str
    input_files: List[str] = Field(default_factory=list)
    claims: List[EvidenceClaim] = Field(default_factory=list)
    analytical_refusals: List[AnalyticalRefusal] = Field(default_factory=list)
    decisions: List[Dict[str, Any]] = Field(default_factory=list)
    limitations: List[str] = Field(default_factory=list)