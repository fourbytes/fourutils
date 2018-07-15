import marshmallow as ma
from icecream import ic
from marshmallow.compat import iteritems, with_metaclass
from marshmallow.decorators import pre_dump, pre_load
from marshmallow.schema import SchemaMeta
from marshmallow_sqlalchemy.convert import ModelConverter
from marshmallow_sqlalchemy.fields import (Related, get_primary_keys,
                                           get_schema_for_field)
from marshmallow_sqlalchemy.schema import (ModelSchema, ModelSchemaMeta,
                                           ModelSchemaOpts)
from sqlalchemy import inspect
from sqlalchemy.orm import with_polymorphic


class PolyRelated(Related):
    def __init__(self, column=None, **kwargs):
        super().__init__(**kwargs)

    @property
    def model(self):
        schema = get_schema_for_field(self)
        return schema.poly_model or schema.opts.model


class PolyModelConverter(ModelConverter):
    def _get_field_class_for_property(self, prop):
        if hasattr(prop, 'direction'):
            field_cls = PolyRelated
        else:
            column = prop.columns[0]
            field_cls = self._get_field_class_for_column(column)
        return field_cls


class PolySchemaMeta(ModelSchemaMeta):
    @classmethod
    def get_declared_fields(mcs, klass, cls_fields, inherited_fields, dict_cls):
        """Updates declared fields with fields converted from the SQLAlchemy model
        passed as the `model` class Meta option.
        """
        declared_fields = dict_cls()
        opts = klass.opts
        converter = PolyModelConverter(schema_cls=klass)
        base_fields = SchemaMeta.get_declared_fields(
            klass, cls_fields, inherited_fields, dict_cls
        )

        # klass.reupdate_fields(klass)
        poly_model = getattr(klass, 'poly_model', opts.model)
        poly_fields = getattr(klass, 'poly_fields', opts.fields)
        declared_fields = mcs.get_fields(converter, opts, base_fields, dict_cls, poly_model, poly_fields)
        declared_fields.update(base_fields)
        return declared_fields

    @classmethod
    def get_fields(mcs, converter, opts, base_fields, dict_cls, poly_model, poly_fields):
        if poly_model is not None:
            return converter.fields_for_model(
                poly_model,
                fields=poly_fields,
                exclude=opts.exclude,
                include_fk=opts.include_fk,
                base_fields=base_fields,
                dict_cls=dict_cls,
            )
        return dict_cls()


class PolySchema(with_metaclass(PolySchemaMeta, ModelSchema)):

    def reupdate_fields(self):
        fields = self.opts.fields
        if fields:
            #ic(fields)
            model_fields = set(dir(self.get_model()))
            #ic([f for f in model_fields if not f.startswith('_')])
            self.poly_fields = list(set(fields).intersection(model_fields))
            #ic(self.poly_fields)

        self.declared_fields = self.__class__.get_declared_fields(
            klass=self,
            cls_fields=[],
            inherited_fields=[],#[list(self.declared_fields.items())],
            dict_cls=self.dict_class
        )

    @pre_dump(pass_many=False)
    def pre_dump_update_opts(self, obj):

        mapper = obj.__mapper__
        self.poly_model = mapper.entity

        self.reupdate_fields()

        return obj

    @pre_load(pass_many=True)
    def dump_only_exception(self, *args, **kwargs):
        raise Exception('Trying to load with a dump only polymorphic schema.')

    def _update_fields(self, obj=None, many=False):
        """Update fields based on the passed in object."""
        opts_fields = getattr(self, 'poly_fields', self.opts.fields)
        if self.only:
            # Return only fields specified in only option
            if opts_fields:
                field_names = self.set_class(opts_fields) & self.set_class(self.only)
            else:
                field_names = self.set_class(self.only)
        elif opts_fields:
            # Return fields specified in fields option
            field_names = self.set_class(opts_fields)
        elif self.opts.additional:
            # Return declared fields + additional fields
            field_names = (self.set_class(self.declared_fields.keys()) |
                            self.set_class(self.opts.additional))
        else:
            field_names = self.set_class(self.declared_fields.keys())

        # If "exclude" option or param is specified, remove those fields
        excludes = set(self.opts.exclude) | set(self.exclude)
        if excludes:
            field_names = field_names - excludes
        ret = self._BaseSchema__filter_fields(field_names, obj, many=many)
        
        # Set parents
        self._BaseSchema__set_field_attrs(ret)
        self.fields = ret
        return self.fields

    def get_model(self):
        return getattr(self, 'poly_model', self.opts.model)
