from .models import *

def can_users_communicate(sender, receiver):
    """an helper function that helps us to know who can send in messages to each other"""
    if sender.blocker_users.filter(id=receiver.id).exists():
        return False, "You have blocked this user"
    
    if receiver.blocker_users.filter(id=sender.id).exists():
        return False, "You have been blocked by this user"
    return "Communication Allowed"