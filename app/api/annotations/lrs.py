#! /usr/bin/env python3

from . import serializers
from . import models

from django.core.exceptions import ValidationError
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import get_object_or_404
from rest_framework import generics, mixins, permissions, status, viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.views import APIView

from django_filters import FilterSet, ModelChoiceFilter
from django_filters import rest_framework as filters

class FeatureTrackDetailView(generics.ListAPIView):
    """
    Detail View for a given FeatureTrack
    """
    serializer_class = serializers.TrackDetailSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    lookup_url_kwarg = 'acc'

    def get_queryset(self):
        """
        This view should return a FeatureTrack by UniProt and name
         Example:
            /featureTracks/<ACC>/<name>/
            /featureTracks/P0DTC4/Genomic_Variants_CNCB/
        """
        uniprot_acc = self.kwargs['acc']
        name = self.kwargs['name']
        return models.FeatureTrack.objects.filter(
            uniprot_entry__accession=uniprot_acc,
            name=name)

class TrackDetailView(generics.RetrieveAPIView):
    """
    Detail View for a given FeatureTrack
    """
    queryset = models.FeatureTrack.objects.all()
    serializer_class = serializers.TrackDetailSerializer
    #permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = (filters.DjangoFilterBackend,
                       SearchFilter, OrderingFilter)
    filterset_fields = ['mutationType', 'sourceType', 'mutationEffect']
    search_fields = ['mutationType']
    ordering_fields = ['mutationType', 'mutationEffect', 'sourceType']
    ordering = ['mutationType']
    lookup_url_kwarg = 'name'
    multiple_lookup_fields = ['uniprot_entry', 'name']

    def get_object(self):
        queryset = self.get_queryset()
        filter = {}
        for field in self.multiple_lookup_fields:
            pass #filter[field] = self.kwargs[field]

        obj = get_object_or_404(queryset, **filter)
        self.check_object_permissions(self.request, obj)
        return obj
