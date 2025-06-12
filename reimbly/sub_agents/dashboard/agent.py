"""
Dashboard Generation Agent
Generates HTML dashboard for admin view
"""

from typing import Dict, List, Any, Optional
import json
from datetime import datetime
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from pydantic import BaseModel, Field
from google.adk.agents import Agent
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

class DashboardConfig(BaseModel):
    """Configuration for the dashboard agent."""
    template_dir: Path = Field(default_factory=lambda: Path(__file__).parent / "templates")
    theme_colors: Dict[str, Dict[str, str]] = Field(default_factory=lambda: {
        "light": {
            "background": "#ffffff",
            "text": "#333333",
            "primary": "#2563eb",
            "secondary": "#64748b",
            "success": "#22c55e",
            "warning": "#f59e0b",
            "danger": "#ef4444"
        },
        "dark": {
            "background": "#1a1a1a",
            "text": "#ffffff",
            "primary": "#3b82f6",
            "secondary": "#94a3b8",
            "success": "#4ade80",
            "warning": "#fbbf24",
            "danger": "#f87171"
        },
        "corporate": {
            "background": "#f8fafc",
            "text": "#1e293b",
            "primary": "#0f172a",
            "secondary": "#475569",
            "success": "#059669",
            "warning": "#d97706",
            "danger": "#dc2626"
        }
    })
    layouts: Dict[str, str] = Field(default_factory=lambda: {
        "grid": "repeat(2, 1fr)",
        "list": "1fr",
        "compact": "repeat(3, 1fr)"
    })

