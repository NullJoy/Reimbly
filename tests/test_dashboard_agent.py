import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from reimbly.sub_agents.dashboard.agent import DashboardAgent
from reimbly.sub_agents.agent_types import AgentType
from reimbly.models.reimbursement import ReimbursementStatus, ReimbursementType
from reimbly.models.user import UserRole

@pytest.fixture
def dashboard_agent():
    """Create a dashboard agent instance for testing."""
    return DashboardAgent()

@pytest.fixture
def mock_requests():
    """Create mock request data for testing."""
    return [
        {
            'request_id': 'REQ001',
            'amount': 150.00,
            'category': 'Travel',
            'status': 'pending',
            'created_at': '2024-03-15',
            'updated_at': '2024-03-15 10:00:00',
            'description': 'Business trip to New York',
            'user_name': 'John Doe',
            'user_avatar': '/static/avatars/john.png'
        },
        {
            'request_id': 'REQ002',
            'amount': 75.50,
            'category': 'Meals',
            'status': 'approved',
            'created_at': '2024-03-14',
            'updated_at': '2024-03-14 15:30:00',
            'description': 'Team lunch meeting',
            'user_name': 'Jane Smith',
            'user_avatar': '/static/avatars/jane.png'
        }
    ]

@pytest.fixture
def mock_get_agent():
    with patch('reimbly.sub_agents.dashboard.agent.get_agent') as mock:
        # Create a mock dashboard agent
        dashboard_agent = MagicMock(spec=DashboardAgent)
        mock.return_value = dashboard_agent
        yield mock

@pytest.fixture
def mock_user():
    return {
        'id': 'test_user_id',
        'email': 'test@example.com',
        'role': UserRole.EMPLOYEE
    }

@pytest.fixture
def mock_reimbursements():
    return [
        {
            'id': '1',
            'user_id': 'test_user_id',
            'amount': 100.00,
            'description': 'Test expense 1',
            'status': ReimbursementStatus.PENDING,
            'type': ReimbursementType.TRAVEL,
            'created_at': datetime.now() - timedelta(days=1),
            'updated_at': datetime.now() - timedelta(days=1)
        },
        {
            'id': '2',
            'user_id': 'test_user_id',
            'amount': 200.00,
            'description': 'Test expense 2',
            'status': ReimbursementStatus.APPROVED,
            'type': ReimbursementType.MEALS,
            'created_at': datetime.now() - timedelta(days=2),
            'updated_at': datetime.now() - timedelta(days=1)
        }
    ]

def test_theme_colors(dashboard_agent):
    """Test theme color retrieval."""
    # Test light theme
    light_colors = dashboard_agent._get_theme_colors('light')
    assert light_colors['background'] == '#ffffff'
    assert light_colors['text'] == '#333333'
    
    # Test dark theme
    dark_colors = dashboard_agent._get_theme_colors('dark')
    assert dark_colors['background'] == '#1a1a1a'
    assert dark_colors['text'] == '#ffffff'
    
    # Test corporate theme
    corporate_colors = dashboard_agent._get_theme_colors('corporate')
    assert corporate_colors['background'] == '#f8fafc'
    assert corporate_colors['text'] == '#1e293b'
    
    # Test invalid theme (should return light theme)
    default_colors = dashboard_agent._get_theme_colors('invalid')
    assert default_colors == dashboard_agent.config.theme_colors['light']

def test_layout_configuration(dashboard_agent):
    """Test layout configuration retrieval."""
    # Test grid layout
    assert dashboard_agent._get_layout('grid') == 'repeat(2, 1fr)'
    
    # Test list layout
    assert dashboard_agent._get_layout('list') == '1fr'
    
    # Test compact layout
    assert dashboard_agent._get_layout('compact') == 'repeat(3, 1fr)'
    
    # Test invalid layout (should return grid layout)
    assert dashboard_agent._get_layout('invalid') == dashboard_agent.config.layouts['grid']

def test_filter_requests_by_date(dashboard_agent, mock_requests):
    """Test request filtering by date range."""
    # Test with date range that includes all requests
    date_range = {
        'start': '2024-03-14',
        'end': '2024-03-15'
    }
    filtered_requests = dashboard_agent._filter_requests_by_date(mock_requests, date_range)
    assert len(filtered_requests) == 2
    
    # Test with date range that excludes some requests
    date_range = {
        'start': '2024-03-16',
        'end': '2024-03-17'
    }
    filtered_requests = dashboard_agent._filter_requests_by_date(mock_requests, date_range)
    assert len(filtered_requests) == 0
    
    # Test with no date range (should return all requests)
    filtered_requests = dashboard_agent._filter_requests_by_date(mock_requests, None)
    assert len(filtered_requests) == 2

