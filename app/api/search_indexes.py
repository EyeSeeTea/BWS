from haystack import indexes
from .models import PdbEntry

class PdbEntryIndex(indexes.SearchIndex, indexes.Indexable):
    text = indexes.CharField(document=True, use_template=True)
    title = indexes.CharField(model_attr='title', boost=2)
    text_auto = indexes.EdgeNgramField(use_template=True, template_name='search/indexes/api/pdbentry_text.txt')

    def get_model(self):
        return PdbEntry

    def index_queryset(self, using=None):
        return self.get_model().objects.all()