class DashboardAgent(Agent):
    """Agent for generating admin dashboards and analytics."""
    
    config: DashboardConfig = Field(default_factory=DashboardConfig)
    env: Any = Field(default=None, exclude=True)
    
    def __init__(self, **data):
        super().__init__(
            name="dashboard_generator",
            description="Agent for generating admin dashboards and analytics",
            model="gemini-2.0-flash",
            instruction=(
                "You are a dashboard agent. Your responsibilities include:\n"
                "1. Generating HTML dashboards for admins\n"
                "2. Providing summary statistics and analytics\n"
                "3. Supporting real-time updates and customization options\n"
                "4. Rendering charts and activity feeds\n"
                "You do not process approvals or notifications.\n"
            ),
            **data
        )
        self.env = Environment(loader=FileSystemLoader(str(self.config.template_dir)))
        self.env.filters['currency'] = lambda v: f"${float(v):,.2f}"

    def _get_theme_colors(self, theme: str) -> Dict[str, str]:
        """Get color scheme for the specified theme."""
        return self.config.theme_colors.get(theme, self.config.theme_colors["light"])

    def _get_layout(self, layout: str) -> str:
        """Get CSS grid layout configuration."""
        return self.config.layouts.get(layout, self.config.layouts["grid"])

    def _filter_requests_by_date(
        self,
        requests: List[Dict[str, Any]],
        date_range: Optional[Dict[str, str]]
    ) -> List[Dict[str, Any]]:
        """Filter requests by date range if specified."""
        if not date_range:
            return requests
            
        start_date = datetime.strptime(date_range['start'], '%Y-%m-%d')
        end_date = datetime.strptime(date_range['end'], '%Y-%m-%d')
        
        return [
            req for req in requests
            if start_date <= datetime.strptime(req['created_at'], '%Y-%m-%d') <= end_date
        ]

    def _prepare_dashboard_data(
        self,
        show_pending: bool = True,
        show_approved: bool = True,
        show_rejected: bool = True,
        max_requests: int = 50,
        date_range: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Prepare dashboard data with optional filtering."""
        # Get all requests
        all_requests = self._get_all_requests()
        
        # Filter by date if specified
        if date_range:
            all_requests = self._filter_requests_by_date(all_requests, date_range)
        
        # Filter by status
        pending_requests = [r for r in all_requests if r['status'] == 'pending'][:max_requests] if show_pending else []
        approved_requests = [r for r in all_requests if r['status'] == 'approved'][:max_requests] if show_approved else []
        rejected_requests = [r for r in all_requests if r['status'] == 'rejected'][:max_requests] if show_rejected else []
        
        # Calculate summary statistics
        total_amount = sum(r.get('amount', 0) for r in all_requests)
        summary_stats = {
            'total_requests': len(all_requests),
            'pending_count': len(pending_requests),
            'approved_count': len(approved_requests),
            'category_distribution': self._calculate_category_distribution(all_requests),
            'trends': {
                'total': 5,  # Example trend values
                'pending': -2,
                'approved': 8
            },
            'total_amount': total_amount
        }
        
        return {
            'summary_stats': summary_stats,
            'pending_requests': pending_requests,
            'approved_requests': approved_requests,
            'rejected_requests': rejected_requests
        }

    def _get_all_requests(self) -> List[Dict[str, Any]]:
        """Get all reimbursement requests."""
        # This would typically come from a database
        # For now, return mock data
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

    def _calculate_category_distribution(self, requests: List[Dict[str, Any]]) -> Dict[str, int]:
        """Calculate distribution of requests by category."""
        distribution = {}
        for request in requests:
            category = request['category']
            distribution[category] = distribution.get(category, 0) + 1
        return distribution

    def generate_dashboard_html(
        self,
        theme: str = "light",
        layout: str = "grid",
        show_pending: bool = True,
        show_approved: bool = True,
        show_rejected: bool = True,
        show_charts: bool = True,
        show_activity: bool = True,
        max_requests: int = 50,
        date_range: Optional[Dict[str, str]] = None,
        border_radius: str = "8px",
        spacing: str = "20px",
        font_family: str = "Arial, sans-serif",
        transition: str = "0.3s ease",
        max_width: str = "1400px",
        data: Optional[Dict[str, Any]] = None
    ) -> dict:
        """Generate dashboard HTML with specified options. Returns dict with status and html."""
        logging.info("generate_dashboard_html called")
        try:
            logging.info("Generating dashboard HTML...")
            template = self.env.get_template('dashboard.html')
            # Prepare data
            if data is None:
                data = self._prepare_dashboard_data(
                    show_pending=show_pending,
                    show_approved=show_approved,
                    show_rejected=show_rejected,
                    max_requests=max_requests,
                    date_range=date_range
                )
            # Get recent activity
            recent_activity = self._get_all_requests()[:10] if show_activity else []
            # Render template
            html = template.render(
                data=data,
                recent_activity=recent_activity,
                colors=self._get_theme_colors(theme),
                layout=self._get_layout(layout),
                show_pending=show_pending,
                show_approved=show_approved,
                show_rejected=show_rejected,
                show_charts=show_charts,
                show_activity=show_activity,
                border_radius=border_radius,
                spacing=spacing,
                font_family=font_family,
                transition=transition,
                max_width=max_width
            )
            logging.info("Dashboard HTML generated successfully.")
            return {"status": "success", "html": html}
        except Exception as e:
            logging.error(f"Error generating dashboard HTML: {str(e)}")
            return {"status": "error", "message": str(e)}

    def save_dashboard(
        self,
        output_path: Optional[str] = None,
        theme: str = "light",
        layout: str = "grid",
        show_pending: bool = True,
        show_approved: bool = True,
        show_rejected: bool = True,
        show_charts: bool = True,
        show_activity: bool = True,
        max_requests: int = 50,
        date_range: Optional[Dict[str, str]] = None,
        border_radius: str = "8px",
        spacing: str = "20px",
        font_family: str = "Arial, sans-serif",
        transition: str = "0.3s ease",
        max_width: str = "1400px"
    ) -> str:
        """Save dashboard HTML to file."""
        if output_path:
            output_file = Path(output_path)
        else:
            output_file = Path("output/dashboard.html")
            
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        html_content = self.generate_dashboard_html(
            theme=theme,
            layout=layout,
            show_pending=show_pending,
            show_approved=show_approved,
            show_rejected=show_rejected,
            show_charts=show_charts,
            show_activity=show_activity,
            max_requests=max_requests,
            date_range=date_range,
            border_radius=border_radius,
            spacing=spacing,
            font_family=font_family,
            transition=transition,
            max_width=max_width
        )
        
        output_file.write_text(html_content)
        return str(output_file)

    def trigger_html_generation(self, command: str) -> dict:
        """Trigger HTML generation based on a command or keyword."""
        logging.info("trigger_html_generation called with command: %s", command)
        if command.lower() == 'generate dashboard':
            return self.generate_dashboard_html()
        else:
            return {"status": "error", "message": "Invalid command. Use 'generate dashboard' to create the dashboard."}

# Create a singleton instance
dashboard_agent = DashboardAgent() 