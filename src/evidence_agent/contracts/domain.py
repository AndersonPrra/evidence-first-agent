from datetime import date
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class OccurrenceStatus(str, Enum):
    PRESENT = "present"
    ABSENT = "absent"


class HumboldtInventorySchema(BaseModel):
    """
    Representação dos principais campos do Humboldt Ecological
    Inventory utilizados pelo sistema.
    """

    id: str = Field(..., description="Identificador do inventário ecológico.")
    targetTaxonomicScope: str = Field(..., description="Escopo taxonômico alvo.")
    isTaxonomicScopeFullyReported: Optional[bool] = Field(None, description="Indica se o escopo taxonômico foi completamente reportado.")
    isAbsenceReported: Optional[bool] = Field(None, description="Indica se não detecções foram registradas.")
    isAbundanceReported: Optional[bool] = Field(None, description="Indica se abundâncias foram reportadas.")
    taxonCompletenessReported: Optional[bool] = Field(None, description="Indica se a completude taxonômica foi reportada.")
    protocolNames: Optional[str] = Field(None, description="Nome original do protocolo de amostragem.")
    samplingEffortValue: Optional[float] = Field(None, ge=0, description="Valor do esforço de amostragem.")
    samplingEffortUnit: Optional[str] = Field(None, description="Unidade do esforço de amostragem.")


class EventSchema(BaseModel):
    """
    Evento de amostragem.

    O eventID deve ser validado quanto à unicidade,
    mas não é assumido como único sem teste nos dados.
    """

    eventID: str = Field(..., description="Identificador do evento.")
    parentEventID: Optional[str] = Field(None, description="Identificador do evento pai, quando existente.")

    eventDate: date = Field(..., description="Data da amostragem.")
    eventTime: Optional[str] = Field(None, description="Horário ou intervalo de horário.")

    samplingProtocol: Optional[str] = Field(None, description="Protocolo original informado na fonte.")
    sampleSizeValue: Optional[float] = Field(None, ge=0, description="Valor do tamanho/duração da amostragem.")
    sampleSizeUnit: Optional[str] = Field(None, description="Unidade de sampleSizeValue.")

    locationID: Optional[str] = Field(None, description="Identificador da localização.")
    decimalLatitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude WGS84.")
    decimalLongitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude WGS84.")

    @field_validator("samplingProtocol", mode="before")
    @classmethod
    def normalize_empty_protocol(cls, value):
        if value is None:
            return None

        if isinstance(value, str) and not value.strip():
            return None

        return value


class OccurrenceSchema(BaseModel):
    """
    Ocorrência taxonômica associada a um evento.
    """

    occurrenceID: str = Field(..., description="Identificador da ocorrência.")
    eventID: str = Field(..., description="Identificador do evento associado.")
    scientificName: str = Field(..., description="Nome científico.")
    occurrenceStatus: OccurrenceStatus = Field(...,description="Status original da ocorrência.")
    individualCount: Optional[int] = Field(None, ge=0, description="Número de indivíduos, quando quantitativo.")

    taxonRank: Optional[str] = Field(None, description="Nível taxonômico.")

    @field_validator("scientificName", mode="before")
    @classmethod
    def validate_scientific_name(cls, value):
        if value is None:
            raise ValueError("scientificName não pode ser nulo.")

        value = str(value).strip()

        if not value:
            raise ValueError("scientificName não pode ser vazio.")

        return value