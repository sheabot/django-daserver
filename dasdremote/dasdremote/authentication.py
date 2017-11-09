from rest_framework.authentication import TokenAuthentication


class DaSDRemoteTokenAuthentication(TokenAuthentication):

    def get_model(self):
        if self.model is not None:
            return self.model
        from .models import DaSDRemoteToken
        return DaSDRemoteToken
