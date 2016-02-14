import django
from django.conf.urls import patterns, url
from django.core.urlresolvers import reverse
from django.views.generic import ListView, CreateView , DetailView, UpdateView, DeleteView, TemplateView


class CrudTracker(type):
    def __init__(cls, name, bases, attrs):
        try:
            if CrudManager not in bases:
                return
        except NameError:
            return
        CrudManager._registry.append(cls)


def identity(f):
    return f


class FallbackTemplateMixin(object, ):
    def get_template_names(self):
        names = super(FallbackTemplateMixin, self).get_template_names()
        
        if not hasattr(self, 'template_name') and not self.template_name:
            names.append('generic_scaffold/list.html')
        
        return names
    

class CrudManager(object, ):
    _registry = []
    __metaclass__ = CrudTracker
    list_mixins = []
    delete_mixins = []
    detail_mixins = []
    create_mixins = []
    update_mixins = []

    def __new__(cls):
        cls.app_label = cls.model._meta.app_label
        try:
            cls.model_name = cls.model._meta.model_name
        except:
            cls.model_name = cls.model._meta.module_name
            
        cls.list_url_name = '{0}_{1}'.format(cls.get_name(), 'list')
        cls.create_url_name = '{0}_{1}'.format(cls.get_name(), 'create')
        cls.detail_url_name = '{0}_{1}'.format(cls.get_name(), 'detail')
        cls.update_url_name = '{0}_{1}'.format(cls.get_name(), 'update')
        cls.delete_url_name = '{0}_{1}'.format(cls.get_name(), 'delete')
        
        return super(CrudManager, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        self.perms = {
            'list': identity,
            'create': identity,
            'update': identity,
            'delete': identity,
            'detail': identity,
        }
        if hasattr(self, 'permissions') and self.permissions:
            self.perms.update(self.permissions)

    def get_get_context_data(self, klazz, **kwargs):
        def wrapped_get_context_data(inst, **kwargs):
            context = super(klazz, inst).get_context_data(**kwargs)
            context['crud'] = self
            #context.update(inst.get_context_data() )
            return context
        return wrapped_get_context_data

    @classmethod
    def get_name(cls):
        try:
            model_name = cls.model._meta.model_name
        except:
            model_name = cls.model._meta.module_name
        return '{0}_{1}'.format(cls.model._meta.app_label, model_name)

    def get_list_class_view(self):
        name = '{0}_{1}'.format(self.get_name(), 'ListView')
        options_dict = {
            'model': self.model,
        }
        
        if hasattr(self, 'list_template_name') and self.list_template_name:
            options_dict['template_name'] = self.list_template_name

        parent_classes_list = [FallbackTemplateMixin]
        parent_classes_list.extend(self.list_mixins)
        parent_classes_list.append(ListView)

        klazz = type(name, tuple(parent_classes_list), options_dict )
        klazz.get_context_data = self.get_get_context_data(klazz)

        return klazz

    def get_create_class_view(self):
        name = '{0}_{1}'.format(self.get_name(), 'CreateView')
        options_dict = {
            'model': self.model,
            'fields': '__all__',
        }
        if hasattr(self, 'form_template_name') and self.form_template_name:
            options_dict['template_name'] = self.form_template_name
        else:
            options_dict['template_name'] = 'generic_scaffold/form.html'
        if hasattr(self, 'form_class') and self.form_class:
            options_dict['form_class'] = self.form_class

        parent_classes_list = []
        parent_classes_list.extend(self.create_mixins)
        parent_classes_list.append(CreateView)
        
        klazz = type(name, tuple(parent_classes_list), options_dict )
        klazz.get_context_data = self.get_get_context_data(klazz)
        return klazz

    def get_detail_class_view(self):
        name = '{0}_{1}'.format(self.get_name(), 'DetailView')
        options_dict = {
            'model': self.model,
        }
        if hasattr(self, 'detail_template_name') and self.detail_template_name:
            options_dict['template_name'] = self.detail_template_name
        else:
            options_dict['template_name'] = 'generic_scaffold/detail.html'

        parent_classes_list = []
        parent_classes_list.extend(self.detail_mixins)
        parent_classes_list.append(DetailView)

        klazz = type(name, tuple(parent_classes_list), options_dict )
        klazz.get_context_data = self.get_get_context_data(klazz)
        return klazz

    def get_update_class_view(self):
        name = '{0}_{1}'.format(self.get_name(), 'UpdateView')
        options_dict = {
            'model': self.model,
            'fields': '__all__',
        }
        if hasattr(self, 'form_template_name') and self.form_template_name:
            options_dict['template_name'] = self.form_template_name
        else:
            options_dict['template_name'] = 'generic_scaffold/form.html'
        if hasattr(self, 'form_class') and self.form_class:
            options_dict['form_class'] = self.form_class

        parent_classes_list = []
        parent_classes_list.extend(self.update_mixins)
        parent_classes_list.append(UpdateView)

        klazz = type(name, tuple(parent_classes_list), options_dict )
        klazz.get_context_data = self.get_get_context_data(klazz)
        return klazz

    def get_delete_class_view(self):
        name = '{0}_{1}'.format(self.get_name(), 'DeleteView')
        options_dict = {
            'model': self.model,
            'fields': '__all__',
            'get_success_url': lambda x: reverse(self.list_url_name),
        }
        if hasattr(self, 'delete_template_name') and self.delete_template_name:
            options_dict['template_name'] = self.delete_template_name
        else:
            options_dict['template_name'] = 'generic_scaffold/confirm_delete.html'

        parent_classes_list = []
        parent_classes_list.extend(self.delete_mixins)
        parent_classes_list.append(DeleteView)

        klazz = type(name, tuple(parent_classes_list), options_dict )
        klazz.get_context_data = self.get_get_context_data(klazz)
        return klazz

    def get_url_patterns(self, prefix):
        url_patterns = [
            url(r'^'+prefix+'/$', self.perms['list'](self.get_list_class_view().as_view()), name=self.list_url_name ),
            url(r'^'+prefix+'create/$', self.perms['create'](self.get_create_class_view().as_view()), name=self.create_url_name ),
            url(r'^'+prefix+'detail/(?P<pk>\d+)$', self.perms['detail'](self.get_detail_class_view().as_view()), name=self.detail_url_name ),
            url(r'^'+prefix+'update/(?P<pk>\d+)$', self.perms['update'](self.get_update_class_view().as_view()), name=self.update_url_name ),
            url(r'^'+prefix+'delete/(?P<pk>\d+)$', self.perms['delete'](self.get_delete_class_view().as_view()), name=self.delete_url_name ),
        ]
        
        if django.VERSION >= (1, 8, 0):
            return url_patterns
        else:
            return patterns('', *url_patterns)

    @classmethod
    def get_url_names(cls, model):
        for r in cls._registry:
            if r.model == model:
                return {
                    'list': r.list_url_name,
                    'create': r.create_url_name,
                    'update': r.update_url_name,
                    'delete': r.delete_url_name,
                    'detal': r.detail_url_name,
                }
                
def get_url_names(model):
    return CrudManager.get_url_names(model)
