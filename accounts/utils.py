from accounts.models import Account

def get_primary_account(user):
    return Account.objects.get(user=user, account_type="PRIMARY")
