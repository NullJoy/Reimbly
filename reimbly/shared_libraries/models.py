from typing import List, Optional, Dict, Any
from datetime import datetime
from dataclasses import dataclass, field
from google.cloud import firestore

@dataclass
class Attachment:
    type: str
    name: str
    url: str

@dataclass
class DecisionLog:
    actor_id: str
    action: str
    timestamp: datetime
    comments: str

@dataclass
class Case:
    case_id: str
    user_id: str
    submitted_at: datetime
    status: str
    amount: float
    currency: str
    category: str
    justification: str
    reimburse_card_number: str
    reviewer_route: List[str]
    decision_log: List[DecisionLog]
    attachments: List[Attachment]
    last_updated: datetime

@dataclass
class UserProfile:
    user_id: str
    name: str
    email: str
    direct_manager_id: str
    department: str
    location: str
    default_card_number: str
    cases: List[str] = field(default_factory=list)

@dataclass
class State:
    user_profile: UserProfile
    case: Optional[Case] = None

def case_to_dict(case: Case) -> Dict[str, Any]:
    """Convert Case object to Firestore-compatible dictionary"""
    return {
        'case_id': case.case_id,
        'user_id': case.user_id,
        'submitted_at': case.submitted_at,
        'status': case.status,
        'amount': case.amount,
        'currency': case.currency,
        'category': case.category,
        'justification': case.justification,
        'reimburse_card_number': case.reimburse_card_number,
        'reviewer_route': case.reviewer_route,
        'decision_log': [
            {
                'actor_id': log.actor_id,
                'action': log.action,
                'timestamp': log.timestamp,
                'comments': log.comments
            }
            for log in case.decision_log
        ],
        'attachments': [
            {
                'type': att.type,
                'name': att.name,
                'url': att.url
            }
            for att in case.attachments
        ],
        'last_updated': case.last_updated
    }

def user_profile_to_dict(profile: UserProfile) -> Dict[str, Any]:
    """Convert UserProfile object to Firestore-compatible dictionary"""
    return {
        'user_id': profile.user_id,
        'name': profile.name,
        'email': profile.email,
        'direct_manager_id': profile.direct_manager_id,
        'cases': profile.cases,
        'department': profile.department,
        'location': profile.location,
        'default_card_number': profile.default_card_number
    }

def dict_to_case(data: Dict[str, Any]) -> Case:
    """Convert Firestore dictionary to Case object"""
    return Case(
        case_id=data['case_id'],
        user_id=data['user_id'],
        submitted_at=data['submitted_at'],
        status=data['status'],
        amount=data['amount'],
        currency=data['currency'],
        category=data['category'],
        justification=data['justification'],
        reimburse_card_number=data['reimburse_card_number'],
        reviewer_route=data['reviewer_route'],
        decision_log=[
            DecisionLog(
                actor_id=log['actor_id'],
                action=log['action'],
                timestamp=log['timestamp'],
                comments=log['comments']
            )
            for log in data['decision_log']
        ],
        attachments=[
            Attachment(
                type=att['type'],
                name=att['name'],
                url=att['url']
            )
            for att in data['attachments']
        ],
        last_updated=data['last_updated']
    )

def dict_to_user_profile(data: Dict[str, Any]) -> UserProfile:
    """Convert Firestore dictionary to UserProfile object"""
    return UserProfile(
        user_id=data['user_id'],
        name=data['name'],
        email=data['email'],
        direct_manager_id=data['direct_manager_id'],
        cases=data.get('cases', []),
        department=data['department'],
        location=data['location'],
        default_card_number=data['default_card_number']
    ) 