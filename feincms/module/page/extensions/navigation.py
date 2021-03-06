"""
Proof-of-concept for extending the navigation with non-page-objects (f.e. if
you'd like to show all albums of a gallery in a submenu or something...)
"""

from django.db import models
from django.utils.translation import ugettext_lazy as _

from feincms.utils import get_object
from feincms._internal import monkeypatch_method


class TypeRegistryMetaClass(type):
    """
    You can access the list of subclasses as <BaseClass>.types
    """

    def __init__(cls, name, bases, attrs):
        if not hasattr(cls, 'types'):
            cls.types = []
        else:
            cls.types.append(cls)


class PagePretender(object):
    # emulate mptt properties to get the template tags working
    class _meta:
        level_attr = 'level'

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get_absolute_url(self):
        return self.url


class NavigationExtension(object):
    __metaclass__ = TypeRegistryMetaClass
    name = _('navigation extension')

    def children(self, page, **kwargs):
        raise NotImplementedError


def register(cls, admin_cls):
    cls.NE_CHOICES = [(
        '%s.%s' % (ext.__module__, ext.__name__), ext.name) for ext in NavigationExtension.types]

    cls.add_to_class('navigation_extension', models.CharField(_('navigation extension'),
        choices=cls.NE_CHOICES, blank=True, max_length=200,
        help_text=_('Select the module providing subpages for this page if you need to customize the navigation.')))

    @monkeypatch_method(cls)
    def extended_navigation(self, **kwargs):
        if not self.navigation_extension:
            return self.children.in_navigation()

        cls = get_object(self.navigation_extension, fail_silently=True)
        if not cls or not callable(cls):
            return self.children.in_navigation()

        return cls().children(self, **kwargs)



