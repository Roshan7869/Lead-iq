"""
workers/mca21-actor/main.py — MCA21 Ministry of Corporate Affairs Collector

Official Indian corporate registry (Ministry of Corporate Affairs).
ALL registered companies must file here. GOLD STANDARD for company legitimacy.

Data: Company name, registered office, directors (DIN + names), incorporation date,
      authorized capital, paid-up capital, filing status

Confidence: 0.85 (official government registry)
Rate Limit: Limited (captcha-protected, use with care)

API: https://www.mca.gov.in/ (web scraping required)
"""
from __future__ import annotations

import asyncio
import re
import structlog
from datetime import datetime
from typing import Any

import httpx

from backend.llm.gemini_service import extract_lead
from backend.llm.cost_guard import check_budget
from backend.services.confidence import compute_confidence

logger = structlog.get_logger()

# MCA21 endpoints
MCA_SEARCH = "https://www.mca.gov.in/efs-ficore/ecorporate/companyMasterDataService"
MCA_COMPANY = "https://www.mca.gov.in/efs-ficore/ecorporate/companyDetailsService"


async def fetch_company_by_cin(cin: str) -> dict[str, Any] | None:
    """
    Fetch company details by CIN (Company Identification Number).

    CIN format: U74999MH2020PTC345678
    - First character: Company type (U=Public, L=Limited)
    - Next 5 digits: NIC code
    - Next 2 letters: State code
    - Next 4 digits: Year of incorporation
    - Next 3 letters: Company type (PTC=Private, PLC=Public)
    - Last 6 digits: Unique ID

    Args:
        cin: Company Identification Number

    Returns:
        Company details dictionary or None
    """
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Note: MCA21 requires captcha solving for web interface
            # For production, use official API or third-party service
            # This is a placeholder for the actual implementation

            payload = {
                "cin": cin,
                "service": "companyMasterDataService",
            }

            # Placeholder - actual implementation requires:
            # 1. Captcha solving service
            # 2. Session management
            # 3. Proper headers and cookies

            logger.info("mca21_fetch_attempt", cin=cin)
            return None  # Placeholder

        except Exception as exc:
            logger.error("mca21_fetch_error", cin=cin, error=str(exc))
            return None


async def search_companies(
    company_name: str,
    state: str | None = None,
) -> list[str]:
    """
    Search for companies by name, return CINs.

    Args:
        company_name: Company name to search
        state: Optional state filter

    Returns:
        List of matching CINs
    """
    # Placeholder - actual implementation requires MCA21 scraping
    logger.info("mca21_search_attempt", company=company_name)
    return []


def parse_cin(cin: str) -> dict[str, str]:
    """
    Parse CIN to extract company details.

    Args:
        cin: Company Identification Number

    Returns:
        Dict with parsed components
    """
    # CIN format: U74999MH2020PTC345678
    pattern = r"^([A-Z])(\d{5})([A-Z]{2})(\d{4})([A-Z]{3})(\d{6})$"
    match = re.match(pattern, cin)

    if not match:
        return {"error": "Invalid CIN format"}

    company_type_code, nic, state, year, entity_type, unique_id = match.groups()

    # Map codes to names
    company_types = {
        "U": "Public Limited",
        "L": "Limited",
        "F": "Foreign Company",
    }

    entity_types = {
        "PTC": "Private Limited Company",
        "PLC": "Public Limited Company",
        "LLP": "Limited Liability Partnership",
        "OPC": "One Person Company",
    }

    return {
        "cin": cin,
        "company_type": company_types.get(company_type_code, "Unknown"),
        "nic_code": nic,
        "state": state,
        "incorporation_year": int(year),
        "entity_type": entity_types.get(entity_type, "Unknown"),
        "unique_id": unique_id,
    }


def transform_mca_to_lead(
    company_data: dict[str, Any],
    directors: list[dict[str, str]],
) -> dict[str, Any]:
    """
    Transform MCA21 company data to lead format.

    Args:
        company_data: Company details from MCA21
        directors: List of directors with DIN and names

    Returns:
        Lead dictionary
    """
    cin = company_data.get("cin", "")

    return {
        "company_name": company_data.get("companyName"),
        "industry": None,  # Not directly available, would need NIC mapping
        "location": f"{company_data.get('registeredOfficeCity', '')}, {company_data.get('registeredOfficeState', 'India')}".strip(", "),
        "founded_year": parse_cin(cin).get("incorporation_year"),
        "website": None,  # Not in MCA21
        "source": "mca21",
        "source_url": f"https://www.mca.gov.in/mcafoportal/showCompanyMasterData.do?cin={cin}",
        "confidence": 0.85,  # Official government registry
        "intent_signals": ["government_registered"],
        "company_size": None,  # Would need authorized capital mapping
        "funding_stage": None,  # Not in MCA21
        "tech_stack": None,  # Not in MCA21
        "email": None,  # Not in MCA21
        "directors": directors,
        "authorized_capital": company_data.get("authorizedCapital"),
        "paid_up_capital": company_data.get("paidUpCapital"),
        "company_status": company_data.get("companyStatus"),  # Active/Dormant/Strike Off
    }


async def run_mca21_actor(
    cins: list[str] | None = None,
    company_names: list[str] | None = None,
) -> list[dict[str, Any]]:
    """
    Main MCA21 collection entry point.

    Args:
        cins: List of CINs to fetch
        company_names: List of company names to search

    Returns:
        List of extracted leads
    """
    all_leads = []

    # Fetch by CIN
    if cins:
        for cin in cins:
            company_data = await fetch_company_by_cin(cin)

            if company_data:
                lead = transform_mca_to_lead(company_data, [])
                all_leads.append(lead)

            await asyncio.sleep(1.0)  # Rate limiting

    # Search by company name
    if company_names:
        for name in company_names:
            cins_found = await search_companies(name)

            for cin in cins_found:
                company_data = await fetch_company_by_cin(cin)

                if company_data:
                    lead = transform_mca_to_lead(company_data, [])
                    all_leads.append(lead)

                await asyncio.sleep(1.0)

    logger.info(
        "mca21_actor_complete",
        leads_collected=len(all_leads),
    )

    return all_leads


if __name__ == "__main__":
    asyncio.run(run_mca21_actor())