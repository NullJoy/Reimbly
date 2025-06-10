import os
import pytest
from reimbly.tools.database import db
from pathlib import Path
from unittest.mock import Mock
from typing import Any, Optional
from reimbly.tools.cache import Cache
import sys

@pytest.fixture(autouse=True)
def setup_test_environment():
    """Set up test environment variables and directories for tests."""
    os.environ['TESTING'] = 'true'
    os.environ['REIMBLY_ENV'] = 'test'

    # Create necessary directories from tests/unit/conftest.py
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Add the project root directory to the Python path from tests/unit/conftest.py
    project_root = str(Path(__file__).parent)
    sys.path.insert(0, project_root)

    yield
    
    # Clean up environment variables
    os.environ.pop('TESTING', None)
    os.environ.pop('REIMBLY_ENV', None)

    # Clean up test files and directories from tests/unit/conftest.py
    if output_dir.exists():
        for file in output_dir.glob("*.html"):
            file.unlink()
        output_dir.rmdir()

@pytest.fixture(autouse=True)
def clear_database():
    """Clear the database before each test."""
    yield
    # Clear all collections after each test
    collections = ['reimbursement_requests', 'users']
    for collection in collections:
        docs = db.db.collection(collection).stream()
        for doc in docs:
            doc.reference.delete()

@pytest.fixture
def mock_template_env():
    """Create a mock template environment."""
    env = Mock()
    template = Mock()
    template.render.return_value = "<html><body>Test Dashboard</body></html>"
    env.get_template.return_value = template
    return env

@pytest.fixture
def cache():
    """Create a cache instance for testing."""
    # Use a test collection to avoid affecting production data
    os.environ['FIRESTORE_CACHE_COLLECTION'] = 'test_cache'
    cache = Cache()
    yield cache
    # Clean up after tests
    cache.clear() 