#!/usr/bin/env python

import datetime
import hashlib, bcrypt, os

from app import db

class IsAuthenticated(db.QuerySet):
    def is_authenticated(): return True

class User(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now(), required=True)
    email = db.EmailField(required=True)
    username = db.StringField(max_length=64, required=True)
    password = db.StringField(required=True)

    def encrypt(self, raw_password):
        # Salt and hashes must be encoded to base64
        # to compensate for MongoEngine's incompetence <3
        raw_password = raw_password.encode('base64', 'strict')
        algorithm = 'bcrypt'

        hash = bcrypt.hashpw(raw_password, bcrypt.gensalt(12))
        hash = hash.encode('base64', 'strict')
        password = '%s$%s' % (algorithm, hash)
        return password

    def clean(self):
        if User.objects(email=self.email):
            raise Exception('Email is already in use!')
        if User.objects(username=self.username):
            raise Exception('Username is already in use!')

        self.password = self.encrypt(self.password)

    def is_active(): return True
    def get_id(self): return unicode(self.id)
    def __unicode__(self): return self.username

    meta = {
        'allow_inheritance': True,
        'ordering': ['-created_at'],
        'queryset_class': IsAuthenticated,
    }

class Post(db.Document):
    id = db.IntField(primary_key=True, min_value=1, required=True)
    created_at = db.DateTimeField(default=datetime.datetime.now(), required=True)
    title = db.StringField(max_length=255, required=True, null=False)
    body = db.StringField(required=True, null=False)
    author = db.ReferenceField(User)

    def clean(self):
        if self.title == None or self.body == None:
            raise Exception('Field left empty!')

    def __unicode__(self): return self.title

    meta = {
        'ordering': ['created_at']
    }

class Draft(db.Document):
    created_at = db.DateTimeField(default=datetime.datetime.now(), required=True)
    title = db.StringField(max_length=255, required=True)
    body = db.StringField(required=True)
    author = db.ReferenceField(User)

    def clean(self):
        if self.title == None or self.body == None:
            raise Exception('Field left empty!')

    def __unicode__(self): return self.title
    meta = {
        'ordering': ['-created_at']
    }
