from flask_login import UserMixin

class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Usuários fictícios para fins de exemplo
users = {'admin': {'password': 'adminpass'}}

def get_user(user_id):
    if user_id in users:
        return User(user_id)
    return None
