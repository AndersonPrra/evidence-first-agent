from enum import Enum
from typing import Any, Dict, List

from pydantic import BaseModel, Field


class IssueSeverity(str, Enum):
    CRITICAL = "CRITICAL" #Impede ou compromete diretamente uma análise.
    WARNING = "WARNING" #Não impede necessariamente a análise, mas exige tratamento ou consideração explícita.
    INFO = "INFO" # Informação relevante para interpretação, sem indicar necessariamente um problema.


class QualityIssue(BaseModel):
    """
    Representa um problema identificado durante a avaliação
    determinística da qualidade dos dados.
    """

    code: str = Field(..., description="Código identificador do problema.")
    severity: IssueSeverity = Field(..., description="Gravidade do problema.")
    description: str = Field(..., description="Descrição legível do problema.")
    affected_records: int = Field(
        0,
        ge=0,
        description="Número de registros afetados.")

    details: Dict[str, Any] = Field(
        default_factory=dict,
        description="Detalhes adicionais, exemplos ou distribuição do problema.")


class SchemaValidationSummary(BaseModel):
    """
    Resumo dos erros estruturais encontrados durante a validação
    dos registros.
    """

    total_invalid_records: int = 0

    errors_by_field: Dict[str, int] = Field(default_factory=dict)
    errors_by_type: Dict[str, int] = Field(default_factory=dict)

    examples: List[Dict[str, Any]] = Field(default_factory=list)


class QualityReport(BaseModel):
    """
    Resultado completo da avaliação determinística do dataset.
    """

    total_events: int
    total_occurrences: int
    total_inventories: int

    # Integridade referencial
    unmatched_occurrence_references: int = 0
    unmatched_inventory_references: int = 0

    # Unicidade
    duplicate_events: int = 0
    duplicate_occurrences: int = 0

    # Schema
    schema_validation: SchemaValidationSummary = Field(default_factory=SchemaValidationSummary)

    # Problemas encontrados
    issues: List[QualityIssue] = Field(default_factory=list)

    # Resultado geral
    is_valid_for_analysis: bool = True

    analysis_limitations: List[str] = Field(default_factory=list)

    def add_issue(
        self,
        code: str,
        severity: IssueSeverity,
        description: str,
        affected_records: int = 0,
        details: Dict[str, Any] | None = None,
    ) -> None:
        """
        Adiciona um problema ao relatório.
        """

        self.issues.append(
            QualityIssue(
                code=code,
                severity=severity,
                description=description,
                affected_records=affected_records,
                details=details or {},
            )
        )

    def finalize(self) -> None:
        """
        Determina se os dados podem seguir para análise.

        Problemas CRITICAL impedem a consideração do dataset
        como estruturalmente válido.
        """

        self.is_valid_for_analysis = not any(
            issue.severity == IssueSeverity.CRITICAL
            for issue in self.issues
        )