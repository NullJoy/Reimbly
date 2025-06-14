"""Common data schema and types for reimbursement agents."""

# Convenient declaration for controlled generation.
import types

from pydantic import BaseModel, Field


json_response_config = types.GenerateContentConfig(
    response_mime_type="application/json"
)

class UserProfile(BaseModel):
    """An example user profile."""
    allergies: list[str] = Field(
        default=[], description="A list of food allergies to avoid"
    )
    diet_preference: list[str] = Field(
        default=[], description="Vegetarian, Vegan... etc."
    )
    passport_nationality: str = Field(
        description="Nationality of traveler, e.g. US Citizen"
    )
    home_address: str = Field(description="Home address of traveler")
    home_transit_preference: str = Field(
        description="Preferred mode of transport around home, e.g. drive"
    )