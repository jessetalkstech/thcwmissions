import pytest
from unittest.mock import AsyncMock, MagicMock
from app.missions import validate_harvest
from app.models import Objective

@pytest.mark.asyncio
async def test_validate_harvest_success():
    # Setup objective with specific requirements
    obj = Objective(
        description="Harvest 5 Deer",
        order_index=1,
        requirements={"species": "deer", "count": 5}
    )
    
    # Valid harvest data
    harvest_data = {"species": "deer", "count": 10}
    
    assert await validate_harvest(harvest_data, obj) is True

@pytest.mark.asyncio
async def test_validate_harvest_wrong_species():
    obj = Objective(
        description="Harvest 5 Deer",
        order_index=1,
        requirements={"species": "deer", "count": 5}
    )
    
    # Wrong species
    harvest_data = {"species": "wolf", "count": 10}
    
    assert await validate_harvest(harvest_data, obj) is False

@pytest.mark.asyncio
async def test_validate_harvest_insufficient_count():
    obj = Objective(
        description="Harvest 5 Deer",
        order_index=1,
        requirements={"species": "deer", "count": 5}
    )
    
    # Correct species but not enough count
    harvest_data = {"species": "deer", "count": 3}
    
    assert await validate_harvest(harvest_data, obj) is False
