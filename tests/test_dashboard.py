import pytest
from unittest.mock import Mock, patch
from reimbly.sub_agents.dashboard.agent import DashboardAgent
from pathlib import Path
import json

@pytest.fixture
def dashboard():
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

def test_theme_colors(dashboard):
    """Test theme color configurations."""
    # Test light theme
    light_colors = dashboard._get_theme_colors('light')
    assert light_colors['background'] == '#ffffff'
    assert light_colors['text'] == '#333333'
    
    # Test dark theme
    dark_colors = dashboard._get_theme_colors('dark')
    assert dark_colors['background'] == '#1a1a1a'
    assert dark_colors['text'] == '#ffffff'
    
    # Test invalid theme (should return light theme)
    default_colors = dashboard._get_theme_colors('invalid')
    assert default_colors == light_colors

def test_layout_configurations(dashboard):
    """Test layout configurations."""
    # Test grid layout
    assert dashboard._get_layout('grid') == 'repeat(2, 1fr)'
    
    # Test list layout
    assert dashboard._get_layout('list') == '1fr'
    
    # Test compact layout
    assert dashboard._get_layout('compact') == 'repeat(3, 1fr)'
    
    # Test invalid layout (should return grid layout)
    assert dashboard._get_layout('invalid') == 'repeat(2, 1fr)'

def test_filter_requests_by_date(dashboard, mock_requests):
    """Test request filtering by date range."""
    date_range = {
        'start': '2024-03-14',
        'end': '2024-03-15'
    }
    
    filtered_requests = dashboard._filter_requests_by_date(mock_requests, date_range)
    assert len(filtered_requests) == 2
    
    # Test with date range that excludes some requests
    date_range = {
        'start': '2024-03-15',
        'end': '2024-03-15'
    }
    filtered_requests = dashboard._filter_requests_by_date(mock_requests, date_range)
    assert len(filtered_requests) == 1
    assert filtered_requests[0]['request_id'] == 'REQ001'

def test_prepare_dashboard_data(dashboard, mock_requests):
    """Test dashboard data preparation."""
    with patch.object(dashboard, '_get_all_requests', return_value=mock_requests):
        data = dashboard._prepare_dashboard_data(
            show_pending=True,
            show_approved=True,
            show_rejected=False
        )
        
        assert data['summary_stats']['total_requests'] == 2
        assert data['summary_stats']['pending_count'] == 1
        assert data['summary_stats']['approved_count'] == 1
        assert 'rejected_requests' not in data
        
        # Test category distribution
        assert data['summary_stats']['category_distribution']['Travel'] == 1
        assert data['summary_stats']['category_distribution']['Meals'] == 1

def test_generate_dashboard_html(dashboard, mock_requests):
    """Test dashboard HTML generation."""
    with patch.object(dashboard, '_get_all_requests', return_value=mock_requests):
        html = dashboard.generate_dashboard_html(
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
        assert 'Recent Activity' in html

def test_save_dashboard(dashboard, mock_requests, tmp_path):
    """Test saving dashboard to file."""
    with patch.object(dashboard, '_get_all_requests', return_value=mock_requests):
        output_file = tmp_path / "dashboard.html"
        saved_path = dashboard.save_dashboard(
            output_path=str(output_file),
            theme='light',
            layout='grid'
        )
        
        assert Path(saved_path).exists()
        content = Path(saved_path).read_text()
        assert '<div class="dashboard-container">' in content

def test_calculate_category_distribution(dashboard, mock_requests):
    """Test category distribution calculation."""
    distribution = dashboard._calculate_category_distribution(mock_requests)
    assert distribution['Travel'] == 1
    assert distribution['Meals'] == 1

def test_dashboard_customization(dashboard, mock_requests):
    """Test dashboard customization options."""
    with patch.object(dashboard, '_get_all_requests', return_value=mock_requests):
        html = dashboard.generate_dashboard_html(
            theme='dark',
            layout='list',
            border_radius='12px',
            spacing='24px',
            font_family='Roboto, sans-serif',
            transition='0.4s ease',
            max_width='1200px'
        )
        
        # Verify customization options are applied
        assert '--background: #1a1a1a' in html
        assert '--border-radius: 12px' in html
        assert '--spacing: 24px' in html
        assert '--font-family: Roboto, sans-serif' in html
        assert '--transition: 0.4s ease' in html
        assert 'max-width: 1200px' in html

def test_dashboard_visibility_options(dashboard, mock_requests):
    """Test dashboard component visibility options."""
    with patch.object(dashboard, '_get_all_requests', return_value=mock_requests):
        # Test with all components hidden
        html = dashboard.generate_dashboard_html(
            show_pending=False,
            show_approved=False,
            show_rejected=False,
            show_charts=False,
            show_activity=False
        )
        
        assert 'Pending Requests' not in html
        assert 'Approved Requests' not in html
        assert 'Rejected Requests' not in html
        assert 'Request Analytics' not in html
        assert 'Recent Activity' not in html
        
        # Test with all components visible
        html = dashboard.generate_dashboard_html(
            show_pending=True,
            show_approved=True,
            show_rejected=True,
            show_charts=True,
            show_activity=True
        )
        
        assert 'Pending Requests' in html
        assert 'Approved Requests' in html
        assert 'Rejected Requests' in html
        assert 'Request Analytics' in html
        assert 'Recent Activity' in html 