"""
Django rest framework default pagination
"""
from rest_framework.pagination import PageNumberPagination


class StandardResultsSetPagination(PageNumberPagination):
    """
    Set pagination limit from query param
    """
    page_size_query_param = 'limit'