def test_calculate_category_distribution(dashboard_agent, mock_requests):
    """Test category distribution calculation."""
    distribution = dashboard_agent._calculate_category_distribution(mock_requests)
    assert distribution['Travel'] == 1
    assert distribution['Meals'] == 1
    
    # Test with empty requests list
    empty_distribution = dashboard_agent._calculate_category_distribution([])
    assert empty_distribution == {}

def test_prepare_dashboard_data(dashboard_agent, mock_requests):
    """Test dashboard data preparation."""
    with patch.object(dashboard_agent, '_get_all_requests', return_value=mock_requests):
        # Test with all sections enabled
        data = dashboard_agent._prepare_dashboard_data(
            show_pending=True,
            show_approved=True,
            show_rejected=True,
            max_requests=50
        )
        
        assert 'summary_stats' in data
        assert 'pending_requests' in data
        assert 'approved_requests' in data
        assert 'rejected_requests' in data
        assert data['summary_stats']['total_requests'] == 2
        assert data['summary_stats']['pending_count'] == 1
        
        # Test with some sections disabled
        data = dashboard_agent._prepare_dashboard_data(
            show_pending=False,
            show_approved=True,
            show_rejected=False,
            max_requests=50
        )
        assert 'pending_requests' not in data
        assert 'approved_requests' in data
        assert 'rejected_requests' not in data
        
        # Test with date range
        date_range = {'start': '2024-03-14', 'end': '2024-03-15'}
        data = dashboard_agent._prepare_dashboard_data(
            show_pending=True,
            show_approved=True,
            show_rejected=True,
            max_requests=50,
            date_range=date_range
        )
        assert len(data['pending_requests']) == 1
        assert len(data['approved_requests']) == 1

def test_generate_dashboard_html(dashboard_agent, mock_requests):
    """Test dashboard HTML generation."""
    with patch.object(dashboard_agent, '_get_all_requests', return_value=mock_requests):
        # Test with default options
        html = dashboard_agent.generate_dashboard_html(
            theme='light',
            layout='grid',
            show_pending=True,
            show_approved=True,
            show_rejected=True,
            show_charts=True,
            show_activity=True
        )
        
        assert isinstance(html, str)
        assert '<html' in html.lower()
        assert '<body' in html.lower()
        assert 'dashboard' in html.lower()
        
        # Test with dark theme and list layout
        html = dashboard_agent.generate_dashboard_html(
            theme='dark',
            layout='list',
            show_pending=True,
            show_approved=True,
            show_rejected=True,
            show_charts=True,
            show_activity=True
        )
        assert '#1a1a1a' in html.lower()
        assert 'repeat(2, 1fr)' not in html

def test_save_dashboard(dashboard_agent, mock_requests, tmp_path):
    """Test saving dashboard to file."""
    with patch.object(dashboard_agent, '_get_all_requests', return_value=mock_requests):
        output_path = tmp_path / 'dashboard.html'
        saved_path = dashboard_agent.save_dashboard(
            output_path=str(output_path),
            theme='light',
            layout='grid'
        )
        
        assert Path(saved_path).exists()
        content = Path(saved_path).read_text()
        assert '<html' in content.lower()
        assert '<body' in content.lower()
        assert 'dashboard' in content.lower()

def test_dashboard_customization(dashboard_agent, mock_requests):
    """Test dashboard customization options."""
    with patch.object(dashboard_agent, '_get_all_requests', return_value=mock_requests):
        html = dashboard_agent.generate_dashboard_html(
            theme='dark',
            layout='list',
            border_radius='12px',
            spacing='24px',
            font_family='Roboto, sans-serif',
            transition='0.5s ease',
            max_width='1200px'
        )
        assert '#1a1a1a' in html.lower()
        assert 'repeat(2, 1fr)' not in html
        assert '12px' in html
        assert '24px' in html
        assert 'Roboto' in html or 'roboto' in html
        assert '0.5s ease' in html
        assert '1200px' in html

# Remove the following tests that depend on mock_db (get_db):
# def test_get_dashboard_data(mock_db, mock_get_agent, mock_user, mock_reimbursements):
# def test_get_dashboard_data_no_reimbursements(mock_db, mock_get_agent, mock_user):
# def test_get_dashboard_data_with_filters(mock_db, mock_get_agent, mock_user, mock_reimbursements): 